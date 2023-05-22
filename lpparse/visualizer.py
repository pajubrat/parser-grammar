#####################################################################
# phrase_structure_graphics
# Provides support for drawing the phrase structure objects visually
######################################################################
import pyglet
import pyglet.window.key
from pyglet import shapes
import re

SCALING_FACTOR = 2
case_features = {'NOM', 'ACC', 'PAR', 'GEN', 'ACC(0)', 'ACC(n)', 'ACC(t)', 'DAT', 'POSS'}


# Definition for the visualizer
class Visualizer:
    def __init__(self, settings):
        self.file_identifier = ''
        self.new_lateral_stretch_needed = True
        self.image_output = False
        self.input_sentence_string = ''
        self.show_features = []
        self.save_image_file_name = ''
        self.input_sentence_string = ''
        self.settings = settings

    def initialize(self, settings):
        self.image_output = True

    # Definition for the drawing function
    def draw(self, ps):
        self.project_to_plane(ps)
        win = ProduceGraphicOutput(ps, self, self.settings)
        pyglet.clock.schedule_once(win.terminate, 0.1)
        pyglet.app.run()

    def project_to_plane(self, ps):
        ps.x = 0
        ps.y = 0
        self.determine_plane_topology(ps)   # Projects the phrase structure into a simple abstract space
        self.remove_overlaps(ps)            # Modifies the projection to remove overlapping texts and lines

    # Creates a basic plane topology with constituent branches by one unit
    def determine_plane_topology(self, ps):
        if ps.left:
            ps.left.x = ps.x - 1
            ps.left.y = ps.y - 1
            self.determine_plane_topology(ps.left)
        if ps.right:
            ps.right.x = ps.x + 1
            ps.right.y = ps.y - 1
            self.determine_plane_topology(ps.right)

    # Removes overlaps when one branch goes on the top of another branch
    def remove_overlaps(self, ps):
        self.new_lateral_stretch_needed = True
        while self.new_lateral_stretch_needed:
            self.new_lateral_stretch_needed = False
            self.lateral_stretch(ps)  # Stretches the structure laterally to avoid overlaps

    def lateral_stretch(self, N):
        if not N.primitive():
            overlap = self.check_lateral_conflicts(N)
            if overlap > 0:
                # Stretches the left and right node apart to avoid overlaps below
                # The multiplier determines the amount fo stretching
                self.move_node(-overlap * 0.5, 0, N.left)
                self.move_node(overlap * 0.5, 0, N.right)
                self.new_lateral_stretch_needed = True
            self.lateral_stretch(N.left)
            self.lateral_stretch(N.right)

    def move_node(self, dx, dy, N):
        N.x = N.x + dx
        N.y = N.y + dy
        if N.complex():
            self.move_node(dx, dy, N.left)
            self.move_node(dx, dy, N.right)

    def check_lateral_conflicts(self, N):
        overlap = 0
        # Get a list of node positions (tuples) from left and right
        left_branch_coordinates = self.get_coordinate_set(N.left, set())
        right_branch_coordinates = self.get_coordinate_set(N.right, set())
        for coordinates_from_left in left_branch_coordinates:
            for coordinates_from_right in right_branch_coordinates:
                if coordinates_from_left[1] == coordinates_from_right[1]:           # Examines nodes in the same Y-axis
                    if coordinates_from_right[0] - coordinates_from_left[0] < 1:    # Examine pairs where there is overlap
                        overlap = coordinates_from_left[0] - coordinates_from_right[0] + 1
        return overlap

    def get_coordinate_set(self, N, coordinate_set):
        coordinate_set.add((N.x, N.y))
        coordinate_set.add((N.x, N.y))
        if N.primitive():
            if self.label_stack_size(N) > 1:
                coordinate_set.add((N.x, N.y - 1))
            if self.label_stack_size(N) > 4:
                coordinate_set.add((N.x, N.y - 2))
        else:
            if not (N.head().check({'φ'}) and self.settings['image_parameter_ignore_internal_structure_of_DPs']):
                coordinate_set |= self.get_coordinate_set(N.left, coordinate_set)
                coordinate_set |= self.get_coordinate_set(N.right, coordinate_set)
        return coordinate_set

    def label_stack_size(self, ps):
        label_stack = 0
        if self.settings['image_parameter_show_words']:
            if ps.get_phonological_string() != ps.label():
                label_stack += 1
        if self.settings['image_parameter_show_glosses']:
            label_stack += 1
        if self.settings['show_features']:
            for feature_pattern in self.settings['show_features']:
                for i, lexical_feature in enumerate(ps.features):
                    if re.match(feature_pattern, lexical_feature):
                        label_stack += 1
        return label_stack

# Definition for the output window behavior
class ProduceGraphicOutput(pyglet.window.Window):
    def __init__(self, ps, visualizer, settings):
        self.visualizer = visualizer
        self.settings = settings
        # Scaling function (larger = more detailed but also larger image)
        self.scale = SCALING_FACTOR

        # Define the grid
        self.x_grid = 50 * self.scale
        self.y_grid = 75 * self.scale
        # offset
        self.x_offset = 0  # Defined later
        self.y_offset = 0  # Defined later
        # Define the margins
        self.margins = (100 * self.scale)
        self.file_identifier = self.visualizer.file_identifier
        self.mouse_position_x = 0
        self.mouse_position_y = 0
        self.max_x_value = 0
        self.max_y_value = 0
        self.mouse_over_node = None
        self.selected_node = None
        self.circle = None
        self.line = None
        self.window_width = 1
        self.window_height = 1
        self.top_node_position = 0
        self.do_not_repeat_information = False

        # Phrase structure that will be projected to the 2D window
        self.phrase_structure = ps

        self.window_width, self.window_height = self.determine_window_size(ps)
        super().__init__(width=self.window_width, height=self.window_height, caption='LF interface', visible=self.settings['image_parameter_stop_after_image'])
        self.background_image = pyglet.image.SolidColorImagePattern((255, 255, 255, 255)).create_image(self.window_width, self.window_height)

    def determine_window_size(self, ps):
        left, right, depth = self.get_tree_size(ps, 0, 0, 0)
        width = (abs(right) + abs(left)) * self.x_grid + self.margins
        height = abs(depth * self.y_grid) + self.y_grid/2 + self.margins + 75 * self.scale
        self.x_offset = width / 2 - (right - (abs(left) + abs(right))/2) * self.x_grid   # Position of the highest node
        self.y_offset = height - self.y_grid  # How much extra room above the highest node (for highest label)
        return int(width), int(height)

    def save_image(self):
        pyglet.image.get_buffer_manager().get_color_buffer().save(self.visualizer.file_identifier)

    def update(self):
        pass

    # Recursive projection function
    def show_in_window(self, ps):

        # Do not repeat information if ps have been copied
        if ps.find_me_elsewhere:
            self.do_not_repeat_information = True

        # Mother node position
        X1 = self.x_offset + ps.x * self.x_grid
        Y1 = self.y_offset + ps.y * self.y_grid

        if X1 > self.max_x_value:
            self.max_x_value = X1
        if Y1 > self.max_y_value:
            self.max_y_value = Y1

        # Prevent drawing outside of window boundaries
        if X1 < 0:
            X1 = 0
        if Y1 < 0:
            Y1 = 0

        # Textual
        head_text_stack = self.determine_label_stack(ps)
        self.draw_node_label(ps, X1, Y1, head_text_stack)
        self.draw_chain_subscript(ps, X1, Y1)
        self.draw_original_sentence()

        if ps.find_me_elsewhere:
            self.do_not_repeat_information = False

        # Phrase structure geometry for daughters
        # Ignore structure conditions
        if (ps.label() == 'DP' or ps.label() == 'φP') and self.settings['image_parameter_ignore_internal_structure_of_DPs']:
            self.draw_node_label(ps, X1, Y1-52, [(ps.phonological_content(), 'PHONOLOGY')])
            return
        if ps.left:
            self.draw_left_line(ps, X1, Y1)
            self.show_in_window(ps.left)
        if ps.right and not ps.has_affix():
            self.draw_right_line(ps, X1, Y1)
            self.show_in_window(ps.right)

    # This functions generates a label stack (list of tuples) for a node
    def determine_label_stack(self, ps):

        # Internal functions
        def legitimate_label(ps):
            phon = ps.get_phonological_string()
            if '.' not in phon:
                return True

        # Main function
        label_stack = []    # Label_stack is a list of tuples (string, type) where _type_ is a code for font style
                            # and string is the label shown on the phrase structure tree
        # Major labels
        if self.settings['image_parameter_nolabels']:
            if ps.get_phonological_string():
                label_stack.append((ps.get_phonological_string(), 'PHONOLOGY'))
            else:
                label_stack.append(('X', 'LABEL'))
        else:
            label_stack.append((self.abbreviate_label(ps.label()), 'LABEL'))

        # Show words
        if not self.do_not_repeat_information:
            if self.settings['image_parameter_show_words'] and ps.primitive():
                if ps.get_phonological_string() != ps.label() and \
                        legitimate_label(ps):
                    label_stack.append((ps.get_phonological_string(), 'PHONOLOGY'))
                    if self.settings['image_parameter_show_glosses']:
                        if ps.gloss() != ps.label() and \
                                ps.gloss() != ps.get_phonological_string() and \
                                legitimate_label(ps):
                            label_stack.append((f"ʻ{ps.gloss()}ʼ", 'GLOSS'))

            # Show features (if any)
            if self.settings['show_features']:
                feature_str = ''
                features_included = set()
                for feature_pattern in self.settings['show_features']:
                    for i, lexical_feature in enumerate(ps.features):
                        if feature_pattern == lexical_feature:
                            lexical_feature_abbreviated = self.abbreviate_feature(lexical_feature, ps)
                            if lexical_feature_abbreviated:
                                if lexical_feature_abbreviated not in features_included:
                                    feature_str += f'{lexical_feature_abbreviated}'
                                    features_included.add(lexical_feature_abbreviated)
                                if len(feature_str) > 4:
                                    label_stack.append((feature_str, 'FEATURE'))
                                    feature_str = ''
                if feature_str != '':
                    label_stack.append((feature_str, 'FEATURE'))
                    feature_str = ''

        return label_stack

    def abbreviate_label(self, feature):
        if feature == 'Neg/fin':
            return 'Neg'
        if feature == 'Neg/finP':
            return 'NegP'
        if self.settings['image_parameter_show_φPs_as_DPs']:
            if feature == 'φ':
                return 'D'
            if feature == 'φP':
                return 'DP'
        if self.settings['image_parameter_show_φPs_as_NPs']:
            if feature == 'φP':
                return 'NP'
        return feature

    def abbreviate_feature(self, feature, ps):
        if 'PHI:' in feature:
            phi, typ, value = feature.split(':')
            if phi == 'iPHI':
                return '[iφ]'
            if phi == 'PHI' and value == '_':
                return '[φ‗]'
            if phi == 'PHI' and value != '_':
                return '[φ]'
        if feature == 'EF':
            return '[EPP]'
        if feature == 'ΦPF':
            return '[φ]'
        if feature == '!SELF:p':
            return '[p]'
        if feature == '!SELF:Φ':
            return '[Φ]'
        if feature == 'OP:Q':
            return '[Q]'
        if 'COMP:φ' in feature or 'SPEC:φ' in feature and not ps.check({'EF'}):
            return '[θ]'
        return f'[{feature}]'

    def draw_node_label(self, ps, X1, Y1, label_stack):
        line_position = -15
        if self.nearby(X1, Y1+12, self.mouse_position_x, self.mouse_position_y):
            self.mouse_over_node = ps

        for i, (label, style) in enumerate(label_stack):
            if style == 'LABEL':
                font_size = 20 * self.scale
            else:
                font_size = 15 * self.scale
            if style == 'FEATURE':
                font_size = 13 * self.scale
                line_space = 0.8
            else:
                line_space = 1
            if style == 'PHONOLOGY':
                italics_style = True
            else:
                italics_style = False
            label_ = pyglet.text.Label(label,
                                      font_name='Times New Roman',
                                      font_size=font_size,
                                      italic=italics_style,
                                      x=X1, y=Y1 + 12 - line_position,
                                      anchor_x='center', anchor_y='center',
                                      color=(50, 50, 50, 255))
            label_.draw()
            line_position = line_position + (25 * line_space * self.scale)

    def draw_right_line(self, ps, X1, Y1):
        X2 = self.x_offset + ps.right.x * self.x_grid
        Y2 = self.y_offset + ps.right.y * self.y_grid + (self.y_grid - self.x_grid)
        line = shapes.Line(X1, Y1, X2, Y2, width=2, color=(50, 50, 50))
        # Adjuncts are marked by double line
        if ps.right.adjunct and self.settings['image_parameter_mark_adjuncts']:
            line2 = shapes.Line(X1 + (5 * self.scale), Y1, X2 + (5 * self.scale), Y2, width=1, color=(50, 50, 50))
            line2.draw()
        line.draw()

    def draw_left_line(self, ps, X1, Y1):
        X2 = self.x_offset + ps.left.x * self.x_grid
        Y2 = self.y_offset + ps.left.y * self.y_grid + (self.y_grid - self.x_grid)
        line = shapes.Line(X1, Y1, X2, Y2, width=2, color=(50, 50, 50))
        # Adjuncts are marked by double line
        if ps.left.adjunct and self.settings['image_parameter_mark_adjuncts']:
            line2 = shapes.Line(X1 + (2 * self.scale), Y1 - 2 * self.scale, X2 + (2 * self.scale), Y2 - 2 * self.scale, width=2, color=(50, 50, 50))
            line2.draw()
        line.draw()

    def draw_vertical_line(self, ps, X1, Y1):
        X2 = X1
        Y2 = self.y_offset + ps.right.y * self.y_grid + (self.y_grid - self.x_grid)
        line = shapes.Line(X1, Y1 - (25 * self.scale), X2, Y2, width=2, color=(50, 50, 50, 255))
        line.draw()

    def draw_original_sentence(self):
        if self.settings['image_parameter_show_sentences']:
            label5 = pyglet.text.Label(self.visualizer.input_sentence_string,
                                       font_name='Times New Roman',
                                       font_size=20,
                                       italic=True,
                                       x=0, y=0,
                                       anchor_x='left', anchor_y='bottom')
            label5.draw()

    def draw_chain_subscript(self, ps, X1, Y1):
        if ps.identity and not ps.primitive():
            label = pyglet.text.Label(ps.identity, font_name='Times New Roman',
                                      font_size=(10 * self.scale),
                                      x=X1+(18 * self.scale),
                                      y=Y1+(5 * self.scale),
                                      anchor_x='center', anchor_y='center', color=(0, 0, 0, 255))
            label.draw()

    def nearby(self, x1, y1, x2, y2):
        if abs(x1-x2) < 15 and abs(y1-y2) < 15:
            return True
        else:
            return False

    def get_tree_size(self, ps, left, right, depth):
        if ps.x < left:
            left = ps.x
        if ps.x > right:
            right = ps.x
        if ps.y < depth:
            depth = ps.y
        if ps.left:
            left, right, depth = self.get_tree_size(ps.left, left, right, depth)
        if ps.right and not ps.has_affix():
            left, right, depth = self.get_tree_size(ps.right, left, right, depth)

        return left, right, depth

    def on_draw(self):
        self.clear()
        self.flip()
        self.background_image.blit(0, 0)

    def terminate(self, dt):
        self.show_in_window(self.phrase_structure)
        self.save_image()
        self.close()
