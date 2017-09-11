import io
import os
import hashlib

from . import bdt_file, tpf_file, dcx_file, bnd3_file, bhf3_file, bhd5_file


def class_for_data(data, include_header_files=False):
    classes_to_check = [bnd3_file.BND3File, tpf_file.TPFFile, dcx_file.DCXFile, bdt_file.BDTFile]

    if include_header_files:
        classes_to_check += bdt_file.BDTFile.HEADER_FILE_CLS

    for file_cls in classes_to_check:
        if data.startswith(file_cls.MAGIC_HEADER):
            return file_cls
    return None


def get_data_for_file(sub_manifest, filename, depth):
    file_cls = class_for_data(sub_manifest['header']['signature'])
    if not file_cls:
        raise RuntimeError("Failed to find file class to parse file {} with signature {}".format(
            filename,
            sub_manifest['header']['signature'])
        )

    return get_data_for_file_cls(file_cls, sub_manifest, filename, depth)


def get_data_for_file_cls(file_cls, sub_manifest, filename, depth):
    with io.BytesIO() as buffer:
        file_cls(buffer, filename).create_file(sub_manifest, depth)
        buffer.seek(0)
        return buffer.read()

def write_data(filepath, data):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    if os.path.isfile(filepath):
        self_digest = hashlib.md5(data).hexdigest()
        other_digest = hashlib.md5(open(filepath, "rb").read()).hexdigest()
        if self_digest == other_digest:
            print("WARN: File already exists and has same hash: {}".format(filepath))
            return
        # This seems to only happen with *.sibcam and *.hkx files
        print("ERROR: File already exists and has different hash: {}".format(filepath))

    file = open(filepath, 'w+b')
    file.write(data)
    file.seek(0)
    return file

