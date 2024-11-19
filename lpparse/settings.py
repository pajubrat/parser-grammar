from phrase_structure import PhraseStructure
import os
from pathlib import Path
from tkinter import filedialog


class Settings:
    def __init__(self, application):
        self.application = application
        self.data = application.local_file_system.root_settings
        self.data.update(self.default_settings())
        self.folders = {}
        self.external_sources = {}
        self.load_and_initialize_settings()

    def load_and_initialize_settings(self):
        self.data.update(self.application.local_file_system.load_settings())
        self.process_settings()
        self.create_settings_for_file_system()

    def default_settings(self):
         return {'image_parameter_grid': 150,
                  'image_parameter_margins': 200,
                  'image_parameter_y_grid': 180,
                  'image_parameter_y_margins': 300,
                  'image_parameter_fit_margins': 100,
                  'image_parameter_canvas_width': 2250,
                  'image_parameter_canvas_height': 1500,
                  'image_parameter_label_padding': 1,
                  'image_parameter_text_spacing': 1.5,
                  'image_parameter_tshrink': 1.0,
                  'image_parameter_arc_curvature': 2,
                  'image_parameter_Y_offset_for_arrow': 50,
                  'image_parameter_tsize': 42}

    def create_settings_for_file_system(self, corpus_filename=None):
        if corpus_filename:
            self.store('file_test_corpus', os.path.basename(corpus_filename))
            self.store('file_study_folder', os.path.dirname(corpus_filename))
        self.folders['study'] = Path(self.retrieve('file_study_folder'))
        self.folders['lexicon'] = Path(self.retrieve('file_lexicon_folder'))
        self.set_external_resources()

    def update(self, dict):
        self.data.update(dict)

    def reset_settings(self):
        self.data = {}

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
                                 "results": self.folders['study'] / (self.data['file_test_corpus'][:-4] + '_results.txt'),
                                 "resources": self.folders['study'] / (self.data['file_test_corpus'][:-4] + '_resources.txt'),
                                 "numeration": self.folders['study'] / self.data['numeration'],
                                 "numeration output": self.folders['study'] / (self.data['file_test_corpus'][:-4] + '_N.txt'),
                                 "redundancy_rules": self.folders['lexicon'] / self.data['file_redundancy_rules'],
                                 "errors": self.folders['study'] / (self.data['file_test_corpus'][:-4] + '_observational_adequacy_errors.txt'),
                                 "descriptive": self.folders['study'] / (self.data['file_test_corpus'][:-4] + '_descriptive_adequacy_errors.txt'),
                                 "simple log": self.folders['study'] / (self.data['file_test_corpus'][:-4] + '_simple_log.txt')
                                 }

    def load_settings_with_user_input(self):
        self.reset_settings()
        self.store('full_name', filedialog.askopenfilename(title='Load study', defaultextension='.txt', initialdir='.'))
        if self.data['full_name']:
            self.data['file_study_folder'], self.data['file_study_configuration'] = os.path.split(self.data['full_name'])
            self.load_and_initialize_settings()
            return True     # This will reset the widgets in the application

    def store(self, key, value):
        self.data[key] = value

    def retrieve(self, key, value=None):
        if key in self.data:
            return self.data[key]
        else:
            return value

    def set(self, key, value):
        self.data[key] = value
