from _collections import OrderedDict
from binary_file import BinaryFile


class TpfReader(BinaryFile):
    MAGIC_HEADER = b"TPF\x00"

    def process_file(self):
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
            manifest['entries'].append(self.read_entry())

        manifest["end_header_pos"] = self.file.tell()

        return manifest

    def read_entry(self):
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

        #print(entry)

        position = self.file.tell()
        filename_offset = self.to_int32(entry['header']['filename_offset'])
        if filename_offset > 0:
            self.file.seek(filename_offset)
            entry['filename'] = self.read_null_terminated_string()

        data_offset = self.to_int32(entry['header']['data_offset'])
        data_size = self.to_int32(entry['header']['data_size'])
        if data_offset > 0:
            print("TPF: Reading data, offset = {}, size = {}, filename = {}".format(data_offset, data_size, entry['filename']))
            self.file.seek(data_offset)
            data = self.read(data_size)
            entry['actual_filename'] = self.join_to_parent_dir(entry['filename']) + ".dds"
            self.write(entry['actual_filename'], data)

        self.file.seek(position)

        return entry
