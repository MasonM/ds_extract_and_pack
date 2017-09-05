import io
import os

from lib.bnd3_file import BND3File
from lib.dcx_file import DCXFile
from lib.tpf_file import TPFFile


def class_for_data(data):
    if data.startswith(BND3File.MAGIC_HEADER):
        return BND3File
    elif data.startswith(TPFFile.MAGIC_HEADER):
        return TPFFile
    elif data.startswith(DCXFile.MAGIC_HEADER):
        return DCXFile
    return None


def get_data_for_file(sub_manifest, filename):
    file_cls = class_for_data(sub_manifest['header']['signature'])
    if not file_cls:
        raise RuntimeError("Failed to find file class to parse file {} with signature {}".format(
            filename,
            sub_manifest['header']['signature'])
        )

    with io.BytesIO() as buffer:
        file_cls(buffer, filename).create_file(sub_manifest)
        buffer.seek(0)
        return buffer.read()


def write_data(filepath, data):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    open(filepath, 'wb').write(data)


def normalize_filepath(path, base_dir):
    if path.lower().startswith("n:\\"):
        path = path[3:]
    path = os.path.join(base_dir, path.lstrip("\\").replace("\\", os.sep))
    return os.path.normpath(path)
