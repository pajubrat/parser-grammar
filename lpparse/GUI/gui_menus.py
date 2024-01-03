import tkinter as tk
from tkinter import messagebox

class MainMenu(tk.Menu):
    # This function is used to generate events for the main window
    def _event(self, sequence):
        def callback(*_):
            root = self.master.winfo_toplevel()
            root.event_generate(sequence)
        return callback

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        # File menu
        file_menu = tk.Menu(self, tearoff=False)
        file_menu.add_command(label='New...', command=self.todo)
        file_menu.add_command(label='Load...', command=self.todo)
        file_menu.add_command(label='Save', command=self.todo)
        file_menu.add_command(label='Preferences...', command=self.todo)
        file_menu.add_command(label='Quit', command=self.todo)
        self.add_cascade(label='File', menu=file_menu)

        # Analysis menu
        analysis_menu = tk.Menu(self, tearoff=False)
        analysis_menu.add_command(label='Run study', command=self._event('<<RunStudy>>'))
        analysis_menu.add_command(label='Analyze one expression', command=self._event('<<Analyze>>'))
        self.add_cascade(label='Analyze', menu=analysis_menu)

        # Settings menu
        settings_menu = tk.Menu(self, tearoff=False)
        settings_menu.add_command(label='Configure study...')
        settings_menu.add_command(label='Simulation settings...')
        settings_menu.add_command(label='Image settings...')
        self.add_cascade(label='Options', menu=settings_menu)

        # Help menu
        help_menu = tk.Menu(self, tearoff=False)
        help_menu.add_command(label='Help', command=self.show_help_dialog)
        self.add_cascade(label='Help', menu=help_menu)

    def show_help_dialog(self):
        about_message = 'Help'
        about_detail = ('Good things come to those who wait.')
        messagebox.showinfo(title='Help', message=about_message, detail=about_detail)

    def show_about_dialog(self):
        about_message = 'LPG Lab'
        about_detail = ('by Pauli Brattico 2024')
        messagebox.showinfo(title='About', message=about_message, detail=about_detail)

    def quit(self):
        pass

    def todo(self):
        pass


