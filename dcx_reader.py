import os
import zlib
from .binary_file_reader import BinaryFileReader


class DcxReader(BinaryFileReader):
    def __init__(self, path):
        super().__init__(path)
        self.endian = "big"

    def extract_file(self):
        self.consume(b"DCX\x00")
        self.consume(0x10000, 4)
        self.consume(0x18, 4)
        self.consume(0x24, 4)
        self.consume(0x24, 4)
        self.data["header_size"] = self.read_int32()

        self.consume(b"DCS\x00")
        self.data["uncompressed_size"] = self.read_int32()
        self.data["compressed_size"] = self.read_int32()

        self.consume(b"DCP\x00DFLT")
        self.file.seek(24, os.SEEK_CUR) # skip unknown bytes
        self.consume(b"DCA\x00")
        self.data["header_size"] = self.read_int32()

        compressed_data = self.read(self.data['compressed_size'])
        decompressed_data = zlib.decompress(compressed_data)
        open(self.file.name.replace(".dcx", ".bnd3"), 'wb').write(decompressed_data)
