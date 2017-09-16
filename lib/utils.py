import os
import hashlib

from . import config, bdt_file, tpf_file, dcx_file, bnd3_file


filesystem = {}

def class_for_data(data):
    classes_to_check = [bnd3_file.BND3File, tpf_file.TPFFile, dcx_file.DCXFile, bdt_file.BDTFile]

    for file_cls in classes_to_check:
        if data.startswith(file_cls.MAGIC_HEADER):
            return file_cls
    return None


def read_data(filepath):
    if config.in_memory and not filepath.endswith("bhd5"):
        return filesystem[filepath]
    else:
        return open(filepath, "rb").read()


def isfile(filepath):
    if config.in_memory:
        return filepath in filesystem
    else:
        return os.path.isfile(filepath)


def write_data(filepath, data):
    if config.in_memory:
        filesystem[filepath] = data
    else:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        if os.path.isfile(filepath):
            if config.debug:
                self_digest = hashlib.md5(data).hexdigest()
                other_digest = hashlib.md5(open(filepath, "rb").read()).hexdigest()
                if self_digest == other_digest:
                    print("WARN: File already exists and has same hash: {}".format(filepath))
                print("ERROR: File already exists and has different hash: {}".format(filepath))
            return

        open(filepath, 'wb').write(data)
