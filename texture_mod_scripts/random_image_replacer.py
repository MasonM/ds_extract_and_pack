"""
Script to randomly replace extracted textures (set by "texture_extract_dir") with one of the
JPEGs in the directory set by "image_corpus_dir", and write the results to the directory set by
"overrides_dir".

Prevents duplicate mappings (i.e. only one JPEG gets mapped to each texture)
"""

from texture_mod_scripts import texture_utils
import glob
import os
import random
import shutil

base_dir = os.curdir
texture_extract_dir = base_dir + "/unpacked"
overrides_dir = base_dir + "/overrides"
image_corpus_dir = base_dir + "/corpus"

shutil.rmtree(overrides_dir)

corpus_images = glob.glob(image_corpus_dir + "/**/*.jpg", recursive=True)

for dds_file in glob.glob(texture_extract_dir + "/**/*.dds", recursive=True):
    print("processing " + dds_file + " ... ")
    final_path = os.path.abspath(dds_file).replace(texture_extract_dir, overrides_dir)
    if os.path.isfile(final_path) or not texture_utils.is_valid(dds_file):
        continue

    os.makedirs(os.path.dirname(final_path), exist_ok=True)
    replacement_img = random.choice(corpus_images)
    print("\treplacing with " + replacement_img)
    texture_utils.jpg_to_dds(replacement_img, dds_file, final_path)
    corpus_images.remove(replacement_img)
