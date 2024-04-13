import tkinter as tk
from tkinter import ttk


class LabeledEntry(ttk.LabelFrame):
    def __init__(self, parent, label_text, text_variable, **kwargs):
        super().__init__(parent, text=label_text)
        self.entry = ttk.Entry(self, textvariable=text_variable, font=('Calibri', 20), width=40, **kwargs)
        self.entry.grid(row=0, column=0, sticky='NWSE')

class OKCancelButtons(tk.Frame):
    def __init__(self, parent, OK_function, Cancel_function):
        super().__init__(parent)
        OK_button = tk.Button(self, text='Update settings', bg='#ddffdd', fg='#000000', font=('Calibri', 12), command=OK_function)
        OK_button.grid(row=0, column=0, sticky=tk.E, padx=20, pady=20)
        OK_button.configure(width=15, height=2)
        CANCEL_button = tk.Button(self, text='Cancel', bg='#ffdddd', fg='#000000', font=('Calibri', 12), command=Cancel_function)
        CANCEL_button.grid(row=0, column=1, sticky=tk.E, padx=20, pady=20)
        CANCEL_button.configure(width=15, height=2)
        self.grid_columnconfigure(0, weight=1)
