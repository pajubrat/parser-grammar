import tkinter as tk
from tkinter import ttk, font


class LogText(tk.Toplevel):
    def __init__(self, parent, filename, text, *args, **kwargs):
        super().__init__(parent, *args, *kwargs)

        self.title('Derivational log file')

        # Label Frame with the message
        lb = tk.LabelFrame(self, text=text, font=('Calibri', 25))
        lb.grid(padx=10, pady=10, sticky='N')

        # Status bar
        tk.Label(self, text=filename, font=('Calibri', 15)).grid(row=1, column=0, sticky='E')

        # Window holding the text from the derivational log file
        self.textWindow = tk.Text(lb, undo=False, spacing1=4, spacing2=2, spacing3=4, height=40, width=150, wrap='none', font=("Courier New", 12))
        self.GetTextFromFile(filename)
        self.textWindow.grid(row=0, column=0, sticky='NSEW')
        self.textWindow.configure(bg='white', fg='black')
        self.focus_set()
        self.grab_set()
        self.wm_attributes("-topmost", True)

        # Mark errors
        self.mark_errors()

        # Create scrollbars
        sby = ttk.Scrollbar(lb, orient=tk.VERTICAL, command=self.textWindow.yview)
        sbx = ttk.Scrollbar(lb, orient=tk.HORIZONTAL, command=self.textWindow.xview)
        self.textWindow.configure(yscrollcommand=sby.set)
        self.textWindow.configure(xscrollcommand=sbx.set)
        sbx.grid(row=1, column=0, sticky='WES')
        sby.grid(row=0, column=1, sticky='NSW')

    def GetTextFromFile(self, filename):
        """Gets the text from the derivational log file"""
        text = open(filename, 'r', encoding='utf8').read()
        self.textWindow.insert('1.0', text)
        self.textWindow.focus()

    def mark_errors(self):
        """Highlights crashes in the derivational log file"""
        start_index = '0.1'
        end_index = 'end'
        while True:
            start_index = self.textWindow.search('@@', start_index, end_index)
            if start_index:
                start_pos = f"{start_index.split('.')[0]}.0"
                end_index = f"{start_index.split('.')[0]}.999"
                self.textWindow.tag_add("ERROR", start_pos, end_index)
                start_index = end_index
                end_index = 'end'
            else:
                break

        self.textWindow.tag_configure('ERROR', background="#FFCCCC", foreground="black")
