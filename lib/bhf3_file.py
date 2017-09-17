from .binary_file import BinaryFile, Manifest
from . import utils


class BHF3File(BinaryFile):
    MAGIC_HEADER = b"BHF3"

    def extract_file(self, depth):
        self.log("Parsing file {}".format(self.path), depth)

        manifest = Manifest(self, header=[
            ("signature", self.consume(self.MAGIC_HEADER)),
            ("id", self.consume(b"07D7R6\x00\x00")),
            ("version", self.read(4)),
            ("record_count", self.read(4)),
            ("header_size", self.read(4)),
            ("padding", self.consume(0x0, 8)),
        ])
        manifest.records = []

        if manifest.int32('version') not in (0x74, 0x54):
            raise ValueError("Invalid version: {:02X}".format(manifest.int32('version')))

        for i in range(manifest.int32('record_count')):
            manifest.records.append(self._read_record(depth))

        self.file.close()
        return manifest

    def _read_record(self, depth):
        record = Manifest(self, header=[
            ("record_separator", self.consume(0x40, 4)),
            ('record_size', self.read(4)),
            ('record_offset', self.read(4)),
            ('id', self.read(4)),
            ('filename_offset', self.read(4)),
            ('redundant_size', self.read(4)),
        ])

        if record.header['record_size'] != record.header['redundant_size']:
            raise ValueError("Data sizes don't match: {} != {}".format(record.header['record_size'], record.header['redundant_size']))

        position = self.file.tell()
        self.file.seek(record.int32('filename_offset'))

        record.record_name = self.read_null_terminated_string()
        if not record.record_name:
            raise ValueError("Got empty record name")
        record.path = utils.normalize_filepath(record.record_name)

        self.file.seek(position)
        return record

    def create_file(self, manifest, depth):
        self.log("Writing file {}".format(self.path), depth)

        self.write_header(manifest)
        for record in manifest.records:
            self.write_header(record)
            current_position = self.file.tell()
            self.file.seek(record.int32('filename_offset'))
            self.write(record.record_name.encode("shift_jis"), b"\x00")
            self.file.seek(current_position)
