import os
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import keyboard
from lib_branch import get_paths
from lib_branch import is_sub_path
from lib_sanitizer import *

valid_date_formats = [
    '19960513', '960513', '1996/05/13', '1996-05-13',
    '96/05/13', '96-05-13', '96/5/13', '96-5-13'
]


class ImageBrowser(tk.Tk):
    def __init__(self, branch_path, sync_function):
        super().__init__()
        self.sync = sync_function
        self.title("Image Browser")
        self.geometry("800x600")

        self.branch_path = branch_path
        self.folder_path = "transactions"
        self.image_files = []
        for f in os.listdir(self.folder_path):
            if not f.endswith(('.jpg', '.png', '.jpeg')):
                continue
            branch = f.split('_')[1].replace('-','/')
            if is_sub_path(branch, self.branch_path):
                self.image_files.append(f)

        self.current_index = 0
        self.branches = [b_path.replace('-', '/') for b_path in get_paths()]
        keyboard.add_hotkey('esc', lambda: self.load_info(self.image_files[self.current_index]))

        # UI 구성 요소
        self.create_widgets()
        self.bind_events()
        self.show_image()
        self.mainloop()

    def create_widgets(self):
        self.image_label = tk.Label(self)
        self.image_label.pack(side="left", fill="both", expand=True)

        self.info_frame = ttk.Frame(self)
        self.info_frame.pack(side="right", fill="both", expand=False)

        self.date_label = ttk.Label(self.info_frame, text="Date")
        self.date_label.pack(anchor="w")
        self.date_entry = ttk.Entry(self.info_frame, width=30)
        self.date_entry.pack(fill="x")

        self.branch_label = ttk.Label(self.info_frame, text="Branch")
        self.branch_label.pack(anchor="w")
        self.branch_var = tk.StringVar()
        self.branch_dropdown = ttk.Combobox(
            self.info_frame,
            textvariable=self.branch_var,
            values=self.branches,
            state='readonly'
        )
        self.branch_dropdown.pack(fill="x")

        self.transaction_label = ttk.Label(self.info_frame, text="Transaction")
        self.transaction_label.pack(anchor="w")
        self.transaction_entry = ttk.Entry(self.info_frame, width=30)
        self.transaction_entry.pack(fill="x")

        self.description_label = ttk.Label(self.info_frame, text="Description")
        self.description_label.pack(anchor="w")
        self.description_entry = ttk.Entry(self.info_frame, width=30)
        self.description_entry.pack(fill="x")

        self.save_button = ttk.Button(self.info_frame, text="Save", command=self.save_info)
        self.save_button.pack(pady=10)

    def bind_events(self):
        self.bind("<Control-Right>", self.next_image)
        self.bind("<Control-Left>", self.prev_image)

    def show_image(self):
        image_path = os.path.join(self.folder_path, self.image_files[self.current_index])
        image = Image.open(image_path)
        image.thumbnail((600, 600))
        photo = ImageTk.PhotoImage(image)

        self.image_label.config(image=photo)
        self.image_label.image = photo

        self.load_info(self.image_files[self.current_index])

    def load_info(self, filename):
        date, branch, transaction, description = filename.split('_')
        description = description.split('.')[0]

        self.date_entry.delete(0, tk.END)
        self.date_entry.insert(0, date)

        branch = branch.replace('-', '/')
        self.branch_var.set(branch)

        self.transaction_entry.delete(0, tk.END)
        self.transaction_entry.insert(0, transaction)

        self.description_entry.delete(0, tk.END)
        self.description_entry.insert(0, description)

    def save_info(self):
        # Date 입력 유효성 검사
        input_date = self.date_entry.get()
        date = format_date(input_date)
        if date is None:
            error_message = f"Invalid date format. Please enter the date in one of the following formats: {', '.join(valid_date_formats)}. You entered: '{input_date}'."
            messagebox.showinfo("Fail", str(error_message))
            return

        # Branch 입력 유효성 검사
        branch = self.branch_var.get().replace('/','-')

        # Transaction 입력 유효성 검사
        try:
            transaction = int(self.transaction_entry.get())
            if transaction > 0:
                transaction = f'+{transaction}'
            else:
                transaction = f'{transaction}'
        except:
            error_message = "Invalid input for cash flow. Please enter numeric values."
            messagebox.showinfo("Fail", str(error_message))
            return

        # Description 입력 유효성 검사
        description = self.description_entry.get()
        if not is_valid_txt(description):
            error_message = f"Content text contains invalid characters. Please avoid using the following characters: {', '.join(invalid_characters)}."
            messagebox.showinfo("Fail", str(error_message))
            return

        old_filename = self.image_files[self.current_index]
        new_filename = f"{date}_{branch}_{transaction}_{description}.jpg"

        old_path = os.path.join(self.folder_path, old_filename)
        new_path = os.path.join(self.folder_path, new_filename)

        try:
            os.rename(old_path, new_path)
            self.image_files[self.current_index] = new_filename
            self.show_image()
            self.destroy()
            self.sync()
        except Exception as e:
            messagebox.showinfo("Fail", str(e))

    def next_image(self, event=None):
        self.current_index = (self.current_index + 1) % len(self.image_files)
        self.show_image()

    def prev_image(self, event=None):
        self.current_index = (self.current_index - 1) % len(self.image_files)
        self.show_image()
