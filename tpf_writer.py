import os
from binary_file import BinaryFile


class TpfWriter(BinaryFile):
    def process_file(self, manifest):
        print("TPF: Writing file {}".format(self.file.name))

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

        self.write(*manifest['header'].values())

        for entry in manifest['entries']:
            print("TPF: Writing entry header for {} at offset {}".format(entry['actual_filename'], self.file.tell()))

            self.write(*entry['header'].values())
            #self.write_entry(entry)

        self.file.close()
