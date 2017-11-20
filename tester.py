import filecmp
import os
import pickle
import shutil

import config
from lib import BDTFile, BHD5File, BHF3File, BND3File, DCXFile, TPFFile

extract_base_dir = os.path.abspath("unpacked")
second_extract_base_dir = os.path.abspath("second_unpacked")
output_base_dir = os.path.abspath("test_output")
separator = "-" * 200


def dir_prep(base_dir):
    for the_file in os.listdir(base_dir):
        file_path = os.path.join(base_dir, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path): shutil.rmtree(file_path)
        except Exception as e:
            print(e)


def do_read_test(filename, cls, base_dir = extract_base_dir):
    print("{}\nSTARTING READ TEST WITH BASE DIR {}\n{}".format(separator, base_dir, separator))
    dir_prep(base_dir)
    config.extract_base_dir = base_dir
    filename = os.path.abspath(filename)
    manifest = cls(open(filename, "rb"), filename).extract_file(depth=1)
    #pprint(manifest)
    return manifest


def do_write_test(filename, manifest, cls):
    print(separator + "\nSTARTING WRITE TEST\n" + separator)
    # dir_prep(output_base_dir)
    filename = os.path.abspath(filename)
    cls(open(filename, "wb"), filename).create_file(manifest, depth=1)


def do_read_write_test(filename, cls):
    in_filename = os.path.join("test_files", filename)
    out_filename = os.path.join(output_base_dir, filename)
    #manifest_filename = os.path.join(output_base_dir, "manifest")
    #manifest = pickle.load(open(manifest_filename, "rb"))

    manifest = do_read_test(in_filename, cls)

    do_write_test(out_filename, manifest, cls)

    config.in_memory = False
    config.data_base_dir = output_base_dir
    do_read_test(out_filename, cls, second_extract_base_dir)

    print("{}\nCOMPARING OUTPUT {} TO {}\n{}".format(separator, out_filename, in_filename, separator))
    if filecmp.cmp(in_filename, out_filename):
        print("Files identical")
    else:
        print("Files differ")
        print("hexdiff {} {}".format(os.path.abspath(in_filename), out_filename))
        #filecmp.dircmp(extract_base_dir, second_extract_base_dir).report_full_closure()


#tpf_file = "o1470."
tpf_file = "c3320."
bnd3_file = "o1470.objbnd."
#bnd3_file = "c5200.anibnd."
#dcx_file = bnd3_file
dcx_file = "mystery."
#dcx_file="menu.drb."
#bdt_file = "m10_0000.tpf"
#bdt_file = "m16_0002.tpf"
#bdt_file = "real_m13_0001.tpf"
#bdt_file = "good_c4100.chrtpf"
bdt_file = "dvdbnd0."

test = "manual"

if test == "manual":
    config.extract_base_dir = extract_base_dir
    dir_prep(extract_base_dir)
    for file in ["dvdbnd0", "dvdbnd1"]:
        path = os.path.join("test_files", file + ".bdt")
        path = os.path.abspath(path)
        manifest = BDTFile(open(path, "rb"), path).extract_file(depth=1)
if test == "tpf":
    do_read_write_test(tpf_file + "tpf", TPFFile)
elif test == "bnd3":
    do_read_write_test(bnd3_file + "bnd3", BND3File)
elif test == "bhd5":
    do_read_write_test(bdt_file + "bhd5", BHD5File)
elif test == "bdt":
    filename = os.path.join("test_files", bdt_file + "bdt")
    manifest_filename = os.path.join(output_base_dir, bdt_file + "manifest")
    out_filename = os.path.join(output_base_dir, bdt_file + "bdt")

    manifest = pickle.loads(open(manifest_filename, "rb").read())
    do_write_test(out_filename, manifest, BDTFile)

    config.data_base_dir = output_base_dir
    manifest = do_read_test(out_filename, BDTFile, second_extract_base_dir)
    #pickle.dump(manifest, open(manifest_filename, "wb"), protocol=4)
    #do_read_write_test(bdt_file + "bdt", BDTFile)
elif test == "dcx":
    do_read_write_test(dcx_file + "dcx", DCXFile)

#print(get_hash_from_string("/param/GeneratorParam_m10_02_00_00.param"))
#pickle.dump(manifest, open(manifest_filename, "wb"))
