import io
from binary_file import BinaryFile
from tpf_writer import TpfWriter


class BND3Writer(BinaryFile):
    def process_file(self, manifest):
        print("BND3: Writing file {}".format(self.path))

        self.file.seek(manifest['end_header_pos'])

        for entry in manifest['entries']:
            print("BND3: Writing entry filename for {} at offset {}".format(entry['actual_filename'], self.file.tell()))
            entry['header']['filename_offset'] = self.int32_bytes(self.file.tell())
            self.write(entry['filename'].encode("shift_jis"), b"\x00")

        manifest['header']['header_size'] = self.int32_bytes(self.file.tell())
        self.write(b"\x00" * 4) # padding

        for entry in manifest['entries']:
            cur_position = self.file.tell()
            print("BND3: Writing entry data for {} at offset {}".format(entry['actual_filename'], cur_position))
            entry['header']['data_offset'] = self.int32_bytes(cur_position)

            if 'tpf' in entry:
                with io.BytesIO() as tpf_buffer:
                    TpfWriter(tpf_buffer, entry['actual_filename']).process_file(entry['tpf'])
                    tpf_buffer.seek(0)
                    self.write(tpf_buffer.read())
            else:
                self.write(open(entry['actual_filename'], "rb").read())

            data_size = self.file.tell() - cur_position
            entry['header']['data_size'] = self.int32_bytes(data_size)
            entry['header']['redundant_size'] = entry['header']['data_size']

        self.file.seek(0)
        self.write_header(manifest)

        for entry in manifest['entries']:
            print("BND3: Writing entry header for {} at offset {}".format(entry['actual_filename'], self.file.tell()))
            self.write_header(entry)
