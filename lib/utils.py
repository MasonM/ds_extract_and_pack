import os
import re
import hashlib

from . import dupe_files, config, bdt_file, tpf_file, dcx_file, bnd3_file

filesystem = {}


def class_for_data(data):
    classes_to_check = [bnd3_file.BND3File, tpf_file.TPFFile, dcx_file.DCXFile, bdt_file.BDTFile]

    for file_cls in classes_to_check:
        if data.startswith(file_cls.MAGIC_HEADER):
            return file_cls
    return None


def normalize_filepath(path):
    if path.lower().startswith("n:\\"):
        path = path[3:]

    path = path.lstrip("\\").replace("\\", "/")

    if path in dupe_files.DUPE_FILES:
        path = dupe_files.fix_dupe_path(path)

    # Flatten directory structure
    path = re.sub(r"((?:[^/]+/)+)FRPG/data/(Model|INTERROOT_win32)/(?:param/)?\1", r"\1", path)
    path = re.sub(r"([^/]+)/FRPG/data/Msg/Data_\1/win32", r"\1", path)
    path = re.sub(r"FRPG/Source/Shader/([^/]*)/WIN32", r"\1", path)
    path = re.sub(r"FRPG/data/Other/Rumble/", "", path)

    return os.path.normpath(path.replace("/", os.sep))


def read_data(file_path):
    if config.in_memory and not file_path.endswith("bhd5"):
        return filesystem[file_path]
    else:
        return open(os.path.join(config.base_dir, file_path), "rb").read()


def isfile(file_path):
    if config.in_memory:
        return file_path in filesystem
    else:
        return os.path.isfile(os.path.join(config.base_dir, file_path))


def write_data(file_path, data):
    if config.in_memory:
        filesystem[file_path] = data
    else:
        file_path = os.path.join(config.base_dir, file_path)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        if os.path.isfile(file_path):
            if config.debug:
                self_digest = hashlib.md5(data).hexdigest()
                other_digest = hashlib.md5(open(file_path, "rb").read()).hexdigest()
                if self_digest == other_digest:
                    print("WARN: File already exists and has same hash: {}".format(file_path))
                print("ERROR: File already exists and has different hash: {}".format(file_path))
            return

        open(file_path, 'wb').write(data)
