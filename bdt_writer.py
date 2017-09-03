import os
import pickle
from .binary_file_writer import BinaryFileWriter, to_int32
from .tpf_reader import TpfReader


class BdtWriter(BinaryFileWriter):
    def __init__(self, manifest_path, path, base_dir):
        super().__init__(path, base_dir)

    def write_file(self):
        print("BDT: Writing file {}".format(self.path))
