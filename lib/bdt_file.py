import io
import os
import glob

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
            manifest = BHF3File(io.BytesIO(c4110_replacement.DATA), self.path[:-3] + "bhd", self.base_dir).extract_file(depth + 1)
        else:
            header_filename = self._get_header_filename()
            self.log("Using header file {}".format(header_filename), depth)
            manifest = self._get_header_extractor(header_filename).extract_file(depth + 1)

        self._extract_records(manifest.records, depth)

        return manifest

    def _get_header_extractor(self, header_filename):
        header_file = open(header_filename, "rb")
        signature = header_file.read(4)
        header_file.seek(0)

        if signature == BHF3File.MAGIC_HEADER:
            file_cls = BHF3File
        elif signature == BHD5File.MAGIC_HEADER:
            file_cls = BHD5File
        else:
            raise RuntimeError("Invalid signature in header file: {}".format(header_filename))

        return file_cls(header_file, header_filename, self.base_dir)

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
        for record_num, record in enumerate(records):
            self.log("Processing record num {} name {}".format(record_num, record.record_name), depth)

            self.file.seek(record.int32('record_offset'))
            data = self.read(record.int32('record_size'))

            file_cls = utils.class_for_data(data)
            if file_cls is None or record.path.endswith("c4110.chrtpfbdt"):
                self.log("Writing data for {} to {}".format(record.record_name, record.path), depth)
                utils.write_data(record.path, data)
            elif file_cls == BDTFile:
                # just store data for now, because we need to wait for the BHD to be extracted
                record.bdt_data = io.BytesIO(data)
            else:
                record.sub_manifest = file_cls(io.BytesIO(data), record.path).extract_file(depth + 1)

        for record_num, record in enumerate(records):
            # Process any BDT files
            if hasattr(record, 'bdt_data'):
                self.log("Processing record num {} BDT {}".format(record_num, record.record_name), depth)
                record.sub_manifest = BDTFile(record.bdt_data, record.path).extract_file(depth + 1)
                del record.bdt_data

    def create_file(self, manifest, depth):
        self.log("Writing file {}".format(self.path), depth)

        self.write(self.MAGIC_HEADER)
        self.write(bytearray(6))

        records = sorted(enumerate(manifest.records), key=lambda r: r[1].int32('record_offset'))

        bdt_data = {}
        for record_num, record in records:
            if not (hasattr(record, 'sub_manifest') and record.record_name.endswith("bdt")):
                continue

            self.log("Writing BDT data for record num {}, name {}, actual name = {}".format(
                record_num,
                record.record_name,
                record.path
            ), depth)

            bdt_data[record.path] = record.sub_manifest.get_data(record.path, depth + 1)

        for record_num, record in records:
            self.log("Writing data for record num {}, name {}, actual name = {}".format(
                record_num,
                record.record_name,
                record.path
            ), depth)

            cur_position = self.file.tell()
            record.header['record_offset'] = self.int32_bytes(cur_position)
            if record.path in bdt_data:
                self.write(bdt_data[record.path])
            elif hasattr(record, 'sub_manifest') and not record.path.endswith("c4110.chrtpfbdt"):
                self.write(record.sub_manifest.get_data(record.path, depth + 1))
            else:
                self.write(open(record.path, "rb").read())
            data_size = self.file.tell() - cur_position
            record.header['record_size'] = self.int32_bytes(data_size)
            if 'redundant_size' in record.header:
                record.header['redundant_size'] = record.header['record_size']
            if record != records[-1][1]:
                if self.file.tell() % 16 > 0:
                    padding = 16 - (self.file.tell() % 16)
                    self.write(b"\x00" * padding)
