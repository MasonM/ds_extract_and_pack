import os
import pickle
from .binary_file_writer import BinaryFileWriter, to_int32


class TpfWriter(BinaryFileWriter):
    def __init__(self, metadata_path):
        self.metadata = pickle.load(open(metadata_path, "rb"))
        tpf_filename = os.path.basename(metadata_path).split(".")[0] + "_new.tpf"
        print(self.metadata)
        super().__init__(tpf_filename)

    def write_file(self):
        print("Writing TPF file {}".format(self.file.name))
        self.write(
            self.metadata['signature'],
            to_int32(self.metadata['size_sum']),
            to_int32(self.metadata['entry_count']),
            self.metadata['flag1'],
            self.metadata['flag2'],
            self.metadata['encoding'],
            self.metadata['flag3'],
        )

        for entry in self.metadata['entries']:
            self.file.close()

    def write_entry(self, entry):
        print("Writing entry #{}".format(entry))
        self.write(
            to_int32(entry['data_offset']),
            to_int32(entry['data_size']),
            entry['format'],
            entry['type'],
            entry['mipmap_count'],
            entry['flags'],
            to_int32(entry['filename_offset']),
            to_int32(entry['unknown']),
        )

        position = self.file.tell()
        if entry['filename_offset'] > 0:
            print("Writing filename, offset = {}".format(entry['filename_offset']))
            self.file.seek(entry['filename_offset'])
            self.write(entry['filename'].encode("ascii"))

        if entry['data_offset'] > 0:
            print("Writing data, offset = {}, size = {}".format(entry['data_offset'], entry['data_size']))
            self.file.seek(entry['data_offset'])
            data = open(entry['filename'] + ".dds", 'rb')
            self.write(data.read())

        self.file.seek(position)
