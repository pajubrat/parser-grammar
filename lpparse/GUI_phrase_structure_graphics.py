import tkinter as tk
from tkinter import simpledialog, filedialog, messagebox
from phrase_structure import PhraseStructure
from feature_processing import clean_string
from g_phrase_structure import GPhraseStructure
import pickle
from GUI_gphrase_structure_canvas import PhraseStructureCanvas


class PhraseStructureGraphics(tk.Toplevel):
    """Window hosting the canvas"""
    def __init__(self, application, **kwargs):
        super().__init__(application)
        GPhraseStructure.application = application
        self.title("Phrase Structure Graphics")
        self.geometry(('2800x1500+100+100'))
        self.speaker_model = kwargs['speaker_model']
        self.image_title = kwargs['title']
        self.application = application
        self.feature_visualizations = {}
        self.root_gps = kwargs['gps']  # Current phrase structure on screen
        self.original_gps = self.root_gps
        self.index_of_analysis_shown = 0
        self.phase_structure_title = None
        self.label = None
        self.stored_filename = None
        self.inventory = {'dependencies': []}
        self.lst_dependencies = []
        self.inspect_window = None  # Shows information (features etc) of a selected node
        self.line_style = {'phrasal_chain': {'fill': 'black', 'dash': None, 'width': 2},
                           'head_chain': {'fill': 'black', 'dash': None, 'width': 2},
                           'Agree': {'fill': 'blue', 'dash': None, 'width': 3},
                           'arrow': {'fill': 'black', 'dash': None, 'width': 2},
                           'custom': {'fill': 'black', 'dash': None, 'width': 2}}

        # Canvas

        self.canvas = PhraseStructureCanvas(self)
        self.canvas.grid(row=4, column=0)
        self.canvas.focus_set()
        self.canvas.configure(closeenough=10, width=self.application.settings.retrieve('image_parameter_canvas_width'), height=self.application.settings.retrieve('image_parameter_canvas_height'), background='white')

        # Scrollbars for the canvas

        xscroll = tk.Scrollbar(self, command=self.canvas.xview, orient=tk.HORIZONTAL)
        xscroll.grid(row=3, column=0, sticky='new')
        yscroll = tk.Scrollbar(self, command=self.canvas.yview, orient=tk.VERTICAL)
        yscroll.grid(row=4, column=1, sticky='nsw')
        self.canvas.configure(yscrollcommand=yscroll.set)
        self.canvas.configure(xscrollcommand=xscroll.set)
        self.canvas.scrollregion=(0, 0, 5000, 5000)

        # Menu

        self.graphics_menu = GraphicsMenu(self)
        self.config(menu=self.graphics_menu)
        # Buttons and status info
        self.ribbon = tk.Frame(self)
        self.ribbon.grid(row=0, column=0, sticky='W')
        self.create_ribbon_buttons()
        status_bar = tk.Frame(self)
        status_bar.grid(row=1, column=0, sticky='W')
        self.status_label = tk.Label(status_bar, text='')
        self.status_label.grid(row=0, column=0, sticky='E')

        # Make host window and canvas visible

        self.grid()

        # Features shown in figures on the basis of settings

        GPhraseStructure.draw_features = {feature.strip() for feature in self.application.settings.retrieve('image_parameter_features', None).split(';')}
        mapping_str = self.application.settings.retrieve('image_parameter_visualization', '')

        # Generate lexical feature visualizations

        if mapping_str:
            self.parse_feature_visualizations(mapping_str)

        self.bind('<<SaveAsStructure>>', self.save_as)
        self.bind('<<Save>>', self.save)
        self.bind('<<LoadAsStructure>>', self.load_as_structure)
        self.bind('<<FitPhraseStructure>>', self.fit_phrase_structure)
        self.bind('<<ResetScaling>>', self.reset_scaling)
        self.bind('<<LF>>', self.LF)
        self.bind('<<PF>>', self.PF)
        self.bind('<<NextImage>>', self.next_image)
        self.bind('<<PreviousImage>>', self.previous_image)
        self.bind('<<FirstImage>>', self.first_image)
        self.bind('<<NextLFImage>>', self.nextLFimage)
        self.bind('<<CaptureImage>>', self.save_image)
        self.bind('<<Inspect>>', self.inspect)
        self.bind('<<CompressNode>>', self.compress_node)
        self.bind('<<CompressNodeIntoHead>>', self.compress_node_into_head)
        self.bind('<<DecompressNode>>', self.decompress_node)
        self.bind('<<SqueezeNode>>', self.squeeze_node)
        self.bind('<<WidenNode>>', self.widen_node)
        self.bind('<<MakeSymmetric>>', self.make_symmetric)
        self.bind('<<MoveUp>>', self.move_up)
        self.bind('<<MoveDown>>', self.move_down)
        self.bind('<<MoveLeft>>', self.move_left)
        self.bind('<<MoveRight>>', self.move_right)
        self.bind('<<CutRightConstituent>>', self.cut_right_constituent)
        self.bind('<<CutLeftConstituent>>', self.cut_left_constituent)
        self.bind('<<AddCircleLeftConstituent>>', self.add_circle_left_constituent)
        self.bind('<<AddCircleRightConstituent>>', self.add_circle_right_constituent)
        self.bind('<<DeleteSpecialMarkings>>', self.delete_special_markings)
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
        self.bind('<<HighlightNode>>', self.highlight)
        self.bind('<<CreateArc>>', self.create_arc)
        self.bind('<<DeleteDependencies>>', self.delete_dependencies)
        self.bind('<<DeleteAllDependencies>>', self.delete_all_dependencies)
        self.bind('<<CreateForwardArrow>>', self.create_forward_arrow)
        self.bind('<<CreateBackwardArrow>>', self.create_backward_arrow)
        self.bind('<<CreateBidirectionalArrow>>', self.create_bidirectional_arrow)
        self.bind('<<CreateArrow>>', self.create_arrow)
        self.bind('<<CustomDependency>>', self.custom_dependency)
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
        self.bind('<<ShrinkAllDPs>>', self.shrink_all_DPs)
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
        self.bind('<<ShowHeadsAll>>', self.covert_heads_enable)
        self.bind('<<ShowHeadsNoCopies>>', self.covert_heads_disable)
        self.bind('<<EnableHeadChains>>', self.enable_head_chains)
        self.bind('<<DisableHeadChains>>', self.disable_head_chains)
        self.bind('<<ModifyDependency>>', self.modify_dependency)
        self.bind('<<ShowFeatures>>', self.show_features)
        self.bind('<<CanvasLayoutControlEnable>>', self.canvas_layout_control_enable)
        self.bind('<<CanvasLayoutControlDisable>>', self.canvas_layout_control_disable)
        self.bind('<<RecalculateLayout>>', self.recalculate_layout)
        self.bind('<MouseWheel>', self.zoomer)
        self.bind('<Control-s>', self.save)
        self.bind('<Key-w>', self.widen_node)
        self.bind('<Key-s>', self.squeeze_node)
        self.bind('<Key-c>', self.create_forward_arrow)
        self.bind('<Key-l>', self.use_custom_label)
        self.bind('<Control-l>', self.change_original_label)
        self.bind('<Key-e>', self.expand_phrase_structure)
        self.bind('<Key-i>', self.inspect)

        # Show phrase structure image

        self.initialize_and_show_image()

    # ----------------------------------------------------------------------------------------------
    # Image drawing functions

    def create_ribbon_buttons(self):
        pad = 2
        column = 0
        self.button_img1 = tk.PhotoImage(file='./lpparse/image resources/first_arrow.png').subsample(2, 2)
        self.create_button(self.button_img1, self.first_image, self.ribbon, pad, column)
        column += 1
        self.button_img2 = tk.PhotoImage(file='./lpparse/image resources/left_arrow.png').subsample(2, 2)
        self.create_button(self.button_img2, self.previous_image, self.ribbon, pad, column)
        column += 1
        self.button_img3 = tk.PhotoImage(file='./lpparse/image resources/right_arrow.png').subsample(2, 2)
        self.create_button(self.button_img3, self.next_image, self.ribbon, pad, column)
        column += 1
        self.button_img4 = tk.PhotoImage(file='./lpparse/image resources/compress.png').subsample(2, 2)
        self.create_button(self.button_img4, self.compress_node, self.ribbon, pad, column)
        column += 1
        self.button_img5 = tk.PhotoImage(file='./lpparse/image resources/phonology.png').subsample(2, 2)
        self.create_button(self.button_img5, self.custom_phonology, self.ribbon, pad, column)
        column += 1
        self.button_img6 = tk.PhotoImage(file='./lpparse/image resources/gloss.png').subsample(2, 2)
        self.create_button(self.button_img6, self.custom_gloss, self.ribbon, pad, column)
        column += 1
        self.button_img12 = tk.PhotoImage(file='./lpparse/image resources/custom_feature.png').subsample(2, 2)
        self.create_button(self.button_img12, self.custom_features, self.ribbon, pad, column)
        column += 1
        self.button_img7 = tk.PhotoImage(file='./lpparse/image resources/no_info.png').subsample(2, 2)
        self.create_button(self.button_img7, self.only_label, self.ribbon, pad, column)
        column += 1
        self.button_img8 = tk.PhotoImage(file='./lpparse/image resources/expand.png').subsample(2, 2)
        self.create_button(self.button_img8, self.expand_phrase_structure, self.ribbon, pad, column)
        column += 1
        self.button_img13 = tk.PhotoImage(file='./lpparse/image resources/DP.png').subsample(2, 2)
        self.create_button(self.button_img13, self.shrink_into_DP, self.ribbon, pad, column)
        column += 1
        self.button_img9 = tk.PhotoImage(file='./lpparse/image resources/custom_label.png').subsample(2, 2)
        self.create_button(self.button_img9, self.use_custom_label, self.ribbon, pad, column)
        column += 1
        self.button_img10 = tk.PhotoImage(file='./lpparse/image resources/widen.png').subsample(2, 2)
        self.create_button(self.button_img10, self.widen_node, self.ribbon, pad, column)
        column += 1
        self.button_img11 = tk.PhotoImage(file='./lpparse/image resources/squeeze.png').subsample(2, 2)
        self.create_button(self.button_img11, self.squeeze_node, self.ribbon, pad,column)

    def create_button(self, image, command, ribbon, pad, column):
        tk.Button(ribbon, command=command,
                  compound=tk.LEFT,
                  image=image,
                  font=('Calibri', 20),
                  bg='white',
                  fg='black').grid(row=0, column=column, sticky=tk.E, padx=pad, pady=pad, ipadx=pad, ipady=pad)

    def initialize_and_show_image(self):
        """
        Initializes settings and canvas and selects the phrase structure to be imagined on the basis
        of whether we want to edit single image (loaded from file), examine whole derivation (output from
        the model) or do nothing (image provided later). This function is also called if the user changed settings.
        """
        self.canvas.delete('all')
        if self.speaker_model:

            # Derivation (sequence of phrase structures, whole output from the model)

            self.draw_phrase_structure_from_derivation(title='Accepted LF-interface')
            if self.application.settings.retrieve('image_parameter_shrink_all_DPs', False):
                self.shrink_all_DPs()
        elif self.root_gps:

            # Single GPS (usually loaded from separate file)

            self.canvas.title = self.image_title
            self.canvas.derivational_index = 0
        else:
            pass    # Canvas is prepared but there will be no image
        self.update_contents()

    def initialize_and_draw_phrase_structure(self, X):
        """Deletes content from the canvas and draws X on it"""
        self.canvas.delete('all')
        self.inventory['dependencies'] = []
        self.root_gps = GPhraseStructure(X.top().copy())
        self.root_gps.initialize_logical_space()
        self.root_gps.remove_overlap()
        spx, spy = self.determine_position_of_highest_node(self.root_gps)
        self.canvas.draw_to_canvas(self.root_gps, spx, spy)

    def draw_phrase_structure_from_derivation(self, **kwargs):
        """Retrieves step from the derivation and calls the drawing function to present it on canvas"""
        start_index = kwargs.get('start', 0)
        if start_index > len(self.speaker_model.results.recorded_steps):
            start_index = 0
        if 'step' in kwargs:
            self.canvas.derivational_index, X, self.canvas.title = self.get_ps_from_speaker_model(self.speaker_model, kwargs['step'])
        if 'title' in kwargs:
            for step, item in enumerate(self.speaker_model.results.recorded_steps):
                if item[2] == kwargs['title'] and step > start_index:
                    self.canvas.derivational_index, X, self.canvas.title = self.get_ps_from_speaker_model(self.speaker_model, step)
                    break
            else:
                return
        else:
            self.canvas.derivational_index, X, self.canvas.title = self.get_ps_from_speaker_model(self.speaker_model, self.index_of_analysis_shown)
        self.canvas.delete('all')
        self.index_of_analysis_shown = self.canvas.derivational_index
        self.initialize_and_draw_phrase_structure(X)

    def get_ps_from_speaker_model(self, speaker_model, index):
        """Returns the phrase structure object to be drawn, None otherwise"""
        if index < len(speaker_model.results.recorded_steps):
            return speaker_model.results.recorded_step(index)

    def draw_and_save_phrase_structure_tree_as_postscript(self, X, filename):
        self.canvas.delete('all')
        self.canvas.title = ''
        self.canvas.derivational_index = 0
        self.fit_into_screen_and_show()
        self.update()
        self.save_image_as_postscript(filename)

    def fit_into_screen_and_show(self, margins=0):
        """
        Collects all elements on the canvas and optimizes its size. Size optimization uses the
        width settings unless the image is larger.
        """
        self.lift()
        x1, y1, x2, y2 = self.canvas.bbox('all')
        self.update_contents(False, margins-x1, margins-y1)
        if x2 - x1 > self.application.settings.retrieve('image_parameter_canvas_width'):
            width = x2 - x1
        else:
            width = self.application.settings.retrieve('image_parameter_canvas_width')    # This matches with A4
        height = y2 - y1 + margins * 2
        self.canvas.configure(width=width, height=height, background='white')

    def save_image_as_postscript(self, filename=''):
        self.canvas.postscript(file=filename + '.eps', colormode='color')

    def implement_chains(self, gX):

        # head chains

        if self.application.settings.retrieve('image_parameter_head_chains', True):
            if gX.zero_level() and gX.affix() and gX.affix().copied and not self.dependency_exists(gX):
                self.inventory['dependencies'].append(Dependency(source=gX, target=gX.top().find_node_with_identity(gX.affix().identity, gX), smooth=True))

        # phrasal chains

        if self.application.settings.retrieve('image_parameter_phrasal_chains', True):
            if gX.complex() and gX.copied and gX != gX.top() and not self.dependency_exists(gX):
                self.inventory['dependencies'].append(Dependency(source=gX, target=gX.top().find_node_with_identity(gX.identity, gX), smooth=False))
        if gX.complex() and not gX.compressed:
            self.implement_chains(gX.L())
            self.implement_chains(gX.R())

    def dependency_exists(self, gX):
        for dep in self.inventory['dependencies']:
            if dep.source_gps == gX:
                return True

    def zoomer(self, event):
        if event.delta > 0:
            self.canvas.scaling_factor += 0.1
        elif event.delta < 0 and self.canvas.scaling_factor > 0.5:
            self.canvas.scaling_factor -= 0.1
        self.update_contents(False)

    def reset_scaling(self, event):
        self.canvas.scaling_factor = 1
        self.update_contents(False)

    # ---------------------------------------------------------------------------------
    # Menu actions

    def inspect(self, *_):
        """
        Shows information about a selected constituent in a separate window.
        The window will remain until the user closes it or clicks somewhere in the screen
        """
        if self.canvas.selected_objects:
            obj = self.canvas.selected_objects[0]
            self.inspect_window = InspectWindow(self, obj)
            self.inspect_window.show()

    def recalculate_layout(self, *_):
        self.update_contents(True)

    def canvas_layout_control_enable(self, *_):
        self.application.settings.set('image_parameter_remove_overlap', True)

    def canvas_layout_control_disable(self, *_):
        self.application.settings.set('image_parameter_remove_overlap', False)

    def squeeze_node(self, *_):
        for gps in self.canvas.selected_objects:
            if gps.complex():
                gps.L().move_x(0.5)
                gps.R().move_x(-0.5)
        self.canvas.redraw(self.root_gps)

    def widen_node(self, *_):
        for gps in self.canvas.selected_objects:
            if gps.complex():
                gps.L().move_x(-0.5)
                gps.R().move_x(+0.5)
        self.canvas.redraw(self.root_gps)

    def make_symmetric(self, *_):
        for gps in self.canvas.selected_objects:
            if gps.complex():
                l = gps.x - gps.L().x
                r = gps.R().x - gps.x
                if l < r:
                    gps.R().move_x(-(r - l))
                else:
                    gps.L().move_x(l - r)
        self.canvas.redraw(self.root_gps)

    def fit_phrase_structure(self, *_):
        self.fit_into_screen_and_show(self.application.settings.retrieve('image_parameter_fit_margins'))

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

    def shrink_all_DPs(self, *_):
        def shrink_all_DPs_(gps):
            if {'D', 'φ'} & gps.head().core.features():
                gps.compressed_into_head = True
                gps.custom_phonology = gps.R().get_phonological_string()
            else:
                if gps.L():
                    shrink_all_DPs_(gps.L())
                if gps.R():
                    shrink_all_DPs_(gps.R())
        shrink_all_DPs_(self.root_gps)
        self.update_contents(True)

    def compress_all_DPs(self, *_):
        def compress_all_DPs_(gps):
            if {'D', 'φ'} & gps.head().core.features():
                gps.compressed = True
            else:
                if gps.L():
                    compress_all_DPs_(gps.L())
                if gps.R():
                    compress_all_DPs_(gps.R())
        compress_all_DPs_(self.root_gps)
        self.update_contents(False)

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
                if gps.L():
                    delete_all_custom_fields_(gps.L())
                if gps.R():
                    delete_all_custom_fields_(gps.R())
        delete_all_custom_fields_(self.root_gps)
        self.update_contents()

    def new_features(self, *_):
        for gps in self.selected_objects_into_gps_list():
            gps.core.add_features(set(simpledialog.askstring(title='Linguistic features', prompt='New linguistic features', parent=self).split(';')))
            self.label_stack_update(gps)
            self.update_contents()

    def change_original_label(self, *_):
        for gps in self.selected_objects_into_gps_list():
            old_label = gps.label()
            gps.core.set_features({f for f in gps.core.features() if not f.startswith('PF:') and not f.startswith('LF:') and f != old_label})
            new_label = simpledialog.askstring(title='Change the original label', prompt='New label', parent=self)
            gps.core.add_features({new_label})
            if new_label not in PhraseStructure.major_cats:
                PhraseStructure.major_cats.insert(0, new_label)
            self.label_stack_update(gps)
            self.update_contents()

    def add_T(self, *_):
        for gps in self.selected_objects_into_gps_list():
            Y = gps.M()
            right = gps.is_R()
            T = GPhraseStructure(PhraseStructure(features={'T'}))
            Host = GPhraseStructure(PhraseStructure(), T, gps)
            if Y:
                if right:
                    Y.const = [Y.L(), Host]
                else:
                    Y.const = [Host, Y.R()]
                Host.mother_ = Y
            else:
                self.root_gps = Host
            self.update_contents()

    def add_V(self, *_):
        for gps in self.selected_objects_into_gps_list():
            Y = gps.M()
            right = gps.is_R()
            V = GPhraseStructure(PhraseStructure(features={'V'}))
            Host = GPhraseStructure(PhraseStructure(), V, gps)
            if Y:
                if right:
                    Y.const = [Y.L(), Host]
                else:
                    Y.const = [Host, Y.R()]
                Host.mother_ = Y
            else:
                self.root_gps = Host
            self.update_contents()

    def add_C(self, *_):
        for gps in self.selected_objects_into_gps_list():
            Y = gps.M()
            right = gps.is_R()
            C = GPhraseStructure(PhraseStructure(features={'C'}))
            Host = GPhraseStructure(PhraseStructure(), C, gps)
            if Y:
                if right:
                    Y.const = [Y.L(), Host]
                else:
                    Y.const = [Host, Y.R()]
                Host.mother_ = Y
            else:
                self.root_gps = Host
            self.update_contents()

    def expand_complex_head(self, *_):
        for gps in self.selected_objects_into_gps_list():
            if not gps.complex():
                H = GPhraseStructure(PhraseStructure())
                affix_lst = gps.affixes()

                # If covert complex heads are set to be disabled, we enable them first

                if [a for a in affix_lst if a.copied]:
                    self.application.settings.store('image_parameter_covert_complex_heads', True)
                last_affix = gps.affixes()[-1]
                last_affix.const = [H]
                H.mother_ = last_affix
                H.core.add_features({'PF:X'})
                self.update_contents()

    def reverse_presentation(self, *_):
        for gps in self.selected_objects_into_gps_list():
            if gps.flip:
                gps.flip = False
            else:
                gps.flip = True
        self.update_contents(False)

    def basic_template(self, *_):
        X = GPhraseStructure(PhraseStructure(features={'X', 'PF:X'}))
        Y = GPhraseStructure(PhraseStructure(features={'Y', 'PF:Y'}))
        Z = GPhraseStructure(PhraseStructure(features={'Z', 'PF:Z'}))
        YP = GPhraseStructure(PhraseStructure(), Y, Z)
        XP = GPhraseStructure(PhraseStructure(), X, YP)
        self.root_gps = XP
        self.update_contents()

    def DP(self):
        D = GPhraseStructure(PhraseStructure(features={'D'}))
        N = GPhraseStructure(PhraseStructure(features={'N'}))
        return GPhraseStructure(PhraseStructure(), D, N)

    def vP(self):
        v = GPhraseStructure(PhraseStructure(features={'v'}))
        vP1 = GPhraseStructure(PhraseStructure(), v, self.VP())
        return GPhraseStructure(PhraseStructure(), self.DP(), vP1)

    def TP(self):
        T = GPhraseStructure(PhraseStructure(features={'T'}))
        TP = GPhraseStructure(PhraseStructure(), T, self.vP())
        return GPhraseStructure(PhraseStructure(), self.DP(), TP)

    def VP(self):
        V = GPhraseStructure(PhraseStructure(features={'V'}))
        return GPhraseStructure(PhraseStructure(), V, self.DP())

    def CP(self):
        C = GPhraseStructure(PhraseStructure(features={'C'}))
        return GPhraseStructure(PhraseStructure(), C, self.TP())

    def template_VP(self, *_):
        self.root_gps = self.VP()
        self.template_cleanup()

    def template_vP(self, *_):
        self.root_gps = self.vP()
        self.template_cleanup()

    def template_TP(self, *_):
        self.root_gps = self.TP()
        self.template_cleanup()

    def template_CP(self, *_):
        self.root_gps = self.CP()
        self.template_cleanup()

    def template_cleanup(self):
        self.inventory['dependencies'] = []
        self.update_contents()

    def add_Head(self, *_):
        for gps in self.selected_objects_into_gps_list():
            Y = gps.M()
            right = gps.is_R()
            X = GPhraseStructure(PhraseStructure())
            Host = GPhraseStructure(PhraseStructure(), X, gps)
            if Y:
                if right:
                    Y.const = [Y.L(), Host]
                else:
                    Y.const = [Host, Y.R()]
                Host.mother_ = Y
            else:
                self.root_gps = Host
            self.update_contents()

    def add_XP(self, *_):
        for gps in self.selected_objects_into_gps_list():
            Z = gps.M()
            right = gps.is_R()

            # Create DP

            X = GPhraseStructure(PhraseStructure(features={'PF:X'}))
            Y = GPhraseStructure(PhraseStructure(features={'PF:Y'}))
            XP = GPhraseStructure(PhraseStructure(), X, Y)
            Host = GPhraseStructure(PhraseStructure(), XP, gps)
            if Z:
                if right:
                    Z.const = [Z.L(), Host]
                else:
                    Z.const = [Host, Z.R()]
                Host.mother_ = Z
            else:
                self.root_gps = Host
            self.update_contents()

    def add_DP(self, *_):
        for gps in self.selected_objects_into_gps_list():
            Y = gps.M()
            right = gps.is_R()

            # Create DP

            D = GPhraseStructure(PhraseStructure(features={'D'}))
            N = GPhraseStructure(PhraseStructure(features={'N'}))
            DP = GPhraseStructure(PhraseStructure(), D, N)

            Host = GPhraseStructure(PhraseStructure(), DP, gps)
            if Y:
                if right:
                    Y.const = [Y.L(), Host]
                else:
                    Y.const = [Host, Y.R()]
                Host.mother_ = Y
            else:
                self.root_gps = Host
            self.update_contents()

    def make_adjunct(self, *_):
        for gps in self.selected_objects_into_gps_list():
            self.application.settings.store('image_parameter_adjuncts', True)
            gps.adjunct = True
            self.update_contents()

    def make_regular(self, *_):
        for gps in self.selected_objects_into_gps_list():
            if gps.complex():
                gps.adjunct = False
                self.update_contents()

    def enable_phrasal_chains(self, *_):
        self.application.settings.store('image_parameter_phrasal_chains', True)
        self.update_contents()

    def disable_phrasal_chains(self, *_):
        self.application.settings.store('image_parameter_phrasal_chains', False)
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

    def cut_right_constituent(self, *_):
        for gps in self.selected_objects_into_gps_list():
            gps.special_right_constituent_marking.append('cut')
        self.update_contents(False)

    def cut_left_constituent(self, *_):
        for gps in self.selected_objects_into_gps_list():
            gps.special_left_constituent_marking.append('cut')
        self.update_contents(False)

    def add_circle_left_constituent(self, *_):
        for gps in self.selected_objects_into_gps_list():
            gps.special_left_constituent_marking.append('ball')
        self.update_contents(False)

    def add_circle_right_constituent(self, *_):
        for gps in self.selected_objects_into_gps_list():
            gps.special_right_constituent_marking.append('ball')
        self.update_contents(False)

    def delete_special_markings(self, *_):
        for gps in self.selected_objects_into_gps_list():
            gps.special_left_constituent_marking = []
            gps.special_right_constituent_marking = []
            gps.highlight = False
        self.update_contents(False)

    def save_as(self, *_):
        filename = filedialog.asksaveasfilename() + '.gps'
        self.stored_filename = filename
        with open(filename, 'wb') as output_file:
            pickle.dump(self.root_gps, output_file)

    def save(self, *_):
        if self.stored_filename:
            with open(self.stored_filename, 'wb') as output_file:
                pickle.dump(self.root_gps, output_file)
                print(f'Phrase structure file {self.stored_filename} saved.')
        else:
            self.save_as()

    def load_as_structure(self, *_):
        filename = filedialog.askopenfilename()
        with open(filename, 'rb') as input_file:
            self.root_gps = pickle.load(input_file)
            self.stored_filename = filename
            self.clear_inventory()
            self.update_contents()

    def clear_inventory(self):
        self.inventory = {'dependencies': []}

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
                self.canvas.selected_objects = [Y]
                self.update_contents()

    def shrink_phrase_structure(self, *_):
        for gps in self.selected_objects_into_gps_list():
            gps.const = []
            gps.compressed = False
        self.update_contents()

    def shrink_into_DP(self, *_):
        for gps in self.selected_objects_into_gps_list():
            gps.head().core.set_features({f for f in gps.head().core.features() if f not in PhraseStructure.major_cats} | {'D', 'φ'})
            gps.compressed_into_head = True
            gps.compressed = False
            self.label_stack_update(gps)
        self.update_contents()

    def delete_phrase_structure(self, *_):
        for gps in self.selected_objects_into_gps_list():
            if gps.M():
                if gps.is_L():
                    preserved_sister = gps.M().R()
                else:
                    preserved_sister = gps.M().L()

                # Delete X and its mother, move the sister upwards

                if gps.M().M():
                    grandmother = gps.M().M()
                    if gps.M().is_R():
                        grandmother.const = [grandmother.L(), preserved_sister]
                    else:
                        grandmother.const = [preserved_sister, grandmother.R()]
                    preserved_sister.mother_ = grandmother

                # We preserve only the sister

                else:
                    preserved_sister.mother_ = None
                    self.root_gps = preserved_sister
        self.update_contents()

    def update_contents(self, recalculate=True, x_offset=0, y_offset=0):
        if recalculate:
            self.root_gps.initialize_logical_space()
            self.implement_chains(self.root_gps)
        self.root_gps.remove_overlap()
        self.recalculate_labels(self.root_gps)
        self.remove_dependency_overlaps()
        self.canvas.redraw(self.root_gps, False, x_offset, y_offset)
        self.canvas.focus_set()

    def recalculate_labels(self, gps):
        gps.generate_label_stack()
        if gps.complex():
            self.recalculate_labels(gps.L())
            self.recalculate_labels(gps.R())

    def reverse_phrase_structure(self, *_):
        for gps in self.selected_objects_into_gps_list():
            if gps.complex():
                gps.const.reverse()
        self.update_contents(False)

    def create_arc(self, *_):
        self.create_dependency(smooth='raw', arrowtype='none', label='')

    def deselect_all(self):
        self.canvas.selected_objects = []
        self.update_contents(False)

    def delete_dependencies(self, *_):
        if self.canvas.selected_dependency:
            self.inventory['dependencies'].remove(self.canvas.selected_dependency)
            self.update_contents(False)

    def delete_all_dependencies(self, *_):
        self.inventory['dependencies'] = []
        self.update_contents(False)

    def create_forward_arrow(self, *_):
        self.create_dependency(arrowtype='last', smooth='', label='')

    def create_backward_arrow(self, *_):
        self.create_dependency(arrowtype='first', smooth='', label='')

    def create_bidirectional_arrow(self, *_):
        self.create_dependency(arrowtype='both', smooth='', label='')

    def create_arrow(self, *_):
        self.create_dependency(arrowtype='none', smooth='', label='')

    def create_dependency(self, **kwargs):
        if len(self.canvas.selected_objects) > 1:
            for i, gps in enumerate(self.canvas.selected_objects):
                if i < len(self.canvas.selected_objects) - 1:
                    dep = Dependency(source=gps, target=self.canvas.selected_objects[i + 1], arrow_type=kwargs['arrowtype'], smooth=kwargs['smooth'], label=kwargs['label'])
                    self.inventory['dependencies'].append(dep)
                    self.canvas.selected_dependency = dep
            self.canvas.selected_objects = []
            self.update_contents(False)

    def modify_dependency(self, *_):
         if self.canvas.selected_dependency:
            old = self.canvas.selected_dependency
            new = DependencyDialog(self.canvas.selected_dependency).show()
            self.inventory['dependencies'].remove(old)
            self.inventory['dependencies'].append(new)
            self.canvas.selected_dependency = new
            self.update_contents(False)

    def custom_dependency(self, *_):
        if len(self.canvas.selected_objects) > 1:
            dep = DependencyDialog().show()
            for i, gps in enumerate(self.canvas.selected_objects):
                if i < len(self.canvas.selected_objects) - 1:
                    dep.source_gps = gps
                    dep.target_gps = self.canvas.selected_objects[i + 1]
                    self.inventory['dependencies'].append(dep)
            self.canvas.selected_objects = []
            self.update_contents(False)

    def remove_dependency_overlaps(self):
        def source_dependencies_for_node(X):
            return [dep for dep in self.inventory['dependencies'] if dep.source_gps == X]

        def target_dependencies_for_node(X):
            return [dep for dep in self.inventory['dependencies'] if dep.target_gps == X]

        for dep in self.inventory['dependencies']:
            sources = source_dependencies_for_node(dep.source_gps)
            targets = target_dependencies_for_node(dep.source_gps)
            if len(sources) > 0 and len(targets) > 0:
                if dep.source_gps.X < dep.target_gps.X:
                    dep.source_X_offset = 10
                    for dep2 in targets:
                        dep2.target_X_offset = -10
                else:
                    dep.source_X_offset = -10
                    for dep2 in targets:
                        dep2.target_X_offset = +10

    def custom_text(self, *_):
        if self.canvas.selected_objects:
            text = simpledialog.askstring(title='Custom text', prompt='New text', parent=self)
            for gps in self.selected_objects_into_gps_list():
                gps.custom_text = text
                self.label_stack_update(gps)
        self.update_contents(False)

    def empty_text(self, *_):
        for gps in self.selected_objects_into_gps_list():
            gps.custom_text = None
            self.label_stack_update(gps)
        self.update_contents(False)

    def highlight(self, *_):
        for gps in self.selected_objects_into_gps_list():
            gps.highlight = True
        self.update_contents(False)

    def custom_features(self, *_):
        if self.canvas.selected_objects:
            features = simpledialog.askstring(title='Custom features', prompt='New features', parent=self).split(';')
            for gps in self.selected_objects_into_gps_list():
                gps.custom_features = features
                self.label_stack_update(gps)
        self.update_contents(False)

    def default_features(self, *_):
        for gps in self.selected_objects_into_gps_list():
            gps.custom_features = None
            self.label_stack_update(gps)
        self.update_contents(False)

    def empty_features(self, *_):
        for gps in self.selected_objects_into_gps_list():
            gps.custom_features = ['$n/a$']
            self.label_stack_update(gps)
        self.update_contents(False)

    def custom_gloss(self, *_):
        if self.canvas.selected_objects:
            gloss = simpledialog.askstring(title='Custom gloss', prompt='New gloss', parent=self)
            for gps in self.selected_objects_into_gps_list():
                gps.custom_gloss = gloss
                self.label_stack_update(gps)
        self.update_contents(False)

    def default_gloss(self, *_):
        for gps in self.selected_objects_into_gps_list():
            gps.custom_gloss = None
            self.label_stack_update(gps)
        self.update_contents(False)

    def empty_gloss(self, *_):
        for gps in self.selected_objects_into_gps_list():
            gps.custom_gloss = '$n/a$'
            self.label_stack_update(gps)
        self.update_contents(False)

    def custom_phonology(self, *_):
        if self.canvas.selected_objects:
            phon = simpledialog.askstring(title='Custom text', prompt='New text', parent=self)
            for gps in self.selected_objects_into_gps_list():
                gps.custom_phonology = phon
                self.label_stack_update(gps)
                gps.ellipsis = False
        self.update_contents(False)

    def mark_ellipsis(self, *_):
        for gps in self.selected_objects_into_gps_list():
            gps.ellipsis=True
            self.label_stack_update(gps)
        self.update_contents(False)

    def default_phonology(self, *_):
        for gps in self.selected_objects_into_gps_list():
            gps.custom_phonology = None
            self.label_stack_update(gps)
            gps.ellipsis = False
        self.update_contents(False)

    def empty_phonology(self, *_):
        for gps in self.selected_objects_into_gps_list():
            gps.custom_phonology = '$n/a$'
            self.label_stack_update(gps)
            gps.ellipsis = False
        self.update_contents(False)

    def default_label(self, *_):
        for gps in self.selected_objects_into_gps_list():
            gps.custom_label = None
            gps.subscript = None
            gps.superscript = None
            self.label_stack_update(gps)
        self.update_contents(False)

    def use_custom_label(self, *_):
        for gps in self.selected_objects_into_gps_list():
            gps.custom_label = simpledialog.askstring(title='Custom label', prompt='New label', parent=self)
            gps.subscript = None
            gps.superscript = None
            self.label_stack_update(gps)
        self.update_contents(False)

    def empty_label(self, *_):
        for gps in self.selected_objects_into_gps_list():
            gps.custom_label = '$n/a$'
            gps.subscript = None
            gps.superscript = None
            self.label_stack_update(gps)
        self.update_contents(False)

    def selected_objects_into_gps_list(self):
        return self.canvas.selected_objects

    def label_stack_update(self, gps):
        gps.generate_label_stack()
        self.canvas.redraw(self.root_gps)

    def compress_node(self, *_):
        for gps in self.canvas.selected_objects:
            # Compress the object
            if gps.complex():
                gps.compressed = True
        self.update_contents(True)

    def compress_node_into_head(self, *_):
        for gps in self.canvas.selected_objects:
            # Compress the object
            if gps.complex():
                gps.compressed_into_head = True
        self.update_contents(True)

    def decompress_node(self, *_):
        for gps in self.selected_objects_into_gps_list():
            gps.compressed = False
            gps.compressed_into_head = False
        self.update_contents(True)

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
                self.draw_phrase_structure_from_derivation(step=self.index_of_analysis_shown + 1)

    def previous_image(self, *_):
        if self.speaker_model.results.recorded_steps:
            if self.index_of_analysis_shown > 0:
                self.index_of_analysis_shown -= 1
            self.draw_phrase_structure_from_derivation(step=self.index_of_analysis_shown - 1)

    def first_image(self, *_):
        if self.speaker_model.results.recorded_steps:
            self.draw_phrase_structure_from_derivation(step=0)

    def LF(self, *_):
        self.draw_phrase_structure_from_derivation(title='Accepted LF-interface', start=0)

    def PF(self, *_):
        self.draw_phrase_structure_from_derivation(title='PF-interface')

    def nextLFimage(self, *_):
        self.draw_phrase_structure_from_derivation(title='Accepted LF-interface', start=self.index_of_analysis_shown + 1)

    def determine_position_of_highest_node(self, gps):
        """Determines the canvas size on the basis of the phrase structure object"""
        left_x, right_x, depth = gps.find_boundaries(0, 0, 0)
        return abs(left_x) * self.application.settings.retrieve('image_parameter_grid') + self.application.settings.retrieve('image_parameter_margins'), self.application.settings.retrieve('image_parameter_y_grid') / 4

    # ------------------------------------------------------------------------------------------
    # Change of settings (from menu)

    def complex_head_style_stack(self, *_):
        self.application.settings.set('image_parameter_phrasal_complex_heads', False)
        GPhraseStructure.image_parameter_phrasal_complex_heads = False
        self.root_gps = self.original_gps
        self.update_settings()

    def complex_head_style_standard(self, *_):
        self.application.settings.set('image_parameter_phrasal_complex_heads', True)
        GPhraseStructure.image_parameter_phrasal_complex_heads = True
        self.update_settings()

    def covert_heads_enable(self, *_):
        self.application.settings.set('image_parameter_covert_complex_heads', True)
        GPhraseStructure.image_parameter_covert_complex_heads = True
        self.update_settings()

    def covert_heads_disable(self, *_):
        self.application.settings.set('image_parameter_covert_complex_heads', False)
        GPhraseStructure.image_parameter_covert_complex_heads = False
        self.update_settings()

    def enable_head_chains(self, *_):
        self.application.settings.set('image_parameter_head_chains', True)
        self.update_settings()

    def disable_head_chains(self, *_):
        self.application.settings.set('image_parameter_head_chains', False)
        self.update_settings()

    def show_features(self, *_):
        features = simpledialog.askstring(title='Show features', prompt='Features', parent=self)
        self.application.settings.set('image_parameter_features', features)
        GPhraseStructure.draw_features = {f.strip() for f in features.split(';')}
        self.update_settings()

    def update_settings(self):
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
        file_menu.add_command(label='Save', command=self._event('<<Save>>'))
        file_menu.add_command(label='Save As...', command=self._event('<<SaveAsStructure>>'))
        file_menu.add_command(label='Save Postscript Image...', command=self._event('<<CaptureImage>>'))
        self.add_cascade(label='File', underline=0, menu=file_menu)

        image_properties_menu = tk.Menu(self, tearoff=False, font=menu_font)
        image_properties_menu.add_command(label='Fit Phrase Structure', command=self._event('<<FitPhraseStructure>>'))
        image_properties_menu.add_command(label='Recalculate layout', command=self._event('<<RecalculateLayout>>'))
        image_properties_menu.add_command(label='Reset scaling', command=self._event('<<ResetScaling>>'))
        self.add_cascade(label='Image', menu=image_properties_menu)

        # Select image menu
        select_image = tk.Menu(self, tearoff=False, font=menu_font)
        select_image.add_command(label='PF-interface', command=self._event('<<PF>>'))
        select_image.add_command(label='First LF-interface', command=self._event('<<LF>>'))
        select_image.add_command(label='Next LF-interface', command=self._event('<<NextLFImage>>'))
        select_image.add_command(label='Next image', command=self._event('<<NextImage>>'))
        select_image.add_command(label='Previous image', command=self._event('<<PreviousImage>>'))
        select_image.add_command(label='First image', command=self._event('<<FirstImage>>'))

        self.add_cascade(label='Source image', menu=select_image)

        # Node menu
        node = tk.Menu(self, tearoff=False, font=menu_font)
        node.add_command(label='Inspect', command=self._event('<<Inspect>>'))
        node.add_separator()
        node.add_command(label='Highlight', command=self._event('<<HighlightNode>>'))
        node.add_command(label='Compress (Triangle)', command=self._event('<<CompressNode>>'))
        node.add_command(label='Compress (Head)', command=self._event('<<CompressNodeIntoHead>>'))
        node.add_command(label='Decompress', command=self._event('<<DecompressNode>>'))
        node.add_separator()
        if True:
            submenu_Shape = tk.Menu(node, tearoff=0, font=menu_font)
            submenu_Shape.add_command(label='Squeeze', underline=0, command=self._event('<<SqueezeNode>>'))
            submenu_Shape.add_command(label='Widen', underline=0, command=self._event('<<WidenNode>>'))
            submenu_Shape.add_command(label='Make Symmetric', underline=0, command=self._event('<<MakeSymmetric>>'))
        node.add_cascade(label='Constituent Shape...', underline=0, menu=submenu_Shape)
        if True:
            submenu_Special = tk.Menu(node, tearoff=0, font=menu_font)
            if True:
                subsubmenu_Const = tk.Menu(submenu_Special, tearoff=0, font=menu_font)
                subsubmenu_Const.add_command(label='Left', command=self._event('<<CutLeftConstituent>>'))
                subsubmenu_Const.add_command(label='Right', command=self._event('<<CutRightConstituent>>'))
            submenu_Special.add_cascade(label='Cut...', menu=subsubmenu_Const)
            if True:
                subsubmenu_Const2 = tk.Menu(submenu_Special, tearoff=0, font=menu_font)
                subsubmenu_Const2.add_command(label='Left', command=self._event('<<AddCircleLeftConstituent>>'))
                subsubmenu_Const2.add_command(label='Right', command=self._event('<<AddCircleRightConstituent>>'))
            submenu_Special.add_cascade(label='Circle...', menu=subsubmenu_Const2)
        node.add_cascade(label='Special Constituent...', menu=submenu_Special)
        node.add_cascade(label='Delete All Specials', command=self._event('<<DeleteSpecialMarkings>>'))
        node.add_separator()
        node.add_separator()
        if True:
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

        dep = tk.Menu(self, tearoff=False, font=menu_font)
        dep.add_command(label='Forward Chain', command=self._event('<<CreateForwardArrow>>'))
        dep.add_command(label='Backward Chain', command=self._event('<<CreateBackwardArrow>>'))
        dep.add_command(label='Bidirectional Chain', command=self._event('<<CreateBidirectionalArrow>>'))
        dep.add_command(label='Directionless Chain', command=self._event('<<CreateArrow>>'))
        dep.add_command(label='Curved Chain', command=self._event('<<CreateArc>>'))
        dep.add_separator()
        dep.add_command(label='Modify...', command=self._event('<<ModifyDependency>>'))
        dep.add_command(label='Custom Dependency...', command=self._event('<<CustomDependency>>'))
        dep.add_separator()
        dep.add_command(label='Delete', command=self._event('<<DeleteDependencies>>'))
        dep.add_command(label='Delete All', command=self._event('<<DeleteAllDependencies>>'))
        self.add_cascade(label='Dependency', menu=dep)

        ps = tk.Menu(self, tearoff=False, font=menu_font)
        # Submenu Add...
        submenu_ps = tk.Menu(ps, tearoff=False, font=menu_font)
        submenu_ps.add_command(label='XP', command=self._event('<<AddXP>>'))
        submenu_ps.add_command(label='Head', command=self._event('<<AddHead>>'))
        submenu_ps.add_command(label='DP', command=self._event('<<AddDP>>'))
        submenu_ps.add_command(label='C', command=self._event('<<AddC>>'))
        submenu_ps.add_command(label='T', command=self._event('<<AddT>>'))
        submenu_ps.add_command(label='V', command=self._event('<<AddV>>'))
        ps.add_cascade(label='Add Left...', menu=submenu_ps)

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
        ps.add_command(label='Shrink all DPs', command=self._event('<<ShrinkAllDPs>>'))
        ps.add_separator()
        ps.add_command(label='Move Up', command=self._event('<<MoveUp>>'))
        ps.add_command(label='Move Down', command=self._event('<<MoveDown>>'))
        ps.add_command(label='Move Left', command=self._event('<<MoveLeft>>'))
        ps.add_command(label='Move Right', command=self._event('<<MoveRight>>'))
        self.add_cascade(label='Phrase Structure', menu=ps)

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

        submenu_remove_overlap = tk.Menu(settings_menu, tearoff=False, font=menu_font)
        submenu_remove_overlap.add_command(label='Enable', command=self._event('<<CanvasLayoutControlEnable>>'))
        submenu_remove_overlap.add_command(label='Disable', command=self._event('<<CanvasLayoutControlDisable>>'))
        settings_menu.add_cascade(label='Canvas Layout Control', menu=submenu_remove_overlap)
        settings_menu.add_separator()
        #Submenu for complex head style
        submenu_complex_head_style = tk.Menu(settings_menu, tearoff=False, font=menu_font)
        submenu_complex_head_style.add_command(label='Stack', command=self._event('<<ComplexHeadStyle_Stack>>'))
        submenu_complex_head_style.add_command(label='Standard', command=self._event('<<ComplexHeadStyle_Standard>>'))
        settings_menu.add_cascade(label='Complex Head Style...', menu=submenu_complex_head_style)
        # Submenu for head chain visibility
        submenu_chains_head = tk.Menu(settings_menu, tearoff=0, font=menu_font)
        submenu_chains_head.add_command(label='Enable', command=self._event('<<EnableHeadChains>>'))
        submenu_chains_head.add_command(label='Disable', command=self._event('<<DisableHeadChains>>'))
        settings_menu.add_cascade(label='Head chains...', menu=submenu_chains_head)
        # Submenu for head chain visibility 2
        submenu_covert_heads = tk.Menu(settings_menu, tearoff=0, font=menu_font)
        submenu_covert_heads.add_command(label='All', command=self._event('<<ShowHeadsAll>>'))
        submenu_covert_heads.add_command(label='No Copies', command=self._event('<<ShowHeadsNoCopies>>'))
        settings_menu.add_cascade(label='Show Heads...', menu=submenu_covert_heads)
        settings_menu.add_separator()
        settings_menu.add_command(label='Show Features...', command=self._event('<<ShowFeatures>>'))
        settings_menu.add_separator()
        # Chain visibility menu
        submenu_chains_phrasal = tk.Menu(settings_menu, tearoff=False, font=menu_font)
        submenu_chains_phrasal.add_command(label='Enable', command=self._event('<<EnablePhrasalChains>>'))
        submenu_chains_phrasal.add_command(label='Disable', command=self._event('<<DisablePhrasalChains>>'))
        settings_menu.add_cascade(label='Phrasal chains...', menu=submenu_chains_phrasal)

        self.add_cascade(label='Settings', menu=settings_menu)

# --------------------------------------------------------------------------------------------
# Definitions for linguistic objects that can appear on canvas


class Dependency:
    def __init__(self, **kwargs):
        self.source_gps = kwargs.get('source', None)
        self.target_gps = kwargs.get('target', None)
        self.arrow_type = kwargs.get('arrow_type', 'none')
        self.label = kwargs.get('label', '')
        self.smooth = kwargs.get('smooth', False)
        self.Y_offset = 0
        self.source_X_offset = 0
        self.target_X_offset = 0
        self.spx = 0
        self.spy = 0
        self.epx = 0
        self.epy = 0


class DependencyDialog(tk.Toplevel):
    """Creates a new dependency or modifies an existing one (provided as an input argument)"""
    def __init__(self, dep=None):
        super().__init__()
        self.dep = dep
        if self.dep:
            self.title(f'Dependency {dep.source_gps.label()} => {dep.target_gps.label()}')
        else:
            self.title('New Dependency')
        self.arrow_map = {'Forward': 'last', 'Backwards': 'first', 'Bidirectional': 'both', 'No direction': 'none'}
        dfont = ('Calibri', 20)

        # Frame: dependency type
        frameDependencyType = tk.LabelFrame(self, text='Dependency type', font=dfont)
        arrow_options = ['Forward', 'Backwards', 'Bidirectional', 'No direction']
        self.selDirection = tk.StringVar()
        if dep:
            for key, value in self.arrow_map.items():
                if value == dep.arrow_type:
                    self.selDirection.set(key)
        else:
            self.selDirection.set('Forward')
        for i, option in enumerate(arrow_options):
            tk.Radiobutton(frameDependencyType, padx=20, pady=20, justify='left', text=option, variable=self.selDirection, value=option, font=dfont).grid(row=0, column=i, sticky='w')
        frameLabel = tk.LabelFrame(frameDependencyType, text='Label', font=dfont)
        self.selLabel = tk.StringVar()
        if dep:
            self.selLabel.set(dep.label)
        tk.Entry(frameLabel, textvariable=self.selLabel, font=dfont).grid(row=0, column=0, sticky='nw', padx=20, pady=20)
        frameLabel.grid(row=0, column=4, sticky='ns')
        frameSmooth = tk.LabelFrame(frameDependencyType, text='Curved', font=dfont)
        self.selSmooth = tk.BooleanVar()
        if dep:
            if dep.smooth:
                self.selSmooth.set(True)
            else:
                self.selSmooth.set(False)
        tk.Checkbutton(frameSmooth, padx=10, pady=10, variable=self.selSmooth, font=dfont).grid(row=0, column=0, sticky='nw')
        frameSmooth.grid(row=0, column=5, sticky='ns')
        frameDependencyType.grid(row=1, column=0, sticky='we')
        # -----------------------------------------------------------------------

        # frame: position
        framePosition = tk.LabelFrame(self, text='Position', font=dfont, padx=20, pady=20)
        self.selSpx = tk.IntVar()
        self.selSpy = tk.IntVar()
        self.selEpx = tk.IntVar()
        self.selEpy = tk.IntVar()
        if dep:
            self.selSpx.set(dep.spx)
            self.selSpy.set(dep.spy)
            self.selEpx.set(dep.epx)
            self.selEpy.set(dep.spx)
        frameSpx = tk.LabelFrame(framePosition, text='Spx', font=dfont, padx=20, pady=20)
        tk.Entry(frameSpx, textvariable=self.selSpx, font=dfont).grid(row=0, column=0, padx=10, pady=10)
        frameSpx.grid(row=0, column=0)
        frameSpy = tk.LabelFrame(framePosition, text='Spy', font=dfont, padx=20, pady=20)
        tk.Entry(frameSpy, textvariable=self.selSpy, font=dfont).grid(row=0, column=0, padx=10, pady=10 )
        frameSpy.grid(row=0, column=1)
        frameEpx = tk.LabelFrame(framePosition, text='Epx', font=dfont, padx=20, pady=20)
        tk.Entry(frameEpx, textvariable=self.selEpx, font=dfont).grid(row=0, column=0, padx=10, pady=10)
        frameEpx.grid(row=0, column=2)
        frameEpy = tk.LabelFrame(framePosition, text='Epy', font=dfont, padx=20, pady=20)
        tk.Entry(frameEpy, textvariable=self.selEpy, font=dfont).grid(row=0, column=0, padx=10, pady=10)
        frameEpy.grid(row=0, column=3)

        frameY_offset = tk.LabelFrame(framePosition, text='Y-axis offset', font=dfont)
        self.selYoffset = tk.IntVar()
        if dep:
            self.selYoffset.set(dep.Y_offset)
        tk.Entry(frameY_offset, textvariable=self.selYoffset, font=dfont).grid(row=0, column=0, sticky='nw')
        frameY_offset.grid(row=1, column=0, sticky='NW')
        framePosition.grid(row=2, column=0, sticky='WE')

        buttonOK = tk.Button(self, text='Done', font=dfont, padx=20, pady=20, command=self.ok, bg='#CCFFCC')
        buttonOK.grid(row=3, column=0, sticky='e', ipadx=50)

    def ok(self):
        self.destroy()

    def show(self):
        self.wm_deiconify()
        self.focus_force()
        self.wait_window()
        if self.dep:
            source_gps = self.dep.source_gps
            target_gps = self.dep.target_gps
        else:
            source_gps = None
            target_gps = None
        if self.selSmooth.get():
            smooth = 'raw'
        else:
            smooth = ''
        dep = Dependency(source=source_gps, target=target_gps, arrow_type=self.arrow_map[self.selDirection.get()], label=self.selLabel.get(), smooth=smooth)
        dep.spx = self.selSpx.get()
        dep.spy = self.selSpy.get()
        dep.epx = self.selEpx.get()
        dep.epy = self.selEpy.get()
        dep.Y_offset = self.selYoffset.get()
        return dep


class DependencyDialog(tk.Toplevel):
    """Creates a new dependency or modifies an existing one (provided as an input argument)"""
    def __init__(self, dep=None):
        super().__init__()
        self.dep = dep
        if self.dep:
            self.title(f'Dependency {dep.source_gps.label()} => {dep.target_gps.label()}')
        else:
            self.title('New Dependency')
        self.arrow_map = {'Forward': 'last', 'Backwards': 'first', 'Bidirectional': 'both', 'No direction': 'none'}
        dfont = ('Calibri', 20)

        # Frame: dependency type
        frameDependencyType = tk.LabelFrame(self, text='Dependency type', font=dfont)
        arrow_options = ['Forward', 'Backwards', 'Bidirectional', 'No direction']
        self.selDirection = tk.StringVar()
        if dep:
            for key, value in self.arrow_map.items():
                if value == dep.arrow_type:
                    self.selDirection.set(key)
        else:
            self.selDirection.set('Forward')
        for i, option in enumerate(arrow_options):
            tk.Radiobutton(frameDependencyType, padx=20, pady=20, justify='left', text=option, variable=self.selDirection, value=option, font=dfont).grid(row=0, column=i, sticky='w')
        frameLabel = tk.LabelFrame(frameDependencyType, text='Label', font=dfont)
        self.selLabel = tk.StringVar()
        if dep:
            self.selLabel.set(dep.label)
        tk.Entry(frameLabel, textvariable=self.selLabel, font=dfont).grid(row=0, column=0, sticky='nw', padx=20, pady=20)
        frameLabel.grid(row=0, column=4, sticky='ns')
        frameSmooth = tk.LabelFrame(frameDependencyType, text='Curved', font=dfont)
        self.selSmooth = tk.BooleanVar()
        if dep:
            if dep.smooth:
                self.selSmooth.set(True)
            else:
                self.selSmooth.set(False)
        tk.Checkbutton(frameSmooth, padx=10, pady=10, variable=self.selSmooth, font=dfont).grid(row=0, column=0, sticky='nw')
        frameSmooth.grid(row=0, column=5, sticky='ns')
        frameDependencyType.grid(row=1, column=0, sticky='we')
        # -----------------------------------------------------------------------

        # frame: position
        framePosition = tk.LabelFrame(self, text='Position', font=dfont, padx=20, pady=20)
        self.selSpx = tk.IntVar()
        self.selSpy = tk.IntVar()
        self.selEpx = tk.IntVar()
        self.selEpy = tk.IntVar()
        if dep:
            self.selSpx.set(dep.spx)
            self.selSpy.set(dep.spy)
            self.selEpx.set(dep.epx)
            self.selEpy.set(dep.spx)
        frameSpx = tk.LabelFrame(framePosition, text='Spx', font=dfont, padx=20, pady=20)
        tk.Entry(frameSpx, textvariable=self.selSpx, font=dfont).grid(row=0, column=0, padx=10, pady=10)
        frameSpx.grid(row=0, column=0)
        frameSpy = tk.LabelFrame(framePosition, text='Spy', font=dfont, padx=20, pady=20)
        tk.Entry(frameSpy, textvariable=self.selSpy, font=dfont).grid(row=0, column=0, padx=10, pady=10 )
        frameSpy.grid(row=0, column=1)
        frameEpx = tk.LabelFrame(framePosition, text='Epx', font=dfont, padx=20, pady=20)
        tk.Entry(frameEpx, textvariable=self.selEpx, font=dfont).grid(row=0, column=0, padx=10, pady=10)
        frameEpx.grid(row=0, column=2)
        frameEpy = tk.LabelFrame(framePosition, text='Epy', font=dfont, padx=20, pady=20)
        tk.Entry(frameEpy, textvariable=self.selEpy, font=dfont).grid(row=0, column=0, padx=10, pady=10)
        frameEpy.grid(row=0, column=3)

        frameY_offset = tk.LabelFrame(framePosition, text='Y-axis offset', font=dfont)
        self.selYoffset = tk.IntVar()
        if dep:
            self.selYoffset.set(dep.Y_offset)
        tk.Entry(frameY_offset, textvariable=self.selYoffset, font=dfont).grid(row=0, column=0, sticky='nw')
        frameY_offset.grid(row=1, column=0, sticky='NW')
        framePosition.grid(row=2, column=0, sticky='WE')

        buttonOK = tk.Button(self, text='Done', font=dfont, padx=20, pady=20, command=self.ok, bg='#CCFFCC')
        buttonOK.grid(row=3, column=0, sticky='e', ipadx=50)

    def ok(self):
        self.destroy()

    def show(self):
        self.wm_deiconify()
        self.focus_force()
        self.wait_window()
        if self.dep:
            source_gps = self.dep.source_gps
            target_gps = self.dep.target_gps
        else:
            source_gps = None
            target_gps = None
        if self.selSmooth.get():
            smooth = 'raw'
        else:
            smooth = ''
        dep = Dependency(source=source_gps, target=target_gps, arrow_type=self.arrow_map[self.selDirection.get()], label=self.selLabel.get(), smooth=smooth)
        dep.spx = self.selSpx.get()
        dep.spy = self.selSpy.get()
        dep.epx = self.selEpx.get()
        dep.epy = self.selEpy.get()
        dep.Y_offset = self.selYoffset.get()
        return dep
class DependencyDialog(tk.Toplevel):
    """Creates a new dependency or modifies an existing one (provided as an input argument)"""
    def __init__(self, dep=None):
        super().__init__()
        self.dep = dep
        if self.dep:
            self.title(f'Dependency {dep.source_gps.label()} => {dep.target_gps.label()}')
        else:
            self.title('New Dependency')
        self.arrow_map = {'Forward': 'last', 'Backwards': 'first', 'Bidirectional': 'both', 'No direction': 'none'}
        dfont = ('Calibri', 20)

        # Frame: dependency type
        frameDependencyType = tk.LabelFrame(self, text='Dependency type', font=dfont)
        arrow_options = ['Forward', 'Backwards', 'Bidirectional', 'No direction']
        self.selDirection = tk.StringVar()
        if dep:
            for key, value in self.arrow_map.items():
                if value == dep.arrow_type:
                    self.selDirection.set(key)
        else:
            self.selDirection.set('Forward')
        for i, option in enumerate(arrow_options):
            tk.Radiobutton(frameDependencyType, padx=20, pady=20, justify='left', text=option, variable=self.selDirection, value=option, font=dfont).grid(row=0, column=i, sticky='w')
        frameLabel = tk.LabelFrame(frameDependencyType, text='Label', font=dfont)
        self.selLabel = tk.StringVar()
        if dep:
            self.selLabel.set(dep.label)
        tk.Entry(frameLabel, textvariable=self.selLabel, font=dfont).grid(row=0, column=0, sticky='nw', padx=20, pady=20)
        frameLabel.grid(row=0, column=4, sticky='ns')
        frameSmooth = tk.LabelFrame(frameDependencyType, text='Curved', font=dfont)
        self.selSmooth = tk.BooleanVar()
        if dep:
            if dep.smooth:
                self.selSmooth.set(True)
            else:
                self.selSmooth.set(False)
        tk.Checkbutton(frameSmooth, padx=10, pady=10, variable=self.selSmooth, font=dfont).grid(row=0, column=0, sticky='nw')
        frameSmooth.grid(row=0, column=5, sticky='ns')
        frameDependencyType.grid(row=1, column=0, sticky='we')
        # -----------------------------------------------------------------------

        # frame: position
        framePosition = tk.LabelFrame(self, text='Position', font=dfont, padx=20, pady=20)
        self.selSpx = tk.IntVar()
        self.selSpy = tk.IntVar()
        self.selEpx = tk.IntVar()
        self.selEpy = tk.IntVar()
        if dep:
            self.selSpx.set(dep.spx)
            self.selSpy.set(dep.spy)
            self.selEpx.set(dep.epx)
            self.selEpy.set(dep.spx)
        frameSpx = tk.LabelFrame(framePosition, text='Spx', font=dfont, padx=20, pady=20)
        tk.Entry(frameSpx, textvariable=self.selSpx, font=dfont).grid(row=0, column=0, padx=10, pady=10)
        frameSpx.grid(row=0, column=0)
        frameSpy = tk.LabelFrame(framePosition, text='Spy', font=dfont, padx=20, pady=20)
        tk.Entry(frameSpy, textvariable=self.selSpy, font=dfont).grid(row=0, column=0, padx=10, pady=10 )
        frameSpy.grid(row=0, column=1)
        frameEpx = tk.LabelFrame(framePosition, text='Epx', font=dfont, padx=20, pady=20)
        tk.Entry(frameEpx, textvariable=self.selEpx, font=dfont).grid(row=0, column=0, padx=10, pady=10)
        frameEpx.grid(row=0, column=2)
        frameEpy = tk.LabelFrame(framePosition, text='Epy', font=dfont, padx=20, pady=20)
        tk.Entry(frameEpy, textvariable=self.selEpy, font=dfont).grid(row=0, column=0, padx=10, pady=10)
        frameEpy.grid(row=0, column=3)

        frameY_offset = tk.LabelFrame(framePosition, text='Y-axis offset', font=dfont)
        self.selYoffset = tk.IntVar()
        if dep:
            self.selYoffset.set(dep.Y_offset)
        tk.Entry(frameY_offset, textvariable=self.selYoffset, font=dfont).grid(row=0, column=0, sticky='nw')
        frameY_offset.grid(row=1, column=0, sticky='NW')
        framePosition.grid(row=2, column=0, sticky='WE')

        buttonOK = tk.Button(self, text='Done', font=dfont, padx=20, pady=20, command=self.ok, bg='#CCFFCC')
        buttonOK.grid(row=3, column=0, sticky='e', ipadx=50)

    def ok(self):
        self.destroy()

    def show(self):
        self.wm_deiconify()
        self.focus_force()
        self.wait_window()
        if self.dep:
            source_gps = self.dep.source_gps
            target_gps = self.dep.target_gps
        else:
            source_gps = None
            target_gps = None
        if self.selSmooth.get():
            smooth = 'raw'
        else:
            smooth = ''
        dep = Dependency(source=source_gps, target=target_gps, arrow_type=self.arrow_map[self.selDirection.get()], label=self.selLabel.get(), smooth=smooth)
        dep.spx = self.selSpx.get()
        dep.spy = self.selSpy.get()
        dep.epx = self.selEpx.get()
        dep.epy = self.selEpy.get()
        dep.Y_offset = self.selYoffset.get()
        return dep
class DependencyDialog(tk.Toplevel):
    """Creates a new dependency or modifies an existing one (provided as an input argument)"""
    def __init__(self, dep=None):
        super().__init__()
        self.dep = dep
        if self.dep:
            self.title(f'Dependency {dep.source_gps.label()} => {dep.target_gps.label()}')
        else:
            self.title('New Dependency')
        self.arrow_map = {'Forward': 'last', 'Backwards': 'first', 'Bidirectional': 'both', 'No direction': 'none'}
        dfont = ('Calibri', 20)

        # Frame: dependency type
        frameDependencyType = tk.LabelFrame(self, text='Dependency type', font=dfont)
        arrow_options = ['Forward', 'Backwards', 'Bidirectional', 'No direction']
        self.selDirection = tk.StringVar()
        if dep:
            for key, value in self.arrow_map.items():
                if value == dep.arrow_type:
                    self.selDirection.set(key)
        else:
            self.selDirection.set('Forward')
        for i, option in enumerate(arrow_options):
            tk.Radiobutton(frameDependencyType, padx=20, pady=20, justify='left', text=option, variable=self.selDirection, value=option, font=dfont).grid(row=0, column=i, sticky='w')
        frameLabel = tk.LabelFrame(frameDependencyType, text='Label', font=dfont)
        self.selLabel = tk.StringVar()
        if dep:
            self.selLabel.set(dep.label)
        tk.Entry(frameLabel, textvariable=self.selLabel, font=dfont).grid(row=0, column=0, sticky='nw', padx=20, pady=20)
        frameLabel.grid(row=0, column=4, sticky='ns')
        frameSmooth = tk.LabelFrame(frameDependencyType, text='Curved', font=dfont)
        self.selSmooth = tk.BooleanVar()
        if dep:
            if dep.smooth:
                self.selSmooth.set(True)
            else:
                self.selSmooth.set(False)
        tk.Checkbutton(frameSmooth, padx=10, pady=10, variable=self.selSmooth, font=dfont).grid(row=0, column=0, sticky='nw')
        frameSmooth.grid(row=0, column=5, sticky='ns')
        frameDependencyType.grid(row=1, column=0, sticky='we')
        # -----------------------------------------------------------------------

        # frame: position
        framePosition = tk.LabelFrame(self, text='Position', font=dfont, padx=20, pady=20)
        self.selSpx = tk.IntVar()
        self.selSpy = tk.IntVar()
        self.selEpx = tk.IntVar()
        self.selEpy = tk.IntVar()
        if dep:
            self.selSpx.set(dep.spx)
            self.selSpy.set(dep.spy)
            self.selEpx.set(dep.epx)
            self.selEpy.set(dep.spx)
        frameSpx = tk.LabelFrame(framePosition, text='Spx', font=dfont, padx=20, pady=20)
        tk.Entry(frameSpx, textvariable=self.selSpx, font=dfont).grid(row=0, column=0, padx=10, pady=10)
        frameSpx.grid(row=0, column=0)
        frameSpy = tk.LabelFrame(framePosition, text='Spy', font=dfont, padx=20, pady=20)
        tk.Entry(frameSpy, textvariable=self.selSpy, font=dfont).grid(row=0, column=0, padx=10, pady=10 )
        frameSpy.grid(row=0, column=1)
        frameEpx = tk.LabelFrame(framePosition, text='Epx', font=dfont, padx=20, pady=20)
        tk.Entry(frameEpx, textvariable=self.selEpx, font=dfont).grid(row=0, column=0, padx=10, pady=10)
        frameEpx.grid(row=0, column=2)
        frameEpy = tk.LabelFrame(framePosition, text='Epy', font=dfont, padx=20, pady=20)
        tk.Entry(frameEpy, textvariable=self.selEpy, font=dfont).grid(row=0, column=0, padx=10, pady=10)
        frameEpy.grid(row=0, column=3)

        frameY_offset = tk.LabelFrame(framePosition, text='Y-axis offset', font=dfont)
        self.selYoffset = tk.IntVar()
        if dep:
            self.selYoffset.set(dep.Y_offset)
        tk.Entry(frameY_offset, textvariable=self.selYoffset, font=dfont).grid(row=0, column=0, sticky='nw')
        frameY_offset.grid(row=1, column=0, sticky='NW')
        framePosition.grid(row=2, column=0, sticky='WE')

        buttonOK = tk.Button(self, text='Done', font=dfont, padx=20, pady=20, command=self.ok, bg='#CCFFCC')
        buttonOK.grid(row=3, column=0, sticky='e', ipadx=50)

    def ok(self):
        self.destroy()

    def show(self):
        self.wm_deiconify()
        self.focus_force()
        self.wait_window()
        if self.dep:
            source_gps = self.dep.source_gps
            target_gps = self.dep.target_gps
        else:
            source_gps = None
            target_gps = None
        if self.selSmooth.get():
            smooth = 'raw'
        else:
            smooth = ''
        dep = Dependency(source=source_gps, target=target_gps, arrow_type=self.arrow_map[self.selDirection.get()], label=self.selLabel.get(), smooth=smooth)
        dep.spx = self.selSpx.get()
        dep.spy = self.selSpy.get()
        dep.epx = self.selEpx.get()
        dep.epy = self.selEpy.get()
        dep.Y_offset = self.selYoffset.get()
        return dep

class InspectWindow(tk.Toplevel):
    """Creates a new dependency or modifies an existing one (provided as an input argument)"""
    def __init__(self, parent, gps):
        super().__init__()
        self.gps = gps
        self.title(f'Inspector')
        self.geometry(f'+{int(parent.winfo_x() + gps.X + 100)}+{int(parent.winfo_y() + gps.Y + 200)}')

        constituent = tk.Label(self, text=f'{gps}({gps.label()})', font=('Calibri', 30, 'bold'))
        constituent.grid(row=0, column=0, sticky='')
        if gps.features:
            feature_lst = ''
            width = 0
            for f in sorted(gps.features):
                width += len(f) + 3
                if width > 50:
                    feature_lst += '\n'
                    width = 0
                feature_lst += f'[{f}] '
            features_Frame = tk.LabelFrame(self, text='Features', font=('Calibri', 20))
            features_Frame.grid(row=1, column=0, padx=20, pady=10)
            features_lst = tk.Label(features_Frame, text=f'{feature_lst}', font=('Courier', 20))
            features_lst.grid(row=0, column=0, padx=20, pady=0)
        geometry_Frame = tk.LabelFrame(self, text='Geometry', font=('Calibri', 20))
        geometry_Frame.grid(row=2, column=0, padx=20, pady=10, sticky='ew')
        head_Label = tk.Label(geometry_Frame, text=f'Head: {gps.head()}', font=('Courier', 20))
        head_Label.grid(row=0, column=0, sticky='w')
        mother_Label = tk.Label(geometry_Frame, text=f'Mother: {gps.M()}', font=('Courier', 20))
        mother_Label.grid(row=1, column=0, sticky='w')
        sister_Label = tk.Label(geometry_Frame, text=f'Sister: {gps.sister()}', font=('Courier', 20))
        sister_Label.grid(row=2, column=0, sticky='w')
        local_edge_Label = tk.Label(geometry_Frame, text=f'Local edge: {gps.local_edge()}', font=('Courier', 20))
        local_edge_Label.grid(row=3, column=0, sticky='w')
        path_Label = tk.Label(geometry_Frame, text=f'Path: {", ".join([str(x) for x in gps.path()])}', font=('Courier', 20))
        path_Label.grid(row=4, column=0, sticky='w')
        search_Label = tk.Label(geometry_Frame, text=f'Search: {", ".join([str(x) for x in gps.minimal_search()])}', font=('Courier', 20))
        search_Label.grid(row=5, column=0, sticky='w')
        container_Label = tk.Label(geometry_Frame, text=f'Container: {gps.container()}', font=('Courier', 20))
        container_Label.grid(row=6, column=0, sticky='w')
        max_Label = tk.Label(geometry_Frame, text=f'Max: {gps.max()}', font=('Courier', 20))
        max_Label.grid(row=7, column=0, sticky='w')
        copied_Label = tk.Label(geometry_Frame, text=f'Copied: {gps.copied}', font=('Courier', 20))
        copied_Label.grid(row=8, column=0, sticky='w')
        self.grid_columnconfigure(0, weight=1)

    def show(self):
        self.wm_deiconify()
        self.focus_force()
        self.wait_window()
        return self
