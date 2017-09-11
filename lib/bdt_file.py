import io
import os
import glob

from .bhd5_file import BHD5File
from .bhf3_file import BHF3File
from .binary_file import BinaryFile
from . import utils, c4110_replacement


class BDTFile(BinaryFile):
    MAGIC_HEADER = b"BDF307D7R6"
    HEADER_FILE_CLS = [BHD5File, BHF3File]

    def extract_file(self, depth):
        self.log("Reading file {}".format(self.path), depth)

        self.consume(self.MAGIC_HEADER)
        self.consume(0x0, 6)

        if self.path.endswith("c4110.chrtpfbdt"):
            manifest = BHF3File(io.BytesIO(c4110_replacement.DATA), self.path[:-3] + "bhd", self.base_dir).extract_file(depth + 1)
        else:
            header_filename = self._get_header_filename()
            self.log("Using header file {}".format(header_filename), depth)
            header_file = open(header_filename, "rb")
            file_cls = utils.class_for_data(header_file.read(4), include_header_files=True)
            header_file.seek(0)

            if file_cls not in self.HEADER_FILE_CLS:
                raise RuntimeError("Invalid signature in header file: {}".format(header_filename))

            manifest = file_cls(header_file, header_filename, self.base_dir).extract_file(depth + 1)
            manifest['actual_header_filename'] = header_filename
            manifest['header_file_cls'] = file_cls

        self._extract_records(manifest['records'], depth)

        return manifest

    def _get_header_filename(self):
        path_without_bdt = self.path.rsplit("bdt", 1)[0]
        for ext in ["bhd", "bhd5"]:
            if os.path.isfile(path_without_bdt + ext):
                return path_without_bdt + ext

        file_dirname = os.path.dirname(self.path)
        results = glob.glob("{}/**/{}bhd*".format(file_dirname, os.path.basename(path_without_bdt)), recursive=True)
        if len(results) != 1:
            raise FileNotFoundError("Got {} results searching for BHD for BDT {}: {}".format(len(results), self.path, results))
        return results[0]

    def _extract_records(self, records, depth):
        for record_num, record_data in enumerate(records):
            self.log("Processing record num {} name {}".format(record_num, record_data['record_name']), depth)

            self.file.seek(self.to_int32(record_data['header']['record_offset']))
            data = self.read(self.to_int32(record_data['header']['record_size']))
            file_cls = utils.class_for_data(data)
            if file_cls is None or record_data['record_name'].endswith("hkxbdt"):
                self.log("Writing data for {} to {}".format(record_data['record_name'], record_data['actual_filename']), depth)
                utils.write_data(record_data['actual_filename'], data)
            elif file_cls == BDTFile:
                # just store data for now, because we need to wait for the BHD to be extracted
                record_data['bdt_data'] = utils.write_data(record_data['actual_filename'], data)
            else:
                file = utils.write_data(record_data['actual_filename'], data)
                record_data['sub_manifest'] = file_cls(file, record_data['actual_filename']).extract_file(depth + 1)

        for record_num, record_data in enumerate(records):
            # Process any BDT files
            if 'bdt_data' in record_data:
                self.log("Processing record num {} BDT {}".format(record_num, record_data['record_name']), depth)
                try:
                    record_data['sub_manifest'] = BDTFile(record_data['bdt_data'], record_data['actual_filename']).extract_file(depth + 1)
                    record_data.pop('bdt_data').close()
                except FileNotFoundError as e:
                    self.log("ERROR: Failed to find header file for {}".format(record_data['actual_filename']), depth)
                    raise e

    def create_file(self, manifest, depth):
        self.log("Writing file {}".format(self.path), depth)

        self.write(self.MAGIC_HEADER)
        self.write(bytearray(6))

        bdt_data = {}
        for record_num, record_data in enumerate(manifest['records']):
            if 'sub_manifest' in record_data and record_data['record_name'].endswith("bdt"):
                sub_manifest = record_data['sub_manifest']
                filename = record_data['actual_filename']
                self.log("Writing BDT data for record num {}, name {}, actual name = {}".format(record_num, record_data['record_name'], filename), depth)
                if filename.endswith("c4110.chrtpfbdt"):
                    bdt_data[filename] = open(record_data['actual_filename'], "rb").read()
                else:
                    bdt_data[filename] = utils.get_data_for_file_cls(BDTFile, sub_manifest, record_data['actual_filename'], depth + 1)
                    sub_manifest["header_file_cls"](open(sub_manifest['actual_header_filename'], "wb"), sub_manifest['actual_header_filename']).create_file(sub_manifest, depth + 1)

        for record_num, record_data in enumerate(manifest['records']):
            filename = record_data['actual_filename']
            self.log("Writing data for record num {}, name {}, actual name = {}".format(record_num, record_data['record_name'], filename), depth)
            cur_position = self.file.tell()
            record_data['header']['record_offset'] = self.int32_bytes(cur_position)
            if filename in bdt_data:
                self.write(bdt_data[filename])
            elif 'sub_manifest' in record_data:
                self.write(utils.get_data_for_file(record_data['sub_manifest'], record_data['actual_filename'], depth + 1))
            else:
                self.write(open(record_data['actual_filename'], "rb").read())
            data_size = self.file.tell() - cur_position
            record_data['header']['record_size'] = self.int32_bytes(data_size)
            if 'redundant_size' in record_data['header']:
                record_data['header']['redundant_size'] = record_data['header']['record_size']
