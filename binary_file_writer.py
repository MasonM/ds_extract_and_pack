class BinaryFileWriter:
    def __init__(self, path):
        self.file = open(path, "rb")

    def write(self, *args):
        for arg in args:
            self.file.write(arg)

def to_int32(i):
    return i.to_bytes(4, byteorder="little")


def to_byte(i):
    return i.to_bytes(1, byteorder="little")
