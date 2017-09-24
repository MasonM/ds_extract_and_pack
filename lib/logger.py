import config


class GuiTextLogger:
    def __init__(self, widget):
        self.widget= widget

    def log(self, msg):
        self.widget.configure(state='normal')
        self.widget.insert("end", msg + '\n')
        self.widget.configure(state='disabled')
        self.widget.yview("end")


def log(msg, depth, additional_prefix=""):
    prefix = ""
    if depth > 1:
        prefix += ("  " * (depth - 1)) + "|"
    config.log_msg_func(prefix + additional_prefix + msg)
