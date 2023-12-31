from local_file_system import LocalFileSystem
import tkinter as tk
from GUI.gui_views import DatasetView, LexiconView, SpeakerModelView
from GUI.gui_phrase_structure_graphics import PhraseStructureGraphics
from tkinter import font

class Application(tk.Tk):
    """Defines the main application window"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title('LPG LAB')
        self.geometry('1200x600')
        self.lfs = LocalFileSystem()
        self.speaker_models, self.sentences_to_parse, self.language_guesser = self.lfs.set_up_experiment()
        self.lex_dictionary = self.lfs.read_lexicons_into_dictionary()
        self.lexicon_frame = LexiconView(self, self.lex_dictionary)
        self.dataset_frame = DatasetView(self, self.sentences_to_parse)
        self.speakermodel_frame = SpeakerModelView(self, self.speaker_models)
        self.lexicon_frame.grid(row=0, column=0, sticky='nwes')
        self.dataset_frame.grid(row=0, column=1, sticky='nwes')
        self.speakermodel_frame.grid(row=1, column=0, sticky='nwes')
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.bind('<<Analyze>>', self._analyze)

    def _analyze(self, *_):
        """Analyzes the input sentence selected from the dataset frame"""
        S = self.dataset_frame.sentences_to_parse_dict[self.dataset_frame.selected_data_item]['sentence']
        language = self.language_guesser.guess_language(S)
        self.lfs.print_sentence_to_console(self.dataset_frame.selected_data_item, S)
        self.speaker_models[language].parse_sentence(self.dataset_frame.selected_data_item, S)
        self.lfs.print_result_to_console(self.speaker_models[language], S)
        psg = PhraseStructureGraphics(self, self.speaker_models[language])





