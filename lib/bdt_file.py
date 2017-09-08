import io
import os
import re

from .bhd5_file import BHD5File
from .bhf3_file import BHF3File
from .binary_file import BinaryFile
from . import utils, c4110_replacement


class BDTFile(BinaryFile):
    MAGIC_HEADER = b"BDF307D7R6"

    def extract_file(self, depth):
        self.log("Reading file {}".format(self.path), depth)

        self.consume(self.MAGIC_HEADER)
        self.consume(0x0, 6)

        if self.path.endswith("c4110.chrtpfbdt"):
            manifest = BHF3File(io.BytesIO(c4110_replacement.DATA), self.path[:-3] + "bhd", self.base_dir).extract_file(depth)
        else:
            header_filename = self._get_header_filename()
            self.log("Using header file {}".format(header_filename), depth)
            header_file = open(header_filename, "rb")
            file_cls = utils.class_for_data(header_file.read(4), include_header_files=True)
            header_file.seek(0)

            if file_cls not in [BHD5File, BHF3File]:
                raise RuntimeError("Invalid signature in header file: {}".format(header_filename))

            manifest = file_cls(header_file, header_filename, self.base_dir).extract_file(depth)

        self._extract_records(manifest['records'], depth + 1)

        return manifest

    def _get_header_filename(self):
        # Convert path like chr/c2320.chrtpfbdt into chr/c2320/c2320.chrtpfbdt
        fixed_path = os.sep.join([
            os.path.dirname(self.path),
            os.path.basename(self.path).split(".")[0],
            os.path.basename(self.path)
        ])
        for ext in ('bhd5', 'bhd'):
            for path in (self.path, fixed_path):
                bhd_filename = path[:-3] + ext
                if os.path.isfile(bhd_filename):
                    return bhd_filename

        raise FileNotFoundError("Could not find BHD for BDT {}".format(self.path))

    def _extract_records(self, records, depth):
        for record_data in records:
            self.log("Processing {}".format(record_data['record_name']), depth)

            self.file.seek(self.to_int32(record_data['header']['record_offset']))
            data = self.read(self.to_int32(record_data['header']['record_size']))
            file_cls = utils.class_for_data(data)
            if file_cls is None:
                self.log("Writing data for {} to {}".format(record_data['record_name'], record_data['actual_filename']), depth)
                utils.write_data(record_data['actual_filename'], data)
            elif file_cls == BDTFile:
                # just store data for now, because we need to wait for the BHD to be extracted
                record_data['bdt_data'] = io.BytesIO(data)
            else:
                record_data['sub_manifest'] = file_cls(io.BytesIO(data), record_data['actual_filename']).extract_file(depth + 1)

        for record_data in records:
            # Process any BDT files
            if 'bdt_data' in record_data:
                try:
                    record_data['sub_manifest'] = BDTFile(record_data['bdt_data'], record_data['actual_filename']).extract_file(depth + 1)
                    record_data.pop('bdt_data').close()
                except FileNotFoundError:
                    self.log("ERROR: Failed to find header file for {}".format(record_data['actual_filename']), depth)
                    utils.write_data(record_data['actual_filename'], record_data.pop('bdt_data').read())

    def create_file(self, manifest, depth):
        self.log("Writing file {}".format(self.path), depth)

        self.write(self.MAGIC_HEADER)
        self.write(bytearray(6))
        self._write_records(manifest['records'], depth)

        file_cls = utils.class_for_data(manifest['header']['signature'], include_header_files=True)
        if file_cls == BHD5File:
            header_filename = self.path[:-3] + "bhd5"
        elif file_cls == BHF3File:
            header_filename = self.path[:-3] + "bhd"
        else:
            raise RuntimeError("Invalid signature in manifest: {}".format(manifest['header']['signature']))

        file_cls(open(header_filename, "wb"), header_filename).create_file(manifest)

    def _write_records(self, records, depth):
        for record_data in records:
            self.log("Writing data for {}".format(record_data['actual_filename']), depth)
            cur_position = self.file.tell()
            record_data['header']['record_offset'] = self.int32_bytes(cur_position)
            if 'sub_manifest' in record_data:
                self.write(utils.get_data_for_file(record_data['sub_manifest'], record_data['actual_filename'], depth + 1))
            else:
                self.write(open(record_data['actual_filename'], "rb").read())
            data_size = self.file.tell() - cur_position
            record_data['header']['record_size'] = self.int32_bytes(data_size)
            if 'redundant_size' in record_data['header']:
                record_data['header']['redundant_size'] = record_data['header']['record_size']
