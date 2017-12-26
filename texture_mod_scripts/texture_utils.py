"""
Various utility functions for dealing with textures
"""

import re
import subprocess
from wand.image import Image


def is_valid(img_file):
    """
    Checks if the texture file given by img_file is something that is a good candidate for replacement.
    """
    # Don't try to convert fonts or menu textures, since that messes up the game
    if "/font/" in img_file or "/menu/" in img_file:
        print("\tskip: font or menu texture")
        return False

    if re.match(".*_[snL](?:_\d+)?\.dds$", img_file):
        print("\tskip: normal or specular map")
        return False

    if "_lit_" in img_file.lower():
        print("\tskip: map file lighting")
        return False
    
    if "EnvSpc" in img_file or "EnvDif" in img_file:
        print("\tskip: environmental specular or diffuse map")
        return False

    command = ["/usr/bin/identify", "-format", "%[type],%[width],%[mean],%C", img_file]
    command_output = subprocess.check_output(command).decode("ascii")
    print("\tIdentify output: {}".format(command_output))

    try:
        color_type, width, channel_mean, compression = command_output.split(',')

        if compression.lower() == "none":
            print("\tskip: unable to determine compression format (corruption?)")
            return False

        if int(width) < 64:
            print("\tskip: too small, width = {}".format(int(width)))
            return False

        if color_type.lower() in ("grayscale", "grayscalematte"):
            print("\tskip: gray, probably text")
            return False

        if float(channel_mean) > 65530:
            print("\tskip: mostly one color (alpha mask?)")
            return False
    except ValueError:
        print("\tskip: got valuerror for {}".format(img_file))
        return False

    blacklist = ["o7501_00", "m10_back_ground", "sfx/tex/s13491", "sfx/tex/s05197",
        "sfx/tex/s05087", "sfx/tex/s05213", "sfx/tex/s12860", "sfx/tex/s01800", "sfx/tex/s00022",
        "map/m15/m15_wall_white_02", "map/m15/m15_wall_pillar_03", "map/m15/m15_wall_relief_04",
        "map/m10/m10_wall_building_12", "map/m15/m15_arch_03", "map/m15/m15_chapel_wall_01",
        "obj/o4550/o4550", "other/title", "other/soul_sequence", "other/DGBTEX"]
    
    for pattern in blacklist:
        if pattern in img_file:
            print("\tskip: hit misc blacklist")
            return False
    
    return True


def dds_to_jpg(dds_path, output_path):
    with Image(filename=dds_path) as img:
        with img.convert('jpeg') as converted:
            converted.compression_quality = 25
            converted.save(filename=output_path)


def jpg_to_dds(jpg_path, orig_dds_path, output_path):
    with Image(filename=orig_dds_path) as orig_dds:
        with Image(filename=jpg_path) as jpg_img:
            with jpg_img.clone() as final_img:
                final_img.format = "dds"
                # Seems orig_dds.compression always returns bzip
                compression_type = subprocess.check_output(["/usr/bin/identify", "-format", "%C", orig_dds_path]).decode("ascii").lower()
                print("\tcompression type: {}".format(compression_type))
                final_img.compression = compression_type
                final_img.resize(orig_dds.width, orig_dds.height)
                if orig_dds.alpha_channel:
                    final_img.composite_channel('default_channels', orig_dds, 'copy_opacity', 0, 0)
                final_img.save(filename=output_path)
