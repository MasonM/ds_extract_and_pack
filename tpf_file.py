import os
from _collections import OrderedDict
from binary_file import BinaryFile


class TPFFile(BinaryFile):
    MAGIC_HEADER = b"TPF\x00"

    def extract_file(self):
        print("TPF: Reading file {}".format(self.path))

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
            print("TPF: Reading entry #{}".format(i))
            manifest['entries'].append(self._read_entry())

        manifest["end_header_pos"] = self.file.tell()

        return manifest

    def _read_entry(self):
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
            print("TPF: Reading data, offset = {}, size = {}, filename = {}, actual filename = {}".format(data_offset, data_size, entry['filename'], entry['actual_filename']))
            self.file.seek(data_offset)
            data = self.read(data_size)
            self.write_data(entry['actual_filename'], data)

        self.file.seek(position)

        return entry

    def create_file(self, manifest):
        print("TPF: Writing file {}".format(self.path))

        self.file.seek(manifest['end_header_pos'])

        for entry in manifest['entries']:
            print("TPF: Writing entry filename for {} at offset {}".format(entry['actual_filename'], self.file.tell()))
            entry['header']['filename_offset'] = self.int32_bytes(self.file.tell())
            self.write(entry['filename'].encode("shift_jis"), b"\x00")

        self.write(b"\x00" * 48) # padding

        size_sum = 0
        for entry in manifest['entries']:
            print("TPF: Writing entry data for {} at offset {}".format(entry['actual_filename'], self.file.tell()))
            entry['header']['data_size'] = self.int32_bytes(os.path.getsize(entry['actual_filename']))
            size_sum += self.to_int32(entry['header']['data_size'])
            entry['header']['data_offset'] = self.int32_bytes(self.file.tell())
            self.write(open(entry['actual_filename'], 'rb').read())

        self.file.seek(0)
        manifest['header']['size_sum'] = self.int32_bytes(size_sum)
        self.write_header(manifest)

        for entry in manifest['entries']:
            print("TPF: Writing entry header for {} at offset {}".format(entry['actual_filename'], self.file.tell()))
            self.write_header(entry)
