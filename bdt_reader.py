import io
from binary_file import BinaryFile
from bhd5_reader import BHD5Reader
from dcx_reader import DcxReader


class BDTReader(BinaryFile):
    MAGIC_HEADER = b"BDF307D7R6"

    def process_file(self):
        print("BDT: Writing file {}".format(self.path))

        bhd5_file = open(self.file.name.replace(".bdt", ".bhd5"), "rb")
        manifest = BHD5Reader(bhd5_file, bhd5_file).process_file()
        self.consume(self.MAGIC_HEADER)
        self.consume(0x0, 6)

        for bin_data in manifest['bins']:
            for record_data in bin_data['records']:
                self.file.seek(record_data['record_offset'])
                data = self.read(record_data['record_size'])
                filepath = self.normalize_filepath(record_data['record_name'])
                print("BDT: extracting {}".format(filepath))
                if data.startswith(DcxReader.MAGIC_HEADER):
                    with io.BytesIO() as dcx_buffer:
                        record_data['dcx'] = DcxReader(dcx_buffer, filepath).process_file()
                else:
                    self.write_data(filepath, data)

        self.file.close()
        return manifest
