import lib


def class_for_data(data):
    classes_to_check = [lib.BND3File, lib.TPFFile, lib.DCXFile, lib.BDTFile]

    for file_cls in classes_to_check:
        if data.startswith(file_cls.MAGIC_HEADER):
            return file_cls
    return None
