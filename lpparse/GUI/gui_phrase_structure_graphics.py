import tkinter as tk

MARGINS = 150
GRID = 150


class PhraseStructureGraphics(tk.Toplevel):
    def __init__(self, root, speaker_model_used_in_analysis):
        super().__init__(root)
        self.title("Phrase Structure Graphics")

        self.root = root
        self.canvas = None
        self.selected_node = None

        # Settings for drawing
        self.s = {'grid': GRID, 'margins': MARGINS}
        self.s['tsize'] = int(self.s['grid']/3.5)
        self.label_style = {'label': ("Times New Roman", int(self.s['tsize'])),
                            'PF': ("Times New Roman", int(self.s['tsize']*0.90), "italic"),
                            'gloss': ("Times New Roman", int(self.s['tsize']*0.90)),
                            'feature': ("Times New Roman", int(self.s['tsize']*0.75))}

        # Get the phrase structure to be drawn and project into logical space
        self.ps = self.get_results_from_speaker_model(speaker_model_used_in_analysis)
        self.project_into_logical_plane(self.ps)
        self.remove_overlap(self.ps)
        width, height, spx, spy = self.calculate_canvas_size(self.ps)
        self.geometry(str(width)+'x'+str(height))   # Set window size based on the input phrase structure
        self.focus()
        self.grid()

        # Drawing
        self.draw_to_canvas(self.ps, width, height, spx, spy, self.s['grid'])

    def get_results_from_speaker_model(self, speaker_model_used_in_analysis):
        """Returns the phrase structure object to be drawn, None otherwise"""
        if speaker_model_used_in_analysis.result_list and speaker_model_used_in_analysis.result_list[0]:
            return speaker_model_used_in_analysis.result_list[0][0].top()

    def project_into_logical_plane(self, ps):
        """Projects the phrase structure object into a logical space"""
        if ps.complex():
            ps.left.x = ps.x - 1
            ps.left.y = ps.y + 1
            self.project_into_logical_plane(ps.left)
            ps.right.x = ps.x + 1
            ps.right.y = ps.y + 1
            self.project_into_logical_plane(ps.right)

    def draw_to_canvas(self, ps, width, height, spx, spy, grid):
        """Creates a canvas and draws the phrase structure object onto it"""
        self.canvas = PhraseStructureCanvas(self, width=width, height=height, background='white')
        self.canvas.pack()
        self.project_into_canvas(ps, spx, spy, grid)
        if self.root.lfs.settings['image_parameter_show_head_chains']:
            self.draw_head_chains(ps)
        if self.root.lfs.settings['image_parameter_show_phrasal_chains']:
            self.draw_phrasal_chains(ps)

    def remove_overlap(self, ps):
        """Stretches child nodes apart if their offspring create overlap"""
        def left_boundary(ps):
            boundary = set()
            boundary.add((ps.x, ps.y))
            if ps.complex():
                boundary = boundary | left_boundary(ps.left)
            return boundary

        def right_boundary(ps):
            boundary = set()
            boundary.add((ps.x, ps.y))
            if ps.complex():
                boundary = boundary | right_boundary(ps.right)
            return boundary

        if self.root.lfs.settings['image_parameter_compress_phrasal_chains'] and (ps.left.find_me_elsewhere or ps.right.find_me_elsewhere):
            return

        if ps.complex():
            self.remove_overlap(ps.left)
            self.remove_overlap(ps.right)
            overlap = 0
            LC_right_boundary = right_boundary(ps.left)
            RC_left_boundary = left_boundary(ps.right)
            for L_bp in LC_right_boundary:
                for R_bp in RC_left_boundary:
                    if L_bp[1] == R_bp[1]:
                        if L_bp[0] >= R_bp[0] and L_bp[0] - R_bp[0] >= overlap:
                            overlap = L_bp[0] - R_bp[0] + 1
            if overlap > 0:
                self.move_x(ps.left, -overlap/2)
                self.move_x(ps.right, overlap/2)

    def calculate_canvas_size(self, ps):
        """Determines the canvas size on the basis of the pharse structure object"""
        def find_boundaries(ps, left_x, right_x, depth):
            if ps.x < left_x:
                left_x = ps.x
            if ps.x > right_x:
                right_x = ps.x
            if ps.y > depth:
                depth = ps.y
            if ps.complex():
                left_x, right_x, depth = find_boundaries(ps.left, left_x, right_x, depth)
                left_x, right_x, depth = find_boundaries(ps.right, left_x, right_x, depth)
            return left_x, right_x, depth
        left_x, right_x, depth = find_boundaries(ps, 0, 0, 0)
        width = (abs(left_x) + abs(right_x)) * self.s['grid'] + 2 * self.s['margins']
        height = depth * self.s['grid'] + 2 * self.s['margins']
        height = height + self.label_size(ps)
        return int(width), int(height), abs(left_x) * self.s['grid'] + self.s['margins'], self.s['margins']

    def label_size(self, ps):
        """Predicts the height of labels on the basis of what will be shown in them
        to make room for them in the margins"""
        return len(self.label_stack(ps)) * self.s['tsize']

    def move_x(self, ps, amount):
        """Moves a node and its offspring"""
        ps.x = ps.x + amount
        if ps.complex():
            self.move_x(ps.left, amount)
            self.move_x(ps.right, amount)

    def project_into_canvas(self, ps, spx, spy, grid):
        """Projects the logical phase structure object into canvas"""
        X1 = spx + ps.x * grid
        Y1 = spy + ps.y * grid
        ps.X = X1   # Memorize the point on the canvas for later chain marking
        ps.Y = Y1
        if ps.complex():
            X2 = spx + ps.left.x * grid
            Y2 = spy + ps.left.y * grid
            X3 = spx + ps.right.x * grid
            Y3 = spy + ps.right.y * grid
            ps.canvas_ID = self.canvas.create_text((X1, Y1), text=ps.label(), font=("Times New Roman", self.s['tsize']))
            if self.root.lfs.settings['image_parameter_compress_phrasal_chains'] and ps.find_me_elsewhere:
                return
            self.canvas.create_line((X1, Y1 + int(self.s['tsize'] / 2)), (X2, Y2 - int(self.s['tsize'] / 2)), width=2, fill='black')
            self.canvas.create_line((X1, Y1 + int(self.s['tsize'] / 2)), (X3, Y3 - int(self.s['tsize'] / 2)), width=2, fill='black')
            self.project_into_canvas(ps.left, spx, spy, grid)
            self.project_into_canvas(ps.right, spx, spy, grid)
        if ps.primitive():
            self.create_primitive_label(ps, X1, Y1)

    def create_primitive_label(self, ps, X1, Y1):
        for i, item in enumerate(self.label_stack(ps)):
            ps.canvas_ID = self.canvas.create_text((X1, Y1 + 1.1 * i * self.s['tsize']), text=item[0], anchor='center', font=self.label_style[item[1]])

    def label_stack(self, ps):
        """Determines the content for primitive labels"""

        # Minimum label is the label itself
        stack = [(ps.label(), 'label')]

        # Phonological string
        if self.root.lfs.settings['image_parameter_show_words']:
            if ps.get_phonological_string() != ps.label():
                stack.append((ps.get_phonological_string(), 'PF'))

        # Gloss
        if self.root.lfs.settings['image_parameter_show_glosses']:
            if ps.gloss() != ps.label() and ps.gloss() != ps.get_phonological_string():
                for head in ps.get_affix_list():
                    stack.append((f"ʻ{head.gloss()}ʼ", 'gloss'))

        if self.root.lfs.settings['show_features']:
            for feature in [x for x in ps.features if x in self.root.lfs.settings['show_features']]:
                stack.append((f'[{self.feature_conversion(feature)}]', 'feature'))

        return stack

    def feature_conversion(self, feature):
        return feature

    def draw_head_chains(self, ps):
        if ps.complex():
            self.draw_head_chains(ps.left)
            self.draw_head_chains(ps.right)
        if ps.primitive() and ps.is_left() and ps.has_affix() and ps.right.find_me_elsewhere and ps.mother:
            target = ps.mother.right.find_constituent_with_index(ps.right.index())
            start_label_size = self.label_size(ps)      # Begin the chain at the bottom of label
            end_label_size = self.label_size(target)    # End the chain at the bottom of label
            self.draw_dependency((ps.X, ps.Y + start_label_size), (target.X, target.Y + end_label_size))

    def draw_phrasal_chains(self, ps):
        if ps.complex() and ps.find_me_elsewhere and ps.identity and ps.mother:
            target = ps.top().find_constituent_with_identity(ps, ps.identity)
            P = ps
            G = target
            self.draw_dependency((P.X, P.Y + self.s['tsize']), (G.X, G.Y + self.s['tsize']))
        if ps.complex():
            self.draw_phrasal_chains(ps.left)
            self.draw_phrasal_chains(ps.right)

    def draw_dependency(self, start_point, end_point):
        """Draws a dependency arc from point to point"""

        # Create an extra point to bend the line
        X = start_point[0] + abs(start_point[0] - end_point[0]) / 2
        Y = end_point[1] + self.s['grid'] * 1.5
        self.canvas.create_line(start_point, (X, Y), end_point, width=1, smooth=True, fill='black')


class PhraseStructureCanvas(tk.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bind("<Button-1>", self.on_click)
        self.selected_node = None

    def on_click(self, event):
        print(self.find_overlapping(event.x, event.y, event.x, event.y))
