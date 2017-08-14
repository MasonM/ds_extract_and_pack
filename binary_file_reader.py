class BinaryFileReader:
    def __init__(self, path):
        self.path = path
        self.file = open(path, "rb")
        self.data = {}
        self.endian = "little"

    def read(self, bytes):
        return self.file.read(bytes)

    def consume(self, expected_bytes, num_to_read=None):
        if num_to_read:
            expected_bytes = expected_bytes.to_bytes(num_to_read, self.endian)
        else:
            num_to_read = len(expected_bytes)
        bytes = self.read(num_to_read)
        if bytes != expected_bytes:
            raise ValueError("Expected {}, got {}".format(expected_bytes, bytes))

    def read_int32(self):
        b = self.read(4)
        return int.from_bytes(b, byteorder=self.endian, signed=False)

    def read_null_terminated_string(self):
        buffer = ""
        while True:
            byte = self.read(1)
            if byte == b'' or byte == b'\x00':
                return buffer
            buffer += byte.decode()

