import io

from .binary_file import BinaryFile, Manifest
from . import filesystem, utils


class BND3File(BinaryFile):
    MAGIC_HEADER = b"BND3"

    def extract_file(self, depth):
        self.log("Reading file {}".format(self.path), depth)

        manifest = Manifest(self, header=[
            ("signature", self.consume(self.MAGIC_HEADER)),
            ("id", self.read(8)),
            ("flags", self.read(4)),
            ("record_count", self.read(4)),
            ("header_size", self.read(4)),
            ("padding", self.consume(0x0, 8)),
        ])
        manifest.records = []

        if manifest.int32('flags') not in (0x74, 0x54, 0x70):
            raise ValueError("Invalid flags: {:02X}".format(manifest.int32('flags')))

        for i in range(manifest.int32('record_count')):
            self.log("Reading record #{}".format(i), depth)
            manifest.records.append(self._read_record(manifest.int32('flags'), depth + 1))

        manifest.end_header_pos = self.file.tell()

        return manifest

    def _read_record(self, flags, depth):
        record = Manifest(self, header=[
            ("record_sep", self.consume(0x40, 4)),
            ('data_size', self.read(4)),
            ('data_offset', self.read(4)),
            ('id', self.read(4)),
            ("filename_offset", self.read(4)),
        ])

        if flags in (0x74, 0x54):
            record.header['redundant_size'] = self.read(4)
            if record.header['redundant_size'] != record.header['data_size']:
                raise ValueError("Expected size {}, got {}".format(
                    record.header['data_size'],
                    record.header['redundant_size'])
                )

        position = self.file.tell()
        if record.int32('filename_offset') > 0:
            self.file.seek(record.int32('filename_offset'))
            record.filename = self.read_null_terminated_string()
            record.path = filesystem.normalize_filepath(record.filename)
            # self.log("got filename %s" % record['filename'])

        if record.int32('data_offset') > 0:
            self.file.seek(record.int32('data_offset'))
            self.log("Reading data, size = {}, filename = {}".format(record.int32('data_size'), record.filename), depth)
            data = self.read(record.int32('data_size'))
            file_cls = utils.class_for_data(data)
            if file_cls:
                record.sub_manifest = file_cls(io.BytesIO(data), record.path).extract_file(depth + 1)
            else:
                self.log("Writing data to {}".format(record.path), depth)
                filesystem.write_data(record.path, data)

        self.file.seek(position)

        return record

    def create_file(self, manifest, depth):
        self.log("Writing file {}".format(self.path), depth)

        self.file.seek(manifest.end_header_pos)

        for record in manifest.records:
            self.log("Writing record filename for {}".format(record.path), depth)
            record.header['filename_offset'] = self.int32_bytes(self.file.tell())
            self.write(record.filename.encode("shift_jis"), b"\x00")

        manifest.header['header_size'] = self.int32_bytes(self.file.tell())

        self.pad_to_hex_boundary()

        for record in manifest.records:
            cur_position = self.file.tell()
            self.log("Writing record data for {}".format(record.path), depth)
            record.header['data_offset'] = self.int32_bytes(cur_position)

            if hasattr(record, 'sub_manifest'):
                self.write(record.sub_manifest.get_data(record.path, depth + 1))
            else:
                self.write(filesystem.read_data(record.path))

            data_size = self.file.tell() - cur_position
            record.header['data_size'] = self.int32_bytes(data_size)
            if manifest.int32('flags') in (0x74, 0x54):
                record.header['redundant_size'] = record.header['data_size']

            if record != manifest.records[-1]:
                self.pad_to_hex_boundary()

        self.file.seek(0)
        self.write_header(manifest)

        for record in manifest.records:
            self.log("Writing record header for {}".format(record.path), depth)
            self.write_header(record)
