import os
from _collections import OrderedDict

from .binary_file import BinaryFile
from . import utils


class TPFFile(BinaryFile):
    MAGIC_HEADER = b"TPF\x00"

    def extract_file(self, depth):
        self.log("Reading file {}".format(self.path), depth)

        manifest = {
            'header': OrderedDict([
                ('signature', self.consume(self.MAGIC_HEADER)),
                ("size_sum", self.read(4)),
                ("entry_count", self.read(4)),
                ("flag1", self.read(1)),
                ("flag2", self.read(1)),
                ("encoding", self.read(1)),
                ("flag3", self.read(1)),
            ]),
            'entries': [],
        }

        for i in range(self.to_int32(manifest['header']['entry_count'])):
            self.log("Reading entry #{}".format(i), depth)
            manifest['entries'].append(self._read_entry(depth + 1))

        manifest["end_header_pos"] = self.file.tell()

        return manifest

    def _read_entry(self, depth):
        entry = {
            'header': OrderedDict([
                ('data_offset', self.read(4)),
                ('data_size', self.read(4)),
                ('format', self.read(1)),
                ('type', self.read(1)),
                ('mipmap_count', self.read(1)),
                ('flags', self.read(1)),
                ('filename_offset', self.read(4)),
                ('unknown', self.read(4)),
            ]),
        }

        position = self.file.tell()
        filename_offset = self.to_int32(entry['header']['filename_offset'])
        if filename_offset > 0:
            self.file.seek(filename_offset)
            entry['filename'] = self.read_null_terminated_string()

        data_offset = self.to_int32(entry['header']['data_offset'])
        data_size = self.to_int32(entry['header']['data_size'])
        if data_offset > 0:
            entry['actual_filename'] = self.normalize_filepath(entry['filename']) + ".dds"
            self.file.seek(data_offset)
            self.log("Reading data, size = {}, filename = {}, actual filename = {}".format(data_size, entry['filename'], entry['actual_filename']), depth)
            data = self.read(data_size)
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

        padding = (16 * len(manifest['entries']))
        self.write(b"\x00" * padding)

        size_sum = 0
        for entry in manifest['entries']:
            self.log("Writing entry data for {}".format(entry['actual_filename']), depth)
            entry['header']['data_size'] = self.int32_bytes(os.path.getsize(entry['actual_filename']))
            size_sum += self.to_int32(entry['header']['data_size'])
            entry['header']['data_offset'] = self.int32_bytes(self.file.tell())
            self.write(open(entry['actual_filename'], 'rb').read())

        self.file.seek(0)
        manifest['header']['size_sum'] = self.int32_bytes(size_sum)
        self.write_header(manifest)

        for entry in manifest['entries']:
            self.log("Writing entry header for {}".format(entry['actual_filename']), depth)
            self.write_header(entry)
