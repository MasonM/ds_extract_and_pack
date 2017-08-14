import os
from .binary_file_reader import BinaryFileReader


class BND3Reader(BinaryFileReader):
    def extract_file(self):
        self.consume(b"BND3")
        self.file.seek(8, os.SEEK_CUR)
        self.data.update({
            "version": self.read_int32(),
            "entry_count": self.read_int32(),
            "header_size": self.read_int32(),
            "entries": [],
        })

        if self.data['version'] not in (0x74, 0x54, 0x70):
            raise ValueError("Invalid version: {:02X}".format(self.data['version']))

        self.consume(0x0, 8)

        for i in range(self.data['entry_count']):
            print("Reading entry #{}".format(i))
            self.data['entries'].append(self.read_entry())

        print(self.data)

    def read_entry(self):
        self.consume(0x40, 4)

        entry = {
            'data_size': self.read_int32(),
            'data_offset': self.read_int32(),
            'id': self.read_int32(),
            "filename_offset": self.read_int32()
        }

        if self.data['version'] in (0x74, 0x54):
            redundant_size = self.read_int32()
            if redundant_size != entry['data_size']:
                raise ValueError("Expected size {:02x}, got {:02x}".format(entry['data_size'], redundant_size))

        position = self.file.tell()
        if entry['filename_offset'] > 0:
            print("Reading filename, offset = {}".format(entry['filename_offset']))
            self.file.seek(entry['filename_offset'])
            entry['filename'] = self.read_null_terminated_string()
            print("got filename %s" % entry['filename'])

        if entry['data_offset'] > 0:
            print("Reading data, offset = {}, size = {}".format(entry['data_offset'], entry['data_size']))
            self.file.seek(entry['data_offset'])
            data = self.read(entry['data_size'])
            #entry['data'] = data
            #open(entry['filename'] + ".dds", 'wb').write(data)

        self.file.seek(position)

        return entry
