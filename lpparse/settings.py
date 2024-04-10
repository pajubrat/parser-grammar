from phrase_structure import PhraseStructure
import os
from pathlib import Path
from tkinter import filedialog
from views import ChangeSettingsNotebook

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
            self.app_settings['open_with'] = f"{self.data['file_study_folder']}/{self.data['file_test_corpus'][:-11]}.lpg"
        self.folders['study'] = Path(self.retrieve('file_study_folder'))
        self.folders['lexicon'] = Path(self.retrieve('file_lexicon_folder'))
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
        self.external_sources = {"test_corpus_file_name": self.folders['study'] / self.data['file_test_corpus'],
                                 "log_file_name": self.folders['study'] / (self.data['file_test_corpus'][:-4] + '_log.txt'),
                                 "results_file_name": self.folders['study'] / (self.data['file_test_corpus'][:-4] + '_results.txt'),
                                 "resources_file_name": self.folders['study'] / (self.data['file_test_corpus'][:-4] + '_resources.txt'),
                                 "numeration": self.folders['study'] / self.data['numeration'],
                                 "numeration_output": self.folders['study'] / (self.data['file_test_corpus'][:-4] + '_N.txt'),
                                 "redundancy_rules": self.folders['lexicon'] / self.data['file_redundancy_rules'],
                                 "error_report_name": self.folders['study'] / (self.data['file_test_corpus'][:-4] + '_error_reports.txt'),
                                 "simple_log_file": self.folders['study'] / (self.data['file_test_corpus'][:-4] + '_simple_log.txt')
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

    def change_settings(self, root, tab_lst=['Image', 'General', 'Meta', 'UG', 'Files']):
        d = ChangeSettingsNotebook(root, self, tab_lst)
        root.wait_window(d)