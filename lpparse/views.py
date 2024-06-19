import tkinter as tk
from tkinter import ttk, simpledialog
from phrase_structure import PhraseStructure
from menus import GraphicsMenu
import widgets as w
from feature_processing import clean_string

MARGINS = 300
GRID = 150

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

        self.results_treeview.insert('', 'end', iid='Ontology', text='Ontology', values=[''])
        for semantic_object, data_dict in speaker_model.results.create_inventory_sorting(speaker_model.narrow_semantics.all_inventories().items()):
            self.results_treeview.insert('Ontology', 'end', iid='Ontology'+semantic_object, text='Object ' + semantic_object + ' in ' + data_dict['Semantic space'], values=[data_dict['Reference']])
            for property in data_dict:
                self.results_treeview.insert('Ontology' + semantic_object, 'end', iid='Ontology'+semantic_object+property, text=property, values=[data_dict[property]])

        self.results_treeview.insert('', 'end', iid='Resources', text='Resources', values=[''])
        for resource in speaker_model.results.resources.keys():
            self.results_treeview.insert('Resources', 'end', iid=resource, text=resource, values=[speaker_model.results.retrieve_resource(resource)])

class ChangeSettingsNotebook(tk.Toplevel):
    """Window for hosting the notebook hosting the settings"""
    def __init__(self, root, settings_instance, tabs_lst):
        super().__init__(root)
        self.settings_instance = settings_instance
        self.title("Study settings")
        self.geometry('1200x900+1000+1000')
        self.focus()
        self.grid()
        self.grab_set()
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=3)
        self.tab_pages = {}

        # Frames for the notebook and buttons
        self.notebook_Frame = tk.Frame(self)
        self.notebook_Frame.grid(row=0, column=0, sticky='NSWE')
        self.notebook = ttk.Notebook(self.notebook_Frame)
        w.OKCancelButtons(self, self.update_settings, self.cancel).grid(row=1, column=0, sticky='NSWE')

        # NOTEBOOK TAB 1: IMAGE SETTINGS
        self.image_boolean_variables = self.create_boolean_GUI_variables_from_settings('image_')
        self.image_string_variables = self.create_string_GUI_variables_from_settings('image_parameter_features')
        self.image_settings_Frame = ttk.LabelFrame(self.notebook, text='Image settings')
        i = 0
        for i, parameter in enumerate(self.image_boolean_variables):
            parameter_name = ' '.join(parameter.split('_')[2:]).capitalize()
            ttk.Checkbutton(self.image_settings_Frame, variable=self.image_boolean_variables[parameter], text=parameter_name).grid(row=i, column=0, sticky='NWSE')
        w.LabeledEntry(self.image_settings_Frame, 'Show features', self.image_string_variables['image_parameter_features']).grid(row=i+1, column=0, sticky='NWSE', pady=20)

        # NOTEBOOK TAB 2: GENERAL SIMULATION SETTINGS
        self.general_boolean_variables = self.create_boolean_GUI_variables_from_settings('general_')
        self.general_settings_Frame = ttk.LabelFrame(self.notebook, text='General simulation settings')
        for i, parameter in enumerate(self.general_boolean_variables):
            parameter_name = ' '.join(parameter.split('_')[2:]).capitalize()
            ttk.Checkbutton(self.general_settings_Frame, variable=self.general_boolean_variables[parameter], text=parameter_name).grid(row=i, column=0, sticky='NWSE')

        #NOTEBOOK TAB 3: METADATA SETTINGS
        self.meta_string_variables = self.create_string_GUI_variables_from_settings('meta_')
        self.meta_Frame = ttk.LabelFrame(self.notebook, text='Metadata')
        self.meta_variables_entry = {}
        for i, parameter in enumerate(self.meta_string_variables):
            parameter_name = ' '.join(parameter.split('_')[1:]).capitalize()
            w.LabeledEntry(self.meta_Frame, parameter_name, self.meta_string_variables[parameter]).grid(row=i, column=0, sticky='NWSE')

        #NOTEBOOK TAB 4: UG SETTINGS
        self.UG_Frame = ttk.LabelFrame(self.notebook, text='UG parameters')
        self.UG_Agree_LabelFrame = ttk.LabelFrame(self.UG_Frame, text='Model of Agree')
        self.str_vari = tk.StringVar(value=self.settings_instance.retrieve('UG_parameter_Agree', 'revised'))
        self.UG_Agree_LabelFrame.grid(row=0, column=0)
        tk.Radiobutton(self.UG_Agree_LabelFrame, variable=self.str_vari, value='standard', text='Standard', font=('Calibri', 20)).grid(row=0, column=0, padx=5, pady=5, sticky='NWSE')
        tk.Radiobutton(self.UG_Agree_LabelFrame, variable=self.str_vari, value='revised', text='Revised', font=('Calibri', 20)).grid(row=0, column=1, padx=5, pady=5, sticky='NWSE')
        self.UG_phase_LabelFrame = ttk.LabelFrame(self.UG_Frame, text='Phase theory')
        self.UG_phase_LabelFrame.grid(row=1, column=0)
        self.include_heads = tk.StringVar(value=self.settings_instance.retrieve('UG_parameter_phase_heads', 'C;v'))
        w.LabeledEntry(self.UG_phase_LabelFrame, 'Phase heads', self.include_heads).grid(row=0, column=0)
        self.exclude_heads = tk.StringVar(value=self.settings_instance.retrieve('UG_parameter_phase_heads_exclude', ''))
        w.LabeledEntry(self.UG_phase_LabelFrame, 'Phase heads excluded', self.exclude_heads).grid(row=1, column=0)

        #NOTEBOOK TAB 5: Filenames
        self.Files_Frame = ttk.LabelFrame(self.notebook, text='External files')
        self.App_configuration_Label = ttk.Label(self.Files_Frame, text='Configuration: ' + self.settings_instance.retrieve('file_study_configuration', '?'))
        self.App_configuration_Label.grid(row=0, column=0, sticky='W', pady=5)
        self.Study_files_Frame = ttk.LabelFrame(self.Files_Frame, text='Study files')
        self.Study_files_Frame.grid(row=1, column=0, sticky='NWSE', pady=5)
        self.corpus_variable = tk.StringVar(value=self.settings_instance.retrieve('file_test_corpus', '?'))
        w.LabeledEntry(self.Study_files_Frame, 'Corpus', self.corpus_variable, state='disabled').grid(row=0, column=0, sticky='NWSE', padx=10)
        self.folder_variable = tk.StringVar(value=self.settings_instance.retrieve('file_study_folder', '?'))
        w.LabeledEntry(self.Study_files_Frame, 'Folder', self.folder_variable, state='disabled').grid(row=1, column=0, sticky='NWSE', padx=10)
        self.Lexicon_files_Frame = ttk.LabelFrame(self.Files_Frame, text='Lexicon files')
        self.Lexicon_files_Frame.grid(row=2, column=0, sticky='NWSE', pady=5)
        lexicon_files = [file.strip() for file in self.settings_instance.retrieve('file_lexicons').split(';')]
        self.Lexicon_files_variables = {}
        for i, lexicon_file in enumerate(lexicon_files):
            self.Lexicon_files_variables[lexicon_file] = tk.StringVar(value=lexicon_file)
            w.LabeledEntry(self.Lexicon_files_Frame, 'file', self.Lexicon_files_variables[lexicon_file], state='disabled').grid(row=i, column=0, sticky='NSWE', padx=20)
        self.lrr = tk.StringVar(value=self.settings_instance.retrieve('file_redundancy_rules', '?'))
        w.LabeledEntry(self.Files_Frame, 'Lexical redundancy rules', self.lrr, state='disabled').grid(row=4, column=0, sticky='NSWE', pady=5)

        self.tab_pages['Image'] = self.image_settings_Frame
        self.tab_pages['General'] = self.general_settings_Frame
        self.tab_pages['Meta'] = self.meta_Frame
        self.tab_pages['UG'] = self.UG_Frame
        self.tab_pages['Files'] = self.Files_Frame
        for tab_text in tabs_lst:
            if tab_text in self.tab_pages:
                self.notebook.add(self.tab_pages[tab_text], text=tab_text, padding=20, sticky='NSEW')

        self.notebook.enable_traversal()
        self.notebook.grid(row=0, column=0, sticky='NSWE')

    def create_boolean_GUI_variables_from_settings(self, pattern):
        return {name: tk.BooleanVar(value=self.settings_instance.retrieve(name, False)) for name in self.settings_instance.data.keys() if name.startswith(pattern) and isinstance(self.settings_instance.retrieve(name, False), bool)}

    def create_string_GUI_variables_from_settings(self, pattern):
        return {name: tk.StringVar(value=self.settings_instance.retrieve(name, '')) for name in self.settings_instance.data.keys() if name.startswith(pattern)}

    def cancel(self):
        self.destroy()

    def update_settings(self):
        self.settings_instance.data.update({key: self.image_boolean_variables[key].get() for key in self.image_boolean_variables.keys()})
        self.settings_instance.data.update({key: self.general_boolean_variables[key].get() for key in self.general_boolean_variables.keys()})
        self.settings_instance.data.update({key: self.meta_string_variables[key].get() for key in self.meta_string_variables.keys()})
        self.settings_instance.data['UG_parameter_Agree'] = self.str_vari.get()
        self.settings_instance.data['UG_parameter_phase_heads'] = self.include_heads.get()
        self.settings_instance.data['UG_parameter_phase_heads_exclude'] = self.exclude_heads.get()
        self.settings_instance.data['file_lexicons'] = ';'.join({self.Lexicon_files_variables[file].get() for file in self.Lexicon_files_variables.keys()})
        self.settings_instance.data['file_test_corpus'] = self.corpus_variable.get()
        self.settings_instance.data['file_study_folder'] = self.folder_variable.get()
        self.settings_instance.data['file_redundancy_rules'] = self.lrr.get()
        for parameter in self.image_string_variables.keys():
            self.settings_instance.data[parameter] = self.image_string_variables[parameter].get()
        self.destroy()

class GPhraseStructure(PhraseStructure):
    """Phrase Structure class that has additional properties related to tree drawing"""

    draw_features = {}

    def __init__(self, source=None, left=None, right=None):
        super().__init__(left, right)

        # Properties of regular constituents
        self.features = source.features
        self.adjunct = source.adjunct
        self.identity = source.identity
        self.copied = source.copied
        if not source.terminal():
            self.create_constituents([GPhraseStructure(const) for const in source.const])

        # Special properties
        self.x = 0
        self.y = 0
        self.X = 0
        self.Y = 0
        self.Y_offset = 0
        self.custom_label = None
        self.custom_phonology = None
        self.custom_gloss = None
        self.custom_features = []
        self.custom_text = None
        self.head_chain_target = None
        self.Agree_target = None
        self.source = source
        self.node_identity = source.node_identity
        self.compressed = False
        self.label_stack = self.generate_label_stack()

    def dominating_nodes(self):
        x = self
        lst = []
        while x.mother_:
            lst.append(x.mother_)
            x = x.mother_
        return lst

    def find_head_chain(self):
        if self.zero_level() and self.is_left() and self.affix() and self.affix().copied and self.mother_:
            return self.mother_.right().find_constituent_with_index(self.affix().index())

    def find_Agree(self):
        if self.zero_level() and self.is_left() and 'ΦLF' in self.features:
            pass
            #return self.argument_by_agreement().head()

    def initialize_logical_space(self):
        """Projects the phrase structure object into a logical space"""
        self.head_chain_target = self.find_head_chain()
        # self.Agree_target = self.find_Agree()
        if self.complex():
            self.left().x = self.x - 1
            self.left().y = self.y + 1
            self.left().initialize_logical_space()
            self.right().x = self.x + 1
            self.right().y = self.y + 1
            self.right().initialize_logical_space()

    def boundary_points(self):
        boundary = set()
        boundary.add((self.x, self.y))
        if self.complex():
            boundary = boundary | self.left().boundary_points()
            boundary = boundary | self.right().boundary_points()
        return boundary

    def find_boundaries(self, left_x, right_x, depth):
        if self.x < left_x:
            left_x = self.x
        if self.x > right_x:
            right_x = self.x
        if self.y > depth:
            depth = self.y
        if self.complex():
            left_x, right_x, depth = self.left().find_boundaries(left_x, right_x, depth)
            left_x, right_x, depth = self.right().find_boundaries(left_x, right_x, depth)
        return left_x, right_x, depth

    def remove_overlap(self):
        """Stretches child nodes apart if their offspring create overlap"""
        if self.complex():
            self.left().remove_overlap()
            self.right().remove_overlap()
            overlap = 0
            LC_right_boundary = self.left().boundary_points()
            RC_left_boundary = self.right().boundary_points()
            for L_bp in LC_right_boundary:
                for R_bp in RC_left_boundary:
                    if L_bp[1] == R_bp[1]:
                        if L_bp[0] >= R_bp[0] and L_bp[0] - R_bp[0] >= overlap:
                            overlap = L_bp[0] - R_bp[0] + 1
            if overlap > 0:
                self.left().move_x(-overlap/2)
                self.right().move_x(overlap/2)

    def move_x(self, amount):
        """Moves a node and its offspring"""
        self.x = self.x + amount
        if self.complex():
            self.left().move_x(amount)
            self.right().move_x(amount)

    def move_y(self, amount):
        """Moves a node and its offspring"""
        self.y = self.y + amount
        if self.complex():
            self.left().move_y(amount)
            self.right().move_y(amount)

    def label_size(self):
        return len(self.label_stack)

    def generate_label_stack(self):
        """Determines the content for primitive labels"""
        def feature_conversion(feature):
            return feature

        label_stack = []

        # Minimum label is the label itself
        if not self.custom_label == '$n/a$':
            if self.custom_label:
                label_stack.append((self.custom_label, 'label'))
            else:
                label_stack.append((self.label(), 'label'))

        if self.zero_level():

            # Phonological string
            if not self.custom_phonology == '$n/a$':
                if self.custom_phonology:
                    label_stack.append((self.custom_phonology, 'PF'))
                else:
                    if self.get_phonological_string() and self.get_phonological_string() != self.label():
                        label_stack.append((self.get_phonological_string(), 'PF'))

            # Gloss
            if not self.custom_gloss == '$n/a$':
                if self.custom_gloss:
                    label_stack.append((f"ʻ{self.custom_gloss}ʼ", 'gloss'))
                else:
                    if self.gloss() and self.gloss() != self.label() and self.gloss() != self.get_phonological_string():
                        label_stack.append((f"ʻ{self.gloss()}ʼ", 'gloss'))

            # Features
            if not self.custom_features == '$n/a$':
                if self.custom_features:
                    for feature in self.custom_features:
                        label_stack.append((feature, 'feature'))
                else:
                    for feature in [x for x in self.features if x in GPhraseStructure.draw_features]:
                        label_stack.append((f'{feature_conversion(feature)}', 'feature'))

            # Custom text
            if self.custom_text:
                label_stack.append((self.custom_text, 'gloss'))

        return label_stack

    def itext(self):
        """Produces information concerning constituents when pointed at the screen by mouse"""
        itext = self.label() + '\n\n'

        if self.complex():

            itext += f'Identity: {self.node_identity}\n'
            itext += f'Reconstructed: {self.copied}\n'
            itext += f'Adjunct Merge: {self.adjunct}\n'
            itext += ' '.join(self.features)
            return itext

        if self.zero_level():

            feature_dict = {'PF:': [],
                            'LF:': [],
                            'COMP:': [],
                            'SPEC:': [],
                            'PHI:': [],
                            'Φ': [],
                            'PROBE:': [],
                            'ε': [],
                            'RESIDUUM': []}

            for feature in sorted(self.features):
                for key in feature_dict.keys():
                    if key in feature:
                        feature_dict[key].append(feature)
                        break
                else:
                    feature_dict['RESIDUUM'].append(feature)

            i = 1
            for category in feature_dict.keys():
                for feature in feature_dict[category]:
                    itext += f"{feature: <20}"
                    if i % 2 == 0:
                        itext += '\n'
                    i += 1

            if self.affix() and not self.right().copied:
                itext += f'\nComplex head with structure '
                for c in self.get_affix_list():
                    itext += f'{c} '

        return itext

    def find_max_label_size(self, label_size):
        """Finds the maximal label size for a phrase structure (to determine canvas margins)"""
        if self.zero_level():
            ls = self.label_size() * len(self.get_affix_list())
            if ls > label_size:
                return ls
            return label_size
        if self.complex():
            label_size = self.left().find_max_label_size(label_size)
            label_size = self.right().find_max_label_size(label_size)
        return label_size

    def hasChain(self):
        for f in self.features:
            if f.startswith('CHAIN:'):
                return int(f.split(':')[1])

class PhraseStructureGraphics(tk.Toplevel):
    """Window hosting the canvas"""
    def __init__(self, root, speaker_model):
        super().__init__(root)
        self.title("Phrase Structure Graphics")
        self.geometry(('1800x1000+1800+500'))
        self.speaker_model = speaker_model
        self.root = root
        self.feature_visualizations = {}

        # Features shown in figures on the basis of settings
        GPhraseStructure.draw_features = {feature.strip() for feature in root.settings.retrieve('image_parameter_features', set()).split(';')}
        mapping_str = self.root.settings.retrieve('image_parameter_visualization', '')
        # Generate lexical feature visualizations
        if mapping_str:
            self.parse_feature_visualizations(mapping_str)

        # Internal variables
        self.index_of_analysis_shown = 0

        # Settings for drawing
        self.s = {'grid': GRID, 'margins': MARGINS}
        self.s['tsize'] = int(self.s['grid']/3.5)

        # Line styles
        self.line_style = {'phrasal_chain': {'fill': 'black', 'dash': None, 'width': 2},
                           'head_chain': {'fill': 'black', 'dash': None, 'width': 2},
                           'Agree': {'fill': 'blue', 'dash': None, 'width': 3}}

        # Menu
        self.graphics_menu = GraphicsMenu(self)
        self.config(menu=self.graphics_menu)

        # Buttons
        pad = 10
        width = 12
        height = 1
        ribbon = tk.Frame(self)
        ribbon.grid(row=0, column=0, sticky='W')
        nextButton = tk.Button(ribbon, command=self.next_image, text='Next >', width=width, height=height, font=('Calibri', 15), bg='#CCCCCC', fg='white')
        nextButton.grid(row=0, column=2, sticky=tk.E, padx=pad, pady=pad)
        previousButton = tk.Button(ribbon, command=self.previous_image, text='< Previous', width=width, height=height, font=('Calibri', 15), bg='#CCCCCC', fg='white')
        previousButton.grid(row=0, column=1, sticky=tk.E, padx=pad, pady=pad)
        firstButton = tk.Button(ribbon, command=self.first_image, text='<< First', width=width, height=height, font=('Calibri', 15), bg='#CCCCCC', fg='white')
        firstButton.grid(row=0, column=0, sticky=tk.E, padx=pad, pady=pad)

        # Make host window and canvas visible
        self.focus()
        self.grid()
        self.canvas = PhraseStructureCanvas(self)
        self.canvas.grid(row=1, column=0)
        self.gps = None     # Current phrase structure e on screen
        self.bind('<<LF>>', self.LF)
        self.bind('<<PF>>', self.PF)
        self.bind('<<NextImage>>', self.next_image)
        self.bind('<<PreviousImage>>', self.previous_image)
        self.bind('<<FirstImage>>', self.first_image)
        self.bind('<<SaveImage>>', self.save_image)
        self.bind('<<Settings>>', self.image_settings)
        self.bind('<<CompressNode>>', self.compress_node)
        self.bind('<<DecompressNode>>', self.decompress_node)
        self.bind('<<CustomLabel>>', self.use_custom_label)
        self.bind('<<DefaultLabel>>', self.default_label)
        self.bind('<<EmptyFeatures>>', self.empty_features)
        self.bind('<<CustomPhonology>>', self.custom_phonology)
        self.bind('<<DefaultPhonology>>', self.default_phonology)
        self.bind('<<EmptyPhonology>>', self.empty_phonology)
        self.bind('<<CustomGloss>>', self.custom_gloss)
        self.bind('<<DefaultGloss>>', self.default_gloss)
        self.bind('<<EmptyGloss>>', self.empty_gloss)
        self.bind('<<CustomFeatures>>', self.custom_features)
        self.bind('<<DefaultFeatures>>', self.default_features)
        self.bind('<<EmptyFeatures>>', self.empty_features)
        self.bind('<<EmptyText>>', self.empty_text)
        self.bind('<<CustomText>>', self.custom_text)

        # Show image
        self.draw_phrase_structure_by_title('Accepted LF-interface')

    def custom_text(self, *_):
        gps = self.selected_object_into_gps()
        if gps:
            gps.custom_text = simpledialog.askstring(title='Custom text', prompt='New text', parent=self)
            self.label_stack_update(gps)

    def empty_text(self, *_):
        gps = self.selected_object_into_gps()
        if gps:
            gps.custom_text = None
            self.label_stack_update(gps)

    def custom_features(self, *_):
        gps = self.selected_object_into_gps()
        if gps:
            gps.custom_features = simpledialog.askstring(title='Custom features', prompt='New features', parent=self).split(';')
            self.label_stack_update(gps)

    def default_features(self, *_):
        gps = self.selected_object_into_gps()
        if gps:
            gps.custom_features = None
            self.label_stack_update(gps)

    def empty_features(self, *_):
        gps = self.selected_object_into_gps()
        if gps:
            gps.custom_features = ['$n/a$']
            self.label_stack_update(gps)

    def custom_gloss(self, *_):
        gps = self.selected_object_into_gps()
        if gps:
            gps.custom_gloss = simpledialog.askstring(title='Custom gloss', prompt='New gloss', parent=self)
            self.label_stack_update(gps)

    def default_gloss(self, *_):
        gps = self.selected_object_into_gps()
        if gps:
            gps.custom_gloss = None
            self.label_stack_update(gps)

    def empty_gloss(self, *_):
        gps = self.selected_object_into_gps()
        if gps:
            gps.custom_gloss = '$n/a$'
            self.label_stack_update(gps)

    def custom_phonology(self, *_):
        gps = self.selected_object_into_gps()
        if gps:
            gps.custom_phonology = simpledialog.askstring(title='Custom text', prompt='New text', parent=self)
            self.label_stack_update(gps)

    def default_phonology(self, *_):
        gps = self.selected_object_into_gps()
        if gps:
            gps.custom_phonology = None
            self.label_stack_update(gps)

    def empty_phonology(self, *_):
        gps = self.selected_object_into_gps()
        if gps:
            gps.custom_phonology = '$n/a$'
            self.label_stack_update(gps)

    def default_label(self, *_):
        gps = self.selected_object_into_gps()
        if gps:
            gps.custom_label = None
            self.label_stack_update(gps)

    def use_custom_label(self, *_):
        gps = self.selected_object_into_gps()
        if gps:
            gps.custom_label = simpledialog.askstring(title='Custom label', prompt='New label', parent=self)
            self.label_stack_update(gps)

    def empty_label(self, *_):
        gps = self.selected_object_into_gps()
        if gps:
            gps.custom_label = '$n/a$'
            self.label_stack_update(gps)

    def selected_object_into_gps(self):
        obj = self.canvas.selected_canvas_object
        if obj:
            return self.canvas.node_to_gps[str(obj)]

    def label_stack_update(self, gps):
        gps.label_stack = gps.generate_label_stack()
        self.canvas.redraw(gps.top())
        self.canvas.focus_force()

    def compress_node(self, *_):
        # Select current, selected object from the canvas
        obj = self.canvas.selected_canvas_object
        if obj:
            # Find the matching GPS object
            gps = self.canvas.node_to_gps[str(obj)]
            # Compress the object
            gps.compressed = True
            # Redraw the image
            self.canvas.redraw(gps.top())

    def decompress_node(self, *_):
        # Select current, selected object from the canvas
        obj = self.canvas.selected_canvas_object
        if obj:
            # Find the matching GPS object
            gps = self.canvas.node_to_gps[str(obj)]
            # Compress the object
            gps.compressed = False
            # Redraw the image
            self.canvas.redraw(gps.top())

    def parse_feature_visualizations(self, stri):
        """
        This function can be used to simplify feature representation in the image and/or force it match
        with the feature presentation in some particular study. The original entries are defined in the
        study configuration file (*.lpg) by parameter 'image_parameter_visualization'. The parsing results
        are stored into dictionary that is used during image drawing.

        The form of feature mappings is A // C > T; A // C > T where
        A = feature to be mapped
        T = target feature appearing in the image
        C = optional context (feature at the node itself)
        A // C > T means print out feature T for feature A if the node has C

        Note: symbol A* matches the beginning of the string, e.g. iPHI* maps all features that begin with iPHI.
        """
        stri = clean_string(stri)                                           #   Remove extra spaces, tabs etc.
        entries = stri.split(';')                                           #   Feature mappings are separated by ;
        for x in entries:
            context = ''                                                    #   If there is no context, then C = ''
            antecedent, target = x.split('>')                               #   Conversion is marked as A > T (A mapped into T)
            if '//' in antecedent:                                          #   Context is marked as A // C, where C is set of features at the node
                antecedent, context = antecedent.split('//')
            self.feature_visualizations[antecedent] = (context, target)     #   Store the result into dictionary [A] = (C, T)

    def image_settings(self, *_):
        self.root.settings.change_settings(self, ['Image'])
        self.draw_phrase_structure()

    def save_image(self, *_):
        filename = self.root.settings.data['study_folder'] + '/phrase_structure_image.ps'
        self.canvas.postscript(file=filename, colormode='color')

    def draw_phrase_structure(self):
        self.prepare_phrase_structure()
        self.canvas.delete("all")
        spx, spy = self.prepare_canvas()
        self.canvas.draw_to_canvas(self.gps, spx, spy, self.s['grid'])

    def prepare_phrase_structure(self):
        self.canvas.derivational_index, ps, self.canvas.title = self.get_ps_from_speaker_model(self.speaker_model, self.index_of_analysis_shown)
        self.gps = GPhraseStructure(ps.top())
        self.gps.initialize_logical_space()
        self.gps.remove_overlap()

    def prepare_canvas(self):
        width, height, spx, spy = self.calculate_canvas_size(self.gps)
        self.canvas.configure(width=width, height=height, background='white')
        self.geometry(str(width) + 'x' + str(height))  # Set window size based on the input phrase structure
        return spx, spy

    def LF(self, *_):
        self.draw_phrase_structure_by_title('Accepted LF-interface')

    def PF(self, *_):
        self.draw_phrase_structure_by_title('PF-interface')

    def draw_phrase_structure_by_title(self, title):
        for i, item in enumerate(self.speaker_model.results.recorded_steps):
            if item[2] == title:
                self.index_of_analysis_shown = i
                self.draw_phrase_structure()
                return

    def next_image(self, *_):
        if self.index_of_analysis_shown < len(self.speaker_model.results.recorded_steps) - 1:
            self.index_of_analysis_shown += 1
            self.draw_phrase_structure()

    def previous_image(self, *_):
        if self.index_of_analysis_shown > 0:
            self.index_of_analysis_shown -= 1
        self.draw_phrase_structure()

    def first_image(self, *_):
        self.index_of_analysis_shown = 0
        self.draw_phrase_structure()

    def calculate_canvas_size(self, gps):
        """Determines the canvas size on the basis of the phrase structure object"""
        left_x, right_x, depth = gps.find_boundaries(0, 0, 0)
        width = (abs(left_x) + abs(right_x)) * self.s['grid'] + 2 * self.s['margins']
        height = depth * self.s['grid'] + 2 * self.s['margins']
        height += gps.label_size() * self.s['tsize'] * gps.find_max_label_size(0)
        return int(width), int(height), abs(left_x) * self.s['grid'] + self.s['margins'], self.s['margins']

    def get_ps_from_speaker_model(self, speaker_model, index):
        """Returns the phrase structure object to be drawn, None otherwise"""
        if index < len(speaker_model.results.recorded_steps):
            return speaker_model.results.recorded_step(index)

class PhraseStructureCanvas(tk.Canvas):
    """Canvas for drawing and manipulating phrase structure objects"""
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.focus_set()
        self.title = None
        self.derivational_index = None
        self.selected_canvas_object = None    # image object selection
        self.selected_logical_object = None   # logical node selection (can be independent of image objects)
        self.parent = parent
        self.node_to_gps = {}
        self.label_style = {'label': ("Times New Roman", int(parent.s['tsize'])),
                            'PF': ("Times New Roman", int(parent.s['tsize']*0.90), "italic"),
                            'gloss': ("Times New Roman", int(parent.s['tsize']*0.90)),
                            'feature': ("Times New Roman", int(parent.s['tsize']*0.75)),
                            'info': ("Courier", int(parent.s['tsize'] * 0.25))}
        self.bind('<Button-1>', self._on_mouse_click)
        self.bind('<KeyPress>', self._key_press)
        self.cursor = None
        self.info_text = None

    def draw_to_canvas(self, gps, spx, spy, grid):
        """Creates a canvas and draws the phrase structure object onto it"""
        self.draw_title(spx)

        self.cursor = self.create_oval((50, 50), (150, 150), state='hidden')    # Image object selection cursor
        self.info_text = self.create_text((200, 300), state='hidden')  # Show information about selected objects

        self.project_into_canvas(gps, spx, spy, grid)
        if self.parent.speaker_model.settings.retrieve('image_parameter_head_chains', True):
            self.draw_head_chains(gps)
        if self.parent.speaker_model.settings.retrieve('image_parameter_phrasal_chains', True):
            self.draw_phrasal_chains(gps)

    def _key_press(self, event):
        if self.selected_canvas_object:
            gps = self.node_to_gps[str(self.selected_canvas_object)]  # Get the phrase structure constituent
            if event.keysym == 'Left':
                gps.move_x(-0.5)
            if event.keysym == 'Right':
                gps.move_x(0.5)
            if event.keysym == 'Down':
                gps.move_y(+0.5)
            if event.keysym == 'Up':
                gps.move_y(-0.5)
            self.redraw(gps.top())
        else:
            if event.keysym == 'Left':
                self.event_generate('<<PreviousImage>>')
            if event.keysym == 'Right':
                self.event_generate('<<NextImage>>')

    def _on_mouse_click(self, *_):
        if self.find_withtag('current'):
            self.selected_canvas_object = self.find_withtag('current')[0]
            if self.gettags('current')[0] == 'node':
                self.selected_logical_object = self.node_to_gps[str(self.selected_canvas_object)]
                x1, y1 = self.coords(self.selected_canvas_object)
                self.itemconfigure(self.cursor, state='normal')
                self.moveto(self.cursor, x1-50, y1-50)
        else:
            self.itemconfigure(self.cursor, state='hidden')
            self.selected_canvas_object = None

    def _show_info(self, *_):
        if self.find_withtag('current'):
            selected = self.find_withtag('current')[0]
            tag = self.gettags('current')[0]
            if tag == 'node':
                gps = self.node_to_gps[str(selected)]
                self.moveto(self.info_text, 200, 300)
                self.itemconfigure(self.info_text, state='normal', fill='black', text=gps.itext(), font=self.label_style['info'])
            if tag == 'phrasal_chain':
                self.moveto(self.info_text, 200, 300)
                self.itemconfigure(self.info_text, state='normal', fill='black', text=tag, font=self.label_style['info'])

    def _hide_info(self, *_):
        self.itemconfigure(self.info_text, state='hidden')

    def draw_title(self, spx):
        self.create_text((spx, 50), font=('times', 20), text='(' + str(self.derivational_index) + ')  ' + self.title)

    def redraw(self, gps):
        self.delete("all")
        gps.remove_overlap()
        width, height, spx, spy = self.parent.calculate_canvas_size(gps)
        self.configure(width=width, height=height, background='white')
        self.parent.geometry(str(width)+'x'+str(height))
        self.cursor = self.create_oval((50, 50), (150, 150), state='hidden')
        self.draw_to_canvas(gps, spx, spy, self.parent.s['grid'])

    def project_into_canvas(self, gps, spx, spy, grid):
        """Projects the logical phase structure object into canvas"""
        X1 = spx + gps.x * grid
        Y1 = spy + gps.y * grid
        gps.X = X1  # Memorize the point on the canvas for later chain marking
        gps.Y = Y1
        gps.generate_label_stack()
        if gps.complex():
            self.create_complex_node(gps, X1, Y1, spx, spy, grid)
        else:
            self.create_primitive_node(gps, X1, Y1)

    def create_complex_node(self, gps, X1, Y1, spx, spy, grid):
        # End coordinates of the left constituent line (gps.x, gps.y contain logical position)
        X2 = spx + gps.left().x * grid
        Y2 = spy + gps.left().y * grid

        # End coordinates of the right constituent line
        X3 = spx + gps.right().x * grid
        Y3 = spy + gps.right().y * grid

        text = self.feature_conversion_for_images(gps.label_stack[0][0], gps)

        # Create text holding the complex label (e.g., XP)
        ID = self.create_text((X1, Y1),
                              text=text,
                              fill='black',
                              activefill='red',
                              tag='node',
                              font=("Times New Roman", self.parent.s['tsize']))

        # Map node to the underlying constituent
        self.node_to_gps[str(ID)] = gps

        # Add Y-offset (lower boundary), for chain drawing etc.
        gps.Y_offset = self.parent.s['tsize']

        # Bind events to the node
        self.tag_bind(ID, '<Enter>', self._show_info)
        self.tag_bind(ID, '<Leave>', self._hide_info)

        if self.selected_logical_object == gps:
            x1, y1 = self.coords(ID)
            self.itemconfigure(self.cursor, state='normal')
            self.moveto(self.cursor, x1 - 50, y1 - 50)

        # Create the two lines for left and right constituents.
        left_dash = None
        right_dash = None
        #if gps.left() and gps.left().adjunct:
        #    left_dash = (10, 10)
        #if gps.right() and gps.right().adjunct:
        #    right_dash = (10, 10)

        if gps.compressed:
            # Compressed complex node will create a triangle without constituents
            self.create_line((X1, Y1 + int(self.parent.s['tsize'] / 1.4)), (X2, Y2 + int(self.parent.s['tsize'] / 1.4)), width=2, fill='black', dash=left_dash)
            self.create_line((X1, Y1 + int(self.parent.s['tsize'] / 1.4)), (X3, Y3 + int(self.parent.s['tsize'] / 1.4)), width=2, fill='black', dash=right_dash)
            self.create_line((X2, Y2 + int(self.parent.s['tsize'] / 1.4)), (X3, Y3 + int(self.parent.s['tsize'] / 1.4)), width=2, fill='black', dash=right_dash)
            text_items = 0
            X = (X2 + X3) / 2
            if gps.custom_phonology and gps.custom_phonology != '$n/a$':
                text_items += 1
                Y = Y2 + text_items * 1.4 * self.parent.s['tsize']
                ID = self.create_text((X, Y),
                                      text=gps.custom_phonology,
                                      fill='black',
                                      activefill='red',
                                      tag='node',
                                      anchor='center',
                                      font=self.label_style['PF'])
            if gps.custom_gloss and gps.custom_gloss != '$n/a$':
                text_items += 1
                Y = Y2 + text_items * 1.4 * self.parent.s['tsize']
                ID = self.create_text((X, Y),
                                      text=f'ʻ{gps.custom_gloss}ʼ',
                                      fill='black',
                                      activefill='red',
                                      tag='node',
                                      anchor='center',
                                      font=self.label_style['gloss'])
            if gps.custom_features and '$n/a$' not in gps.custom_features:
                text_items += 1
                Y = Y2 + text_items * 1.4 * self.parent.s['tsize']
                ID = self.create_text((X, Y),
                                      text=' '.join(gps.custom_features),
                                      fill='black',
                                      activefill='red',
                                      tag='node',
                                      anchor='center',
                                      font=self.label_style['feature'])
            if gps.custom_text:
                text_items += 1
                Y = Y2 + text_items * 1.4 * self.parent.s['tsize']
                ID = self.create_text((X, Y),
                                      text=gps.custom_text,
                                      fill='black',
                                      activefill='red',
                                      tag='node',
                                      anchor='center',
                                      font=self.label_style['gloss'])

        else:
            self.create_line((X1, Y1 + int(self.parent.s['tsize'] / 1.4)), (X2, Y2 - int(self.parent.s['tsize'] / 1.4)), width=2, fill='black', dash=left_dash)
            self.create_line((X1, Y1 + int(self.parent.s['tsize'] / 1.4)), (X3, Y3 - int(self.parent.s['tsize'] / 1.4)), width=2, fill='black', dash=right_dash)
            # Recursive calls (for non-compressed complex nodes)
            self.project_into_canvas(gps.left(), spx, spy, grid)
            self.project_into_canvas(gps.right(), spx, spy, grid)
        return ID

    def create_primitive_node(self, gps, X1, Y1):
        Y_offset = 0    # Y_offset determines the lower boundary of the node + its label(s)

        # Reproduce the head and all of its affixes
        for j, affix in enumerate(gps.get_affix_list(), start=1):

            # Do not reproduce copies
            if affix.copied:
                break

            # Do not produce affixes if blocked by settings
            if j > 1 and not self.parent.speaker_model.settings.retrieve('image_parameter_complex_heads', True):
                break

            # Generate the label text (label + phonological exponent + gloss)
            for i, item in enumerate(affix.label_stack):

                # Perform feature conversions (e.g., simplifications, adjustments based on theory)
                text = self.feature_conversion_for_images(item[0], gps)
                if text and item[1] == 'feature':
                    text = '[' + text + ']'

                if item[1] == 'gloss' and not self.parent.speaker_model.settings.retrieve('image_parameter_glosses', True):
                    continue

                if item[1] == 'PF' and not self.parent.speaker_model.settings.retrieve('image_parameter_words', True):
                    continue

                # Create the text widget for the element
                ID = self.create_text((X1, Y1 + Y_offset),
                                      fill='black',
                                      activefill='red',
                                      tag='node',
                                      text=text,
                                      anchor='center',
                                      font=self.label_style[item[1]])

                # Update the offset
                Y_offset += 1.2 * self.parent.s['tsize']

                # Add the node to the mapping from nodes to affixes
                self.node_to_gps[str(ID)] = affix

                # Add events to the first element (i == 0 when producing the label)
                if i == 0:
                    self.tag_bind(ID, '<Enter>', self._show_info)
                    self.tag_bind(ID, '<Leave>', self._hide_info)

        # Store the offset for later use (e.g., drawing chains, agreement)
        gps.Y_offset = Y_offset
        self.update_cursor(gps, X1, Y1)

    def feature_conversion_for_images(self, text, node):
        if self.parent.speaker_model.settings.retrieve('image_parameter_DP_hypothesis', False):
            if text == 'φ':
                text = 'D'
            if text == 'φP':
                text = 'DP'
        for feature in self.parent.feature_visualizations.keys():                               #   Stores feature conversions for images
            if (feature.endswith('*') and text.startswith(feature[:-1])) or (feature == text):  #   wildcard (*) processing
                context, target = self.parent.feature_visualizations[feature]                   #   context = features in the node itself, target = features to print out
                if not context:                                                                 #   if not context, then print out target
                    return target
                elif set(context.split(',')) <= node.features:                                  #   additional context test, if applicable
                    return target
        return text                                                                             #   No change to the feature

    def update_cursor(self, gps, x1, y1):
        if self.selected_logical_object == gps:
            self.itemconfigure(self.cursor, state='normal')
            self.moveto(self.cursor, x1 - 50, y1 - 50)

    def draw_head_chains(self, gps):
        if gps.head_chain_target:
            if gps.sister() != gps.head_chain_target or self.parent.speaker_model.settings.retrieve('image_parameter_trivial_head_chains', False) or not gps.nonverbal():
                self.draw_dependency('head_chain', gps, gps.head_chain_target)
        if gps.complex() and not gps.compressed:
            self.draw_head_chains(gps.left())
            self.draw_head_chains(gps.right())

    def draw_phrasal_chains(self, gps):
        i = gps.hasChain()
        if i and gps.sister():
            target = gps.sister().find_node_with_identity(i)
            if target:
                self.draw_dependency('phrasal_chain', gps, target)
        if gps.complex() and not gps.compressed:
            self.draw_phrasal_chains(gps.left())
            self.draw_phrasal_chains(gps.right())

    def draw_Agree(self, gps):
        pass
        #if gps.Agree_target:
        #    self.draw_dependency('Agree', gps, gps.Agree_target)
        #if gps.complex():
        #    self.draw_Agree(gps.left())
        #    self.draw_Agree(gps.right())

    def draw_dependency(self, style, source_gps, target_gps):
        """Draws a dependency arc from point to point"""

        # If the target node is inside a compressed node, we do not currently draw any arc into it
        if {x for x in target_gps.dominating_nodes() if x.compressed}:
            return

        # Phrasal chains start from the bottom of the complex constituent
        if style == 'phrasal_chain':
            X1 = source_gps.X
            X3 = target_gps.X
            offset = 0
            if source_gps.compressed:
                if source_gps.custom_phonology and source_gps.custom_phonology != '$n/a$':
                    offset += 1
                if source_gps.custom_gloss and source_gps.custom_gloss != '$n/a$':
                    offset += 1
                if source_gps.custom_text:
                    offset += 1
            Y1 = source_gps.left().Y + 1.4 * self.parent.s['tsize'] * offset
            Y3 = target_gps.left().Y
        # Head chains start from the head
        else:
            X1 = source_gps.X
            Y1 = source_gps.Y
            X3 = target_gps.X
            Y3 = target_gps.Y
        # Middle point X2
        X2 = X1 + abs(X1 - X3) / 2
        if X1 == X3:
            Y3 = Y3 - self.parent.s['tsize']
        # Middle point Y2
        curvature = self.parent.speaker_model.settings.retrieve('image_parameter_chain_curvature', 1)
        Y2 = Y3 + target_gps.Y_offset + self.parent.s['grid'] * int(curvature) * 1.2
        #if style == 'phrasal_chain' and abs(Y1 - Y3) < self.parent.s['grid'] * 2:
        #    Y2 = Y2 * 1.2

        # Create arc
        self.create_line((X1, Y1 + source_gps.Y_offset), (X2, Y2), (X3, Y3 + target_gps.Y_offset), dash=self.parent.line_style[style]['dash'], width=self.parent.line_style[style]['width'], smooth=True, tag=style, fill=self.parent.line_style[style]['fill'])
