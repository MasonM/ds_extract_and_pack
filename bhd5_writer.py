from binary_file import BinaryFile


class BHD5Writer(BinaryFile):
    def process_file(self, manifest):
        print("BHD5: Writing file {}".format(self.path))

        self.write_header(manifest)
        for bin_data in manifest['bins']:
            self.write_header(bin_data)
            position = self.file.tell()
            self.file.seek(self.to_int32(bin_data['header']['offset']))
            for record_data in bin_data['records']:
                self.write_header(record_data)
            self.file.seek(position)
