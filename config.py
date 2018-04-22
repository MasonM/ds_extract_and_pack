import os

in_memory = False
debug = False
zlib_compression_level = 1

log_msg_func = print
data_base_dir = os.path.abspath("test_files")
extract_base_dir = os.path.abspath("unpacked")
override_dir = os.path.abspath("overrides")

try:
    import winreg
    steam_dir_key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, "Software\Valve\Steam")
    steam_dir = winreg.QueryValueEx(steam_dir_key, "SteamPath")[0]
    target_file = os.path.join(steam_dir, "SteamApps", "Common", "Dark Souls Prepare to Die Edition", "DATA")
    target_file = os.path.abspath(target_file)
except (ImportError, OSError):
    target_file = None
