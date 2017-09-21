import io
import os
import zlib

import config
import lib


class DCXFile(lib.BinaryFile):
    MAGIC_HEADER = b"DCX\x00"

    def __init__(self, file, path):
        super().__init__(file, path)
        self.endian = "big"

    def extract_file(self, depth):
        self.log("Reading file {}".format(self.path), depth)

        manifest = lib.Manifest(self, header=[
            ("signature", self.expect(self.MAGIC_HEADER)),
            ("unknown1", self.expect(0x10000, 4)),
            ("dcs_offset", self.expect(0x18, 4)),
            ("dcp_offset", self.expect(0x24, 4)),
            ("redundant_dcp_offset", self.expect(0x24, 4)),
            ("dcs_header_size", self.expect(0x2c, 4)),
            ("dcs_signature", self.expect(b"DCS\x00")),
            ("uncompressed_size", self.read(4)),
            ("compressed_size", self.read(4)),
            ("dcp_signature", self.expect(b"DCP\x00")),
            ("dcp_method", self.expect(b"DFLT")),
            ("dca_offset", self.expect(0x20, 4)),
            ("compression_level", self.expect(0x09000000, 4)),
            ("unknown2", self.expect(0x0, 12)),
            ("zlib_version", self.expect(0x00010100, 4)),
            ("dca_signature", self.expect(b"DCA\x00")),
            ("dca_header_size", self.expect(0x8, 4)),
        ])
        manifest.end_header_pos = self.file.tell()

        compressed_data = self.read(manifest.int32('compressed_size'))
        uncompressed_data = zlib.decompress(compressed_data)
        if len(uncompressed_data) != manifest.int32('uncompressed_size'):
            msg = "Expected uncompressed size {}, got {}".format(
                manifest.int32('uncompressed_size'),
                len(uncompressed_data)
            )
            raise ValueError(msg)

        uncompressed_filename = lib.filesystem.normalize_filepath(os.path.basename(self.path)[:-4], self.path)
        manifest.uncompressed_filename = uncompressed_filename

        file_cls = self.class_for_data(uncompressed_data)
        if file_cls:
            manifest.sub_manifest = file_cls(io.BytesIO(uncompressed_data), uncompressed_filename).extract_file(depth + 1)
        else:
            self.log("Writing fixed_data to {}".format(uncompressed_filename), depth)
            lib.filesystem.write_data(uncompressed_filename, uncompressed_data)

        return manifest

    def create_file(self, manifest, depth):
        self.log("Writing file {}".format(self.path), depth)

        self.file.seek(manifest.end_header_pos)

        if hasattr(manifest, 'sub_manifest'):
            uncompressed_data = manifest.sub_manifest.get_data(manifest.uncompressed_filename, depth + 1)
        else:
            uncompressed_data = lib.filesystem.read_data(manifest.uncompressed_filename)

        manifest.header['uncompressed_size'] = self.int32_bytes(len(uncompressed_data))

        compressed_data = zlib.compress(uncompressed_data, config.zlib_compression_level)

        manifest.header['compressed_size'] = self.int32_bytes(len(compressed_data))
        self.write(compressed_data)

        self.file.seek(0)
        self.write_header(manifest)
