from local_file_system import LocalFileSystem
import tkinter as tk
from tkinter import ttk, font
import ctypes
from support import is_comment
from settings import Settings
from language_guesser import LanguageGuesser
from speaker_model import SpeakerModel
from views import DatasetView, LexiconView, SpeakerModelView, ResultsView, PhraseStructureGraphics, LogTextWindow
from menus import MainMenu


class Application(tk.Tk):
    """Defines the main application window"""
    def __init__(self, arg_lst, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.taskbar_icon = tk.PhotoImage(file='./lpparse/image resources/applogo.png')
        self.iconphoto(True, self.taskbar_icon)
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
        self.title('LPG Lab')
        self.geometry('1600x1000+100+500')

        self.style = ttk.Style()
        self.style.configure("mystyle.Treeview.Heading", font=('Calibri', 16))

        tk_font = font.nametofont('TkDefaultFont')
        tk_font.configure(size=20)

        self.local_file_system = LocalFileSystem()
        self.settings = Settings(self.local_file_system, self.local_file_system.read_app_settings(arg_lst))
        self.speaker_model, self.sentences_to_parse, self.language_guesser = self.set_up_experiment(self.settings)
        self.lex_dictionary = self.local_file_system.read_lexicons_into_dictionary(self.settings)

        # Set up widgets for the main window
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Widgets
        self.lexicon_frame = None
        self.dataset_frame = None
        self.speakermodel_frame = None
        self.results_frame = None
        self.setup_widgets()

        # Set up main menu
        main_menu = MainMenu(self)
        self.config(menu=main_menu)

        # Callbacks
        self.bind('<<Analyze>>', self.analyze)    # This causes the first item to be analyzed automatically upon launch
        self.bind('<<RunStudy>>', self.run_study)
        self.bind('<<SaveStudy>>', self.save_study)
        self.bind('<<LoadStudy>>', self.load_study)
        self.bind('<<Settings>>', self.modify_settings)
        self.bind('<<CreateNewFromFile>>', self.create_new_from_corpus_file)
        self.bind('<<ExamineDerivationalLog>>', self.examine_derivational_log)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        self.destroy()

    def examine_derivational_log(self, event):
        LogTextWindow(self, self.settings.external_sources["log_file_name"], 'Derivation')

    def modify_settings(self, event):
        self.settings.change_settings(self)

    def create_new_from_corpus_file(self, *_):
        self.local_file_system.create_new_from_corpus_file(self.settings)
        self.load_study()

    def setup_widgets(self):

        self.lexicon_frame = LexiconView(self, self.lex_dictionary)
        self.lexicon_frame.grid(row=0, column=0, sticky='WE')

        self.dataset_frame = DatasetView(self, self.sentences_to_parse)
        self.dataset_frame.grid(row=0, column=1, sticky='WE')

        self.speakermodel_frame = SpeakerModelView(self, self.speaker_model)
        self.speakermodel_frame.grid(row=1, column=0, sticky='nwes')

        self.results_frame = ResultsView(self, self.speaker_model)
        self.results_frame.grid(row=1, column=1, sticky='nwes')

        self.status_bar = tk.Label(self, padx=5, pady=5, bg='green', fg='white', anchor='e', justify='right', text=f'Current study: {self.settings.retrieve("file_study_configuration")}, {self.settings.retrieve("file_study_folder", "?")}/{self.settings.retrieve("file_test_corpus", "?")}', font=('Calibri 16'))
        self.status_bar.grid(row=2, column=0, columnspan=2, sticky='e')

    def save_study(self, *_):
        self.local_file_system.save_study(self.settings)

    def load_study(self, *_):
        if self.settings.load_settings_with_user_input():
            self.speaker_model, self.sentences_to_parse, self.language_guesser = self.set_up_experiment(self.settings)
            self.lex_dictionary = self.local_file_system.read_lexicons_into_dictionary(self.settings)
            self.reset_widgets()
            self.setup_widgets()

    def reset_widgets(self):
        self.lexicon_frame.destroy()
        self.dataset_frame.destroy()
        self.speakermodel_frame.destroy()
        self.results_frame.destroy()
        self.status_bar.destroy()

    def set_up_experiment(self, settings):
        lg = LanguageGuesser(settings)
        speaker_model = {}
        for language in lg.languages:
            speaker_model[language] = SpeakerModel(settings, language)
            speaker_model[language].initialize()
        sentences_to_parse = [(index, sentence, group, part_of_conversation, grammatical)
                              for (index, sentence, group, part_of_conversation, grammatical)
                              in self.local_file_system.read_test_corpus(settings)]
        return speaker_model, sentences_to_parse, lg

    def analyze(self, *_):
        self.local_file_system.initialize_output_files(self.settings)
        S = self.dataset_frame.sentences_to_parse_dict[self.dataset_frame.selected_data_item]['sentence']
        language = self.language_guesser.guess_language(S)
        self.speaker_model[language].parse_sentence(self.dataset_frame.selected_data_item, S)
        print(f'\n{self.speaker_model[language].results}')
        if self.speaker_model[language].results.syntax_semantics:
            self.local_file_system.save_output(self.speaker_model[language], 1, S, '0', True)
            self.results_frame.fill_with_data(self.speaker_model[language])
            PhraseStructureGraphics(self, self.speaker_model[language])                    # Show phrase structure image
        else:
            LogTextWindow(self, self.settings.external_sources["log_file_name"], 'Derivation')
            self.results_frame.results_treeview.delete(*self.results_frame.results_treeview.get_children())
        self.speaker_model[language].narrow_semantics.global_cognition.end_conversation()

    def run_study(self, *_):
        self.local_file_system.initialize_output_files(self.settings)
        for index, sentence, experimental_group, part_of_conversation, grammatical in self.sentences_to_parse:
            if not is_comment(sentence):
                language = self.language_guesser.guess_language(sentence)
                print(f'\n{index}. ' + ' '.join(sentence))
                self.speaker_model[language].parse_sentence(index, sentence)
                print(f'\n{self.speaker_model[language].results}')
                self.local_file_system.save_output(self.speaker_model[language], index, sentence, experimental_group, grammatical)
                if not part_of_conversation:
                    self.speaker_model[language].narrow_semantics.global_cognition.end_conversation()
            else:
                self.local_file_system.write_comment_line(sentence)
        self.local_file_system.close_all_output_files()

        sp = list(self.speaker_model.keys())[0]
        self.speaker_model[sp].results.report_results_to_console()
