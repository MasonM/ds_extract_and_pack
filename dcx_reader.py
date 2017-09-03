import zlib
import io
from binary_file import BinaryFile
from bnd3_reader import BND3Reader


class DcxReader(BinaryFile):
    MAGIC_HEADER = b"DCX\x00"

    def __init__(self, file, base_dir=None):
        super().__init__(file, base_dir)
        self.endian = "big"

    def process_file(self):
        print("DCX: Reading file {}".format(self.path))

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
        if len(decompressed_data) != self.to_int32(manifest['header']['uncompressed_size']):
            msg = "Expected decompressed size {:02x}, got {:02x}".format(
                manifest['header']['uncompressed_size'],
                len(decompressed_data)
            )
            raise ValueError(msg)

        decompressed_filename = self.path.replace(".dcx", "")

        if decompressed_filename.endswith("bnd"):
            with io.BytesIO(decompressed_data) as bnd3_buffer:
                manifest['bnd'] = BND3Reader(bnd3_buffer, decompressed_filename).process_file()
        else:
            self.write_data(decompressed_filename, decompressed_data)

        return manifest
