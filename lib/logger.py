import config


class GuiTextLogger:
    def __init__(self, widget, master_update_callback):
        self.widget = widget
        self.master_update_callback= master_update_callback

    def log(self, msg):
        self.widget.configure(state='normal')
        self.widget.insert("end", msg + '\n')
        self.widget.configure(state='disabled')
        self.widget.yview("end")
        self.master_update_callback()


def log(msg, depth, additional_prefix=""):
    if not config.debug:
        return
    prefix = ""
    if depth > 1:
        prefix += ("  " * (depth - 1)) + "|"
    config.log_msg_func(prefix + additional_prefix + msg)
