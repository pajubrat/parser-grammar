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
        file_menu.add_command(label='Save...', command=self._event('<<SaveAsStructure>>'))
        self.add_cascade(label='File', menu=file_menu)

        # Select image menu
        select_image = tk.Menu(self, tearoff=False, font=menu_font)
        select_image.add_command(label='PF-interface', command=self._event('<<PF>>'))
        select_image.add_command(label='LF-interface', command=self._event('<<LF>>'))
        select_image.add_command(label='Next image', command=self._event('<<NextImage>>'))
        select_image.add_command(label='Previous image', command=self._event('<<PreviousImage>>'))
        select_image.add_command(label='First image', command=self._event('<<FirstImage>>'))
        self.add_cascade(label='Image source', menu=select_image)

        # Node menu
        node = tk.Menu(self, tearoff=False, font=menu_font)
        node.add_command(label='Compress', command=self._event('<<CompressNode>>'))
        node.add_command(label='Decompress', command=self._event('<<DecompressNode>>'))

        # Submenu for Label
        submenu_Node_Label = tk.Menu(node, tearoff=0, font=menu_font)
        submenu_Node_Label.add_command(label='New', command=self._event('<<CustomLabel>>'))
        submenu_Node_Label.add_command(label='Default', command=self._event('<<DefaultLabel>>'))
        submenu_Node_Label.add_command(label='Empty', command=self._event('<<EmptyLabel>>'))
        node.add_cascade(label='Label', menu=submenu_Node_Label)

        # Submenu for Text
        submenu_Node_Text = tk.Menu(node, tearoff=0, font=menu_font)
        submenu_Node_Text.add_command(label='New', command=self._event('<<CustomPhonology>>'))
        submenu_Node_Text.add_command(label='Default', command=self._event('<<DefaultPhonology>>'))
        submenu_Node_Text.add_command(label='Empty', command=self._event('<<EmptyPhonology>>'))
        node.add_cascade(label='Phonology', menu=submenu_Node_Text)

        # Submenu for Gloss
        submenu_Node_Gloss = tk.Menu(node, tearoff=0, font=menu_font)
        submenu_Node_Gloss.add_command(label='New', command=self._event('<<CustomGloss>>'))
        submenu_Node_Gloss.add_command(label='Default', command=self._event('<<DefaultGloss>>'))
        submenu_Node_Gloss.add_command(label='Empty', command=self._event('<<EmptyGloss>>'))
        node.add_cascade(label='Gloss', menu=submenu_Node_Gloss)

        # Submenu for features
        submenu_Node_Features = tk.Menu(node, tearoff=0, font=menu_font)
        submenu_Node_Features.add_command(label='New', command=self._event('<<CustomFeatures>>'))
        submenu_Node_Features.add_command(label='Default', command=self._event('<<DefaultFeatures>>'))
        submenu_Node_Features.add_command(label='Empty', command=self._event('<<EmptyFeatures>>'))
        node.add_cascade(label='Features', menu=submenu_Node_Features)

        # Submenu for free text
        submenu_Node_Text = tk.Menu(node, tearoff=0, font=menu_font)
        submenu_Node_Text.add_command(label='New', command=self._event('<<CustomText>>'))
        submenu_Node_Text.add_command(label='Empty', command=self._event('<<EmptyText>>'))
        node.add_cascade(label='Free text', menu=submenu_Node_Text)

        # Add the whole menu to window menu bar
        self.add_cascade(label='Node', menu=node)

        arc = tk.Menu(self, tearoff=False, font=menu_font)
        arc.add_command(label='Set startpoint', command=self._event('<<SetArcStartpoint>>'))
        arc.add_command(label='Set endpoint', command=self._event('<<SetArcEndpoint>>'))
        arc.add_command(label='Set Label', command=self._event('<<LabelArc>>'))
        arc.add_command(label='Create', command=self._event('<<CreateArc>>'))
        arc.add_command(label='Clear points', command=self._event('<<ClearPoints>>'))
        arc.add_command(label='Clear label', command=self._event('<<DeleteArcLabel>>'))
        arc.add_command(label='Delete all', command=self._event('<<DeleteArc>>'))
        self.add_cascade(label='Arc', menu=arc)

        ps = tk.Menu(self, tearoff=False, font=menu_font)
        ps.add_command(label='Reverse', command=self._event('<<ReversePhraseStructure>>'))
        ps.add_command(label='Expand', command=self._event('<<ExpandPhraseStructure>>'))
        ps.add_command(label='Shrink', command=self._event('<<ShrinkPhraseStructure>>'))
        ps.add_command(label='Delete', command=self._event('<<DeletePhraseStructure>>'))
        ps.add_command(label='Recover original', command=self._event('<<Recalibrate>>'))
        ps.add_command(label='Move Up', command=self._event('<<MoveUp>>'))
        ps.add_command(label='Move Down', command=self._event('<<MoveDown>>'))
        ps.add_command(label='Move Left', command=self._event('<<MoveLeft>>'))
        ps.add_command(label='Move Right', command=self._event('<<MoveRight>>'))
        self.add_cascade(label='Phrase Structure', menu=ps)

        # Settings menu
        settings_menu = tk.Menu(self, tearoff=False, font=menu_font)
        settings_menu.add_command(label='Image settings...', command=self._event('<<Settings>>'))
        self.add_cascade(label='Settings', menu=settings_menu)

    def todo(self):
        pass

    def print(self):
        pass