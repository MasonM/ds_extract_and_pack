import io
import zlib
from binary_file import BinaryFile
from bnd3_writer import BND3Writer


class DCXWriter(BinaryFile):
    def __init__(self, file, path):
        super().__init__(file, path)
        self.endian = "big"

    def process_file(self, manifest):
        print("DCX: Writing file {}".format(self.path))

        self.file.seek(manifest['end_header_pos'])

        cur_position = self.file.tell()
        print("DCX: Writing uncompressed file {} at offset {}".format(manifest['uncompressed_filename'], cur_position))
        if "bnd" in manifest:
            with io.BytesIO() as bnd3_buffer:
                BND3Writer(bnd3_buffer, manifest['uncompressed_filename']).process_file(manifest['bnd'])
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
