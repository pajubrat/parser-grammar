
from local_file_system import LocalFileSystem
import tkinter as tk
from tkinter import font
import ctypes
from settings import Settings
from language_guesser import LanguageGuesser
from speaker_model import SpeakerModel
from GUI_main_application import DatasetView, LexiconView, SpeakerModelView, ResultsView, LogTextWindow, MainMenu
from GUI_phrase_structure_graphics import PhraseStructureGraphics
import pickle
from tkinter import ttk, filedialog
from phrase_structure import PhraseStructure
from g_phrase_structure import GPhraseStructure


class Application(tk.Tk):
    """
    Defines the main application window and the functions which run studies.

    The actual GUI component is activated only if the user provides the -app parameter when launching the application
    """
    def __init__(self, arg_lst, *args, **kwargs):
        super().__init__(*args, **kwargs)                                               # Basic window handling functions are inherited

        # Program icon

        self.taskbar_icon = tk.PhotoImage(file='./lpparse/image resources/applogo.png')
        self.iconphoto(True, self.taskbar_icon)

        # Main window parameters

        self.title('LPG Lab')
        self.geometry('1600x1000+100+500')

        # Fonts and style

        ctypes.windll.shcore.SetProcessDpiAwareness(1)
        tk_font = font.nametofont('TkDefaultFont')
        tk_font.configure(size=20)
        self.style = ttk.Style()
        self.style.configure("mystyle.Treeview.Heading", font=('Calibri', 16))

        # Provides access to functions in LocalFileSystem class which handle I/O tasks

        self.local_file_system = LocalFileSystem(self)

        # Configure the application

        self.local_file_system.read_app_settings(arg_lst)
        self.settings = Settings(self)

        # Set up an experiment (read study configuration, read input data, create speaker models)

        self.speaker_model, self.language_guesser, self.input_data = self.set_up_experiment()
        self.lex_dictionary = self.local_file_system.read_lexicons_into_dictionary()

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

        # Callbacks (actions triggered by the user in the GUI)

        self.bind('<<Analyze>>', self.analyze_one)
        self.bind('<<RunStudy>>', self.run_study)
        self.bind('<<RunStudyWithImages>>', self.run_study_with_images)
        self.bind('<<SaveStudy>>', self.save_study)
        self.bind('<<LoadStudy>>', self.load_study)
        self.bind('<<LoadPhraseStructure>>', self.load_phrase_structure)
        self.bind('<<CreateNewFromFile>>', self.create_new_from_corpus_file)
        self.bind('<<ExamineDerivationalLog>>', self.examine_derivational_log)
        self.bind('<<NewImage>>', self.new_image)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        self.destroy()

    def examine_derivational_log(self, event):
        LogTextWindow(self, self.settings.external_sources["log_file_name"], 'Derivation')

    def create_new_from_corpus_file(self, *_):
        self.local_file_system.create_new_from_corpus_file()
        self.load_study()

    def setup_widgets(self):

        self.lexicon_frame = LexiconView(self, self.lex_dictionary)
        self.lexicon_frame.grid(row=0, column=0, sticky='WE')

        self.dataset_frame = DatasetView(self, self.input_data)
        self.dataset_frame.grid(row=0, column=1, sticky='WE')

        self.speakermodel_frame = SpeakerModelView(self, self.speaker_model)
        self.speakermodel_frame.grid(row=1, column=0, sticky='nwes')

        self.results_frame = ResultsView(self, self.speaker_model)
        self.results_frame.grid(row=1, column=1, sticky='nwes')

        self.status_bar = tk.Label(self, padx=5, pady=5, bg='green', fg='white', anchor='e', justify='right', text=f'Current study: {self.settings.retrieve("file_study_configuration")}, {self.settings.retrieve("file_study_folder", "?")}/{self.settings.retrieve("file_test_corpus", "?")}', font=('Calibri 16'))
        self.status_bar.grid(row=2, column=0, columnspan=2, sticky='e')

    def save_study(self, *_):
        self.local_file_system.save_study()

    def load_study(self, *_):
        if self.settings.load_settings_with_user_input():
            self.speaker_model, self.language_guesser, self.input_data = self.set_up_experiment()
            self.lex_dictionary = self.local_file_system.read_lexicons_into_dictionary()
            self.reset_widgets()
            self.setup_widgets()

    def load_phrase_structure(self, *_):
        filename = filedialog.askopenfilename()
        with open(filename, 'rb') as input_file:

            # Open the phrase structure with the first speaker model available (SM contains settings)
            # PhraseStructureGraphics class handles graphics processing and manipulation

            PhraseStructureGraphics(self, speaker_model=None, gps=pickle.load(input_file), title=filename)

    def reset_widgets(self):
        self.lexicon_frame.destroy()
        self.dataset_frame.destroy()
        self.speakermodel_frame.destroy()
        self.results_frame.destroy()
        self.status_bar.destroy()

    def set_up_experiment(self):

        # LanguageGuesser will determine the language of the input expressions

        lg = LanguageGuesser(self.settings)

        # Speaker models are collected into a dictionary, one model for each language
        # recognized in the lexicon on the basis of LANG:XX features

        speaker_model = {}
        for language in lg.languages:
            speaker_model[language] = SpeakerModel(self.settings, language)
            speaker_model[language].initialize()

        # Acquire the input data from the test corpus
        # File locations etc are defined in the Settings object

        input_data = self.local_file_system.read_test_corpus()
        return speaker_model, lg, input_data

    def analyze_one(self, *_):
        """
        Analyzes one ad hoc input sentence (usually selected by user)
        """

        # Prepare input

        self.local_file_system.initialize_output_files()
        ad_hoc_data_item = {'index': self.dataset_frame.selected_data_item, 'word_list': self.dataset_frame.sentences_to_parse_dict[self.dataset_frame.selected_data_item]['word_list']}
        language = self.language_guesser.guess_language(ad_hoc_data_item)

        # Parse the input expression and show results

        self.speaker_model[language].parse_sentence(ad_hoc_data_item)
        print(f'\n{self.speaker_model[language].results}')

        # Show results

        if self.speaker_model[language].results.syntax_semantics:
            self.results_frame.fill_with_data(self.speaker_model[language])
            PhraseStructureGraphics(self, speaker_model=self.speaker_model[language], gps=None, title='')
        else:
            LogTextWindow(self, self.settings.external_sources["log_file_name"], 'Derivation')
            self.results_frame.results_treeview.delete(*self.results_frame.results_treeview.get_children())
        self.speaker_model[language].narrow_semantics.global_cognition.reset()

    def run_study_with_images(self, *_):
        """This function will run the study while drawing and saving the results in graphics format"""

        # Open the graphics window but do not show it

        image_window = PhraseStructureGraphics(self, settings=self.speaker_model[list(self.speaker_model.keys())[0]].settings, speaker_model=None, gps=None, title='')
        image_window.withdraw()

        # Run the study, while saving the result images (as set by parameter image_window).

        self.run_study(image_window=image_window)

    def new_image(self, *_):
        """
        Allows the user to draw images from scratch
        """

        X = PhraseStructure(features={'X'})
        GX = GPhraseStructure(PhraseStructure(X))
        image_window = PhraseStructureGraphics(self, settings=self.speaker_model[list(self.speaker_model.keys())[0]].settings, speaker_model=None, gps=GX, title='')

    def run_study(self, *_, **kwargs):
        """
        Run one complete study as defined by the configuration files
        """

        # Preparations

        self.local_file_system.initialize_output_files()

        # Examine all input data items (real items are indexed  > 0, the rest are comments that the user wants to keep and show)

        for data_item in [data for data in self.input_data.get_all() if data.get('index', 0) > 0]:

            # Determine language

            language = self.language_guesser.guess_language(data_item)

            # Analyse the expression

            self.speaker_model[language].parse_sentence(data_item)

            # Save output

            self.local_file_system.save_output(self.speaker_model[language], data_item)

            # Save image if required, otherwise show the results on the screen

            if kwargs and kwargs['image_window']:
                self.save_result_image(language, kwargs['image_window'], data_item)
            else:
                print(self.speaker_model[language].results)

            # Handle conversations (sequences of sentences)

            if not data_item['part_of_conversation']:
                self.speaker_model[language].ongoing_conversation = False
                self.speaker_model[language].narrow_semantics.global_cognition.reset()

        # Closing tasks

        self.local_file_system.close_all_output_files()
        sp = list(self.speaker_model.keys())[0]
        self.speaker_model[sp].results.report_results_to_console()

    def save_result_image(self, language, image_window, data_item):
        lf = self.speaker_model[language].results.get_results_by_title('Accepted LF-interface')
        if lf:
            image_window.settings = self.speaker_model[language].settings
            image_window.draw_and_save_phrase_structure_tree_as_postscript(lf[0], f'{image_window.settings.retrieve("file_study_folder", "")}/' f'{data_item["index"]}')

    def dev_logging(self, stri):
        self.local_file_system.write_dev_log(stri)

