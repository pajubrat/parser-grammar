import tkinter as tk
from tkinter import messagebox

menu_font = ('Calibri', 20)


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
        file_menu = tk.Menu(self, tearoff=False, font=menu_font)
        file_menu.config(font=menu_font)
        file_menu.add_command(label='New...', command=self.todo)
        file_menu.add_command(label='Load Study...', command=self._event('<<LoadStudy>>'))
        file_menu.add_command(label='Save Study As...', command=self._event('<<SaveStudy>>'))
        file_menu.add_command(label='Preferences...', command=self.todo)
        file_menu.add_command(label='Quit', command=self.todo)
        self.add_cascade(label='File', menu=file_menu)

        # Analysis menu
        analysis_menu = tk.Menu(self, tearoff=False,font=menu_font)
        analysis_menu.add_command(label='Analyze expression', command=self._event('<<Analyze>>'))
        self.add_cascade(label='Analyse', menu=analysis_menu)

        # Study menu
        study_menu = tk.Menu(self, tearoff=False, font=menu_font)
        study_menu.add_command(label='New from corpus...', command=self._event('<<CreateNewFromFile>>'))
        study_menu.add_command(label='Run complete study', command=self._event('<<RunStudy>>'))
        self.add_cascade(label='Study', menu=study_menu)

        # Examine_results_menu
        examine_results_menu = tk.Menu(self, tearoff=False, font=menu_font)
        examine_results_menu.add_command(label='Results...', command=self.todo)
        examine_results_menu.add_command(label='Derivation...', command=self.todo)
        examine_results_menu.add_command(label='Examine log...', command=self.todo)
        self.add_cascade(label='Results', menu=examine_results_menu)

        # Theory/UG menu
        theory_menu = tk.Menu(self, tearoff=False, font=menu_font)
        theory_menu.add_command(label='UG parameters...', command=self._event('<<TheorySettings>>'))
        self.add_cascade(label='Theory', menu=theory_menu)

        # Settings menu
        settings_menu = tk.Menu(self, tearoff=False, font=menu_font)
        settings_menu.add_command(label='Configure study...')
        settings_menu.add_command(label='Simulation settings...')
        settings_menu.add_command(label='Image settings...')
        self.add_cascade(label='Options', menu=settings_menu)

        # Help menu
        help_menu = tk.Menu(self, tearoff=False, font=menu_font)
        help_menu.add_command(label='Help', command=self.show_help_dialog)
        help_menu.add_command(label='About', command=self.show_about_dialog)
        self.add_cascade(label='Help', menu=help_menu)

    def show_help_dialog(self):
        about_message = 'Help'
        about_detail = ('Good things come to those who wait.')
        messagebox.showinfo(title='Help', message=about_message, detail=about_detail)

    def show_about_dialog(self):
        about_message = 'LPG Lab'
        about_detail = ('GUI Interface v. 0.1\nLPG/UG version 19.0\nby Pauli Brattico 2024')
        messagebox.showinfo(title='About', message=about_message, detail=about_detail)

    def quit(self):
        pass

    def todo(self):
        pass


class GraphicsMenu(tk.Menu):
    def _event(self, sequence):
        def callback(*_):
            root = self.master.winfo_toplevel()
            root.event_generate(sequence)
        return callback

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        # File menu
        file_menu = tk.Menu(self, tearoff=False, font=menu_font)
        file_menu.config(font=menu_font)
        file_menu.add_command(label='New...', command=self.todo)
        file_menu.add_command(label='Load...', command=self.todo)
        file_menu.add_command(label='Save', command=self.todo)
        file_menu.add_command(label='Preferences...', command=self.todo)
        file_menu.add_command(label='Quit', command=self.todo)
        self.add_cascade(label='File', menu=file_menu)

        # Select image menu
        select_image = tk.Menu(self, tearoff=False, font=menu_font)
        select_image.add_command(label='PF-interface', command=self._event('<<PF>>'))
        select_image.add_command(label='LF-interface', command=self._event('<<LF>>'))
        select_image.add_command(label='Next image', command=self._event('<<NextImage>>'))
        select_image.add_command(label='Previous image', command=self._event('<<PreviousImage>>'))
        select_image.add_command(label='First image', command=self._event('<<FirstImage>>'))
        self.add_cascade(label='Image source', menu=select_image)

    def todo(self):
        pass