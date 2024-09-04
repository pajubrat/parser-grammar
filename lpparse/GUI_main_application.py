import tkinter as tk
from tkinter import ttk, messagebox


class DatasetView(tk.LabelFrame):
    """Defines the GUI widget to show the dataset"""
    def __init__(self, parent, input_data, **kwargs):
        super().__init__(parent, text='Dataset', font=('Calibri 16'), **kwargs)
        self.style = ttk.Style()

        self.style.configure('mystyle.Treeview', font=('Calibri', 20), rowheight=40)
        self.input_data = input_data
        self.sentences_to_parse_dict = {}
        self.selected_data_item = 1
        self.dataset_treeview = ttk.Treeview(self, columns=['Expression'], selectmode='browse', style="mystyle.Treeview")
        self.dataset_treeview.heading('#0', text='Item')
        self.dataset_treeview.column('#0', width=200)
        self.dataset_treeview.heading('Expression', text='Expression')
        self.dataset_treeview.column('Expression', width=600)
        self.fill_with_data()
        self.dataset_treeview.selection_set(1)
        sc = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.dataset_treeview.yview)
        sc.grid(row=0, column=1, sticky='NSW')
        self.dataset_treeview.configure(yscrollcommand=sc.set)
        self.dataset_treeview.grid(row=0, column=0, sticky='nwes')

        # Bindings
        self.dataset_treeview.bind('<Double-1>', self._analyze)

    def selected_item(self):
        return self.dataset_treeview.selection()[0]

    def fill_with_data(self):
        sentence_nro = 1
        prefix = ''
        for data_item in self.input_data.get_all():
            if not data_item['grammaticality']:
                prefix = '*'
            self.dataset_treeview.insert('', 'end', iid=data_item['index'], text=data_item['index'], values=[data_item['expression']])
            self.sentences_to_parse_dict[sentence_nro] = {'word_list': data_item["word_list"], 'grammatical': data_item["grammaticality"]}
            sentence_nro += 1

    def _analyze(self, k):
        if self.dataset_treeview.selection():
            self.selected_data_item = int(self.dataset_treeview.selection()[0])
            self.event_generate('<<Analyze>>')


class LogTextWindow(tk.Toplevel):
    color_scheme = {'Next head': {'color': 'black', 'mark whole line': True, 'mark until': None},
                    'Accepted': {'color': 'green', 'mark whole line': False, 'mark until': None},
                    'PF/LF-interface mapping': {'color': 'black', 'mark whole line': False, 'mark until': 'LF-interface and postsyntactic legibility tests'},
                    '$': {'color': '#eeeeee', 'mark whole line': False, 'mark until': '$'},
                    'Solution was rejected': {'color': 'red', 'mark whole line': True, 'mark until': None},
                    'Sentence #': {'color': 'black', 'mark whole line': True, 'mark until': None},
                    'fail': {'color': 'red', 'mark whole line': True, 'mark until': None}
                    }

    def __init__(self, parent, filename, text, *args, **kwargs):
        super().__init__(parent, *args, *kwargs)

        self.title('Derivational log file')

        # Label Frame with the message
        lb = tk.LabelFrame(self, text=text, font=('Calibri', 25))
        lb.grid(padx=10, pady=10, sticky='N')

        # Status bar
        tk.Label(self, text=filename, font=('Calibri', 15)).grid(row=1, column=0, sticky='E')

        # Window holding the text from the derivational log file
        self.textWindow = tk.Text(lb, undo=False, spacing1=4, spacing2=2, spacing3=4, height=40, width=150, wrap='none', font=("Cascadia Code", 14), tabs=('1c', '2c', '3c', '4c'))
        self.GetTextFromFile(filename)
        self.textWindow.grid(row=0, column=0, sticky='NSEW')
        self.textWindow.configure(bg='white', fg='#555555')
        self.focus_set()
        self.wm_attributes("-topmost", True)

        # Mark errors
        # self.mark_colors()

        # Create scrollbars
        sby = ttk.Scrollbar(lb, orient=tk.VERTICAL, command=self.textWindow.yview)
        sbx = ttk.Scrollbar(lb, orient=tk.HORIZONTAL, command=self.textWindow.xview)
        self.textWindow.configure(yscrollcommand=sby.set)
        self.textWindow.configure(xscrollcommand=sbx.set)
        sbx.grid(row=1, column=0, sticky='WES')
        sby.grid(row=0, column=1, sticky='NSW')

    def GetTextFromFile(self, filename):
        """Gets the text from the derivational log file"""
        text = open(filename, 'r', encoding='utf8').read()
        self.textWindow.insert('1.0', text)
        self.textWindow.focus()

    def mark_colors(self):
        for target in LogTextWindow.color_scheme.keys():
            start_index = '0.1'
            end_index = 'end'
            while True:
                where = self.textWindow.search(target, start_index, end_index)
                if where:
                    line, position = where.split('.')
                    if LogTextWindow.color_scheme[target]['mark whole line']:
                        s = line + '.0'
                        e = s + ' lineend'
                    elif LogTextWindow.color_scheme[target]['mark until']:
                        s = where
                        selection_end = self.textWindow.search(LogTextWindow.color_scheme[target]['mark until'], where + '+1c', end_index)
                        e = selection_end.split('.')[0] + '.0 lineend'
                    else:
                        s = where
                        e = where + ('+%dc' % len(target))
                    self.textWindow.tag_add(target, s, e)
                    start_index = e
                else:
                    break
            self.textWindow.tag_configure(target, background="white", foreground=LogTextWindow.color_scheme[target]['color'])

class LexiconView(tk.LabelFrame):
    """Defines the GUI widget to show the lexicon"""
    def __init__(self, parent, lexicon_dict, **kwargs):
        super().__init__(parent, text='Lexicon', font=('Calibri 16'), **kwargs)

        self.style = ttk.Style()
        self.style.configure('mystyle.Treeview', font=('Calibri', 20), rowheight=40)
        self.style.configure("mystyle.Treeview.Heading", font=('Calibri', 16))

        # LabelFrame formatting
        self.configure()
        self.columnconfigure(0, weight=1)

        # Create Treeview
        self.lexicon_treeview = ttk.Treeview(self, columns=['Language', 'Comment'], selectmode='browse', style='mystyle.Treeview')
        self.lexicon_treeview.heading('#0', text='Item')

        # self.lexicon_treeview.column('#0', width=150, stretch='no')
        self.lexicon_treeview.heading('Comment', text='Comment')
        self.lexicon_treeview.heading('Language', text='Language')

        self.lexicon_dict = lexicon_dict

        # fill Treeview
        self.fill_with_data()

        # Create scrollbar
        self.scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.lexicon_treeview.yview)
        self.lexicon_treeview.configure(yscrollcommand=self.scrollbar.set)

        # Position the elements
        self.lexicon_treeview.grid(row=0, column=0, sticky='NSWE')
        self.scrollbar.grid(row=0, column=1, sticky='NSW')

    # Fill the treeview with the elements in the lexicon dictionary
    def fill_with_data(self):

        for lexicon_file in list(self.lexicon_dict.keys()):
            self.lexicon_treeview.insert('', 'end', iid=lexicon_file, text=lexicon_file, values=['', ''])
            for item in list(self.lexicon_dict[lexicon_file].keys()):
                self.lexicon_treeview.insert(lexicon_file, 'end', iid=lexicon_file + item, text=item, values=self.values(lexicon_file, item))
                for feature in (self.lexicon_dict[lexicon_file][item].keys()):
                    self.lexicon_treeview.insert(lexicon_file + item, 'end', iid=lexicon_file + item + feature, text=feature, values=['', self.lexicon_dict[lexicon_file][item][feature]])

    def values(self, lexicon_file, item):
        value1 = ''
        value2 = ''
        for feature in self.lexicon_dict[lexicon_file][item].keys():
            if '#' in feature and 'PC' not in feature:
                value2 = '(Chunk)'
            if 'LANG' in feature:
                value1 = '(' + feature[5:] + ')'
        return [value1, value2]


class SpeakerModelView(tk.LabelFrame):
    """Defines the GUI widget to show the speaker models"""
    def __init__(self, parent, speaker_models, **kwargs):
        super().__init__(parent, text='Speaker Models', font=('Calibri 16'), **kwargs)
        self.speaker_models = speaker_models
        self.columnconfigure(0, weight=1)

        # Create Treeview
        self.style = ttk.Style()
        self.style.configure('mystyle.Treeview', font=('Calibri', 20), rowheight=40)
        self.speakermodel_treeview = ttk.Treeview(self, columns=['Features'], selectmode='browse', style='mystyle.Treeview')
        self.speakermodel_treeview.heading('#0', text='Model')
        self.speakermodel_treeview.heading('Features', text='Features')
        self.speakermodel_treeview.column('Features', width=300)
        self.speakermodel_treeview.columnconfigure(0, weight=1)
        self.speakermodel_treeview.grid(row=0, column=0, sticky='WE')

        # Create scrollbar
        self.scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.speakermodel_treeview.yview)
        self.scrollbarx = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.speakermodel_treeview.xview)
        self.speakermodel_treeview.configure(yscrollcommand=self.scrollbar.set)
        self.speakermodel_treeview.configure(xscrollcommand=self.scrollbarx.set)
        self.scrollbar.grid(row=0, column=1, sticky='NSWE')

        # Get data for the treeview
        self.fill_with_data()

    def fill_with_data(self):
        for model in self.speaker_models.keys():
            self.speakermodel_treeview.insert('', 'end', iid=model, text=model, values=[''])
            for lex_list in self.speaker_models[model].lexicon.speaker_lexicon.keys():
                for lex in self.speaker_models[model].lexicon.speaker_lexicon[lex_list]:
                    features = '  '.join(lex.features)
                    self.speakermodel_treeview.insert(model, 'end', text=lex, values=[features])     # Add features


class ResultsView(tk.LabelFrame):
    def __init__(self, parent, speaker_models, **kwargs):
        super().__init__(parent, text='Results', font=('Calibri 16 bold'), **kwargs)
        self.speaker_models = speaker_models

        # Create Treeview
        self.results_treeview = ttk.Treeview(self, columns=['Result'], selectmode='browse', style='mystyle.Treeview')
        self.results_treeview.heading('#0', text='Solution')
        self.results_treeview.heading('Result', text='Result')
        self.results_treeview.column('#0', width=300)
        self.results_treeview.column('Result', width=600)
        self.results_treeview.columnconfigure(0, weight=1)
        self.results_treeview.grid(row=0, column=0, sticky='NSWE')

        # Create scrollbar
        self.scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.results_treeview.yview)
        self.scrollbarx = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.results_treeview.xview)
        self.results_treeview.configure(yscrollcommand=self.scrollbar.set)
        self.results_treeview.configure(xscrollcommand=self.scrollbarx.set)
        self.scrollbar.grid(row=0, column=1, sticky='NSW')

    def fill_with_data(self, speaker_model):
        self.results_treeview.delete(*self.results_treeview.get_children())
        for i, solution in enumerate(speaker_model.results.syntax_semantics, start=1):
            self.results_treeview.insert('', 'end', iid=str(i), text=str(i), values=[f'{speaker_model.results.retrieve_syntax(solution)}'])
            for semantic_attribute in speaker_model.results.semantic_attributes(solution):
                self.results_treeview.insert(str(i), 'end', iid=str(i) + semantic_attribute, text=semantic_attribute, values=[''])
                for interpretation in speaker_model.results.interpretation(solution, semantic_attribute):
                    self.results_treeview.insert(str(i) + semantic_attribute, 'end', text='', values=[interpretation])

        self.results_treeview.insert('', 'end', iid='Resources', text='Resources', values=[''])
        for resource in speaker_model.results.resources.keys():
            self.results_treeview.insert('Resources', 'end', iid=resource, text=resource, values=[speaker_model.results.retrieve_resource(resource)])


class MainMenu(tk.Menu):
    def _event(self, sequence):
        # This function generates events for the main window
        def callback(*_):
            root = self.master.winfo_toplevel()
            root.event_generate(sequence)
        return callback

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        menu_font = ('Calibri', 20)

        # File menu
        file_menu = tk.Menu(self, tearoff=False, font=menu_font)
        file_menu.config(font=menu_font)
        file_menu.add_command(label='New...', command=self.todo)
        file_menu.add_command(label='Load Study...', command=self._event('<<LoadStudy>>'))
        file_menu.add_command(label='Save Study As...', command=self._event('<<SaveStudy>>'))
        file_menu.add_separator()
        file_menu.add_command(label='Load GPS...', command=self._event('<<LoadPhraseStructure>>'))
        file_menu.add_separator()
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
        study_menu.add_command(label='Run Study', command=self._event('<<RunStudy>>'))
        study_menu.add_command(label='Run Study and Generate Images', command=self._event('<<RunStudyWithImages>>'))
        self.add_cascade(label='Study', menu=study_menu)

        # Examine_results_menu
        examine_results_menu = tk.Menu(self, tearoff=False, font=menu_font)
        examine_results_menu.add_command(label='Results...', command=self.todo)
        examine_results_menu.add_command(label='Derivation...', command=self.todo)
        examine_results_menu.add_command(label='Examine log...', command=self._event('<<ExamineDerivationalLog>>'))
        self.add_cascade(label='Results', menu=examine_results_menu)

        # Image menu
        image_menu = tk.Menu(self, tearoff=False, font=menu_font)
        image_menu.add_command(label='New Image', command=self._event('<<NewImage>>'))
        self.add_cascade(label='Image', menu=image_menu)

        # Settings menu
        settings_menu = tk.Menu(self, tearoff=False, font=menu_font)
        settings_menu.add_command(label='Settings...', command=self._event('<<Settings>>'))
        self.add_cascade(label='Settings', menu=settings_menu)

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
