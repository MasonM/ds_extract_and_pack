import os
import pickle
from .binary_file_reader import BinaryFileReader


class TpfReader(BinaryFileReader):
    def extract_file(self):
        self.data.update({
            "size": os.stat(self.path).st_size,
            "signature": self.read(4),
            "size_sum": self.read_int32(),
            "entry_count": self.read_int32(),
            "flag1": self.read(1),
            "flag2": self.read(1),
            "encoding": self.read(1),
            "flag3": self.read(1),
            "entries": [],
        })

        print("Found %i entries" % self.data['entry_count'])

        for i in range(self.data['entry_count']):
            print("Reading entry #{}".format(i))
            self.data['entries'].append(self.read_entry())
        print(self.data)
        metadata_filename = os.path.basename(self.path).split(".")[0] + ".metadata"
        pickle.dump(self.data, open(metadata_filename, "wb"))

    def read_entry(self):
        entry = {
            'data_offset': self.read_int32(),
            'data_size': self.read_int32(),
            'format': self.read(1),
            'type': self.read(1),
            'mipmap_count': self.read(1),
            'flags': self.read(1),
            'filename_offset': self.read_int32(),
            'unknown': self.read_int32(),
        }

        #print(entry)

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
            open(entry['filename'] + ".dds", 'wb').write(data)

        self.file.seek(position)

        return entry
