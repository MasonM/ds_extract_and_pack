import io
import os
from itertools import chain

from .bhd5_file import BHD5File
from .bhf3_file import BHF3File
from .binary_file import BinaryFile
from . import utils


class BDTFile(BinaryFile):
    MAGIC_HEADER = b"BDF307D7R6"

    def extract_file(self):
        self.log("BDT: Reading file {}".format(self.path))

        self.consume(self.MAGIC_HEADER)
        self.consume(0x0, 6)

        header_filename = self._get_header_filename()
        self.log("BDT: Using header file {}".format(header_filename))
        header_file = open(header_filename, "rb")
        signature = header_file.read(4)
        header_file.seek(0)

        if signature == BHD5File.MAGIC_HEADER:
            manifest = BHD5File(header_file, header_filename, self.depth, self.base_dir).extract_file()
            self._extract_records(chain.from_iterable(bin_data['records'] for bin_data in manifest['bins']))
        elif signature == BHF3File.MAGIC_HEADER:
            manifest = BHF3File(header_file, header_filename, self.depth, self.base_dir).extract_file()
            self._extract_records(manifest['records'])
        else:
            raise RuntimeError("Invalid signature in header file: {}".format(signature))

        return manifest

    def _get_header_filename(self):
        for ext in ('bhd5', 'bhd'):
            bhd_filename = self.path.replace("bdt", ext)
            if os.path.isfile(bhd_filename):
                return bhd_filename
        raise FileNotFoundError("Could not find BHD for BDT {}".format(self.path))

    def _extract_records(self, records):
        for record_data in records:
            self.log("BDT: extracting {}".format(record_data['actual_filename']))

            self.file.seek(self.to_int32(record_data['header']['record_offset']))
            data = self.read(self.to_int32(record_data['header']['record_size']))
            file_cls = utils.class_for_data(data)
            if file_cls == self:
                # just store data for now, because we need to wait for the BHD to be extracted
                record_data['bdt_data'] = io.BytesIO(data)
            elif file_cls is not None:
                record_data['sub_manifest'] = file_cls(io.BytesIO(data), record_data['actual_filename'], self.depth + 1).extract_file()
            else:
                utils.write_data(record_data['actual_filename'], data)

        for record_data in records:
            # Process any BDT files
            if 'bdt_data' in record_data:
                record_data['sub_manifest'] = BDTFile(record_data['bdt_data'], record_data['actual_filename'], self.depth + 1).extract_file()
                record_data['bdt_data'].close()

    def create_file(self, manifest):
        self.log("BDT: Writing file {}".format(self.path))

        self.write(self.MAGIC_HEADER)
        self.write(bytearray(6))

        if manifest['header']['signature'] == BHD5File.MAGIC_HEADER:
            self._write_records(chain.from_iterable(bin_data['records'] for bin_data in manifest['bins']))
            bhd5_file = self.path.replace("bdt", "bhd5")
            BHD5File(open(bhd5_file, "wb"), bhd5_file).create_file(manifest)
        elif manifest['header']['signature'] == BHF3File.MAGIC_HEADER:
            self._write_records(manifest['records'])
            bhf3_file = self.path.replace("bdt", "bhd")
            BHF3File(open(bhf3_file, "wb"), bhf3_file).create_file(manifest)
        else:
            raise RuntimeError("Invalid signature in manifest: {}".format(manifest['header']['signature']))

    def _write_records(self, records):
        for record_data in records:
            self.log("BDT: Writing data for {}".format(record_data['actual_filename']))
            cur_position = self.file.tell()
            record_data['header']['record_offset'] = self.int32_bytes(cur_position)
            if 'sub_manifest' in record_data:
                self.write(utils.get_data_for_file(record_data['sub_manifest'], record_data['actual_filename'], self.depth + 1))
            else:
                self.write(open(record_data['actual_filename'], "rb").read())
            data_size = self.file.tell() - cur_position
            record_data['header']['record_size'] = self.int32_bytes(data_size)
            if 'redundant_size' in record_data['header']:
                record_data['header']['redundant_size'] = record_data['header']['record_size']
