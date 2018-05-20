"""
Script to replace every single extracted texture (set by "texture_extract_dir") with a
given image (set by "image"), and write the results to the directory set by "overrides_dir".
"""

from texture_mod_scripts import texture_utils
import glob
import os
import shutil
import subprocess

base_dir = os.path.abspath(os.curdir)
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
    subprocess.check_output(["/usr/bin/convert", dds_file, "-dither", "FloydSteinberg", "-remap", base_dir + "/texture_mod_scripts/gameboy_palette.png", final_path])
