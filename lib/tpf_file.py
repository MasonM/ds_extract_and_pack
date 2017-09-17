from .binary_file import BinaryFile, Manifest
from . import filesystem


class TPFFile(BinaryFile):
    MAGIC_HEADER = b"TPF\x00"

    def extract_file(self, depth):
        self.log("Reading file {}".format(self.path), depth)

        manifest = Manifest(self, header=[
            ('signature', self.consume(self.MAGIC_HEADER)),
            ("size_sum", self.read(4)),
            ("record_count", self.read(4)),
            ("flags", self.consume(0x20300, 4)),
        ])
        manifest.records = []

        for i in range(manifest.int32('record_count')):
            self.log("Reading record #{}".format(i), depth)
            manifest.records.append(self._read_record(depth + 1))

        manifest.end_header_pos = self.file.tell()

        return manifest

    def _read_record(self, depth):
        record = Manifest(self, header=[
            ('data_offset', self.read(4)),
            ('data_size', self.read(4)),
            ('id', self.read(4)),
            ('filename_offset', self.read(4)),
            ('padding', self.consume(0x0, 4)),
        ])

        position = self.file.tell()
        if record.int32('filename_offset') > 0:
            self.file.seek(record.int32('filename_offset'))
            record.filename = self.read_null_terminated_string()

        if record.int32('data_offset') > 0:
            record.path = filesystem.normalize_filepath(record.filename) + ".dds"
            self.file.seek(record.int32('data_offset'))
            self.log("Reading data, size = {}, filename = {}, actual filename = {}".format(
                record.int32('data_size'),
                record.filename,
                record.path
            ), depth)
            data = self.read(record.int32('data_size'))
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

        padding = (16 * len(manifest.records))
        self.write(b"\x00" * padding)

        size_sum = 0
        for record in manifest.records:
            self.log("Writing record data for {}".format(record.path), depth)
            data = filesystem.read_data(record.path)
            record.header['data_size'] = self.int32_bytes(len(data))
            size_sum += record.int32('data_size')
            record.header['data_offset'] = self.int32_bytes(self.file.tell())
            self.write(data)

        self.file.seek(0)
        manifest.header['size_sum'] = self.int32_bytes(size_sum)
        self.write_header(manifest)

        for record in manifest.records:
            self.log("Writing record header for {}".format(record.path), depth)
            self.write_header(record)
