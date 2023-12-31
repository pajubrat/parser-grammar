import tkinter as tk
from tkinter import ttk


class DatasetView(ttk.LabelFrame):
    """Defines the GUI widget to show the dataset"""
    def __init__(self, parent, sentences_to_parse, **kwargs):
        super().__init__(parent, text='Dataset', **kwargs)
        self.style = ttk.Style()
        self.style.theme_use('vista')
        self.sentences_to_parse = sentences_to_parse
        self.sentences_to_parse_dict = {}
        self.selected_data_item = 1
        self.dataset_treeview = ttk.Treeview(self, columns=['Expression'], selectmode='browse')
        self.dataset_treeview.heading('#0', text='Item')
        self.dataset_treeview.column('#0', width=80, stretch='no')
        self.dataset_treeview.column('Expression', width=500)
        self.dataset_treeview.heading('Expression', text='Expression')
        self.fill()
        sc = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.dataset_treeview.yview)
        sc.grid(row=0, column=1, sticky='NSW')
        self.dataset_treeview.configure(yscrollcommand=sc.set)
        self.dataset_treeview.grid(row=0, column=0, sticky='nwes')
        self.dataset_treeview.bind('<Double-1>', self._analyze)

    def fill(self):
        sentence_nro = 1
        for index, word_list, experimental_group, part_of_conversation, grammatical in self.sentences_to_parse:
            sentence = ' '.join(word_list)
            if not grammatical:
                sentence = '*' + sentence
            if not sentence or not sentence.startswith('&') and not sentence.startswith('#') and not sentence.startswith("\'"):
                self.dataset_treeview.insert('', 'end', iid=str(index), text=str(index), values=[sentence])
                self.sentences_to_parse_dict[sentence_nro] = {'sentence': word_list, 'grammatical': grammatical}
                sentence_nro += 1

    def _analyze(self, k):
        print(self.style.theme_names())
        if self.dataset_treeview.selection():
            self.selected_data_item = int(self.dataset_treeview.selection()[0])
            self.event_generate('<<Analyze>>')

class LexiconView(ttk.LabelFrame):
    """Defines the GUI widget to show the lexicon"""
    def __init__(self, parent, lexicon_dict, **kwargs):
        super().__init__(parent, text='Lexicon', **kwargs)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.lexicon_dict = lexicon_dict

        # Create Treeview
        self.lexicon_treeview = ttk.Treeview(self, columns=['Language', 'Comment'], selectmode='browse')
        self.lexicon_treeview.heading('#0', text='Item')
        self.lexicon_treeview.column('#0', width=150, stretch='no')
        self.lexicon_treeview.heading('Comment', text='Comment', anchor='center')
        self.lexicon_treeview.heading('Language', text='Language', anchor='center')
        self.lexicon_treeview.column('Language', width=100, stretch='no')

        # fill Treeview
        self.fill()

        # Create scrollbar
        self.scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.lexicon_treeview.yview)
        self.lexicon_treeview.configure(yscrollcommand=self.scrollbar.set)

        # Position the elements
        self.lexicon_treeview.grid(row=0, column=0, sticky='nwes')
        self.scrollbar.grid(row=0,column=1, sticky='NSW')

    # Fill the treeview with the elements in the lexicon dictionary
    def fill(self):

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


class SpeakerModelView(ttk.LabelFrame):
    """Defines the GUI widget to show the speaker models"""
    def __init__(self, parent, speaker_models, **kwargs):
        super().__init__(parent, text='Speaker Models', **kwargs)
        self.speaker_models = speaker_models

        # Create Treeview
        self.speakermodel_treeview = ttk.Treeview(self, columns=['Features'], selectmode='browse')
        self.speakermodel_treeview.heading('#0', text='Model')
        self.speakermodel_treeview.heading('Features', text='Features', anchor='center')
        self.speakermodel_treeview.column('Features', width=300, anchor=tk.W)
        self.fill()

        # Create scrollbar
        self.scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.speakermodel_treeview.yview)
        self.scrollbarx = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.speakermodel_treeview.xview)
        self.speakermodel_treeview.configure(yscrollcommand=self.scrollbar.set)
        self.speakermodel_treeview.configure(xscrollcommand=self.scrollbarx.set)

        # Position the elements
        self.speakermodel_treeview.grid(row=0, column=0, sticky='nwes')
        self.scrollbar.grid(row=0,column=1, sticky='NSW')
        self.scrollbarx.grid(row=1, column=0, sticky='WE')

        # Position the elements
        self.speakermodel_treeview.grid(row=0, column=0, sticky='NSWE')

    def fill(self):
        for model in self.speaker_models.keys():
            self.speakermodel_treeview.insert('', 'end', iid=model, text=model, values=[''])
            for lex_list in self.speaker_models[model].lexicon.surface_lexicon.keys():
                for lex in self.speaker_models[model].lexicon.surface_lexicon[lex_list]:
                    features = '  '.join(lex.features)
                    self.speakermodel_treeview.insert(model, 'end', text=lex, values=[features])     # Add features
