import os

in_memory = True
debug = True
zlib_compression_level = 9

data_base_dir = os.path.abspath(os.path.join("..", "test_files"))
extract_base_dir = os.path.abspath("test")
override_dir = "" #os.path.abspath("final")