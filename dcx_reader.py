import zlib
import io
from _collections import OrderedDict
from binary_file import BinaryFile
from bnd3_reader import BND3Reader


class DCXReader(BinaryFile):
    MAGIC_HEADER = b"DCX\x00"

    def __init__(self, file, path):
        super().__init__(file, path)
        self.endian = "big"

    def process_file(self):
        print("DCX: Reading file {}".format(self.path))

        manifest = {
            "header": OrderedDict([
                ("dcx_signature", self.consume(self.MAGIC_HEADER)),
                ("unknown1", self.consume(0x10000, 4)),
                ("unknown2", self.consume(0x18, 4)),
                ("unknown3", self.consume(0x24, 4)),
                ("unknown4", self.consume(0x24, 4)),
                ("dcs_header_size", self.read(4)),
                ("dcs_signature", self.consume(b"DCS\x00")),
                ("uncompressed_size", self.read(4)),
                ("compressed_size", self.read(4)),
                ("dcp_signature", self.consume(b"DCP\x00DFLT")),
                ("unknown5", self.read(24)),
                ("dca_signature", self.consume(b"DCA\x00")),
                ("dca_header_size", self.read(4)),
            ]),
        }

        manifest["end_header_pos"] = self.file.tell()

        compressed_data = self.read(self.to_int32(manifest['header']['compressed_size']))
        uncompressed_data = zlib.decompress(compressed_data)
        if len(uncompressed_data) != self.to_int32(manifest['header']['uncompressed_size']):
            msg = "Expected uncompressed size {:02x}, got {:02x}".format(
                manifest['header']['uncompressed_size'],
                len(uncompressed_data)
            )
            raise ValueError(msg)

        uncompressed_filename = self.path.replace(".dcx", "")
        manifest['uncompressed_filename'] = uncompressed_filename

        if uncompressed_filename.endswith("bnd"):
            with io.BytesIO(uncompressed_data) as bnd3_buffer:
                manifest['bnd'] = BND3Reader(bnd3_buffer, uncompressed_filename).process_file()
        else:
            self.write_data(uncompressed_filename, uncompressed_data)

        return manifest
