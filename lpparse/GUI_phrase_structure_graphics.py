import tkinter as tk
from tkinter import simpledialog, filedialog, messagebox
from phrase_structure import PhraseStructure
from feature_processing import clean_string
from g_phrase_structure import GPhraseStructure
import pickle
from GUI_gphrase_structure_canvas import PhraseStructureCanvas


class PhraseStructureGraphics(tk.Toplevel):
    """Window hosting the canvas"""
    def __init__(self, root, **kwargs):
        super().__init__(root)
        self.settings = kwargs['settings']
        self.title("Phrase Structure Graphics")
        self.geometry(('2800x1500+100+100'))
        self.speaker_model = kwargs['speaker_model']
        self.image_title = kwargs['title']
        self.root = root
        self.feature_visualizations = {}
        self.root_gps = kwargs['gps']  # Current phrase structure on screen
        self.original_gps = kwargs['gps']   # Store the original (to reset)
        if kwargs['gps']:
            self.show_whole_derivation = False
        else:
            self.show_whole_derivation = True

        # Settings for drawing
        self.S = {'grid': 150,
                  'margins': 200,
                  'y_grid': 180,
                  'y_margins': 300,
                  'label_padding': 1,
                  'text_spacing': 1.5,
                  'tshrink': 1.1,
                  'arc_curvature': 1,
                  'tsize': int(150 / 3.5)}

        self.canvas = PhraseStructureCanvas(self)
        self.canvas.grid(row=4, column=0)
        self.canvas.focus_set()
        self.canvas.configure(width=2600, height=1400, background='white')
        self.canvas.scrollregion=(0, 0, 5000, 5000)

        # Scrollbars for the canvas
        xscroll = tk.Scrollbar(self, command=self.canvas.xview, orient=tk.HORIZONTAL)
        xscroll.grid(row=3, column=0, sticky='new')
        yscroll = tk.Scrollbar(self, command=self.canvas.yview, orient=tk.VERTICAL)
        yscroll.grid(row=4, column=1, sticky='nsw')
        self.canvas.configure(yscrollcommand=yscroll.set)
        self.canvas.configure(xscrollcommand=xscroll.set)

        # Shows information about elements in the canvas
        self.infoframe = tk.Label(self, borderwidth=20, bg='white')

        # Features shown in figures on the basis of settings
        if self.settings:
            GPhraseStructure.draw_features = {feature.strip() for feature in self.settings.retrieve('image_parameter_features', None).split(';')}
            mapping_str = self.settings.retrieve('image_parameter_visualization', '')
            # Generate lexical feature visualizations
            if mapping_str:
                self.parse_feature_visualizations(mapping_str)

        # Internal variables
        self.index_of_analysis_shown = 0
        self.phase_structure_title = None
        self.label = None

        # Line styles
        self.line_style = {'phrasal_chain': {'fill': 'black', 'dash': None, 'width': 2},
                           'head_chain': {'fill': 'black', 'dash': None, 'width': 2},
                           'Agree': {'fill': 'blue', 'dash': None, 'width': 3},
                           'arrow': {'fill': 'black', 'dash': None, 'width': 2},
                           'custom': {'fill': 'black', 'dash': None, 'width': 2}}

        # Menu
        self.graphics_menu = GraphicsMenu(self)
        self.config(menu=self.graphics_menu)

        # Buttons and status info
        pad = 2
        ribbon = tk.Frame(self)
        ribbon.grid(row=0, column=0, sticky='W')
        status_bar = tk.Frame(self)
        status_bar.grid(row=1, column=0, sticky='W')
        self.status_label = tk.Label(status_bar, text='')
        self.status_label.grid(row=0, column=0, sticky='E')

        if self.speaker_model and self.speaker_model.results.recorded_steps:
            self.firstButtonImage = tk.PhotoImage(file='./lpparse/image resources/first_arrow.png').subsample(2, 2)
            firstButton = tk.Button(ribbon, command=self.first_image,
                                    compound=tk.LEFT,
                                    image=self.firstButtonImage,
                                    font=('Calibri', 20),
                                    bg='white',
                                    fg='black')
            firstButton.grid(row=0, column=0, sticky=tk.E, padx=pad, pady=pad)

        if self.speaker_model and self.speaker_model.results.recorded_steps:
            self.previousButtonImage = tk.PhotoImage(file='./lpparse/image resources/left_arrow.png').subsample(2, 2)
            previousButton = tk.Button(ribbon, command=self.previous_image,
                                       image=self.previousButtonImage,
                                       compound=tk.LEFT,
                                       font=('Calibri', 20),
                                       bg='white',
                                       fg='black')
            previousButton.grid(row=0, column=1, sticky=tk.E, padx=pad, pady=pad)

        if self.speaker_model and self.speaker_model.results.recorded_steps:
            self.nextButtonImage = tk.PhotoImage(file='./lpparse/image resources/right_arrow.png').subsample(2, 2)
            nextButton = tk.Button(ribbon, command=self.next_image,
                                   compound=tk.LEFT,
                                   image=self.nextButtonImage,
                                   font=('Calibri', 20),
                                   bg='white',
                                   fg='black')
            nextButton.grid(row=0, column=2, sticky=tk.E, padx=pad, pady=pad)

        self.compressButtonImage = tk.PhotoImage(file='./lpparse/image resources/compress.png').subsample(2, 2)
        compressButton = tk.Button(ribbon, command=self.compress_node,
                                   compound=tk.LEFT,
                                   image=self.compressButtonImage,
                                   font=('Calibri', 20),
                                   bg='white',
                                   fg='black')
        compressButton.grid(row=0, column=3, sticky=tk.E, padx=pad, pady=pad)

        self.phonologyButtonImage = tk.PhotoImage(file='./lpparse/image resources/phonology.png').subsample(2, 2)
        phonologyButton = tk.Button(ribbon, command=self.custom_phonology,
                                    compound=tk.LEFT,
                                    image=self.phonologyButtonImage,
                                    font=('Calibri', 20),
                                    bg='white',
                                    fg='black')
        phonologyButton.grid(row=0, column=4, sticky=tk.E, padx=pad, pady=pad)

        self.glossButtonImage = tk.PhotoImage(file='./lpparse/image resources/gloss.png').subsample(2, 2)
        phonologyButton = tk.Button(ribbon, command=self.custom_gloss,
                                    compound=tk.LEFT,
                                    image=self.glossButtonImage,
                                    font=('Calibri', 20),
                                    bg='white',
                                    fg='black')
        phonologyButton.grid(row=0, column=5, sticky=tk.E, padx=pad, pady=pad)

        self.no_infoButtonImage = tk.PhotoImage(file='./lpparse/image resources/no_info.png').subsample(2, 2)
        no_infoButton = tk.Button(ribbon, command=self.only_label,
                                  compound=tk.LEFT,
                                  image=self.no_infoButtonImage,
                                  font=('Calibri', 20),
                                  bg='white',
                                  fg='black')
        no_infoButton.grid(row=0, column=6, sticky=tk.E, padx=pad, pady=pad)

        self.expandButtonImage = tk.PhotoImage(file='./lpparse/image resources/expand.png').subsample(2, 2)
        expandButton = tk.Button(ribbon, command=self.expand_phrase_structure,
                                 compound=tk.LEFT,
                                 image=self.expandButtonImage,
                                 font=('Calibri', 20),
                                 bg='white',
                                 fg='black')
        expandButton.grid(row=0, column=7, sticky=tk.E, padx=pad, pady=pad)

        self.custom_labelButtonImage = tk.PhotoImage(file='./lpparse/image resources/custom_label.png').subsample(2, 2)
        expandButton = tk.Button(ribbon, command=self.use_custom_label,
                                 compound=tk.LEFT,
                                 image=self.custom_labelButtonImage,
                                 font=('Calibri', 20),
                                 bg='white',
                                 fg='black')
        expandButton.grid(row=0, column=8, sticky=tk.E, padx=pad, pady=pad)

        # Make host window and canvas visible
        self.grid()

        self.bind('<<SaveAsStructure>>', self.save_as_structure)
        self.bind('<<LoadAsStructure>>', self.load_as_structure)
        self.bind('<<FitPhraseStructure>>', self.fit_phrase_structure)
        self.bind('<<LF>>', self.LF)
        self.bind('<<PF>>', self.PF)
        self.bind('<<NextImage>>', self.next_image)
        self.bind('<<PreviousImage>>', self.previous_image)
        self.bind('<<FirstImage>>', self.first_image)
        self.bind('<<CaptureImage>>', self.save_image)
        self.bind('<<CompressNode>>', self.compress_node)
        self.bind('<<DecompressNode>>', self.decompress_node)
        self.bind('<<MoveUp>>', self.move_up)
        self.bind('<<MoveDown>>', self.move_down)
        self.bind('<<MoveLeft>>', self.move_left)
        self.bind('<<MoveRight>>', self.move_right)
        self.bind('<<CustomLabel>>', self.use_custom_label)
        self.bind('<Alt-l>', self.use_custom_label)
        self.bind('<<DefaultLabel>>', self.default_label)
        self.bind('<<EmptyLabel>>', self.empty_label)
        self.bind('<<LabelSubscript>>', self.label_subscript)
        self.bind('<<LabelSuperscript>>', self.label_superscript)
        self.bind('<<EmptyFeatures>>', self.empty_features)
        self.bind('<<CustomPhonology>>', self.custom_phonology)
        self.bind('<<DefaultPhonology>>', self.default_phonology)
        self.bind('<<EmptyPhonology>>', self.empty_phonology)
        self.bind('<<MarkEllipsis>>', self.mark_ellipsis)
        self.bind('<<CustomGloss>>', self.custom_gloss)
        self.bind('<<DefaultGloss>>', self.default_gloss)
        self.bind('<<EmptyGloss>>', self.empty_gloss)
        self.bind('<<CustomFeatures>>', self.custom_features)
        self.bind('<<DefaultFeatures>>', self.default_features)
        self.bind('<<EmptyFeatures>>', self.empty_features)
        self.bind('<<NewFeatures>>', self.new_features)
        self.bind('<<ChangeOriginalLabel>>', self.change_original_label)
        self.bind('<<EmptyText>>', self.empty_text)
        self.bind('<<CreateArc>>', self.create_arc)
        self.bind('<<DeleteDependencies>>', self.delete_dependencies)
        self.bind('<<CreateForwardArrow>>', self.create_forward_arrow)
        self.bind('<<CreateBackwardArrow>>', self.create_backward_arrow)
        self.bind('<<CreateBidirectionalArrow>>', self.create_bidirectional_arrow)
        self.bind('<<CreateArrow>>', self.create_arrow)
        self.bind('<<CreateNamedArrow>>', self.create_named_arrow)
        self.bind('<<ChangeCurvature>>', self.change_curvature)
        self.bind('<<AddXP>>', self.add_XP)
        self.bind('<<AddDP>>', self.add_DP)
        self.bind('<<AddHead>>', self.add_Head)
        self.bind('<<AddC>>', self.add_C)
        self.bind('<<AddT>>', self.add_T)
        self.bind('<<AddV>>', self.add_V)
        self.bind('<<ReversePhraseStructure>>', self.reverse_phrase_structure)
        self.bind('<<ReversePresentation>>', self.reverse_presentation)
        self.bind('<<ExpandPhraseStructure>>', self.expand_phrase_structure)
        self.bind('<<ExpandComplexHead>>', self.expand_complex_head)
        self.bind('<<ShrinkPhraseStructure>>', self.shrink_phrase_structure)
        self.bind('<<ShrinkDP>>', self.shrink_into_DP)
        self.bind('<<DeletePhraseStructure>>', self.delete_phrase_structure)
        self.bind('<<MakeAdjunct>>', self.make_adjunct)
        self.bind('<<MakeRegular>>', self.make_regular)
        self.bind('<<CompressAllDPs>>', self.compress_all_DPs)
        self.bind('<<DeleteAllCustomFields>>', self.delete_all_custom_fields)
        self.bind('<<MoveUp>>', self.move_up)
        self.bind('<<MoveDown>>', self.move_down)
        self.bind('<<MoveLeft>>', self.move_left)
        self.bind('<<MoveRight>>', self.move_right)
        self.bind('<<Recalibrate>>', self.recalibrate)
        self.bind('<<ClearNode>>', self.clear_content)
        self.bind('<<EnableHeadChains>>', self.enable_head_chains)
        self.bind('<<DisableHeadChains>>', self.disable_head_chains)
        self.bind('<<EnablePhrasalChains>>', self.enable_phrasal_chains)
        self.bind('<<DisablePhrasalChains>>', self.disable_phrasal_chains)
        self.bind('<<BasicTemplate>>', self.basic_template)
        self.bind('<<TemplateVP>>', self.template_VP)
        self.bind('<<TemplatevP>>', self.template_vP)
        self.bind('<<TemplateTP>>', self.template_TP)
        self.bind('<<TemplateCP>>', self.template_CP)
        self.bind('<<OnlyLabel>>', self.only_label)
        self.bind('<<ComplexHeadStyle_Stack>>', self.complex_head_style_stack)
        self.bind('<<ComplexHeadStyle_Standard>>', self.complex_head_style_standard)

        # Show image
        self.initialize_and_show_image()

    # ----------------------------------------------------------------------------------------------
    # Image drawing functions

    def initialize_and_show_image(self):
        """
        Initializes settings and canvas and selects the phrase structure to be imagined on the basis
        of whether we want to edit single image (loaded from file) or examine whole derivation (output from
        the model). This function is also called if the user changed settings.
        """
        GPhraseStructure.image_parameter_phrasal_complex_heads = self.settings.retrieve('image_parameter_phrasal_complex_heads', False)
        GPhraseStructure.image_parameter_covert_complex_heads = self.settings.retrieve('image_parameter_phrasal_complex_heads', False)
        self.canvas.delete('all')
        if self.show_whole_derivation:
            # Derivation (sequence of phrase structures, whole output from the model)
            self.draw_phrase_structure_from_derivation(title='Accepted LF-interface')
        else:
            # Single GPS (usually loaded from separate file)
            self.canvas.title=self.image_title
            self.canvas.derivational_index = 0

    def draw_phrase_structure(self, X):
        """Deletes content from the canvas and draws X on it"""
        self.canvas.delete('all')
        self.root_gps = GPhraseStructure(X.top().copy())
        self.root_gps.initialize_logical_space()
        self.root_gps.remove_overlap()
        spx, spy = self.determine_position_of_highest_node(self.root_gps)
        self.canvas.draw_to_canvas(self.root_gps, spx, spy)

    def draw_phrase_structure_from_derivation(self, **kwargs):
        """Retrieves step from the derivation and calls the drawing function to present it on canvas"""
        if 'step' in kwargs:
            self.canvas.derivational_index, X, self.canvas.title = self.get_ps_from_speaker_model(self.speaker_model, kwargs['step'])
        if 'title' in kwargs:
            for step, item in enumerate(self.speaker_model.results.recorded_steps):
                if item[2] == kwargs['title']:
                    self.canvas.derivational_index, X, self.canvas.title = self.get_ps_from_speaker_model(self.speaker_model, step)
        else:
            self.canvas.derivational_index, X, self.canvas.title = self.get_ps_from_speaker_model(self.speaker_model, self.index_of_analysis_shown)
        self.index_of_analysis_shown = self.canvas.derivational_index
        self.draw_phrase_structure(X)

    def get_ps_from_speaker_model(self, speaker_model, index):
        """Returns the phrase structure object to be drawn, None otherwise"""
        if index < len(speaker_model.results.recorded_steps):
            return speaker_model.results.recorded_step(index)

    def draw_and_save_phrase_structure_tree_as_postscript(self, X, filename):
        self.canvas.delete('all')
        self.canvas.title = ''
        self.canvas.derivational_index = 0
        self.draw_phrase_structure(X)
        self.fit_into_screen_and_show()
        self.update()
        self.save_image_as_postscript(filename)

    def fit_into_screen_and_show(self):
        self.lift()
        x1, y1, x2, y2 = self.canvas.bbox('all')
        self.update_contents(False, -x1, -y1)
        if x2 - x1 > 2800:
            width = x2 - x1
        else:
            width = 2800
        self.canvas.configure(width=width, height=y2, background='white')

    def save_image_as_postscript(self, filename=''):
        self.canvas.postscript(file=filename + '.eps', colormode='color')

    # ---------------------------------------------------------------------------------
    # Menu actions

    def LF(self, *_):
        self.draw_phrase_structure_from_derivation(title='Accepted LF-interface')

    def PF(self, *_):
        self.draw_phrase_structure_from_derivation(title='PF-interface')

    def fit_phrase_structure(self, *_):
        self.fit_into_screen_and_show()

    def change_curvature(self, *_):
        self.S['arc_curvature'] = float(simpledialog.askstring(title='Change arc curvature', prompt='Curvature (0-5)', parent=self))
        self.update_contents()

    def label_subscript(self, *_):
        for gps in self.selected_objects_into_gps_list():
            gps.subscript = simpledialog.askstring(title='Add subscript', prompt='Subscript', parent=self)
            self.label_stack_update(gps)
            self.update_contents()

    def label_superscript(self, *_):
        for gps in self.selected_objects_into_gps_list():
            gps.superscript = simpledialog.askstring(title='Add superscript', prompt='Superscript', parent=self)
            self.label_stack_update(gps)
            self.update_contents()

    def compress_all_DPs(self, *_):
        def compress_all_DPs_(gps):
            if {'D', 'φ'} & gps.head().features:
                gps.compressed = True
            else:
                if gps.left():
                    compress_all_DPs_(gps.left())
                if gps.right():
                    compress_all_DPs_(gps.right())
        compress_all_DPs_(self.root_gps)
        self.update_contents()

    def delete_all_custom_fields(self, *_):
        def delete_all_custom_fields_(gps):
            if not gps.complex():
                gps.custom_label = None
                gps.custom_phonology = '$n/a$'
                gps.custom_gloss = '$n/a$'
                gps.custom_features = ['$n/a$']
                gps.custom_text = None
                self.label_stack_update(gps)
            else:
                if gps.left():
                    delete_all_custom_fields_(gps.left())
                if gps.right():
                    delete_all_custom_fields_(gps.right())
        delete_all_custom_fields_(self.root_gps)
        self.parent.update_contents()

    def new_features(self, *_):
        for gps in self.selected_objects_into_gps_list():
            gps.features = set(simpledialog.askstring(title='Linguistic features', prompt='New linguistic features', parent=self).split(';'))
            self.label_stack_update(gps)
            self.update_contents()

    def change_original_label(self, *_):
        for gps in self.selected_objects_into_gps_list():
            old_label = gps.label()
            gps.features = {f for f in gps.features if not f.startswith('PF:') and not f.startswith('LF:') and f != old_label}
            gps.features.add(simpledialog.askstring(title='Change the original label', prompt='New label', parent=self))
            self.label_stack_update(gps)
            self.update_contents()

    def add_T(self, *_):
        for gps in self.selected_objects_into_gps_list():
            Y = gps.mother()
            right = gps.is_right()
            T = GPhraseStructure(PhraseStructure())
            T.features = {'T'}
            Host = GPhraseStructure(PhraseStructure(), T, gps)
            if Y:
                if right:
                    Y.const = [Y.left(), Host]
                else:
                    Y.const = [Host, Y.right()]
                Host.mother_ = Y
            else:
                self.root_gps = Host
            self.update_contents()

    def add_V(self, *_):
        for gps in self.selected_objects_into_gps_list():
            Y = gps.mother()
            right = gps.is_right()
            V = GPhraseStructure(PhraseStructure())
            V.features = {'V'}
            Host = GPhraseStructure(PhraseStructure(), V, gps)
            if Y:
                if right:
                    Y.const = [Y.left(), Host]
                else:
                    Y.const = [Host, Y.right()]
                Host.mother_ = Y
            else:
                self.root_gps = Host
            self.update_contents()

    def add_C(self, *_):
        for gps in self.selected_objects_into_gps_list():
            Y = gps.mother()
            right = gps.is_right()
            C = GPhraseStructure(PhraseStructure())
            C.features = {'C'}
            Host = GPhraseStructure(PhraseStructure(), C, gps)
            if Y:
                if right:
                    Y.const = [Y.left(), Host]
                else:
                    Y.const = [Host, Y.right()]
                Host.mother_ = Y
            else:
                self.root_gps = Host
            self.update_contents()

    def expand_complex_head(self, *_):
        for gps in self.selected_objects_into_gps_list():
            if not gps.complex():
                H = GPhraseStructure(PhraseStructure())
                affix_lst = gps.get_affix_list()
                # If covert complex heads are set to be disabled, we enable them first
                if [a for a in affix_lst if a.copied]:
                    self.settings.store('image_parameter_covert_complex_heads', True)
                last_affix = gps.get_affix_list()[-1]
                last_affix.const = [H]
                H.mother_ = last_affix
                H.features.add('PF:X')
                self.update_contents()

    def reverse_presentation(self, *_):
        for gps in self.selected_objects_into_gps_list():
            if gps.flip:
                gps.flip = False
            else:
                gps.flip = True
        self.update_contents()

    def basic_template(self, *_):
        X = GPhraseStructure(PhraseStructure())
        X.features = {'X', 'PF:X'}
        Y = GPhraseStructure(PhraseStructure())
        Y.features = {'Y', 'PF:Y'}
        Z = GPhraseStructure(PhraseStructure())
        Z.features = {'Z', 'PF:Z'}
        YP = GPhraseStructure(PhraseStructure(), Y, Z)
        XP = GPhraseStructure(PhraseStructure(), X, YP)
        self.root_gps = XP
        self.update_contents()

    def DP(self):
        D = GPhraseStructure(PhraseStructure())
        D.features = {'D'}
        N = GPhraseStructure(PhraseStructure())
        N.features = {'N'}
        return GPhraseStructure(PhraseStructure(), D, N)

    def vP(self):
        v = GPhraseStructure(PhraseStructure())
        v.features = {'v'}
        vP1 = GPhraseStructure(PhraseStructure(), v, self.VP())
        return GPhraseStructure(PhraseStructure(), self.DP(), vP1)

    def TP(self):
        T = GPhraseStructure(PhraseStructure())
        T.features = {'T'}
        TP = GPhraseStructure(PhraseStructure(), T, self.vP())
        return GPhraseStructure(PhraseStructure(), self.DP(), TP)

    def VP(self):
        V = GPhraseStructure(PhraseStructure())
        V.features = {'V'}
        return GPhraseStructure(PhraseStructure(), V, self.DP())

    def CP(self):
        C = GPhraseStructure(PhraseStructure())
        C.features = {'C'}
        return GPhraseStructure(PhraseStructure(), C, self.TP())

    def template_VP(self, *_):
        self.root_gps = self.VP()
        self.update_contents()

    def template_vP(self, *_):
        self.root_gps = self.vP()
        self.update_contents()

    def template_TP(self, *_):
        self.root_gps = self.TP()
        self.update_contents()

    def template_CP(self, *_):
        self.root_gps = self.CP()
        self.update_contents()

    def add_Head(self, *_):
        for gps in self.selected_objects_into_gps_list():
            Y = gps.mother()
            right = gps.is_right()
            X = GPhraseStructure(PhraseStructure())
            Host = GPhraseStructure(PhraseStructure(), X, gps)
            if Y:
                if right:
                    Y.const = [Y.left(), Host]
                else:
                    Y.const = [Host, Y.right()]
                Host.mother_ = Y
            else:
                self.root_gps = Host
            self.update_contents()

    def add_XP(self, *_):
        for gps in self.selected_objects_into_gps_list():
            Z = gps.mother()
            right = gps.is_right()

            # Create DP
            X = GPhraseStructure(PhraseStructure())
            X.features = {'PF:X'}
            Y = GPhraseStructure(PhraseStructure())
            Y.features = {'PF:Y'}
            XP = GPhraseStructure(PhraseStructure(), X, Y)
            Host = GPhraseStructure(PhraseStructure(), XP, gps)
            if Z:
                if right:
                    Z.const = [Z.left(), Host]
                else:
                    Z.const = [Host, Z.right()]
                Host.mother_ = Z
            else:
                self.root_gps = Host
            self.update_contents()

    def add_DP(self, *_):
        for gps in self.selected_objects_into_gps_list():
            Y = gps.mother()
            right = gps.is_right()

            # Create DP
            D = GPhraseStructure(PhraseStructure())
            D.features = {'D'}
            N = GPhraseStructure(PhraseStructure())
            N.features = {'N'}
            DP = GPhraseStructure(PhraseStructure(), D, N)

            Host = GPhraseStructure(PhraseStructure(), DP, gps)
            if Y:
                if right:
                    Y.const = [Y.left(), Host]
                else:
                    Y.const = [Host, Y.right()]
                Host.mother_ = Y
            else:
                self.root_gps = Host
            self.update_contents()

    def make_adjunct(self, *_):
        for gps in self.selected_objects_into_gps_list():
            if gps.complex():
                gps.adjunct = True
                self.update_contents()

    def make_regular(self, *_):
        for gps in self.selected_objects_into_gps_list():
            if gps.complex():
                gps.adjunct = False
                self.update_contents()

    def enable_head_chains(self, *_):
        self.settings.data['image_parameter_head_chains'] = True
        self.update_contents()

    def disable_head_chains(self, *_):
        self.settings.data['image_parameter_head_chains'] = False
        self.update_contents()

    def enable_phrasal_chains(self, *_):
        self.settings.data['image_parameter_phrasal_chains'] = True
        self.update_contents()

    def disable_phrasal_chains(self, *_):
        self.settings.data['image_parameter_phrasal_chains'] = False
        self.update_contents()

    def only_label(self, *_):
        for gps in self.selected_objects_into_gps_list():
            if not gps.complex():
                gps.custom_label = None
                gps.custom_text = None
                gps.custom_gloss = '$n/a$'
                gps.custom_phonology = '$n/a$'
                gps.custom_features = ['$n/a$']
                self.label_stack_update(gps)
                self.update_contents()

    def clear_content(self, *_):
        for gps in self.selected_objects_into_gps_list():
            if not gps.complex():
                gps.custom_label = ' '
                gps.features = set()
                gps.custom_text = None
                gps.custom_gloss = None
                gps.custom_phonology = None
                self.label_stack_update(gps)
                self.update_contents()

    def recalibrate(self, *_):
        self.draw_phrase_structure_from_derivation(step=self.canvas.derivational_index)

    def move_up(self, *_):
        for gps in self.selected_objects_into_gps_list():
            gps.move_y(-0.5)
        self.canvas.redraw(self.root_gps)

    def move_down(self, *_):
        for gps in self.selected_objects_into_gps_list():
            gps.move_y(+0.5)
        self.canvas.redraw(self.root_gps)

    def move_left(self, *_):
        for gps in self.selected_objects_into_gps_list():
            gps.move_x(-0.5)
        self.canvas.redraw(self.root_gps)

    def move_right(self, *_):
        for gps in self.selected_objects_into_gps_list():
            gps.move_x(+0.5)
        self.canvas.redraw(self.root_gps)

    def save_as_structure(self, *_):
        filename = filedialog.asksaveasfilename() + '.gps'
        with open(filename, 'wb') as output_file:
            pickle.dump(self.root_gps, output_file)

    def load_as_structure(self, *_):
        filename = filedialog.askopenfilename()
        with open(filename, 'rb') as input_file:
            self.root_gps = pickle.load(input_file)
            self.update_contents()

    def expand_phrase_structure(self, *_):
        for gps in self.selected_objects_into_gps_list():
            if not gps.complex():
                empty_const = PhraseStructure()
                X = GPhraseStructure(gps)
                Y = GPhraseStructure(empty_const)
                X.mother_ = gps
                Y.mother_ = gps
                gps.const = [X, Y]
                gps.features = set()
                self.update_contents()

    def shrink_phrase_structure(self, *_):
        for gps in self.selected_objects_into_gps_list():
            gps.const = []
        self.update_contents()

    def shrink_into_DP(self, *_):
        for gps in self.selected_objects_into_gps_list():
            gps.const = []
            gps.custom_label = 'DP'
            self.label_stack_update(gps)
        self.update_contents()

    def delete_phrase_structure(self, *_):
        for gps in self.selected_objects_into_gps_list():
            if gps.mother():
                if gps.is_left():
                    preserved_sister = gps.mother().right()
                else:
                    preserved_sister = gps.mother().left()
                # Delete X and its mother, move the sister upwards
                if gps.mother().mother():
                    grandmother = gps.mother().mother()
                    if gps.mother().is_right():
                        grandmother.const = [grandmother.left(), preserved_sister]
                    else:
                        grandmother.const = [preserved_sister, grandmother.right()]
                    preserved_sister.mother_ = grandmother
                # We preserve only the sister
                else:
                    preserved_sister.mother_ = None
                    self.root_gps = preserved_sister
        self.update_contents()

    def update_contents(self, recalculate=True, x_offset=0, y_offset=0):
        if recalculate:
            self.root_gps.initialize_logical_space()
        self.root_gps.remove_overlap()
        self.recalculate_labels(self.root_gps)
        self.canvas.redraw(self.root_gps, False, x_offset, y_offset)

    def recalculate_labels(self, gps):
        gps.generate_label_stack()
        if gps.complex():
            self.recalculate_labels(gps.left())
            self.recalculate_labels(gps.right())

    def reverse_phrase_structure(self, *_):
        for gps in self.selected_objects_into_gps_list():
            if gps.complex():
                gps.const.reverse()
        self.update_contents()

    def create_arc(self, *_):
        if len(self.canvas.selected_objects) > 1:
            for i, gps_ID in enumerate(self.canvas.selected_objects):
                if i < len(self.canvas.selected_objects) - 1:
                    source_gps = self.canvas.node_to_gps[str(gps_ID)]
                    target_gps = self.canvas.node_to_gps[str(self.canvas.selected_objects[i + 1])]
                    source_gps.custom_arcs.append((target_gps, 'label'))
        self.canvas.redraw(self.root_gps)

    def create_named_arrow(self, *_):
        self.label = simpledialog.askstring(title='Label for arrow', prompt='Label', parent=self)
        self.create_arrow()
        self.label = None
        self.deselect_all()

    def deselect_all(self):
        self.canvas.selected_objects = []
        self.update_contents()

    def create_forward_arrow(self, *_):
        self.create_arrow_('last')

    def create_backward_arrow(self, *_):
        self.create_arrow_('first')

    def create_bidirectional_arrow(self, *_):
        self.create_arrow_('both')

    def create_arrow(self, *_):
        self.create_arrow_('none')

    def create_arrow_(self, arrowtype):
        if len(self.canvas.selected_objects) > 1:
            for i, gps in enumerate(self.canvas.selected_objects):
                if i < len(self.canvas.selected_objects) - 1:
                    source_gps = gps
                    target_gps = self.canvas.selected_objects[i + 1]
                    source_gps.custom_arrows.append((target_gps, self.label, arrowtype))
            self.update_contents()
        self.deselect_all()

    def delete_dependencies(self, *_):
        for gps in self.selected_objects_into_gps_list():
            gps.custom_arcs = []
            gps.custom_arrows = []
        self.deselect_all()
        self.canvas.redraw(gps.top())

    def custom_text(self, *_):
        if self.canvas.selected_objects:
            text = simpledialog.askstring(title='Custom text', prompt='New text', parent=self)
            for gps in self.selected_objects_into_gps_list():
                gps.custom_text = text
                self.label_stack_update(gps)
        self.deselect_all()
        self.canvas.redraw(gps.top())

    def empty_text(self, *_):
        for gps in self.selected_objects_into_gps_list():
            gps.custom_text = None
            self.label_stack_update(gps)
        self.deselect_all()
        self.canvas.redraw(gps.top())

    def custom_features(self, *_):
        if self.canvas.selected_objects:
            features = simpledialog.askstring(title='Custom features', prompt='New features', parent=self).split(';')
            for gps in self.selected_objects_into_gps_list():
                gps.custom_features = features
                self.label_stack_update(gps)
        self.deselect_all()
        self.canvas.redraw(gps.top())

    def default_features(self, *_):
        for gps in self.selected_objects_into_gps_list():
            gps.custom_features = None
            self.label_stack_update(gps)
        self.deselect_all()
        self.canvas.redraw(gps.top())

    def empty_features(self, *_):
        for gps in self.selected_objects_into_gps_list():
            gps.custom_features = ['$n/a$']
            self.label_stack_update(gps)
        self.deselect_all()
        self.canvas.redraw(gps.top())

    def custom_gloss(self, *_):
        if self.canvas.selected_objects:
            gloss = simpledialog.askstring(title='Custom gloss', prompt='New gloss', parent=self)
            for gps in self.selected_objects_into_gps_list():
                gps.custom_gloss = gloss
                self.label_stack_update(gps)
        self.deselect_all()
        self.canvas.redraw(gps.top())

    def default_gloss(self, *_):
        for gps in self.selected_objects_into_gps_list():
            gps.custom_gloss = None
            self.label_stack_update(gps)
        self.deselect_all()
        self.canvas.redraw(gps.top())

    def empty_gloss(self, *_):
        for gps in self.selected_objects_into_gps_list():
            gps.custom_gloss = '$n/a$'
            self.label_stack_update(gps)
        self.deselect_all()
        self.canvas.redraw(gps.top())

    def custom_phonology(self, *_):
        if self.canvas.selected_objects:
            phon = simpledialog.askstring(title='Custom text', prompt='New text', parent=self)
            for gps in self.selected_objects_into_gps_list():
                gps.custom_phonology = phon
                self.label_stack_update(gps)
                gps.ellipsis = False
        self.deselect_all()
        self.canvas.redraw(gps.top())

    def mark_ellipsis(self, *_):
        for gps in self.selected_objects_into_gps_list():
            gps.ellipsis=True
            self.label_stack_update(gps)
        self.deselect_all()
        self.canvas.redraw(gps.top())

    def default_phonology(self, *_):
        for gps in self.selected_objects_into_gps_list():
            gps.custom_phonology = None
            self.label_stack_update(gps)
            gps.ellipsis = False
        self.deselect_all()
        self.canvas.redraw(gps.top())

    def empty_phonology(self, *_):
        for gps in self.selected_objects_into_gps_list():
            gps.custom_phonology = '$n/a$'
            self.label_stack_update(gps)
            gps.ellipsis = False
        self.deselect_all()
        self.canvas.redraw(gps.top())

    def default_label(self, *_):
        for gps in self.selected_objects_into_gps_list():
            gps.custom_label = None
            gps.subscript = None
            gps.superscript = None
            self.label_stack_update(gps)
        self.deselect_all()
        self.canvas.redraw(gps.top())

    def use_custom_label(self, *_):
        for gps in self.selected_objects_into_gps_list():
            gps.custom_label = simpledialog.askstring(title='Custom label', prompt='New label', parent=self)
            gps.subscript = None
            gps.superscript = None
            self.label_stack_update(gps)
        self.update_contents()

    def empty_label(self, *_):
        for gps in self.selected_objects_into_gps_list():
            gps.custom_label = '$n/a$'
            gps.subscript = None
            gps.superscript = None
            self.label_stack_update(gps)
        self.deselect_all()
        self.canvas.redraw(gps.top())

    def selected_objects_into_gps_list(self):
        return [self.canvas.node_to_gps[str(obj)] for obj in self.canvas.selected_objects]

    def label_stack_update(self, gps):
        gps.generate_label_stack()
        self.canvas.redraw(gps.top())

    def compress_node(self, *_):
        for gps in self.selected_objects_into_gps_list():
            # Compress the object
            gps.compressed = True
        self.canvas.redraw(gps.top())

    def decompress_node(self, *_):
        for gps in self.selected_objects_into_gps_list():
            gps.compressed = False
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

    def save_image(self, *_):
        self.fit_into_screen_and_show()
        filename = filedialog.asksaveasfilename()
        self.save_image_as_postscript(filename)
        messagebox.showinfo(title='Image Saving', message=f'Image Saved as {filename}.eps')

    def next_image(self, *_):
        if self.speaker_model.results.recorded_steps:
            if self.index_of_analysis_shown < len(self.speaker_model.results.recorded_steps) - 1:
                self.draw_phrase_structure_from_derivatio(step=self.index_of_analysis_show + 1)

    def previous_image(self, *_):
        if self.speaker_model.results.recorded_steps:
            if self.index_of_analysis_shown > 0:
                self.index_of_analysis_shown -= 1
            self.draw_phrase_structure_from_derivation(step=self.index_of_analysis_shown - 1)

    def first_image(self, *_):
        if self.speaker_model.results.recorded_steps:
            self.draw_phrase_structure_from_derivation(step=0)

    def determine_position_of_highest_node(self, gps):
        """Determines the canvas size on the basis of the phrase structure object"""
        left_x, right_x, depth = gps.find_boundaries(0, 0, 0)
        return abs(left_x) * self.S['grid'] + self.S['margins'], self.S['y_grid'] / 4

    # ------------------------------------------------------------------------------------------
    # Change of settings (from menu)

    def complex_head_style_stack(self, *_):
        self.root.settings.set('image_parameter_phrasal_complex_heads', False)
        self.root_gps = self.original_gps
        self.update_settings()

    def complex_head_style_standard(self, *_):
        self.root.settings.set('image_parameter_phrasal_complex_heads', True)
        self.update_settings()

    def update_settings(self):
        self.settings = self.root.settings
        GPhraseStructure.image_parameter_phrasal_complex_heads = self.root.settings.data['image_parameter_phrasal_complex_heads']
        self.initialize_and_show_image()

# -------------------------------------------------------------------------------------------
# Definition for main menu

class GraphicsMenu(tk.Menu):
    def _event(self, sequence):
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
        file_menu.add_command(label='Load...', command=self._event('<<LoadAsStructure>>'))
        file_menu.add_command(label='Save As...', command=self._event('<<SaveAsStructure>>'))
        file_menu.add_command(label='Save Postscript Image...', command=self._event('<<CaptureImage>>'))
        self.add_cascade(label='File', underline=0, menu=file_menu)

        image_properties_menu = tk.Menu(self, tearoff=False, font=menu_font)
        image_properties_menu.add_command(label='Fit Phrase Structure', command=self._event('<<FitPhraseStructure>>'))
        self.add_cascade(label='Image', menu=image_properties_menu)

        # Select image menu
        select_image = tk.Menu(self, tearoff=False, font=menu_font)
        select_image.add_command(label='PF-interface', command=self._event('<<PF>>'))
        select_image.add_command(label='LF-interface', command=self._event('<<LF>>'))
        select_image.add_command(label='Next image', command=self._event('<<NextImage>>'))
        select_image.add_command(label='Previous image', command=self._event('<<PreviousImage>>'))
        select_image.add_command(label='First image', command=self._event('<<FirstImage>>'))
        self.add_cascade(label='Source image', menu=select_image)

        # Node menu
        node = tk.Menu(self, tearoff=False, font=menu_font)
        node.add_command(label='Compress', command=self._event('<<CompressNode>>'))
        node.add_command(label='Decompress', command=self._event('<<DecompressNode>>'))

        submenu_Move = tk.Menu(node, tearoff=0, font=menu_font)
        submenu_Move.add_command(label='Up', underline=0, command=self._event('<<MoveUP>>'))
        submenu_Move.add_command(label='Right', underline=0, command=self._event('<<MoveRight>>'))
        submenu_Move.add_command(label='Down', underline=0, command=self._event('<<MoveDown>>'))
        submenu_Move.add_command(label='Left', underline=0, command=self._event('<<MoveLeft>>'))
        node.add_cascade(label='Move..', underline=0, menu=submenu_Move)

        node.add_separator()
        node.add_command(label='Clear', command=self._event('<<ClearNode>>'))
        node.add_command(label='Only label', command=self._event('<<OnlyLabel>>'))

        # Submenu for Label
        submenu_Node_Label = tk.Menu(node, tearoff=0, font=menu_font)
        submenu_Node_Label.add_command(label='New', underline=0, command=self._event('<<CustomLabel>>'))
        submenu_Node_Label.add_command(label='Original', command=self._event('<<DefaultLabel>>'))
        submenu_Node_Label.add_command(label='Empty', command=self._event('<<EmptyLabel>>'))
        node.add_cascade(label='Custom label...', underline=0, menu=submenu_Node_Label)

        # Submenu for Label subscript
        submenu_Label_Subscript = tk.Menu(node, tearoff=0, font=menu_font)
        submenu_Label_Subscript.add_command(label='Subscript', command=self._event('<<LabelSubscript>>'))
        submenu_Label_Subscript.add_command(label='Superscript', command=self._event('<<LabelSuperscript>>'))
        node.add_cascade(label='Special labels...', menu=submenu_Label_Subscript)

        # Submenu for Phonology
        submenu_Node_Text = tk.Menu(node, tearoff=0, font=menu_font)
        submenu_Node_Text.add_command(label='New', command=self._event('<<CustomPhonology>>'))
        submenu_Node_Text.add_command(label='Original', command=self._event('<<DefaultPhonology>>'))
        submenu_Node_Text.add_command(label='Empty', command=self._event('<<EmptyPhonology>>'))
        submenu_Node_Text.add_separator()
        submenu_Node_Text.add_command(label='Mark Ellipsis', command=self._event('<<MarkEllipsis>>'))
        node.add_cascade(label='Phonology...', menu=submenu_Node_Text)

        # Submenu for Gloss
        submenu_Node_Gloss = tk.Menu(node, tearoff=0, font=menu_font)
        submenu_Node_Gloss.add_command(label='New', command=self._event('<<CustomGloss>>'))
        submenu_Node_Gloss.add_command(label='Original', command=self._event('<<DefaultGloss>>'))
        submenu_Node_Gloss.add_command(label='Empty', command=self._event('<<EmptyGloss>>'))
        node.add_cascade(label='Gloss...', menu=submenu_Node_Gloss)

        # Submenu for features
        submenu_Node_Features = tk.Menu(node, tearoff=0, font=menu_font)
        submenu_Node_Features.add_command(label='New', command=self._event('<<CustomFeatures>>'))
        submenu_Node_Features.add_command(label='Original', command=self._event('<<DefaultFeatures>>'))
        submenu_Node_Features.add_command(label='Empty', command=self._event('<<EmptyFeatures>>'))
        node.add_cascade(label='Custom features', menu=submenu_Node_Features)
        node.add_cascade(label='Free text', menu=submenu_Node_Text)

        node.add_separator()
        node.add_command(label='Change original label...', command=self._event('<<ChangeOriginalLabel>>'))
        node.add_command(label='Linguistic features...', command=self._event('<<NewFeatures>>'))

        # Submenu for free text
        submenu_Node_Text = tk.Menu(node, tearoff=0, font=menu_font)
        submenu_Node_Text.add_command(label='New', command=self._event('<<CustomText>>'))
        submenu_Node_Text.add_command(label='Empty', command=self._event('<<EmptyText>>'))
        self.add_cascade(label='Node', underline=0, menu=node)

        arc = tk.Menu(self, tearoff=False, font=menu_font)
        arc.add_command(label='Curved', command=self._event('<<CreateArc>>'))
        arc.add_command(label='Change Curvature', command=self._event('<<ChangeCurvature>>'))
        arc.add_separator()

        arc_submenu = tk.Menu(arc, tearoff=False, font=menu_font)
        arc_submenu.add_command(label='Forward', command=self._event('<<CreateForwardArrow>>'))
        arc_submenu.add_command(label='Backward', command=self._event('<<CreateBackwardArrow>>'))
        arc_submenu.add_command(label='Bidirectional', command=self._event('<<CreateBidirectionalArrow>>'))
        arc_submenu.add_command(label='No direction', command=self._event('<<CreateArrow>>'))
        arc.add_cascade(label='Chain...', menu=arc_submenu)

        arc.add_command(label='Named Arrow', command=self._event('<<CreateNamedArrow>>'))
        arc.add_separator()
        arc.add_command(label='Delete', command=self._event('<<DeleteDependencies>>'))
        self.add_cascade(label='Dependency', menu=arc)

        ps = tk.Menu(self, tearoff=False, font=menu_font)
        # Submenu Add...
        submenu_ps = tk.Menu(ps, tearoff=False, font=menu_font)
        submenu_ps.add_command(label='XP', command=self._event('<<AddXP>>'))
        submenu_ps.add_command(label='Head', command=self._event('<<AddHead>>'))
        submenu_ps.add_command(label='DP', command=self._event('<<AddDP>>'))
        submenu_ps.add_command(label='C', command=self._event('<<AddC>>'))
        submenu_ps.add_command(label='T', command=self._event('<<AddT>>'))
        submenu_ps.add_command(label='V', command=self._event('<<AddV>>'))
        ps.add_cascade(label='Add...', menu=submenu_ps)

        submenu_expand_ps = tk.Menu(ps, tearoff=False, font=menu_font)
        submenu_expand_ps.add_command(label='Phrase', command=self._event('<<ExpandPhraseStructure>>'))
        submenu_expand_ps.add_command(label='Complex head', command=self._event('<<ExpandComplexHead>>'))
        ps.add_cascade(label='Expand...', menu=submenu_expand_ps)
        ps.add_command(label='Shrink', command=self._event('<<ShrinkPhraseStructure>>'))
        ps.add_command(label='Shrink Into DP', command=self._event('<<ShrinkDP>>'))
        ps.add_command(label='Delete', command=self._event('<<DeletePhraseStructure>>'))
        ps.add_command(label='Recover Original', command=self._event('<<Recalibrate>>'))
        submenu_mark_special = tk.Menu(ps, tearoff=False, font=menu_font)
        submenu_mark_special.add_command(label='Break Constituency (not functional)', command=self._event('<<BreakConstituency>>'))
        ps.add_cascade(label='Special Marking...', menu=submenu_mark_special)
        ps.add_separator()
        ps.add_command(label='Flip (structure)', command=self._event('<<ReversePhraseStructure>>'))
        ps.add_command(label='Flip (presentation)', command=self._event('<<ReversePresentation>>'))
        ps.add_separator()
        ps.add_command(label='Make Adjunct', command=self._event('<<MakeAdjunct>>'))
        ps.add_command(label='Make Regular', command=self._event('<<MakeRegular>>'))
        ps.add_separator()
        ps.add_command(label='Compress all DPs', command=self._event('<<CompressAllDPs>>'))
        ps.add_command(label='Bare bones', command=self._event('<<DeleteAllCustomFields>>'))
        ps.add_separator()
        ps.add_command(label='Move Up', command=self._event('<<MoveUp>>'))
        ps.add_command(label='Move Down', command=self._event('<<MoveDown>>'))
        ps.add_command(label='Move Left', command=self._event('<<MoveLeft>>'))
        ps.add_command(label='Move Right', command=self._event('<<MoveRight>>'))
        self.add_cascade(label='Phrase Structure', menu=ps)

        # Chain visibility menu
        chains_menu = tk.Menu(self, tearoff=False, font=menu_font)
        # Submenu for chains
        submenu_chains_phrasal = tk.Menu(chains_menu, tearoff=False, font=menu_font)
        submenu_chains_phrasal = tk.Menu(chains_menu, tearoff=0, font=menu_font)
        submenu_chains_phrasal.add_command(label='Enable', command=self._event('<<EnablePhrasalChains>>'))
        submenu_chains_phrasal.add_command(label='Disable', command=self._event('<<DisablePhrasalChains>>'))
        chains_menu.add_cascade(label='Phrasal chains...', menu=submenu_chains_phrasal)
        self.add_cascade(label='Chains', menu=chains_menu)

        # Templates menu
        templates_menu = tk.Menu(self, tearoff=False, font=menu_font)
        templates_menu.add_command(label='Basic XP', command=self._event('<<BasicTemplate>>'))
        templates_menu.add_command(label='VP', command=self._event('<<TemplateVP>>'))
        templates_menu.add_command(label='vP', command=self._event('<<TemplatevP>>'))
        templates_menu.add_command(label='TP', command=self._event('<<TemplateTP>>'))
        templates_menu.add_command(label='CP', command=self._event('<<TemplateCP>>'))
        self.add_cascade(label='Templates', menu=templates_menu)

        # Settings menu
        settings_menu = tk.Menu(self, tearoff=False, font=menu_font)

        #Submenu for complex head style
        submenu_complex_head_style = tk.Menu(settings_menu, tearoff=False, font=menu_font)
        submenu_complex_head_style.add_command(label='Stack', command=self._event('<<ComplexHeadStyle_Stack>>'))
        submenu_complex_head_style.add_command(label='Standard', command=self._event('<<ComplexHeadStyle_Standard>>'))
        settings_menu.add_cascade(label='Complex Head Style...', menu=submenu_complex_head_style)
        # Submenu for head chain visibility
        submenu_chains_head = tk.Menu(settings_menu, tearoff=0, font=menu_font)
        submenu_chains_head.add_command(label='Enable', command=self._event('<<EnableHeadChains>>'))
        submenu_chains_head.add_command(label='Disable', command=self._event('<<DisableHeadChains>>'))
        settings_menu.add_cascade(label='Head chains visibility...', menu=submenu_chains_head)
        # Submenu for head chain visibility 2
        submenu_covert_heads = tk.Menu(settings_menu, tearoff=0, font=menu_font)
        submenu_covert_heads.add_command(label='Enable', command=self._event('<<CovertHeadsEnable>>'))
        submenu_covert_heads.add_command(label='Disable', command=self._event('<<CovertHeadsDisable>>'))
        settings_menu.add_cascade(label='Covert heads...', menu=submenu_covert_heads)
        settings_menu.add_separator()

        self.add_cascade(label='Settings', menu=settings_menu)
