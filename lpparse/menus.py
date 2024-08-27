import tkinter as tk
from tkinter import messagebox

menu_font = ('Calibri', 20)


class MainMenu(tk.Menu):
    # This function is used to generate events for the main window
    def _event(self, sequence):
        def callback(*_):
            root = self.master.winfo_toplevel()
            root.event_generate(sequence)
        return callback

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        # File menu
        file_menu = tk.Menu(self, tearoff=False, font=menu_font)
        file_menu.config(font=menu_font)
        file_menu.add_command(label='New...', command=self.todo)
        file_menu.add_command(label='Load Study...', command=self._event('<<LoadStudy>>'))
        file_menu.add_command(label='Save Study As...', command=self._event('<<SaveStudy>>'))
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
        study_menu.add_command(label='Run complete study', command=self._event('<<RunStudy>>'))
        self.add_cascade(label='Study', menu=study_menu)

        # Examine_results_menu
        examine_results_menu = tk.Menu(self, tearoff=False, font=menu_font)
        examine_results_menu.add_command(label='Results...', command=self.todo)
        examine_results_menu.add_command(label='Derivation...', command=self.todo)
        examine_results_menu.add_command(label='Examine log...', command=self._event('<<ExamineDerivationalLog>>'))
        self.add_cascade(label='Results', menu=examine_results_menu)

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

class GraphicsMenu(tk.Menu):
    def _event(self, sequence):
        def callback(*_):
            root = self.master.winfo_toplevel()
            root.event_generate(sequence)
        return callback

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        # File menu
        file_menu = tk.Menu(self, tearoff=False, font=menu_font)
        file_menu.config(font=menu_font)
        file_menu.add_command(label='Load...', command=self._event('<<LoadAsStructure>>'))
        file_menu.add_command(label='Save As Structure...', command=self._event('<<SaveAsStructure>>'))
        file_menu.add_command(label='Save As Image...', command=self._event('<<SaveAsImage>>'))
        self.add_cascade(label='File', menu=file_menu)

        # Select image menu
        select_image = tk.Menu(self, tearoff=False, font=menu_font)
        select_image.add_command(label='PF-interface', command=self._event('<<PF>>'))
        select_image.add_command(label='LF-interface', command=self._event('<<LF>>'))
        select_image.add_command(label='Next image', command=self._event('<<NextImage>>'))
        select_image.add_command(label='Previous image', command=self._event('<<PreviousImage>>'))
        select_image.add_command(label='First image', command=self._event('<<FirstImage>>'))
        self.add_cascade(label='Image properties', menu=select_image)

        # Node menu
        node = tk.Menu(self, tearoff=False, font=menu_font)
        node.add_command(label='Compress', command=self._event('<<CompressNode>>'))
        node.add_command(label='Decompress', command=self._event('<<DecompressNode>>'))
        node.add_separator()
        node.add_command(label='Clear', command=self._event('<<ClearNode>>'))
        node.add_command(label='Only label', command=self._event('<<OnlyLabel>>'))

        # Submenu for Label
        submenu_Node_Label = tk.Menu(node, tearoff=0, font=menu_font)
        submenu_Node_Label.add_command(label='New', command=self._event('<<CustomLabel>>'))
        submenu_Node_Label.add_command(label='Original', command=self._event('<<DefaultLabel>>'))
        submenu_Node_Label.add_command(label='Empty', command=self._event('<<EmptyLabel>>'))
        node.add_cascade(label='Custom label...', menu=submenu_Node_Label)

        # Submenu for Label subscript
        submenu_Label_Subscript = tk.Menu(node, tearoff=0, font=menu_font)
        submenu_Label_Subscript.add_command(label='Subscript', command=self._event('<<LabelSubscript>>'))
        submenu_Label_Subscript.add_command(label='Superscript', command=self._event('<<LabelSuperscript>>'))
        node.add_cascade(label='Special labels...', menu=submenu_Label_Subscript)

        # Submenu for Text
        submenu_Node_Text = tk.Menu(node, tearoff=0, font=menu_font)
        submenu_Node_Text.add_command(label='New', command=self._event('<<CustomPhonology>>'))
        submenu_Node_Text.add_command(label='Original', command=self._event('<<DefaultPhonology>>'))
        submenu_Node_Text.add_command(label='Empty', command=self._event('<<EmptyPhonology>>'))
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

        # Add the whole menu to window menu bar
        self.add_cascade(label='Node', menu=node)

        arc = tk.Menu(self, tearoff=False, font=menu_font)
        arc.add_command(label='Set startpoint', command=self._event('<<SetArcStartpoint>>'))
        arc.add_command(label='Set endpoint', command=self._event('<<SetArcEndpoint>>'))
        arc.add_command(label='Create', command=self._event('<<CreateArc>>'))
        arc.add_separator()
        arc.add_command(label='Change curvature', command=self._event('<<ChangeCurvature>>'))
        arc.add_command(label='Clear points', command=self._event('<<ClearPoints>>'))
        arc.add_command(label='Delete all', command=self._event('<<DeleteArc>>'))
        self.add_cascade(label='Arc', menu=arc)

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
        ps.add_command(label='Delete', command=self._event('<<DeletePhraseStructure>>'))
        ps.add_command(label='Recover original', command=self._event('<<Recalibrate>>'))
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
        submenu_chains_head = tk.Menu(chains_menu, tearoff=0, font=menu_font)
        submenu_chains_head.add_command(label='Enable', command=self._event('<<EnableHeadChains>>'))
        submenu_chains_head.add_command(label='Disable', command=self._event('<<DisableHeadChains>>'))
        chains_menu.add_cascade(label='Head chains...', menu=submenu_chains_head)
        submenu_chains_phrasal = tk.Menu(chains_menu, tearoff=False, font=menu_font)
        # Submenu for chains
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
        settings_menu.add_command(label='Image settings...', command=self._event('<<Settings>>'))
        self.add_cascade(label='Settings', menu=settings_menu)

    def todo(self):
        pass

    def print(self):
        pass