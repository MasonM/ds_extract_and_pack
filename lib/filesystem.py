import hashlib
import os
import re

import config
import fixed_data.dupe_files
import fixed_data.filenames

filesystem = {}
dupe_counter = {}
name_hash_cache = {}


def get_hash_from_string(s):
    hash_val = 0
    for char in s.lower():
        hash_val *= 37
        hash_val += ord(char)
    hash_val &= 0xffffffff # truncate to 32 bits
    return hash_val


def get_name_from_hash(file_hash):
    if not name_hash_cache:
        for name in fixed_data.filenames.FILENAMES:
            name_hash_cache[get_hash_from_string(name)] = name
    return name_hash_cache[file_hash]


def fix_dupe_path(path):
    count = dupe_counter.get(path, 0) + 1
    dupe_counter[path] = count
    suffix = "_%d" % count
    if '.' in path:
        head, sep, tail = path.rpartition('.')
        return head + suffix + sep + tail
    else:
        return path + suffix


def normalize_filepath(path, base_path):
    if base_path.startswith(config.data_base_dir):
        base_path = base_path[len(config.data_base_dir) + 1:]
    base_path = base_path.lstrip(os.path.sep)

    if path.lower().startswith("n:\\"):
        path = path[3:]
    path = path.lstrip("\\")

    if path.replace("\\", "/") in fixed_data.dupe_files.DUPE_FILES:
        path = fix_dupe_path(path)

    path = os.path.join(os.path.dirname(base_path), path).replace("\\", "/")

    # Flatten directory structure
    path = re.sub(r"/([^/]+)/\1/", r"/\1/", path)
    path = re.sub(r"((?:[^/]+/)+)FRPG/data/(Model|INTERROOT_win32)/(?:param/)?\1", r"\1", path)
    path = re.sub(r"([^/]+)/FRPG/data/Msg/Data_\1/win32", r"\1", path)
    path = re.sub(r"FRPG/Source/Shader/([^/]*)/WIN32", r"\1", path)
    path = re.sub(r"FRPG/data/Other/Rumble/", "", path)

    return os.path.normpath(path.replace("/", os.sep))


def read_data(file_path):
    if config.override_dir:
        override_file_path = os.path.join(config.override_dir, file_path)
        if os.path.isfile(override_file_path):
            print("USING OVERRIDE PATH {}".format(override_file_path))
            return open(override_file_path, "rb").read()
    if config.in_memory and not file_path.endswith("bhd5"):
        return filesystem[file_path]
    return open(os.path.join(config.extract_base_dir, file_path), "rb").read()


def isfile(file_path):
    if config.in_memory:
        return file_path in filesystem
    else:
        return os.path.isfile(os.path.join(config.extract_base_dir, file_path))


def write_data(file_path, data):
    if config.in_memory:
        if file_path in filesystem:
            compare_data(file_path, data, filesystem[file_path])
        else:
            filesystem[file_path] = data
    else:
        file_path = os.path.join(config.extract_base_dir, file_path)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        if os.path.isfile(file_path):
            compare_data(file_path, data, open(file_path, "rb").read())
        else:
            open(file_path, 'wb').write(data)


def compare_data(file_path, first, second):
    if not config.debug:
        return
    self_digest = hashlib.md5(first).hexdigest()
    other_digest = hashlib.md5(second).hexdigest()
    if self_digest == other_digest:
        print("WARN: File already exists and has same hash: {}".format(file_path))
    else:
        raise ValueError("ERROR: File already exists and has different hash: {}".format(file_path))
