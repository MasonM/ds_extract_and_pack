from . import texture_utils
import glob
import os
import shutil
import subprocess

base_dir = os.path.abspath(os.curdir)
texture_extract_dir = base_dir + "/unpacked"
overrides_dir = base_dir + "/overrides"

shutil.rmtree(overrides_dir)

for dds_file in glob.glob(texture_extract_dir + "/**/*.dds", recursive=True):
    print("processing " + dds_file + " ... ")
    final_path = os.path.abspath(dds_file).replace(texture_extract_dir, overrides_dir)
    if os.path.isfile(final_path) or not texture_utils.is_valid(dds_file):
        continue

    os.makedirs(os.path.dirname(final_path), exist_ok=True)
    subprocess.check_output([os.path.dirname(__file__) + "/cartoon", dds_file, final_path])
