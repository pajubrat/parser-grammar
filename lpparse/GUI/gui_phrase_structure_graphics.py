import tkinter as tk
from phrase_structure import PhraseStructure
from GUI.gui_menus import GraphicsMenu

MARGINS = 300
GRID = 150


class GPhraseStructure(PhraseStructure):
    """Phrase Structure class that has additional properties related to tree drawing"""
    settings = {}

    def __init__(self, source=None, left=None, right=None):
        super().__init__(left, right)

        # Properties of regular constituents
        if source:
            self.features = source.features
            self.adjunct = source.adjunct
            self.identity = source.identity
            self.find_me_elsewhere = source.find_me_elsewhere
            if source.left:
                self.left = GPhraseStructure(source.left)
                self.left.mother = self
            if source.right:
                self.right = GPhraseStructure(source.right)
                self.right.mother = self

        # Special properties
        self.x = 0
        self.y = 0
        self.X = 0
        self.Y = 0
        self.label_stack = []
        self.label_stack = self.generate_label_stack()
        self.phrasal_chain_target = None
        self.head_chain_target = None
        self.Agree_target = None

    def find_phrasal_chain(self):
        if self.complex() and self.find_me_elsewhere and self.identity:
            return self.top().find_constituent_with_identity(self, self.identity)

    def find_head_chain(self):
        if self.primitive() and self.is_left() and self.has_affix() and self.right.find_me_elsewhere and self.mother:
            return self.mother.right.find_constituent_with_index(self.right.index())

    def find_Agree(self):
        if self.primitive() and self.is_left() and 'ΦLF' in self.features:
            return self.argument_by_agreement().head()

    def initialize_logical_space(self):
        """Projects the phrase structure object into a logical space"""
        self.phrasal_chain_target = self.find_phrasal_chain()
        self.head_chain_target = self.find_head_chain()
        self.Agree_target = self.find_Agree()
        if self.complex():
            self.left.x = self.x - 1
            self.left.y = self.y + 1
            self.left.initialize_logical_space()
            self.right.x = self.x + 1
            self.right.y = self.y + 1
            self.right.initialize_logical_space()

    def left_boundary(self):
        boundary = set()
        boundary.add((self.x, self.y))
        if self.complex():
            boundary = boundary | self.left.left_boundary()
        return boundary

    def right_boundary(self):
        boundary = set()
        boundary.add((self.x, self.y))
        if self.complex():
            boundary = boundary | self.right.right_boundary()
        return boundary

    def find_boundaries(self, left_x, right_x, depth):
        if self.x < left_x:
            left_x = self.x
        if self.x > right_x:
            right_x = self.x
        if self.y > depth:
            depth = self.y
        if self.complex():
            left_x, right_x, depth = self.left.find_boundaries(left_x, right_x, depth)
            left_x, right_x, depth = self.right.find_boundaries(left_x, right_x, depth)
        return left_x, right_x, depth

    def remove_overlap(self):
        """Stretches child nodes apart if their offspring create overlap"""
        if self.complex():
            self.left.remove_overlap()
            self.right.remove_overlap()
            overlap = 0
            LC_right_boundary = self.left.right_boundary()
            RC_left_boundary = self.right.left_boundary()
            for L_bp in LC_right_boundary:
                for R_bp in RC_left_boundary:
                    if L_bp[1] == R_bp[1]:
                        if L_bp[0] >= R_bp[0] and L_bp[0] - R_bp[0] >= overlap:
                            overlap = L_bp[0] - R_bp[0] + 1
            if overlap > 0:
                self.left.move_x(-overlap/2)
                self.right.move_x(overlap/2)

    def move_x(self, amount):
        """Moves a node and its offspring"""
        self.x = self.x + amount
        if self.complex():
            self.left.move_x(amount)
            self.right.move_x(amount)

    def move_y(self, amount):
        """Moves a node and its offspring"""
        self.y = self.y + amount
        if self.complex():
            self.left.move_y(amount)
            self.right.move_y(amount)

    def label_size(self):
        return len(self.label_stack)

    def generate_label_stack(self):
        """Determines the content for primitive labels"""
        def feature_conversion(feature):
            return feature

        # Minimum label is the label itself
        label_stack = [(self.label(), 'label')]

        if self.primitive():

            # Phonological string
            if GPhraseStructure.settings['image_parameter_show_words']:
                if self.get_phonological_string() != self.label():
                    label_stack.append((self.get_phonological_string(), 'PF'))

            # Gloss
            if GPhraseStructure.settings['image_parameter_show_glosses']:
                if self.gloss() != self.label() and self.gloss() != self.get_phonological_string():
                    for head in self.get_affix_list():
                        label_stack.append((f"ʻ{head.gloss()}ʼ", 'gloss'))

            # Features
            if GPhraseStructure.settings['show_features']:
                for feature in [x for x in self.features if x in GPhraseStructure.settings['show_features']]:
                    label_stack.append((f'[{feature_conversion(feature)}]', 'feature'))

        return label_stack

    def itext(self):
        itext = self.label() + '\n\n'

        if self.primitive():

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

            if self.has_affix() and not self.right.find_me_elsewhere:
                itext += f'\nComplex head with structure '
                for c in self.get_affix_list():
                    itext += f'{c} '
        return itext


class PhraseStructureGraphics(tk.Toplevel):
    """Window hosting the canvas"""
    def __init__(self, root, speaker_model):
        super().__init__(root)
        self.title("Phrase Structure Graphics")
        GPhraseStructure.settings = root.lfs.settings
        self.geometry(('1800x1000+1800+500'))

        # Internal variables
        self.index_of_analysis_shown = 0

        # Settings for drawing
        self.s = {'grid': GRID, 'margins': MARGINS}
        self.s['tsize'] = int(self.s['grid']/3.5)

        # Line styles
        self.line_style = {'phrasal chain': {'fill': 'black', 'dash': None, 'width': 1},
                           'head chain': {'fill': 'black', 'dash': None, 'width': 1},
                           'Agree': {'fill': 'blue', 'dash': None, 'width': 3}}

        # Menu
        self.graphics_menu = GraphicsMenu(self)
        self.config(menu=self.graphics_menu)

        # Make host window and canvas visible
        self.focus()
        self.grid()
        self.canvas = PhraseStructureCanvas(self)
        self.canvas.pack()
        self.gps = None     # Current phrase structure on screen
        self.speaker_model = speaker_model
        self.bind('<<LF>>', self.LF)
        self.bind('<<PF>>', self.PF)
        self.bind('<<NextImage>>', self.next_image)
        self.bind('<<PreviousImage>>', self.previous_image)
        self.bind('<<FirstImage>>', self.first_image)

        # Show image
        self.draw_phrase_structure_by_title('LF-interface')

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
        self.draw_phrase_structure_by_title('LF-interface')

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
        height = height + gps.label_size() * self.s['tsize']
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
        self.selected_canvas_node = None    # image object selection
        self.selected_logical_node = None   # logical node selection (can be independent of image objects)
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
        if gps.settings['image_parameter_show_head_chains']:
            self.draw_head_chains(gps)
        if gps.settings['image_parameter_show_phrasal_chains']:
            self.draw_phrasal_chains(gps)
        if gps.settings['image_parameter_show_Agree']:
            self.draw_Agree(gps)

    def _key_press(self, event):
        if self.selected_canvas_node:
            gps = self.node_to_gps[str(self.selected_canvas_node)]  # Get the phrase structure constituent
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
            self.selected_canvas_node = self.find_withtag('current')[0]
            self.selected_logical_node = self.node_to_gps[str(self.selected_canvas_node)]
            x1, y1 = self.coords(self.selected_canvas_node)
            self.itemconfigure(self.cursor, state='normal')
            self.moveto(self.cursor, x1-50, y1-50)
        else:
            self.itemconfigure(self.cursor, state='hidden')
            self.selected_canvas_node = None

    def _show_info(self, *_):
        if self.find_withtag('current'):
            selected = self.find_withtag('current')[0]
            gps = self.node_to_gps[str(selected)]
            if gps.primitive():
                self.moveto(self.info_text, 200, 300)
                self.itemconfigure(self.info_text, state='normal', fill='black', text=gps.itext(), font=self.label_style['info'])

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
        if gps.complex():
            self.create_complex_node(gps, X1, Y1, spx, spy, grid)
        else:
            self.create_primitive_node(gps, X1, Y1)

    def create_complex_node(self, gps, X1, Y1, spx, spy, grid):
        X2 = spx + gps.left.x * grid
        Y2 = spy + gps.left.y * grid
        X3 = spx + gps.right.x * grid
        Y3 = spy + gps.right.y * grid
        ID = self.create_text((X1, Y1), text=gps.label_stack[0][0], fill='black', activefill='red', tag='node', font=("Times New Roman", self.parent.s['tsize']))
        self.node_to_gps[str(ID)] = gps
        self.tag_bind(ID, '<Enter>', self._show_info)
        self.tag_bind(ID, '<Leave>', self._hide_info)
        if self.selected_logical_node == gps:
            x1, y1 = self.coords(ID)
            self.itemconfigure(self.cursor, state='normal')
            self.moveto(self.cursor, x1 - 50, y1 - 50)
        self.create_line((X1, Y1 + int(self.parent.s['tsize'] / 2)), (X2, Y2 - int(self.parent.s['tsize'] / 2)), width=2, fill='black')
        self.create_line((X1, Y1 + int(self.parent.s['tsize'] / 2)), (X3, Y3 - int(self.parent.s['tsize'] / 2)), width=2, fill='black')
        self.project_into_canvas(gps.left, spx, spy, grid)
        self.project_into_canvas(gps.right, spx, spy, grid)
        return ID

    def create_primitive_node(self, gps, X1, Y1):
        for i, item in enumerate(gps.label_stack):
            ID = self.create_text((X1, Y1 + 1.2 * i * self.parent.s['tsize']), fill='black', activefill='red', tag='node', text=item[0], anchor='center', font=self.label_style[item[1]])
            self.node_to_gps[str(ID)] = gps
            if i == 0:
                self.tag_bind(ID, '<Enter>', self._show_info)
                self.tag_bind(ID, '<Leave>', self._hide_info)
        self.update_cursor(gps, X1, Y1)

    def update_cursor(self, gps, x1, y1):
        if self.selected_logical_node == gps:
            self.itemconfigure(self.cursor, state='normal')
            self.moveto(self.cursor, x1 - 50, y1 - 50)

    def draw_head_chains(self, gps):
        if gps.head_chain_target:
            self.draw_dependency('phrasal chain', gps, gps.head_chain_target)
        if gps.complex():
            self.draw_head_chains(gps.left)
            self.draw_head_chains(gps.right)

    def draw_phrasal_chains(self, gps):
        if gps.phrasal_chain_target:
            self.draw_dependency('head chain', gps, gps.phrasal_chain_target)
        if gps.complex():
            self.draw_phrasal_chains(gps.left)
            self.draw_phrasal_chains(gps.right)

    def draw_Agree(self, gps):
        if gps.Agree_target:
            self.draw_dependency('Agree', gps, gps.Agree_target)
        if gps.complex():
            self.draw_Agree(gps.left)
            self.draw_Agree(gps.right)

    def draw_dependency(self, style, source, target):
        """Draws a dependency arc from point to point"""
        X1 = source.X
        Y1 = source.Y
        X3 = target.X
        Y3 = target.Y
        X2 = X1 + abs(X1 - X3) / 2
        if X1 == X3:
            Y3 = Y3 - self.parent.s['tsize'] * 3.5
        Y2 = Y3 + self.parent.s['grid'] * 1.5
        start_offset = source.label_size() * self.parent.s['tsize']
        end_offset = target.label_size() * self.parent.s['tsize']
        self.create_line((X1, Y1 + start_offset), (X2, Y2), (X3, Y3 + end_offset),
                         dash=self.parent.line_style[style]['dash'],
                         width=self.parent.line_style[style]['width'],
                         smooth=True,
                         fill=self.parent.line_style[style]['fill'])
