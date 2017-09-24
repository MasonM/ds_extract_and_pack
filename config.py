import os

in_memory = False
debug = False
zlib_compression_level = 9

log_msg_func = print
data_base_dir = os.path.abspath("test_files")
extract_base_dir = os.path.abspath("test")
override_dir = os.path.abspath("final")
target_file = os.path.join(data_base_dir, "dvdbnd2.bdt")