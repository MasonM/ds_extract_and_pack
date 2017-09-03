import io
from binary_file import BinaryFile
from bdt_reader import BDTReader
from dcx_writer import DCXWriter
from bhd5_writer import BHD5Writer


class BDTWriter(BinaryFile):
    def process_file(self, manifest):
        print("BDT: Writing file {}".format(self.path))

        self.write(BDTReader.MAGIC_HEADER)
        self.write(b"0x00" * 6)

        for bin_data in manifest['bins']:
            bin_data['header']['offset'] = self.int32_bytes(self.file.tell())
            for record_data in bin_data['records']:
                cur_position = self.file.tell()
                record_data['header']['record_offset'] = self.int32_bytes(cur_position)
                print("BDT: Writing data for {}".format(record_data['actual_filename']))
                if "dcx" in record_data:
                    with io.BytesIO() as dcx_buffer:
                        DCXWriter(dcx_buffer, record_data['actual_filename']).process_file(record_data['dcx'])
                        dcx_buffer.seek(0)
                        self.write(dcx_buffer.read())
                else:
                    self.write(open(record_data['actual_filename'], "rb").read())
                data_size = self.file.tell() - cur_position
                record_data['header']['record_size'] = self.int32_bytes(data_size)

        self.file.close()

        bhd5_file = self.path.replace(".bdt", ".bhd5")
        BHD5Writer(open(bhd5_file, "wb"), bhd5_file).process_file(manifest)
