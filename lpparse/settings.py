from phrase_structure import PhraseStructure
import tkinter as tk
from tkinter import messagebox
import os
from tkinter import ttk
from pathlib import Path
from tkinter import filedialog, messagebox

class Settings:
    def __init__(self, local_file_system, app_settings_dict=None):
        self.app_settings = {}  # Store the application settings (default values)
        self.local_file_system = local_file_system
        self.data = {}
        self.folders = {}
        self.external_sources = {}
        self.encoding = 'utf8'
        self.app_settings = {}
        self.default_study_parameters = {'author': 'Unknown author',
                                         'year': 'Unknown year',
                                         'date': 'Unknown date',
                                         'study_id': '1',
                                         'only_first_solution': 'False',
                                         'logging': 'True',
                                         'study_folder': 'language data working directory/',
                                         'lexicon_folder': 'language data working directory/lexicons/',
                                         'test_corpus_file': 'default_corpus.txt',
                                         'test_corpus_folder': 'language data working directory/',
                                         'ignore_ungrammatical_sentences': 'False',
                                         'console_output': 'Full',
                                         'datatake_full': 'False',
                                         'datatake_images': 'False',
                                         'image_parameter_stop_after_each_image': 'False',
                                         'image_parameter_show_words': 'True',
                                         'image_parameter_nolabels': 'False',
                                         'image_parameter_spellout': 'False',
                                         'image_parameter_case': 'False',
                                         'image_parameter_show_sentences': 'False',
                                         'image_parameter_show_glosses': 'True',
                                         'image_parameter_chain_curvature': 1,
                                         'UG_parameter_phase_heads': {'C', 'v', 'FORCE', 'Inf'},
                                         'UG_parameter_phase_heads_exclude': {'φ', 'v', 'TO/inf'},
                                         'extra_ranking': 'True',
                                         'filter': 'True',
                                         'lexical_anticipation': 'True',
                                         'closure': 'Bottom-up',
                                         'working_memory': 'True',
                                         'positive_spec_selection': '100',
                                         'negative_spec_selection': '-100',
                                         'break_head_comp_relations': '-100',
                                         'negative_tail_test': '-100',
                                         'positive_head_comp_selection': '100',
                                         'negative_head_comp_selection': '-100',
                                         'negative_semantics_match': '-100',
                                         'lf_legibility_condition': '-100',
                                         'negative_adverbial_test': '-100',
                                         'positive_adverbial_test': '100'
                                         }

        self.app_settings = app_settings_dict
        self.local_file_system.load_settings(self, app_settings_dict)
        self.process_settings()
        self.create_settings_for_file_system()

    def create_settings_for_file_system(self, corpus_filename=None):
        if corpus_filename:
            self.data['test_corpus'] = os.path.basename(corpus_filename)
            self.data['study_folder'] = os.path.dirname(corpus_filename)
            self.app_settings['open_with'] = f"{self.data['study_folder']}/{self.data['test_corpus'][:-11]}.lpg"
        self.set_folders()
        self.set_external_resources()

    def set_folders(self):
        self.folders['study'] = Path(self.data['study_folder'])
        self.folders['lexicon'] = Path(self.data['lexicon_folder'])

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

    def process_settings(self):
        for key in self.data:
            if isinstance(self.data[key], str):
                if self.data[key].lower() in {'true', 'yes'}:
                    self.data[key] = True
                elif self.data[key].lower() in {'false', 'no'}:
                    self.data[key] = False
                elif self.data[key].lstrip('-').isdigit():
                    self.data[key] = int(self.data[key])

        PhraseStructure.phase_heads = self.data['UG_parameter_phase_heads']
        PhraseStructure.phase_heads_exclude = self.data['UG_parameter_phase_heads_exclude']
        PhraseStructure.spellout_heads = self.data['image_parameter_spellout_complex_heads']

    def get(self):
        return self.data

    def change_theory_settings(self, root):
        d = ChangeTheorySettingsDialog(root, self)


class ChangeTheorySettingsDialog(tk.Toplevel):
    """Window hosting the dialog for changing the theory settings"""
    def __init__(self, root, settings_instance):
        super().__init__(root)
        self.settings_instance = settings_instance
        self.variables = {'UG_parameter_Agree': tk.StringVar,
                          'UG_parameter_phase_heads': tk.StringVar(value=';'.join(settings_instance.data['UG_parameter_phase_heads'])),
                          'UG_parameter_phase_heads_exclude': tk.StringVar(value=';'.join(settings_instance.data['UG_parameter_phase_heads_exclude']))}
        text_font = ('Calibri', 20)
        self.title("Change UG Parameters")
        self.geometry('800x500+1000+1000')
        self.focus()
        self.grid()
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=3)

        # Agreement parameters
        self.Agree_frame = ttk.LabelFrame(self, text='Agreement parameters')
        self.Agree_frame.grid(row=0, column=0, sticky='NW', padx=30, pady=30)

        ttk.Label(self.Agree_frame, text='Agreement model', font=text_font).grid(row=0, column=0, sticky='W', padx=10, pady=10)
        available_models = ['standard', 'revised']
        self.combobox = ttk.Combobox(self.Agree_frame, textvariable=self.variables['UG_parameter_Agree'], values=available_models, font=text_font)
        self.combobox.current(available_models.index(settings_instance.data['UG_parameter_Agree']))
        self.combobox.grid(row=1, column=0, sticky='W', padx=10, pady=10)

        # Phase theory parameters
        self.PhaseTheory_frame = ttk.LabelFrame(self, text='Phase theory')
        self.PhaseTheory_frame.grid(row=0, column=1, sticky='NW', padx=30, pady=30)

        ttk.Label(self.PhaseTheory_frame, text='Phase nodes', font=text_font).grid(row=0, column=0, sticky='W', padx=10, pady=10)
        self.phase_head_field = ttk.Entry(self.PhaseTheory_frame, textvariable=self.variables['UG_parameter_phase_heads'], font=text_font)
        self.phase_head_field.grid(row=1, column=0, sticky='W', padx=10, pady=10)

        ttk.Label(self.PhaseTheory_frame, text='Excluded phase nodes', font=text_font).grid(row=2, column=0, sticky='W', padx=10, pady=10)
        self.excluded_phase_head_field = ttk.Entry(self.PhaseTheory_frame, textvariable=self.variables['UG_parameter_phase_heads_exclude'], font=text_font)
        self.excluded_phase_head_field.grid(row=3, column=0, sticky='W', padx=10, pady=10)

        # Buttons
        self.Button_Frame = ttk.Frame(self)
        self.Button_Frame.grid(row=3, column=1, sticky='SE', padx=30, pady=30)
        self.OK_Button = tk.Button(self.Button_Frame, text='OK', command=self.OK, default='active', height=3, width=20)
        self.OK_Button.grid(row=0, column=1, sticky='SE', padx=10, pady=10)

        self.Cancel_Button = tk.Button(self.Button_Frame, text='Cancel', command=self.Cancel, default='normal', height=3, width=20)
        self.Cancel_Button.grid(row=0, column=0, stick='SW', padx=10, pady=10)

    def OK(self, *_):
        self.settings_instance.data['UG_parameter_Agree'] = self.combobox.get()
        self.settings_instance.data['UG_parameter_phase_heads'] = {x.strip() for x in self.phase_head_field.get().split(';')}
        self.settings_instance.data['UG_parameter_phase_heads_exclude'] = {x.strip() for x in self.excluded_phase_head_field.get().split(';')}
        tk.messagebox.showinfo(message='UG parameters have been changed')
        self.destroy()

    def Cancel(self, *_):
        self.destroy()









