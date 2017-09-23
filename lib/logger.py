def log(msg, depth, additional_prefix=""):
    prefix = ""
    if depth > 1:
        prefix += ("  " * (depth - 1)) + "|"
    print(prefix + additional_prefix + msg)
