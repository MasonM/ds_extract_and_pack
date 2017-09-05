from _collections import OrderedDict

from .binary_file import BinaryFile
from . import utils


class BHF3File(BinaryFile):
    MAGIC_HEADER = b"BHF3"

    def extract_file(self):
        self.log("BHF3: Parsing file {}".format(self.path))

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
            manifest['records'].append(self._read_record())

        self.file.close()
        #pprint.pprint(self.data)
        return manifest

    def _read_record(self):
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
        entry['actual_filename'] = self.normalize_filepath(entry['record_name'])

        self.file.seek(position)
        return entry

    def create_file(self, manifest, depth):
        self.log("BHF3: Writing file {}".format(self.path))

        self.write_header(manifest)
        for record_data in manifest['records']:
            self.write_header(record_data)
