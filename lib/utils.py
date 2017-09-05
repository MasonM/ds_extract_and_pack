import io
import os


from . import bdt_file, tpf_file, dcx_file, bnd3_file


def class_for_data(data):
    if data.startswith(bnd3_file.BND3File.MAGIC_HEADER):
        return bnd3_file.BND3File
    elif data.startswith(tpf_file.TPFFile.MAGIC_HEADER):
        return tpf_file.TPFFile
    elif data.startswith(dcx_file.DCXFile.MAGIC_HEADER):
        return dcx_file.DCXFile
    elif data.startswith(bdt_file.BDTFile.MAGIC_HEADER):
        return bdt_file.BDTFile
    return None


def get_data_for_file(sub_manifest, filename, depth):
    file_cls = class_for_data(sub_manifest['header']['signature'])
    if not file_cls:
        raise RuntimeError("Failed to find file class to parse file {} with signature {}".format(
            filename,
            sub_manifest['header']['signature'])
        )

    with io.BytesIO() as buffer:
        file_cls(buffer, filename, depth).create_file(sub_manifest)
        buffer.seek(0)
        return buffer.read()


def write_data(filepath, data):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    open(filepath, 'wb').write(data)
