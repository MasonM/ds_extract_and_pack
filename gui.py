import os
import pickle
import tkinter as tk
import tkinter.filedialog
import tkinter.scrolledtext
import tkinter.messagebox
import tkinter.ttk as ttk

import config
import lib


class Application(tk.Frame):
    MODE_EXTRACT = 0
    MODE_REPACK = 1
    MODE_PATCH = 2

    TARGET_TYPE_ALL = "All data files in directory"
    TARGET_TYPE_FILE = "Specific data file"

    def __init__(self, master=None):
        super().__init__(master)
        self.mode = tk.IntVar(value=self.MODE_EXTRACT)
        self.target = tk.StringVar(value=config.target_file)
        self.target_type = tk.StringVar(value=self.TARGET_TYPE_FILE if config.target_file else self.TARGET_TYPE_ALL)
        self.extract_base_dir = tk.StringVar(value=config.extract_base_dir)
        self.override_dir = tk.StringVar(value=config.override_dir)
        self.debug = tk.BooleanVar(value=config.debug)

        self.master.columnconfigure(0, weight=1)
        self.master.columnconfigure(1, weight=1)
        self.master.rowconfigure(0, weight=1, pad=15)
        self.master.rowconfigure(1, weight=1, pad=15)
        self.master.rowconfigure(2, weight=10, pad=15)

        self.create_mode_widgets()
        self.create_target_widgets()
        self.create_option_widgets()
        self.create_button_widgets()
        self.create_log_widgets()

        self.mode_changed()
        self.target_type_changed()

    def create_target_widgets(self):
        label_frame = tk.LabelFrame(self.master, text="Target", bd=1, relief=tk.RAISED)
        label_frame.grid(row=0, column=1, sticky=tk.NSEW)
        label_frame.columnconfigure(1, weight=1)
        label_frame.rowconfigure(0, weight=1)

        self.target_type.trace("w", self.target_type_changed)
        ttk.Combobox(label_frame, values=(self.TARGET_TYPE_FILE, self.TARGET_TYPE_ALL), state="readonly",
                     textvariable=self.target_type).grid(row=0, sticky=tk.W)

        self.data_file_frame = tk.Frame(label_frame, bd=5)
        self.data_file_frame.grid(row=0, column=1, sticky=tk.EW)
        self.create_filedir_widgets(self.data_file_frame, self.target, callback=self.file_button_click)

        self.data_dir_frame = tk.Frame(label_frame, bd=5)
        self.data_dir_frame.grid(row=0, column=1, sticky=tk.EW)
        self.create_filedir_widgets(self.data_dir_frame, self.target, callback=self.dir_button_click)

    def target_type_changed(self, *args):
        target_type = self.target_type.get()
        if target_type == self.TARGET_TYPE_ALL:
            self.data_dir_frame.grid()
            self.data_file_frame.grid_remove()
        elif target_type == self.TARGET_TYPE_FILE:
            self.data_dir_frame.grid_remove()
            self.data_file_frame.grid()

    def create_mode_widgets(self):
        frame = tk.LabelFrame(self.master, text="Mode", bd=1, relief=tk.RAISED)
        frame.grid(row=0, sticky=tk.NSEW, rowspan=2)

        tk.Radiobutton(frame, text="Extract data files", variable=self.mode, value=self.MODE_EXTRACT,
                       command=self.mode_changed).grid(row=0, sticky=tk.W)

        tk.Radiobutton(frame, text="Repack data files", variable=self.mode, value=self.MODE_REPACK,
                       command=self.mode_changed).grid(row=1, sticky=tk.W)

        tk.Radiobutton(frame, text="Patch data files", variable=self.mode, value=self.MODE_PATCH,
                       command=self.mode_changed).grid(row=2, sticky=tk.W)

    def mode_changed(self):
        mode = self.mode.get()
        if mode == self.MODE_EXTRACT:
            self.override_dir_frame.grid_remove()
            self.extract_base_dir_frame.grid()
        elif mode == self.MODE_REPACK:
            self.override_dir_frame.grid()
            self.extract_base_dir_frame.grid()
        elif mode == self.MODE_PATCH:
            self.override_dir_frame.grid()
            self.extract_base_dir_frame.grid_remove()

    def create_option_widgets(self):
        label_frame = tk.LabelFrame(self.master, text="Options", bd=1, relief=tk.RAISED)
        label_frame.grid(row=1, column=1, sticky=tk.NSEW)
        label_frame.columnconfigure(0, weight=1)

        self.extract_base_dir_frame = tk.Frame(label_frame, bd=5)
        self.extract_base_dir_frame.grid(row=2, sticky=tk.EW)
        self.create_filedir_widgets(self.extract_base_dir_frame, self.extract_base_dir, "Base directory for extracted files")

        self.override_dir_frame = tk.Frame(label_frame, bd=5)
        self.override_dir_frame.grid(row=3, sticky=tk.EW)
        self.create_filedir_widgets(self.override_dir_frame, self.override_dir, "Texture override directory (optional)")

        debug_frame = tk.Frame(label_frame, bd=5)
        debug_frame.grid(row=4, sticky=tk.EW)
        tk.Label(debug_frame, text="Debug", width=20).grid(row=0, sticky=tk.E)
        tk.Checkbutton(debug_frame, variable=self.debug).grid(row=0, column=1, sticky=tk.EW)

    def create_filedir_widgets(self, frame, string_var, label=None, callback=None):
        callback = callback or self.dir_button_click
        col_weights = []
        if label:
            tk.Label(frame, text=label, wraplength=150, width=20) \
                .grid(row=0, column=len(col_weights), sticky=tk.E)
            col_weights.append(0)

        tk.Entry(frame, width=10, textvariable=string_var) \
            .grid(row=0, column=len(col_weights), sticky=tk.EW)
        col_weights.append(2)

        tk.Button(frame, text='Browse', command=callback(frame, string_var)) \
            .grid(row=0, column=len(col_weights), sticky=tk.E)
        col_weights.append(0)

        for column_num, weight in enumerate(col_weights):
            frame.columnconfigure(column_num, weight=weight)

    def create_button_widgets(self):
        frame = tk.Frame(self.master, bd=5)
        frame.grid(row=2, columnspan=2, sticky=tk.N)

        self.execute_button = tk.Button(frame, text="Execute", command=self.execute)
        self.execute_button.grid(row=0, padx=10)

        self.restore_backup_button = tk.Button(frame, text="Restore Backup", command=self.master.destroy)
        self.restore_backup_button.grid(row=0, column=1)

    def create_log_widgets(self):
        self.log_widget = tk.scrolledtext.ScrolledText(self.master, wrap=tk.WORD, pady=2, padx=2, state=tk.DISABLED)
        self.log_widget.grid(row=3, columnspan=2, sticky=tk.NSEW)
        self.logger = lib.logger.GuiTextLogger(self.log_widget, self.master.update)

    def execute(self):
        self.execute_button.configure(state=tk.DISABLED)
        self.restore_backup_button.configure(state=tk.DISABLED)
        self.do_execute()
        self.execute_button.configure(state=tk.NORMAL)
        self.restore_backup_button.configure(state=tk.NORMAL)

    def do_execute(self):
        target_type = self.target_type.get()
        target = self.target.get()
        if target_type == self.TARGET_TYPE_FILE:
            if not target:
                tk.messagebox.showerror("Error", "Must set target file")
                return
            if not os.path.isfile(target):
                tk.messagebox.showerror("Error", "Target is not a file")
                return
            target_files = [target]
        else:
            if not self.check_directory(target, type="target"):
                return
            target_files = os.listdir(target)

        mode = self.mode.get()
        if mode in (self.MODE_EXTRACT, self.MODE_REPACK) and \
                not self.check_directory(self.extract_base_dir.get(), type="extracted files"):
            return

        if mode == self.MODE_PATCH and not self.check_directory(self.override_dir.get(), type="texture overrides"):
            return

        config.extract_base_dir = self.extract_base_dir.get()
        config.debug = self.debug.get()
        config.log_msg_func = self.logger.log
        config.in_memory = (mode in (self.MODE_REPACK, self.MODE_PATCH))
        config.override_dir = self.override_dir.get()
        found = False

        if mode == self.MODE_REPACK:
            for target_file in target_files:
                manifest_filename = target_file + ".manifest"
                if os.path.isfile(manifest_filename):
                    found = True
                    self.logger.log("Repacking data file {}".format(target_file))
                    manifest = pickle.load(open(manifest_filename, "rb"))
                    data = manifest.get_data(target_file, 1)
                    open(target_file + ".repacked", 'wb').write(data)
                    self.logger.log("Finished repacking data file {}".format(target_file))
        else:
            if mode == self.MODE_EXTRACT:
                for target_path in target_files:
                    binary_reader = lib.BinaryFile.class_for_filename(target_path)
                    if not binary_reader:
                        continue
                    found = True
                    self.logger.log("Extracting file {} to {}".format(target, config.extract_base_dir))
                    manifest = binary_reader.extract_file(depth=1)
                    pickle.dump(manifest, open(target + ".manifest", "wb"), protocol=4)
                    self.logger.log("Finished extracting {}".format(target_path))
            elif mode == self.MODE_PATCH:
                for target_path in target_files:
                    binary_reader = lib.BinaryFile.class_for_filename(target_path)
                    if not binary_reader:
                        continue
                    found = True
                    self.logger.log("Patching file {}".format(target_path))
                    manifest = binary_reader.extract_file(depth=1)
                    data = manifest.get_data(target_path, 1)
                    open(target_path + ".repacked", "wb").write(data)
                    self.logger.log("Finished patching {}".format(target_path))
        if not found:
            if target_type == self.TARGET_TYPE_FILE:
                tk.messagebox.showerror("Error", "Unknown file type for " + target_type)
            else:
                tk.messagebox.showerror("Error", "No DS data files found in " + target_type)

    @staticmethod
    def check_directory(directory, type):
        if not directory:
            tk.messagebox.showerror("Error", "Must set base directory for " + type)
            return False
        elif not os.path.isdir(directory):
            tk.messagebox.showerror("Error", "Invalid base directory for " + type)
            return False
        return True

    @staticmethod
    def file_button_click(frame, file_string):
        def do_click():
            data_file = tk.filedialog.askopenfilename(initialdir='.', parent=frame, title='select data file')
            file_string.set(data_file)
            print(file_string.get())
        return do_click

    @staticmethod
    def dir_button_click(frame, dir_string):
        def do_click():
            directory = tk.filedialog.askdirectory(initialdir='.', parent=frame, title='select directory')
            dir_string.set(os.path.normpath(directory))
            print(dir_string.get())
        return do_click


def main():
    root = tk.Tk()
    app = Application(master=root)
    app.mainloop()


if __name__ == '__main__':
    main()
