import tkinter as tk
from tkinter import ttk


class DatasetView(tk.LabelFrame):
    """Defines the GUI widget to show the dataset"""
    def __init__(self, parent, sentences_to_parse, **kwargs):
        super().__init__(parent, text='Dataset', font=('Calibri 16'), **kwargs)
        self.style = ttk.Style()

        self.style.configure('mystyle.Treeview', font=('Calibri', 20), rowheight=40)
        self.sentences_to_parse = sentences_to_parse
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
        for index, word_list, experimental_group, part_of_conversation, grammatical in self.sentences_to_parse:
            sentence = ' '.join(word_list)
            if not grammatical:
                sentence = '*' + sentence
            if sentence and not sentence.startswith('&') and not sentence.startswith('#') and not sentence.startswith("\'"):
                self.dataset_treeview.insert('', 'end', iid=str(sentence_nro), text=str(sentence_nro), values=[sentence])
                self.sentences_to_parse_dict[sentence_nro] = {'sentence': word_list, 'grammatical': grammatical}
                sentence_nro += 1

    def _analyze(self, k):
        if self.dataset_treeview.selection():
            self.selected_data_item = int(self.dataset_treeview.selection()[0])
            self.event_generate('<<Analyze>>')


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
            for lex_list in self.speaker_models[model].lexicon.surface_lexicon.keys():
                for lex in self.speaker_models[model].lexicon.surface_lexicon[lex_list]:
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

        self.results_treeview.insert('', 'end', iid='Ontology', text='Ontology', values=[''])
        for semantic_object, data_dict in speaker_model.results.create_inventory_sorting(speaker_model.narrow_semantics.all_inventories().items()):
            self.results_treeview.insert('Ontology', 'end', iid='Ontology'+semantic_object, text='Object ' + semantic_object + ' in ' + data_dict['Semantic space'], values=[data_dict['Reference']])
            for property in data_dict:
                self.results_treeview.insert('Ontology' + semantic_object, 'end', iid='Ontology'+semantic_object+property, text=property, values=[data_dict[property]])

        self.results_treeview.insert('', 'end', iid='Resources', text='Resources', values=[''])
        for resource in speaker_model.results.resources.keys():
            self.results_treeview.insert('Resources', 'end', iid=resource, text=resource, values=[speaker_model.results.retrieve_resource(resource)])
