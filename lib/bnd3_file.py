import io
from _collections import OrderedDict

from lib.tpf_file import TPFFile
from lib.binary_file import BinaryFile


class BND3File(BinaryFile):
    MAGIC_HEADER = b"BND3"

    def extract_file(self, base_dir):
        print("BND3: Reading file {}".format(self.path))

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
            print("BND3: Reading entry #{}".format(i))
            manifest['entries'].append(self._read_entry(version, base_dir))

        manifest["end_header_pos"] = self.file.tell()

        return manifest

    def _read_entry(self, version, base_dir):
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
            print("BND3: Reading filename, offset = {}".format(filename_offset))
            self.file.seek(filename_offset)
            entry['filename'] = self.read_null_terminated_string()
            entry['actual_filename'] = self.normalize_filepath(entry['filename'], base_dir)
            #print("BND3: got filename %s" % entry['filename'])

        data_offset = self.to_int32(entry['header']['data_offset'])
        data_size = self.to_int32(entry['header']['data_size'])
        if data_offset > 0:
            self.file.seek(data_offset)
            data = self.read(data_size)
            print("BND3: Reading data, offset = {}, size = {}, filename = {}".format(
                data_offset, data_size, entry['actual_filename'])
            )
            if data.startswith(TPFFile.MAGIC_HEADER):
                with io.BytesIO(data) as tpf_buffer:
                    entry['tpf'] = TPFFile(tpf_buffer, entry['actual_filename']).extract_file(base_dir)
            else:
                self.write_data(entry['actual_filename'], data)

        self.file.seek(position)

        return entry

    def create_file(self, manifest):
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
                    TPFFile(tpf_buffer, entry['actual_filename']).create_file(entry['tpf'])
                    tpf_buffer.seek(0)
                    self.write(tpf_buffer.read())
            else:
                self.write(open(entry['actual_filename'], "rb").read())

            data_size = self.file.tell() - cur_position
            entry['header']['data_size'] = self.int32_bytes(data_size)
            if self.to_int32(manifest['header']['version']) in (0x74, 0x54):
                entry['header']['redundant_size'] = entry['header']['data_size']

        self.file.seek(0)
        self.write_header(manifest)

        for entry in manifest['entries']:
            print("BND3: Writing entry header for {} at offset {}".format(entry['actual_filename'], self.file.tell()))
            self.write_header(entry)
