import io
from _collections import OrderedDict

from .binary_file import BinaryFile
from . import utils


class BND3File(BinaryFile):
    MAGIC_HEADER = b"BND3"

    def extract_file(self, depth):
        self.log("Reading file {}".format(self.path), depth)

        manifest = {
            "header": OrderedDict([
                ("signature", self.consume(self.MAGIC_HEADER)),
                ("unknown_bytes", self.read(8)),
                ("version", self.read(4)),
                ("entry_count", self.read(4)),
                ("header_size", self.read(4)),
                ("padding", self.consume(0x0, 8)),
            ]),
            "entries": [],
        }

        version = self.to_int32(manifest['header']['version'])
        if version not in (0x74, 0x54, 0x70):
            raise ValueError("Invalid version: {:02X}".format(manifest['header']['version']))

        for i in range(self.to_int32(manifest['header']['entry_count'])):
            self.log("Reading entry #{}".format(i), depth)
            manifest['entries'].append(self._read_entry(version, depth + 1))

        manifest["end_header_pos"] = self.file.tell()

        return manifest

    def _read_entry(self, version, depth):
        entry = {
            "header": OrderedDict([
                ("record_sep", self.consume(0x40, 4)),
                ('data_size', self.read(4)),
                ('data_offset', self.read(4)),
                ('id', self.read(4)),
                ("filename_offset", self.read(4)),
            ]),
        }

        if version in (0x74, 0x54):
            entry['header']['redundant_size'] = self.read(4)
            if entry['header']['redundant_size'] != entry['header']['data_size']:
                raise ValueError("Expected size {:02x}, got {:02x}".format(
                    entry['header']['data_size'],
                    entry['header']['redundant_size'])
                )

        position = self.file.tell()
        filename_offset = self.to_int32(entry['header']['filename_offset'])
        if filename_offset > 0:
            self.file.seek(filename_offset)
            entry['filename'] = self.read_null_terminated_string()
            entry['actual_filename'] = self.normalize_filepath(entry['filename'])
            # self.log("got filename %s" % entry['filename'])

        data_offset = self.to_int32(entry['header']['data_offset'])
        data_size = self.to_int32(entry['header']['data_size'])
        if data_offset > 0:
            self.file.seek(data_offset)
            self.log("Reading data, size = {}, filename = {}".format(data_size, entry['filename']), depth)
            data = self.read(data_size)
            file_cls = utils.class_for_data(data)
            if file_cls:
                entry['sub_manifest'] = file_cls(io.BytesIO(data), entry['actual_filename']).extract_file(depth + 1)
            else:
                self.log("Writing data to {}".format(entry['actual_filename']), depth)
                utils.write_data(entry['actual_filename'], data)

        self.file.seek(position)

        return entry

    def create_file(self, manifest, depth):
        self.log("Writing file {}".format(self.path), depth)

        self.file.seek(manifest['end_header_pos'])

        for entry in manifest['entries']:
            self.log("Writing entry filename for {}".format(entry['actual_filename']), depth)
            entry['header']['filename_offset'] = self.int32_bytes(self.file.tell())
            self.write(entry['filename'].encode("shift_jis"), b"\x00")

        manifest['header']['header_size'] = self.int32_bytes(self.file.tell())
        self.write(b"\x00" * 4) # padding

        for entry in manifest['entries']:
            cur_position = self.file.tell()
            self.log("Writing entry data for {}".format(entry['actual_filename']), depth)
            entry['header']['data_offset'] = self.int32_bytes(cur_position)

            if 'sub_manifest' in entry:
                self.write(utils.get_data_for_file(entry['sub_manifest'], entry['actual_filename'], depth + 1))
            else:
                self.write(open(entry['actual_filename'], "rb").read())

            data_size = self.file.tell() - cur_position
            entry['header']['data_size'] = self.int32_bytes(data_size)
            if self.to_int32(manifest['header']['version']) in (0x74, 0x54):
                entry['header']['redundant_size'] = entry['header']['data_size']

        self.file.seek(0)
        self.write_header(manifest)

        for entry in manifest['entries']:
            self.log("Writing entry header for {}".format(entry['actual_filename']), depth)
            self.write_header(entry)
