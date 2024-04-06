from phrase_structure import PhraseStructure
import tkinter as tk
from tkinter import messagebox
import os
from tkinter import ttk
from pathlib import Path
from tkinter import filedialog

class Settings:
    def __init__(self, local_file_system, app_settings_dict=None):
        self.app_settings = {}
        self.local_file_system = local_file_system
        self.data = {}
        self.folders = {}
        self.external_sources = {}
        self.encoding = 'utf8'
        self.app_settings = app_settings_dict
        self.local_file_system.load_settings(self, app_settings_dict)
        self.process_settings()
        self.create_settings_for_file_system()

    def create_settings_for_file_system(self, corpus_filename=None):
        if corpus_filename:
            self.store('test_corpus', os.path.basename(corpus_filename))
            self.store('study_folder', os.path.dirname(corpus_filename))
            self.app_settings['open_with'] = f"{self.data['study_folder']}/{self.data['test_corpus'][:-11]}.lpg"
        self.folders['study'] = Path(self.retrieve('study_folder'))
        self.folders['lexicon'] = Path(self.retrieve('lexicon_folder'))
        self.set_external_resources()

    def process_settings(self):
        for key in self.data:
            if isinstance(self.data[key], str):
                if self.data[key].lower() == 'true':
                    self.data[key] = True
                elif self.data[key].lower() == 'false':
                    self.data[key] = False
                elif self.data[key].lstrip('-').isdigit():
                    self.data[key] = int(self.data[key])
        PhraseStructure.phase_heads = {f.strip() for f in self.retrieve('UG_parameter_phase_heads', '').split(';')}
        PhraseStructure.phase_heads_exclude = {f.strip() for f in self.retrieve('UG_parameter_phase_heads_exclude', '').split(';')}

    def set_external_resources(self):
        self.external_sources = {"test_corpus_file_name": self.folders['study'] / self.data['test_corpus'],
                                 "log_file_name": self.folders['study'] / (self.data['test_corpus'][:-4] + '_log.txt'),
                                 "results_file_name": self.folders['study'] / (self.data['test_corpus'][:-4] + '_results.txt'),
                                 "resources_file_name": self.folders['study'] / (self.data['test_corpus'][:-4] + '_resources.txt'),
                                 "numeration": self.folders['study'] / self.data['numeration'],
                                 "numeration_output": self.folders['study'] / (self.data['test_corpus'][:-4] + '_N.txt'),
                                 "redundancy_rules": self.folders['lexicon'] / self.data['redundancy_rules'],
                                 "error_report_name": self.folders['study'] / (self.data['test_corpus'][:-4] + '_error_reports.txt'),
                                 "simple_log_file": self.folders['study'] / (self.data['test_corpus'][:-4] + '_simple_log.txt')
                                 }

    def load_settings_with_user_input(self):
        filename = filedialog.askopenfilename(title='Load  study', defaultextension='.txt', initialdir='.')
        if filename:
            print('Loading new study...')
            self.local_file_system.load_settings(self, filename)
            return True     # This will reset the widgets in the application

    def store(self, key, value):
        self.data[key] = value

    def retrieve(self, key, value=None):
        if key in self.data:
            return self.data[key]
        else:
            return value

    def change_settings(self, root, tab_lst=['Image', 'General']):
        d = ChangeSettingsNotebook(root, self, tab_lst)
        root.wait_window(d)

class ChangeSettingsNotebook(tk.Toplevel):
    """Window for hosting the notebook hosting the settings"""
    def __init__(self, root, settings_instance, tabs_lst):
        super().__init__(root)
        self.settings_instance = settings_instance
        self.title("Study settings")
        self.geometry('1200x800+1000+1000')
        self.focus()
        self.grid()
        self.grab_set()
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=3)
        self.tab_pages = {}

        s = ttk.Style()
        s.configure('TNotebook.Tab', font=('Calibri', '20'))
        style = ttk.Style(root)
        style.configure('TCheckbutton', font=('Calibri', '20'))

        # Frames for the notebook and buttons
        self.notebook_Frame = tk.Frame(self)
        self.notebook_Frame.grid(row=0, column=0, sticky='NSWE')
        self.buttons_Frame = tk.Frame(self)
        self.buttons_Frame.grid(row=1, column=0, sticky='NSWE')
        self.buttons_Frame.grid_rowconfigure(0, weight=1)
        self.buttons_Frame.grid_columnconfigure(0, weight=1)
        self.CANCEL_button = tk.Button(self.buttons_Frame, text='Cancel', bg='#ffdddd', fg='#000000', font=('Calibri', 12), command=self.cancel)
        self.CANCEL_button.grid(row=0, column=1, sticky=tk.E, padx=20, pady=20)
        self.CANCEL_button.configure(width=15, height=2)
        self.OK_button = tk.Button(self.buttons_Frame, text='Update settings', bg='#ddffdd', fg='#000000', font=('Calibri', 12), command=self.update_settings)
        self.OK_button.grid(row=0, column=0, sticky=tk.E, padx=20, pady=20)
        self.OK_button.configure(width=15, height=2)
        self.notebook = ttk.Notebook(self.notebook_Frame)

        # NOTEBOOK TAB 1: IMAGE SETTINGS
        # Read settings dict into variables that are manipulated by the GUI components
        self.image_boolean_variables = {name: tk.BooleanVar(value=self.settings_instance.retrieve(name, False)) for name in self.settings_instance.data.keys() if name.startswith('image_') and isinstance(self.settings_instance.retrieve(name, False), bool)}
        self.image_string_variables = {'image_parameter_features': tk.StringVar(value=self.settings_instance.retrieve('image_parameter_features', ''))}
        self.image_settings_Frame = ttk.LabelFrame(self.notebook, text='Image settings')
        # Boolean variables are set by checkboxes
        self.image_variable_checkboxes = {}
        for i, parameter in enumerate(self.image_boolean_variables):
            parameter_name = ' '.join(parameter.split('_')[2:]).capitalize()
            self.image_variable_checkboxes[parameter] = ttk.Checkbutton(self.image_settings_Frame, variable=self.image_boolean_variables[parameter], text=parameter_name)
            self.image_variable_checkboxes[parameter].grid(row=i, column=0, sticky='NWSE')
        # Features are set by entry
        self.show_features_Frame = tk.LabelFrame(self.image_settings_Frame, text='Show features', font=('Calibri', 20))
        self.show_features_field = ttk.Entry(self.show_features_Frame, textvariable=self.image_string_variables['image_parameter_features'], font=('Calibri', 20), width=40)
        self.show_features_Frame.grid(row=i, column=0, sticky='NWSE', pady=20)
        self.show_features_field.grid(row=0, column=0, sticky='NWSE')
        self.tab_pages['Image'] = self.image_settings_Frame

        # NOTEBOOK TAB 2: GENERAL SIMULATION SETTINGS
        self.general_boolean_variables = {name: tk.BooleanVar(value=self.settings_instance.retrieve(name, False)) for name in self.settings_instance.data.keys() if name.startswith('general_') and isinstance(self.settings_instance.retrieve(name, False), bool)}
        self.general_settings_Frame = ttk.LabelFrame(self.notebook, text='General simulation settings')
        self.general_variables_checkboxes = {}
        for i, parameter in enumerate(self.general_boolean_variables):
            parameter_name = ' '.join(parameter.split('_')[2:]).capitalize()
            self.general_variables_checkboxes[parameter] = ttk.Checkbutton(self.general_settings_Frame, variable=self.general_boolean_variables[parameter], text=parameter_name)
            self.general_variables_checkboxes[parameter].grid(row=i, column=0, sticky='NWSE')
        self.tab_pages['General'] = self.general_settings_Frame

        for tab_text in tabs_lst:
            if tab_text in self.tab_pages:
                self.notebook.add(self.tab_pages[tab_text], text=tab_text, padding=20, sticky='NSEW')

        self.notebook.enable_traversal()

        self.notebook.grid(row=0, column=0, sticky='NSWE')

    def cancel(self):
        self.destroy()

    def update_settings(self):
        self.settings_instance.data.update({key: self.image_boolean_variables[key].get() for key in self.image_boolean_variables.keys()})
        self.settings_instance.data.update({key: self.general_boolean_variables[key].get() for key in self.general_boolean_variables.keys()})
        for parameter in self.image_string_variables.keys():
            self.settings_instance.data[parameter] = self.image_string_variables[parameter].get()
        self.destroy()
