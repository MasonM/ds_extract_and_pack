import os

from .binary_file import BinaryFile
from .name_hash_handler import get_name_from_hash


class BHD5File(BinaryFile):
    MAGIC_HEADER = b"BHD5"

    def extract_file(self, depth):
        self.log("Parsing file {}".format(self.path), depth)

        manifest = self.manifest(header=[
            ("signature", self.consume(self.MAGIC_HEADER)),
            ("unknown1", self.consume(b"\xff\x00\x00\x00\x01\x00\x00\x00")),
            ("file_size", self.read(4)),
            ("bin_count", self.read(4)),
            ("bin_record_offset", self.read(4)),
        ])
        manifest.records = []
        manifest.bin_records = []
        manifest.actual_header_filename = self.path

        # self.log(self.to_int32(manifest['header']['file_size']), depth)

        for i in range(manifest.int32('bin_count')):
            self.log("Reading bin #{}".format(i), depth)
            bin_record = self._read_bin(depth)
            manifest.bin_records.append(bin_record)
            # Add ability to iterate over records for uniformity with BHF3File
            manifest.records += bin_record.records

        self.file.close()

        return manifest

    def _read_bin(self, depth):
        bin_record = self.manifest(header=[
            ("record_count", self.read(4)),
            ("offset", self.read(4)),
        ])
        bin_record.records = []

        position = self.file.tell()
        self.file.seek(bin_record.int32('offset'))
        for i in range(bin_record.int32('record_count')):
            bin_record.records.append(self._read_record())
        self.file.seek(position)

        return bin_record

    def _read_record(self):
        record = self.manifest(header=[
            ('record_hash', self.read(4)),
            ('record_size', self.read(4)),
            ('record_offset', self.read(4)),
            ('padding', self.consume(0x0, 4)),
        ])

        record_hash = record.int32('record_hash')
        try:
            record.record_name = get_name_from_hash(record_hash).lstrip("/").replace("/", os.sep)
        except KeyError:
            raise ValueError("Failed to find {} in name hash dict".format(record_hash))

        filepath = self.normalize_filepath(record.record_name)
        record.actual_filename = filepath

        return record

    def create_file(self, manifest, depth):
        self.log("Writing file {}".format(self.path), depth)

        self.write_header(manifest)
        for bin_record in manifest.bin_records:
            self.write_header(bin_record)
            position = self.file.tell()
            self.file.seek(bin_record.int32('offset'))
            for record in bin_record.records:
                self.write_header(record)
            self.file.seek(position)
