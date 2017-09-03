from .binary_file import BinaryFile
from .bhd5_reader import BHD5Reader
from .dcx_reader import DcxReader


class BDTReader(BinaryFile):
    MAGIC_HEADER = b"BDF307D7R6"

    def process_file(self):
        manifest = BHD5Reader(self.path.replace(".bdt", ".bhd5")).process_file()
        self.consume(self.MAGIC_HEADER)
        self.consume(0x0, 6)

        for bin_data in manifest['bins']:
            for record_data in bin_data['records']:
                self.file.seek(record_data['record_offset'])
                data = self.read(record_data['record_size'])
                filepath = self.join_to_parent_dir(record_data['record_name'])
                print("BDT: extracting {}".format(filepath))
                self.write(filepath, data)
                if data.startswith(DcxReader.MAGIC_HEADER):
                    dcx_reader = DcxReader(filepath, self.base_dir)
                    record_data['dcx'] = dcx_reader.process_file()
                    dcx_reader.remove()

        self.file.close()
        return manifest
