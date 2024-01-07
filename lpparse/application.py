from local_file_system import LocalFileSystem
import tkinter as tk
from tkinter import ttk
import ctypes
from support import is_comment
from settings import Settings
from language_guesser import LanguageGuesser
from speaker_model import SpeakerModel
from GUI.gui_views import DatasetView, LexiconView, SpeakerModelView
from GUI.gui_phrase_structure_graphics import PhraseStructureGraphics
from GUI.gui_views import ResultsView
from GUI.gui_menus import MainMenu


class Application(tk.Tk):
    """Defines the main application window"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
        self.title('LPG LAB')
        self.geometry('1600x1000+100+500')

        self.style = ttk.Style()
        self.style.configure("mystyle.Treeview.Heading", font=('Calibri', 16))

        self.local_file_system = LocalFileSystem()
        self.settings = Settings(self.local_file_system)
        self.speaker_models, self.sentences_to_parse, self.language_guesser = self.set_up_experiment()
        self.lex_dictionary = self.local_file_system.read_lexicons_into_dictionary(self.settings)

        # Set up widgets for the main window
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.lexicon_frame = LexiconView(self, self.lex_dictionary)
        self.lexicon_frame.grid(row=0, column=0, sticky='WE')

        self.dataset_frame = DatasetView(self, self.sentences_to_parse)
        self.dataset_frame.grid(row=0, column=1, sticky='WE')

        self.speakermodel_frame = SpeakerModelView(self, self.speaker_models)
        self.speakermodel_frame.grid(row=1, column=0, sticky='nwes')

        self.results_frame = ResultsView(self, self.speaker_models)
        self.results_frame.grid(row=1, column=1, sticky='nwes')

        # Set up main menu
        main_menu = MainMenu(self)
        self.config(menu=main_menu)

        # Callbacks
        self.bind('<<Analyze>>', self._analyze)
        self.bind('<<RunStudy>>', self.run_study)
        self.bind('<<TheorySettings>>', self.change_theory_settings)

    def change_theory_settings(self, event):
        self.settings.change_theory_settings(self)

    def set_up_experiment(self):
        lg = LanguageGuesser(self.settings)
        speaker_model = {}
        for language in lg.languages:
            speaker_model[language] = SpeakerModel(self.settings, self.local_file_system, language)
            speaker_model[language].initialize()
        sentences_to_parse = [(index, sentence, group, part_of_conversation, grammatical)
                              for (index, sentence, group, part_of_conversation, grammatical)
                              in self.local_file_system.read_test_corpus(self.settings)]
        return speaker_model, sentences_to_parse, lg

    def _analyze(self, *_):
        """Analyzes the input sentence selected from the dataset frame"""
        S = self.dataset_frame.sentences_to_parse_dict[self.dataset_frame.selected_data_item]['sentence']
        language = self.language_guesser.guess_language(S)
        self.speaker_models[language].parse_sentence(self.dataset_frame.selected_data_item, S)
        print(f'{self.speaker_models[language].results}')
        if self.speaker_models[language].results.syntax_semantics:
            self.results_frame.fill_with_data(self.speaker_models[language])
            PhraseStructureGraphics(self, self.speaker_models[language])
        else:
            print('\nInput sentence is ungrammatical.')

    def run_study(self, *_):
        self.local_file_system.initialize_output_files(self.settings)
        for index, sentence, experimental_group, part_of_conversation, grammatical in self.sentences_to_parse:
            if not is_comment(sentence):
                language = self.language_guesser.guess_language(sentence)
                print(f'\n{index}. ' + ' '.join(sentence))
                self.speaker_models[language].parse_sentence(index, sentence)
                print(f'\n{self.speaker_models[language].results}')
                self.local_file_system.save_output(self.speaker_models[language], index, sentence, experimental_group, grammatical)
                if not part_of_conversation:
                    self.speaker_models[language].narrow_semantics.global_cognition.end_conversation()
            else:
                self.local_file_system.write_comment_line(sentence)
        self.local_file_system.close_all_output_files()
        self.local_file_system.report_errors_to_console(self.settings)
        print('\n\n(You can use the script via graphical user interface by \"python lpparse -app\")')

    def quit(self):
        pass




