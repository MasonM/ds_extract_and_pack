import os
import io
import zlib
from _collections import OrderedDict

from lib.binary_file import BinaryFile
import lib.utils


class DCXFile(BinaryFile):
    MAGIC_HEADER = b"DCX\x00"

    def __init__(self, file, path):
        super().__init__(file, path)
        self.endian = "big"

    def extract_file(self, base_dir):
        print("DCX: Reading file {}".format(self.path))

        manifest = {
            "header": OrderedDict([
                ("signature", self.consume(self.MAGIC_HEADER)),
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

        file_cls = lib.utils.class_for_data(uncompressed_data)
        if file_cls:
            manifest['sub_manifest'] = file_cls(io.BytesIO(uncompressed_data), uncompressed_filename).extract_file(base_dir)
        else:
            lib.utils.write_data(uncompressed_filename, uncompressed_data)

        return manifest

    def create_file(self, manifest):
        print("DCX: Writing file {}".format(self.path))

        self.file.seek(manifest['end_header_pos'])

        cur_position = self.file.tell()
        print("DCX: Writing uncompressed file {} at offset {}".format(manifest['uncompressed_filename'], cur_position))
        if 'sub_manifest' in manifest:
            uncompressed_data = lib.utils.get_data_for_file(manifest['sub_manifest'], manifest['uncompressed_filename'])
        else:
            uncompressed_data = open(manifest['uncompressed_filename'], "rb").read()

        manifest['header']['uncompressed_size'] = self.int32_bytes(len(uncompressed_data))

        compressed_data = zlib.compress(uncompressed_data)
        manifest['header']['compressed_size'] = self.int32_bytes(len(compressed_data))
        self.write(compressed_data)

        self.file.seek(0)
        self.write_header(manifest)
