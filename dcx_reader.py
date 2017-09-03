import zlib
from .binary_file import BinaryFile
from .bnd3_reader import BND3Reader


class DcxReader(BinaryFile):
    MAGIC_HEADER = b"DCX\x00"

    def __init__(self, file, base_dir=None):
        super().__init__(file, base_dir)
        self.endian = "big"

    def process_file(self):
        manifest = {
            "header": {
                "dcx_signature": self.consume(self.MAGIC_HEADER),
                "unknown1": self.consume(0x10000, 4),
                "unknown2": self.consume(0x18, 4),
                "unknown3": self.consume(0x24, 8),
                "dcs_header_size": self.read(4),
                "dcs_signature": self.consume(b"DCS\x00"),
                "uncompressed_size": self.read(4),
                "compressed_size": self.read(4),
                "dcp_signature": self.consume(b"DCP\x00DFLT"),
                'unknown4': self.read(24),
                "dca_signature": self.consume(b"DCA\x00"),
                "dca_header_size": self.read(4),
            }
        }

        compressed_data = self.read(self.to_int32(manifest['header']['compressed_size']))
        decompressed_data = zlib.decompress(compressed_data)
        decompressed_filename = self.path.replace(".dcx", "")
        self.write(decompressed_filename, decompressed_data)

        if decompressed_filename.endswith("bnd"):
            bnd3_reader = BND3Reader(decompressed_filename, self.base_dir)
            manifest['bnd'] = bnd3_reader.process_file()
            bnd3_reader.remove()

        return manifest
