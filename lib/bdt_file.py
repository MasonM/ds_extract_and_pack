import io
import os

import fixed_data.c4110_replacement
import lib


class BDTFile(lib.BinaryFile):
    MAGIC_HEADER = b"BDF3"
    MAGIC_ID = b"07D7R6"
    C4110_FILENAME = "c4110.chrtpfbdt" # this file is missing the BHD header

    def extract_file(self, depth):
        self.log("Reading file {}".format(self.path), depth)

        self.expect(self.MAGIC_HEADER)
        self.expect(self.MAGIC_ID)
        self.expect(0x0, 6)

        if self.path.endswith(self.C4110_FILENAME):
            data = io.BytesIO(fixed_data.c4110_replacement.DATA)
            manifest = lib.BHF3File(data, self.path[:-3] + "bhd").extract_file(depth + 1)
        else:
            header_filename = self._get_header_filename(depth)
            self.log("Using header file {}".format(header_filename), depth)
            manifest = self._get_header_extractor(header_filename).extract_file(depth + 1)

        self._extract_records(manifest.records, depth)

        return manifest

    @staticmethod
    def _get_header_extractor(header_filename):
        header_data = lib.filesystem.read_data(header_filename)

        if header_data.startswith(lib.BHF3File.MAGIC_HEADER):
            file_cls = lib.BHF3File
        elif header_data.startswith(lib.BHD5File.MAGIC_HEADER):
            file_cls = lib.BHD5File
        else:
            raise RuntimeError("Invalid signature in header file: {}".format(header_filename))

        return file_cls(io.BytesIO(header_data), header_filename)

    def _get_header_filename(self, depth):
        path = self.path.rsplit("bdt", 1)[0] + "bhd"
        if depth == 1:
            return path + "5"

        if not lib.filesystem.isfile(path):
            basename, ext = os.path.basename(path).rsplit('.', 1)
            path = os.sep.join([os.path.dirname(path), basename, basename + "." + ext])

            if not lib.filesystem.isfile(path):
                raise FileNotFoundError("Got no results searching for BHD for BDT {}".format(self.path))

        return path

    def _extract_records(self, records, depth):
        for record_num, record in enumerate(records):
            self.log("Processing record num {} name {}".format(record_num, record.record_name), depth)

            self.file.seek(record.int32('record_offset'))
            data = self.read(record.int32('record_size'))

            file_cls = self.class_for_data(data)
            if file_cls is None or record.path.endswith(self.C4110_FILENAME):
                self.log("Writing data for {} to {}".format(record.record_name, record.path), depth)
                lib.filesystem.write_data(record.path, data)
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
        self.write(self.MAGIC_ID)
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

            with io.BytesIO() as buffer:
                BDTFile(buffer, record.path).create_file(record.sub_manifest, depth + 1)
                buffer.seek(0)
                bdt_data[record.path] = buffer.read()

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
            elif hasattr(record, 'sub_manifest') and not record.path.endswith(self.C4110_FILENAME):
                self.write(record.sub_manifest.get_data(record.path, depth + 1))
            else:
                self.write(lib.filesystem.read_data(record.path))
            data_size = self.file.tell() - cur_position
            record.header['record_size'] = self.int32_bytes(data_size)
            if 'redundant_size' in record.header:
                record.header['redundant_size'] = record.header['record_size']
            if record != records[-1][1]:
                self.pad_to_hex_boundary()

        if depth == 1:
            self.log("Writing BDT header for {}".format(self.path), depth)
            header_filename = self._get_header_filename(depth)
            manifest.file_cls(open(header_filename, "wb"), header_filename).create_file(manifest, depth + 1)

