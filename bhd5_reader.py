import os
import pprint
from .binary_file import BinaryFile
from .name_hash_handler import build_name_hash_dict


class BHD5Reader(BinaryFile):
    MAGIC_HEADER = b"BHD5\xff"

    def process_file(self):
        self.name_hash_dict = build_name_hash_dict()

        manifest = {
            "header": {
                "signature": self.consume(self.MAGIC_HEADER),
                "unknown1": self.consume(b"\x00\x00\x00\x01\x00\x00\x00"),
                "file_size": self.read(4),
                "bin_count": self.read(4),
                "bin_record_offset": self.read(4),
            },
            "bins": [],
        }

        for i in range(self.to_int32(manifest["header"]['bin_count'])):
            print("BHD5: Reading bin #{}".format(i))
            manifest["bins"].append(self.read_bin())

        self.file.close()
        #pprint.pprint(self.data)
        return manifest

    def read_bin(self):
        bin_data = {
            "header": {
                "record_count": self.read(4),
                "offset": self.read(4),
            },
            "records": [],
        }

        position = self.file.tell()
        self.file.seek(self.to_int32(bin_data['header']['offset']))

        for i in range(self.to_int32(bin_data['header']['record_count'])):
            bin_data['records'].append(self.read_record())

        self.file.seek(position)
        return bin_data

    def read_record(self):
        entry = {
            "header": {
                'record_hash': self.read(4),
                'record_size': self.read(4),
                'record_offset': self.read(4),
                'padding': self.consume(0x0, 4),
            },
        }

        record_hash = self.to_int32(entry['header']['record_hash'])
        if record_hash not in self.name_hash_dict:
            raise ValueError("Failed to find {} in name hash dict".format(record_hash))

        entry['record_name'] = self.name_hash_dict[record_hash].lstrip("/").replace("/", os.sep)

        return entry
