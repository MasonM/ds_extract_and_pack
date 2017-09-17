import filecmp
import os
import pickle
import shutil

import config
from lib.bdt_file import BDTFile
from lib.bhd5_file import BHD5File
from lib.bhf3_file import BHF3File
from lib.bnd3_file import BND3File
from lib.dcx_file import DCXFile
from lib.tpf_file import TPFFile

extract_base_dir = os.path.abspath("test")
second_extract_base_dir = os.path.abspath("second_test")
output_base_dir = os.path.abspath("test_output")


def dir_prep(base_dir):
    for the_file in os.listdir(base_dir):
        file_path = os.path.join(base_dir, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path): shutil.rmtree(file_path)
        except Exception as e:
            print(e)


def do_read_test(filename, cls):
    dir_prep(extract_base_dir)
    config.extract_base_dir = extract_base_dir
    filename = os.path.abspath(filename)
    manifest = cls(open(filename, "rb"), filename).extract_file(depth=1)
    #pprint(manifest)
    return manifest


def do_write_test(filename, manifest, cls):
    # dir_prep(output_base_dir)
    filename = os.path.abspath(filename)
    cls(open(filename, "wb"), filename).create_file(manifest, depth=1)


def do_read_write_test(filename, cls):
    in_filename = os.path.join("..", "test_files", filename)
    out_filename = os.path.join(output_base_dir, filename)
    manifest_filename = os.path.join(output_base_dir, "manifest")
    #manifest = pickle.load(open(manifest_filename, "rb"))

    manifest = do_read_test(in_filename, cls)
    pickle.dump(manifest, open(manifest_filename, "wb"), protocol=4)

    do_write_test(out_filename, manifest, cls)

    if manifest.file_cls == BHD5File or manifest.file_cls == BHF3File:
        header_filepath = os.path.join(output_base_dir, os.path.basename(manifest.path))
        open(header_filepath, "wb").write(manifest.get_data(header_filepath, 1))

    #dir_prep(second_extract_base_dir)
    #config.extract_base_dir = second_extract_base_dir
    #cls(open(out_filename, "rb"), out_filename).extract_file(depth=1)

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
dcx_file = "m18_00_00_00.emeld."
#dcx_file="menu.drb."
#bdt_file = "m10_0000.tpf"
#bdt_file = "m16_0002.tpf"
#bdt_file = "good_c4100.chrtpf"
bdt_file = "dvdbnd1."

test = "bdt"

if test == "tpf":
    do_read_write_test(tpf_file + "tpf", TPFFile)
elif test == "bnd3":
    do_read_write_test(bnd3_file + "bnd3", BND3File)
elif test == "bhd5":
    do_read_write_test(bdt_file + "bhd5", BHD5File)
elif test == "bdt":
    filename = os.path.join("..", "test_files", "dvdbnd0.bdt")
    manifest_filename = os.path.join(output_base_dir, "manifest")
    do_read_write_test(bdt_file + "bdt", BDTFile)

    #pickle.dump(manifest, open(manifest_filename, "wb"))

    #manifest = pickle.loads(open(manifest_filename, "rb").read())
    #output_filename = os.path.join(output_base_dir, filename)
    #do_write_test(os.path.join(output_base_dir, bdt_file + "bdt"), manifest, BDTFile)

    #filename = os.path.join("..", "test_files", "dvdbnd1.bdt")
    #manifest = BDTFile(open(filename, "rb"), filename, extract_base_dir).extract_file(depth=1)
    #manifest_filename = os.path.join(output_base_dir, "dvdbnd1.manifest")
    #pickle.dump(manifest, open(manifest_filename, "wb"))

    #manifest_filename = os.path.join(output_base_dir, "manifest")
    #manifest = pickle.loads(open(manifest_filename, "rb").read())
    #manifest = do_read_test(os.path.join("..", "test_files", bdt_file + "bdt"), BDTFile)
    #do_write_test(os.path.join(output_base_dir, bdt_file + "bdt"), manifest, BDTFile)
    #do_read_test(os.path.join(output_base_dir, bdt_file + "bdt"), BDTFile)

    #do_read_test(os.path.join("..", "test_files", bdt_file + "bdt"), BDTFile)
    #do_read_test(os.path.join(output_base_dir, bdt_file + "bdt"), BDTFile)
elif test == "dcx":
    do_read_write_test(dcx_file + "dcx", DCXFile)

#print(get_hash_from_string("/param/GeneratorParam_m10_02_00_00.param"))
#pickle.dump(manifest, open(manifest_filename, "wb"))
