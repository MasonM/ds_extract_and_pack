import io
from _collections import OrderedDict

import lib


class BinaryFile:
    def __init__(self, file, path):
        self.file = file
        self.path = path
        self.endian = "little"

    @staticmethod
    def class_for_data(data):
        classes_to_check = [lib.BND3File, lib.TPFFile, lib.DCXFile, lib.BDTFile]

        for file_cls in classes_to_check:
            if data.startswith(file_cls.MAGIC_HEADER):
                return file_cls
        return None

    def write(self, *args):
        for arg in args:
            self.file.write(arg)

    def write_header(self, manifest):
        self.write(*manifest.header.values())

    def read(self, num_bytes):
        return self.file.read(num_bytes)

    def consume(self, expected_bytes, num_to_read=None):
        if num_to_read:
            expected_bytes = expected_bytes.to_bytes(num_to_read, self.endian)
        else:
            num_to_read = len(expected_bytes)
        actual_bytes = self.read(num_to_read)
        if actual_bytes != expected_bytes:
            raise ValueError("Expected {}, got {}".format(expected_bytes, actual_bytes))
        return actual_bytes

    def read_null_terminated_string(self):
        buffer = b""
        while True:
            byte = self.read(1)
            if byte == b'' or byte == b'\x00':
                break
            buffer += byte
        try:
            return buffer.decode("shift_jis")
        except UnicodeDecodeError as e:
            self.log("Failed to decode {}".format(buffer), 1)
            raise e

    def pad_to_hex_boundary(self):
        if self.file.tell() % 16 > 0:
            padding = 16 - (self.file.tell() % 16)
            self.write(b"\x00" * padding)

    def int32_bytes(self, i):
        return i.to_bytes(4, byteorder=self.endian)

    def log(self, msg, depth):
        prefix = ""
        if depth > 1:
            prefix += ("  " * (depth - 1)) + "|"
        prefix += self.__class__.__name__.replace("File", "")
        prefix += "(offset=" + str(self.file.tell()) + "): "
        print(prefix + msg)


class Manifest:
    def __init__(self, binary_file_reader, header):
        self.file_cls = binary_file_reader.__class__
        self.path = binary_file_reader.path
        self.endian = binary_file_reader.endian
        self.header = OrderedDict(header)

    def int32(self, key):
        return int.from_bytes(self.header[key], byteorder=self.endian, signed=False)

    def get_data(self, filename, depth):
        with io.BytesIO() as buffer:
            self.file_cls(buffer, filename).create_file(self, depth)
            buffer.seek(0)
            return buffer.read()
