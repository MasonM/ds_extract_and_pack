import os
import io
import zlib
from _collections import OrderedDict

from lib.bnd3_file import BND3File
from lib.binary_file import BinaryFile


class DCXFile(BinaryFile):
    MAGIC_HEADER = b"DCX\x00"

    def __init__(self, file, path):
        super().__init__(file, path)
        self.endian = "big"

    def extract_file(self, base_dir):
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
            "end_header_pos": self.file.tell(),
        }

        compressed_data = self.read(self.to_int32(manifest['header']['compressed_size']))
        uncompressed_data = zlib.decompress(compressed_data)
        if len(uncompressed_data) != self.to_int32(manifest['header']['uncompressed_size']):
            msg = "Expected uncompressed size {:02x}, got {:02x}".format(
                manifest['header']['uncompressed_size'],
                len(uncompressed_data)
            )
            raise ValueError(msg)

        uncompressed_filename = os.path.join(base_dir, os.path.basename(self.path).replace(".dcx", ""))
        manifest['uncompressed_filename'] = uncompressed_filename

        if uncompressed_filename.endswith("bnd"):
            with io.BytesIO(uncompressed_data) as bnd3_buffer:
                manifest['bnd'] = BND3File(bnd3_buffer, uncompressed_filename).extract_file(base_dir)
        else:
            self.write_data(uncompressed_filename, uncompressed_data)

        return manifest

    def create_file(self, manifest):
        print("DCX: Writing file {}".format(self.path))

        self.file.seek(manifest['end_header_pos'])

        cur_position = self.file.tell()
        print("DCX: Writing uncompressed file {} at offset {}".format(manifest['uncompressed_filename'], cur_position))
        if "bnd" in manifest:
            with io.BytesIO() as bnd3_buffer:
                BND3File(bnd3_buffer, manifest['uncompressed_filename']).create_file(manifest['bnd'])
                bnd3_buffer.seek(0)
                uncompressed_data = bnd3_buffer.read()
        else:
            uncompressed_data = open(manifest['uncompressed_filename'], "rb").read()

        manifest['header']['uncompressed_size'] = self.int32_bytes(len(uncompressed_data))

        compressed_data = zlib.compress(uncompressed_data)
        manifest['header']['compressed_size'] = self.int32_bytes(len(compressed_data))
        self.write(compressed_data)

        self.file.seek(0)
        self.write_header(manifest)
