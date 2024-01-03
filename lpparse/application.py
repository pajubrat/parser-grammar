from local_file_system import LocalFileSystem
import tkinter as tk
import ctypes
from support import is_comment
from GUI.gui_views import DatasetView, LexiconView, SpeakerModelView
from GUI.gui_phrase_structure_graphics import PhraseStructureGraphics
from GUI.gui_menus import MainMenu

class Application(tk.Tk):
    """Defines the main application window"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
        self.title('LPG LAB')
        self.geometry('1600x1000')
        self.lfs = LocalFileSystem()
        self.speaker_models, self.sentences_to_parse, self.language_guesser = self.lfs.set_up_experiment()
        self.lex_dictionary = self.lfs.read_lexicons_into_dictionary()
        self.lexicon_frame = LexiconView(self, self.lex_dictionary)
        self.dataset_frame = DatasetView(self, self.sentences_to_parse)
        self.speakermodel_frame = SpeakerModelView(self, self.speaker_models)
        main_menu = MainMenu(self)
        self.config(menu=main_menu)
        self.lexicon_frame.grid(row=0, column=0, sticky='nwes')
        self.dataset_frame.grid(row=0, column=1, sticky='nwes')
        self.speakermodel_frame.grid(row=1, column=0, sticky='nwes')
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Callbacks
        self.bind('<<Analyze>>', self._analyze)
        self.bind('<<RunStudy>>', self.run_study)

    def _analyze(self, *_):
        """Analyzes the input sentence selected from the dataset frame"""
        S = self.dataset_frame.sentences_to_parse_dict[self.dataset_frame.selected_data_item]['sentence']
        language = self.language_guesser.guess_language(S)
        self.lfs.print_sentence_to_console(self.dataset_frame.selected_data_item, S)
        self.speaker_models[language].parse_sentence(self.dataset_frame.selected_data_item, S)
        self.lfs.print_result_to_console(self.speaker_models[language], S)
        if self.speaker_models[language].result_list and self.speaker_models[language].result_list[0]:
            psg = PhraseStructureGraphics(self, self.speaker_models[language])
        else:
            print('\nInput sentence is ungrammatical.')

    def run_study(self, *_):
        self.lfs.initialize_output_files()
        for index, sentence, experimental_group, part_of_conversation, grammatical in self.sentences_to_parse:
            if not is_comment(sentence):
                language = self.language_guesser.guess_language(sentence)
                self.lfs.print_sentence_to_console(index, sentence)
                self.speaker_models[language].parse_sentence(index, sentence)
                self.lfs.save_output(self.speaker_models[language],
                                index,
                                sentence,
                                experimental_group,
                                part_of_conversation,
                                grammatical)
                if not part_of_conversation:
                    self.speaker_models[language].narrow_semantics.global_cognition.end_conversation()
            else:
                self.lfs.write_comment_line(sentence)
        self.lfs.close_all_output_files()
        self.lfs.report_errors_to_console()

    def quit(self):
        pass




