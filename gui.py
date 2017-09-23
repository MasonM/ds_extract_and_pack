import os
import pickle
import tkinter as tk
import tkinter.filedialog
import tkinter.scrolledtext
import tkinter.messagebox

import config
import lib


class Application(tk.Frame):
    MODE_EXTRACT = 0
    MODE_REPACK = 1
    MODE_PATCH = 2

    TARGET_TYPE_ALL = 0
    TARGET_TYPE_FILE = 1

    def __init__(self, master=None):
        super().__init__(master)
        self.mode = tk.IntVar(value=self.MODE_EXTRACT)
        self.target_type = tk.IntVar(value=self.TARGET_TYPE_FILE)
        self.row_num = 0

        for x in range(4):
            self.master.columnconfigure(x, weight=1)
            self.master.rowconfigure(x, weight=1, pad=15)

        self.create_mode_widgets()
        self.create_target_widgets()
        self.create_option_widgets()
        self.create_button_widgets()
        self.create_log_widgets()
        self.mode_changed()
        self.target_changed()

    def create_target_widgets(self):
        label_frame = tk.LabelFrame(self.master, text="Target", bd=1, relief=tk.RAISED)
        label_frame.grid(row=self.row_num, sticky=tk.EW)
        label_frame.columnconfigure(0, weight=1)

        tk.Radiobutton(label_frame, text="All data files in directory",
                       variable=self.target_type, value=self.TARGET_TYPE_ALL,
                       command=self.target_changed).grid(row=0, sticky=tk.W)

        tk.Radiobutton(label_frame, text="Specific data file",
                       variable=self.target_type, value=self.TARGET_TYPE_FILE,
                       command=self.target_changed).grid(row=1, sticky=tk.W)

        self.data_file = tk.StringVar()
        self.data_file_frame = tk.Frame(label_frame, bd=5)
        self.data_file_frame.grid(row=2, sticky=tk.EW)
        self.create_dir_widgets(self.data_file_frame, self.data_file, "Data file", self.file_button_click)

        self.data_dir = tk.StringVar()
        self.data_dir_frame = tk.Frame(label_frame, bd=5)
        self.data_dir_frame.grid(row=3, sticky=tk.EW)
        self.create_dir_widgets(self.data_dir_frame, self.data_dir, "Data directory", self.dir_button_click)

        self.row_num += 1

    def create_mode_widgets(self):
        frame = tk.LabelFrame(self.master, text="Mode", bd=1, relief=tk.RAISED)
        frame.grid(row=self.row_num, sticky=tk.EW)

        tk.Radiobutton(frame, text="Extract data files", variable=self.mode, value=self.MODE_EXTRACT,
                       command=self.mode_changed).grid(row=0, column=1, sticky=tk.W)

        tk.Radiobutton(frame, text="Repack data files", variable=self.mode, value=self.MODE_REPACK,
                       command=self.mode_changed).grid(row=2, column=1, sticky=tk.W)

        tk.Radiobutton(frame, text="Patch data files", variable=self.mode, value=self.MODE_PATCH,
                       command=self.mode_changed).grid(row=3, column=1, sticky=tk.W)

        self.row_num += 1

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

    def target_changed(self):
        target = self.target_type.get()
        if target == self.TARGET_TYPE_ALL:
            self.data_dir_frame.grid()
            self.data_file_frame.grid_remove()
        elif target == self.TARGET_TYPE_FILE:
            self.data_dir_frame.grid_remove()
            self.data_file_frame.grid()

    def create_option_widgets(self):
        label_frame = tk.LabelFrame(self.master, text="Options", bd=1, relief=tk.RAISED)
        label_frame.grid(row=self.row_num, sticky=tk.EW)
        label_frame.columnconfigure(0, weight=1)

        self.extract_base_dir = tk.StringVar()
        self.extract_base_dir_frame = tk.Frame(label_frame, bd=5)
        self.extract_base_dir_frame.grid(row=2, sticky=tk.EW)
        self.create_dir_widgets(self.extract_base_dir_frame, self.extract_base_dir, "Base directory for extracted files")

        self.override_dir = tk.StringVar()
        self.override_dir_frame = tk.Frame(label_frame, bd=5)
        self.override_dir_frame.grid(row=3, sticky=tk.EW)
        self.create_dir_widgets(self.override_dir_frame, self.override_dir, "Texture override directory")

        self.row_num += 1

    def create_dir_widgets(self, frame, string_var, label, callback=None):
        callback = callback or self.dir_button_click
        tk.Label(frame, text=label, wraplength=150, width=20) \
            .grid(row=0, sticky=tk.E)
        tk.Entry(frame, width=10, textvariable=string_var) \
            .grid(row=0, column=1, sticky=tk.EW)
        tk.Button(frame, text='Browse', command=callback(frame, string_var)) \
            .grid(row=0, column=2, sticky=tk.E)

        frame.columnconfigure(0, weight=0)
        frame.columnconfigure(1, weight=2)
        frame.columnconfigure(2, weight=0)

    def create_button_widgets(self):
        frame = tk.Frame(self.master, bd=5)
        frame.grid(row=self.row_num)

        tk.Button(frame, text="Execute", command=self.do_execute).grid(row=0, padx=10)
        tk.Button(frame, text="Restore Backup", command=self.master.destroy).grid(row=0, column=1)

        self.row_num += 1

    def create_log_widgets(self):
        frame = tk.Frame(self.master, bd=5)
        frame.grid(row=self.row_num)

        tk.scrolledtext.ScrolledText(frame, height=10, wrap=tk.WORD, pady=2, padx=2).grid()

    def do_execute(self):
        target_type = self.target_type.get()
        if target_type == self.TARGET_TYPE_FILE:
            target = self.data_file.get()
            if not target:
                tk.messagebox.showerror("Error", "Must set target file")
                return
            if not os.path.isfile(target):
                tk.messagebox.showerror("Error", "Target is not a file")
                return
            target_files = [target]
        else:
            target = self.data_dir.get()
            if not self.check_directory(target, type="target"):
                return
            target_files = os.listdir(target)

        mode = self.mode.get()
        if mode == self.MODE_EXTRACT:
            if not self.check_directory(self.extract_base_dir.get(), type="extracted files"):
                return

            config.extract_base_dir = self.extract_base_dir.get()
            recognized = self.extract_files(target_files)
            if not recognized:
                if target_type == self.TARGET_TYPE_FILE:
                    tk.messagebox.showerror("Error", "Unknown file type for " + target)
                else:
                    tk.messagebox.showerror("Error", "Not DS data files foudn in " + target)
                return
        elif mode == self.MODE_REPACK:
            if not self.check_directory(self.extract_base_dir.get(), type="extracted files"):
                return
            if not self.check_directory(self.override_dir.get(), type="texture overrides"):
                return
            pass
        elif mode == self.MODE_PATCH:
            pass

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
    def extract_files(target_files):
        recognized = []
        for target in target_files:
            binary_reader = lib.BinaryFile.class_for_filename(target)
            if not binary_reader:
                continue

            manifest = binary_reader.extract_file(depth=1)
            manifest_filename = target.rsplit(".", 1)[0] + ".manifest"
            pickle.dump(manifest, open(manifest_filename, "wb"), protocol=4)
            recognized.append(target)
        return recognized

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
            dir_string.set(directory)
            print(dir_string.get())
        return do_click


def main():
    root = tk.Tk()
    app = Application(master=root)
    app.mainloop()


if __name__ == '__main__':
    main()
