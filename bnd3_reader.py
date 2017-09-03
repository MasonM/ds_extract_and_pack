import io
from binary_file import BinaryFile
from tpf_reader import TpfReader


class BND3Reader(BinaryFile):
    MAGIC_HEADER = b"BND3"

    def process_file(self):
        print("BND3: Reading file {}".format(self.path))

        manifest = {
            "header": {
                "signature": self.consume(self.MAGIC_HEADER),
                "unknown_bytes": self.read(8),
                "version": self.read(4),
                "entry_count": self.read(4),
                "header_size": self.read(4),
                "padding": self.consume(0x0, 8),
            },
            "entries": [],
        }

        version = self.to_int32(manifest['header']['version'])
        if version not in (0x74, 0x54, 0x70):
            raise ValueError("Invalid version: {:02X}".format(manifest['header']['version']))

        for i in range(self.to_int32(manifest['header']['entry_count'])):
            print("BND3: Reading entry #{}".format(i))
            manifest['entries'].append(self.read_entry(version))

        manifest["end_header_pos"] = self.file.tell()

        return manifest

    def read_entry(self, version):
        entry = {
            "header": {
                "record_sep": self.consume(0x40, 4),
                'data_size': self.read(4),
                'data_offset': self.read(4),
                'id': self.read(4),
                "filename_offset": self.read(4),
            },
        }

        if version in (0x74, 0x54):
            redundant_size = self.read(4)
            if redundant_size != entry['header']['data_size']:
                raise ValueError("Expected size {:02x}, got {:02x}".format(entry['header']['data_size'], redundant_size))

        position = self.file.tell()
        filename_offset = self.to_int32(entry['header']['filename_offset'])
        if filename_offset > 0:
            #print("BND3: Reading filename, offset = {}".format(entry['filename_offset']))
            self.file.seek(filename_offset)
            entry['filename'] = self.read_null_terminated_string()
            entry['actual_filename'] = self.normalize_filepath(entry['filename'])
            #print("BND3: got filename %s" % entry['filename'])

        data_offset = self.to_int32(entry['header']['data_offset'])
        data_size = self.to_int32(entry['header']['data_size'])
        if data_offset > 0:
            self.file.seek(data_offset)
            data = self.read(data_size)
            print("BND3: Reading data, offset = {}, size = {}, filename = {}".format(data_offset, data_size, entry['actual_filename']))
            if data.startswith(TpfReader.MAGIC_HEADER):
                with io.BytesIO(data) as tpf_buffer:
                    entry['tpf'] = TpfReader(tpf_buffer, entry['actual_filename']).process_file()
            else:
                self.write_data(entry['actual_filename'], data)

        self.file.seek(position)

        return entry
