from . import bdt_file, tpf_file, dcx_file, bnd3_file


def class_for_data(data):
    classes_to_check = [bnd3_file.BND3File, tpf_file.TPFFile, dcx_file.DCXFile, bdt_file.BDTFile]

    for file_cls in classes_to_check:
        if data.startswith(file_cls.MAGIC_HEADER):
            return file_cls
    return None
