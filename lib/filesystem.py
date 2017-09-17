import hashlib
import os
import re

import config
import lib.dupe_files

filesystem = {}


def normalize_filepath(path, base_path):
    if base_path.startswith(config.data_base_dir):
        base_path = base_path[len(config.data_base_dir) + 1:]
    base_path = base_path.lstrip(os.path.sep)

    if path.lower().startswith("n:\\"):
        path = path[3:]

    path = path.lstrip("\\").replace("\\", "/")

    if path in lib.dupe_files.DUPE_FILES:
        path = lib.dupe_files.fix_dupe_path(path)

    path = os.path.join(os.path.dirname(base_path), path)

    # Flatten directory structure
    path = re.sub(r"((?:[^/]+/)+)FRPG/data/(Model|INTERROOT_win32)/(?:param/)?\1", r"\1", path)
    path = re.sub(r"([^/]+)/FRPG/data/Msg/Data_\1/win32", r"\1", path)
    path = re.sub(r"FRPG/Source/Shader/([^/]*)/WIN32", r"\1", path)
    path = re.sub(r"FRPG/data/Other/Rumble/", "", path)

    return os.path.normpath(path.replace("/", os.sep))


def read_data(file_path):
    if config.override_dir:
        override_file_path = os.path.join(config.override_dir, file_path)
        if os.path.isfile(override_file_path):
            return open(override_file_path, "rb").read()
    if config.in_memory and not file_path.endswith("bhd5"):
        return filesystem[file_path]
    else:
        return open(os.path.join(config.extract_base_dir, file_path), "rb").read()


def isfile(file_path):
    if config.in_memory:
        return file_path in filesystem
    else:
        return os.path.isfile(os.path.join(config.extract_base_dir, file_path))


def write_data(file_path, data):
    if config.in_memory:
        filesystem[file_path] = data
    else:
        file_path = os.path.join(config.extract_base_dir, file_path)
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
