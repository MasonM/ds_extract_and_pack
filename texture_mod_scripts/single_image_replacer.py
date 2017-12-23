from . import texture_utils
import glob
import os
import shutil

base_dir = os.curdir
texture_extract_dir = base_dir + "/unpacked"
overrides_dir = base_dir + "/overrides"
image = base_dir + "/image.jpg"

shutil.rmtree(overrides_dir)

for dds_file in glob.glob(texture_extract_dir + "/**/*.dds", recursive=True):
    print("processing " + dds_file + " ... ")
    final_path = os.path.abspath(dds_file).replace(texture_extract_dir, overrides_dir)
    if os.path.isfile(final_path) or not texture_utils.is_valid(dds_file):
        continue

    os.makedirs(os.path.dirname(final_path), exist_ok=True)
    texture_utils.jpg_to_dds(image, dds_file, final_path)
