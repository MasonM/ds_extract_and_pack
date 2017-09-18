import tkinter as tk
import tkinter.filedialog
import tkinter.scrolledtext


class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.data_dir = ""
        self.override_dir = ""
        self.pack()
        self.create_widgets()

    def create_widgets(self):
        self.create_dir_widgets()
        self.create_button_widgets()
        self.create_log_widgets()

    def create_dir_widgets(self):
        dir_info = (
            ("data_dir", "Data Directory"),
            ("override_dir", "Texture Override Directory")
        )
        for dir_type, label in dir_info:
            frame = tk.Frame(self.master, bd=5)
            frame.pack(fill=tk.X)

            label = tk.Label(frame, text=label, wraplength=150, width=15)
            label.pack(side=tk.LEFT)

            dir_string = tk.StringVar(frame)
            setattr(self, dir_type, dir_string)
            entry = tk.Entry(frame, width=10, textvariable=dir_string)
            entry.pack(side=tk.LEFT, expand=True, fill=tk.X)

            button = tk.Button(frame, text='Browse', command=self.dir_button_click(frame, dir_string))
            button.pack(side=tk.LEFT)

    def create_button_widgets(self):
        frame = tk.Frame(self.master, bd=5)
        frame.pack()

        patch_files = tk.Button(frame, text="Patch Data Files", command=self.master.destroy)
        patch_files.pack(side=tk.LEFT)

        restore_backup = tk.Button(frame, text="Restore Backup", command=self.master.destroy)
        restore_backup.pack(side=tk.RIGHT)

    def create_log_widgets(self):
        frame = tk.Frame(self.master, bd=5)
        frame.pack()

        logs = tk.scrolledtext.ScrolledText(frame, height=10, wrap=tk.WORD, pady=2, padx=2)
        logs.pack()

    @staticmethod
    def dir_button_click(frame, dir_string):
        def do_click():
            override_dir = tk.filedialog.askdirectory(initialdir='.', parent=frame, title='select directory')
            dir_string.set(override_dir)
            print(dir_string.get())
        return do_click


def main():
    root = tk.Tk()
    app = Application(master=root)
    app.mainloop()


if __name__ == '__main__':
    main()
