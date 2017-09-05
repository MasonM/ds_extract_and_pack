import os
from _collections import OrderedDict

from .binary_file import BinaryFile
from .name_hash_handler import get_name_from_hash
from . import utils


class BHD5File(BinaryFile):
    MAGIC_HEADER = b"BHD5"

    def extract_file(self):
        self.log("BHD5: Parsing file {}".format(self.path))

        manifest = {
            "header": OrderedDict([
                ("signature", self.consume(self.MAGIC_HEADER)),
                ("unknown1", self.consume(b"\xff\x00\x00\x00\x01\x00\x00\x00")),
                ("file_size", self.read(4)),
                ("bin_count", self.read(4)),
                ("bin_record_offset", self.read(4)),
            ]),
            "bins": [],
        }

        #self.log(self.to_int32(manifest['header']['file_size']))

        for i in range(self.to_int32(manifest["header"]['bin_count'])):
            self.log("BHD5: Reading bin #{}".format(i))
            manifest["bins"].append(self._read_bin())

        self.file.close()
        #pprint.pprint(self.data)
        return manifest

    def _read_bin(self):
        bin_data = {
            "header": OrderedDict([
                ("record_count", self.read(4)),
                ("offset", self.read(4)),
            ]),
            "records": [],
        }

        position = self.file.tell()
        self.file.seek(self.to_int32(bin_data['header']['offset']))

        for i in range(self.to_int32(bin_data['header']['record_count'])):
            bin_data['records'].append(self._read_record())

        self.file.seek(position)
        return bin_data

    def _read_record(self):
        entry = {
            "header": OrderedDict([
                ('record_hash', self.read(4)),
                ('record_size', self.read(4)),
                ('record_offset', self.read(4)),
                ('padding', self.consume(0x0, 4)),
            ]),
        }

        record_hash = self.to_int32(entry['header']['record_hash'])
        try:
            entry['record_name'] = get_name_from_hash(record_hash).lstrip("/").replace("/", os.sep)
        except KeyError:
            raise ValueError("Failed to find {} in name hash dict".format(record_hash))

        filepath = self.normalize_filepath(entry['record_name'])
        entry['actual_filename'] = filepath

        return entry

    def create_file(self, manifest):
        self.log("BHD5: Writing file {}".format(self.path))

        self.write_header(manifest)
        for bin_data in manifest['bins']:
            self.write_header(bin_data)
            position = self.file.tell()
            self.file.seek(self.to_int32(bin_data['header']['offset']))
            for record_data in bin_data['records']:
                self.write_header(record_data)
            self.file.seek(position)
