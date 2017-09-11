from _collections import OrderedDict

from .binary_file import BinaryFile


class BHF3File(BinaryFile):
    MAGIC_HEADER = b"BHF3"

    def extract_file(self, depth):
        self.log("Parsing file {}".format(self.path), depth)

        manifest = {
            "header": OrderedDict([
                ("signature", self.consume(self.MAGIC_HEADER)),
                ("id", self.consume(b"07D7R6\x00\x00")),
                ("version", self.read(4)),
                ("record_count", self.read(4)),
                ("header_size", self.read(4)),
                ("padding2", self.consume(0x0, 8)),
            ]),
            "records": [],
        }

        if self.to_int32(manifest['header']['version']) not in (0x74, 0x54):
            raise ValueError("Invalid version: {:02X}".format(manifest['header']['version']))

        for i in range(self.to_int32(manifest['header']['record_count'])):
            manifest['records'].append(self._read_record(depth))

        self.file.close()
        #pprint.pprint(self.data)
        return manifest

    def _read_record(self, depth):
        entry = {
            "header": OrderedDict([
                ("record_separator", self.consume(0x40, 4)),
                ('record_size', self.read(4)),
                ('record_offset', self.read(4)),
                ('id', self.read(4)),
                ('filename_offset', self.read(4)),
                ('redundant_size', self.read(4)),
            ]),
        }

        if entry['header']['record_size'] != entry['header']['redundant_size']:
            raise ValueError("Data sizes don't match: {} != {}".format(entry['header']['record_size'], entry['header']['redundant_size']))

        position = self.file.tell()
        self.file.seek(self.to_int32(entry['header']['filename_offset']))

        entry['record_name'] = self.read_null_terminated_string()
        if not entry['record_name']:
            raise ValueError("Got empty record name")
        entry['actual_filename'] = self.normalize_filepath(entry['record_name'])

        self.file.seek(position)
        return entry

    def create_file(self, manifest, depth):
        self.log("Writing file {}".format(self.path), depth)

        self.write_header(manifest)
        for record_data in manifest['records']:
            self.write_header(record_data)
            current_position = self.file.tell()
            self.file.seek(self.to_int32(record_data['header']['filename_offset']))
            self.write(record_data['record_name'].encode("shift_jis"), b"\x00")
            self.file.seek(current_position)
