from .binary_file import BinaryFile
from .tpf_reader import TpfReader


class BND3Reader(BinaryFile):
    MAGIC_HEADER = b"BND3"

    def process_file(self):
        manifest= {
            "header": {
                "signature": self.consume(self.MAGIC_HEADER),
                "unknown_bytes": self.read(8),
                "version": self.read(4),
                "entry_count": self.read(4),
                "header_size": self.read(4),
            },
            "entries": [],
        }

        version = self.to_int32(manifest['header']['version'])
        if version not in (0x74, 0x54, 0x70):
            raise ValueError("Invalid version: {:02X}".format(manifest['header']['version']))

        self.consume(0x0, 8)

        for i in range(self.to_int32(manifest['header']['entry_count'])):
            print("BND3: Reading entry #{}".format(i))
            manifest['entries'].append(self.read_entry(version))

        return manifest

    def read_entry(self, version):
        entry = {
            "header": {
                "record_sep": self.consume(0x40, 4),
                'data_size': self.read(4),
                'data_offset': self.read(4),
                'id': self.read(4),
                "filepath_offset": self.read(4),
            },
        }

        if version in (0x74, 0x54):
            redundant_size = self.read(4)
            if redundant_size != entry['header']['data_size']:
                raise ValueError("Expected size {:02x}, got {:02x}".format(entry['header']['data_size'], redundant_size))

        position = self.file.tell()
        filepath_offset = self.to_int32(entry['header']['filepath_offset'])
        if filepath_offset > 0:
            #print("BND3: Reading filepath, offset = {}".format(entry['filepath_offset']))
            self.file.seek(filepath_offset)
            entry['filepath'] = self.read_null_terminated_string()
            #print("BND3: got filepath %s" % entry['filepath'])

        data_offset = self.to_int32(entry['header']['data_offset'])
        data_size = self.to_int32(entry['header']['data_size'])
        if data_offset > 0:
            self.file.seek(data_offset)
            data = self.read(data_size)
            filepath = self.join_to_parent_dir(entry['filepath'])
            print("BND3: Reading data, offset = {}, size = {}, filepath = {}".format(data_offset, data_size, filepath))
            self.write(filepath, data)
            if data.startswith(TpfReader.MAGIC_HEADER):
                tpf_reader = TpfReader(filepath, self.base_dir)
                entry['tpf'] = tpf_reader.process_file()
                tpf_reader.remove()

        self.file.seek(position)

        return entry
