#####################################################################
# phrase_structure_graphics
# Provides support for drawing the phrase structure objects visually
######################################################################
import pyglet
import pyglet.window.key
from pyglet import shapes, window
from pyglet.gl import GL_POINTS, GL_LINES, glBegin, glEnd, glVertex2f, gl, glLineWidth, glColor4f, glClearColor, \
    glClear, GL_COLOR_BUFFER_BIT

import phrase_structure
import time

# Definition for the visualizer
class Visualizer:
    def __init__(self):
        self.file_identifier = ''
        self.new_lateral_stretch_needed = True
        self.stop_after_each_image = False
        self.image_output = False
        self.show_words = False
        self.show_glosses = False
        self.input_sentence_string = ''
        self.show_sentences = False
        self.nolabels = False
        self.spellout = False
        self.show_tails = False
        self.show_cases = False
        self.save_image_file_name = ''
        self.input_sentence_string = ''

    # Definition for the drawing function
    def draw(self, ps):
        self.project_to_plane(ps)
        win = ProduceGraphicOutput(ps, self)
        pyglet.app.run()
        if not self.stop_after_each_image:
            win.close()

    def project_to_plane(self, ps):
        ps.x = 0
        ps.y = 0
        self.determine_plane_topology(ps)
        self.remove_overlaps(ps)

    def remove_overlaps(self, ps):
        self.new_lateral_stretch_needed = True
        while self.new_lateral_stretch_needed:
            self.new_lateral_stretch_needed = False
            self.lateral_stretch(ps)

    def determine_plane_topology(self, ps):
            if ps.left_const:
                ps.left_const.x = ps.x - 1
                ps.left_const.y = ps.y - 1
                self.determine_plane_topology(ps.left_const)
            if ps.right_const:
                ps.right_const.x = ps.x + 1
                ps.right_const.y = ps.y - 1
                self.determine_plane_topology(ps.right_const)

    def move_node(self, dx, dy, N):
        N.x = N.x + dx
        N.y = N.y + dy
        if N.is_complex_head():
            self.move_node(dx, dy, N.right_const)
        elif N.is_complex():
            self.move_node(dx, dy, N.left_const)
            self.move_node(dx, dy, N.right_const)

    # Definition for lateral stretch for constituent N (should be the top node)
    def lateral_stretch(self, N):

        # Internal functions
        def check_lateral_conflicts(N):
            left_branch_coordinates = get_coordinate_set(N.left_const, set())
            right_branch_coordinates = get_coordinate_set(N.right_const, set())
            max_overlap = 1
            for coordinates_from_left in left_branch_coordinates:
                for coordinates_from_right in right_branch_coordinates:
                    if coordinates_from_left[1] == coordinates_from_right[1]:
                        if coordinates_from_right[0] - coordinates_from_left[0] < max_overlap:
                            max_overlap = coordinates_from_right[0] - coordinates_from_left[0]

            return max_overlap

        def get_coordinate_set(N, coordinate_set):
            coordinate_set.add((N.x, N.y))
            if N.is_complex():
                coordinate_set |= get_coordinate_set(N.left_const, coordinate_set)
                coordinate_set |= get_coordinate_set(N.right_const, coordinate_set)
            return coordinate_set

        # ---------------------------------- Main function -------------------------------------------------#
        if N.is_primitive():
            if N.is_complex_head() and self.spellout:
                self.move_node(-1, 0, N.right_const)
                self.lateral_stretch(N.right_const)
            return
        else:
            # Checks if the the branches conflict and return the amount of lateral overlap
            # k = 0:    some N at some y occupy the same x (repair  k-1)
            # k < 0:    some N at some y overlap with the amount -k (repair (k-1)
            # k > 0:    the smallest space between some N at some y is +k (do not repair)
            k = check_lateral_conflicts(N)
            if k <= 0:
                # Move K laterally by the amount
                self.move_node(k-1, 0, N.left_const)
                self.new_lateral_stretch_needed = True

            # Check lateral stretch for the two constituents, recursively
            self.lateral_stretch(N.left_const)
            self.lateral_stretch(N.right_const)

# Definition for the output window behavior
class ProduceGraphicOutput(pyglet.window.Window):
    def __init__(self,
                 ps,
                 visualizer):

        self.visualizer = visualizer
        # Define the grid
        self.x_grid = 50
        self.y_grid = 75
        # offset
        self.x_offset = 0
        self.y_offset = 0
        # Define the margins
        self.margins = 100
        self.top_node_position = 0
        self.file_identifier = self.visualizer.file_identifier
        self.mouse_position_x = 0
        self.mouse_position_y = 0
        self.mouse_over_node = None
        self.selected_node = None
        # Phrase structure that will be projected to the 2D window
        self.phrase_structure = ps
        if self.visualizer.show_words:
            self.margins += 10
        if self.visualizer.nolabels and not self.show_words:
            self.margins += 10
        if self.visualizer.show_glosses:
            self.margins += 10

        width, height = self.determine_window_size(ps)
        if self.visualizer.stop_after_each_image:
            visible = True
        else:
            visible = True
        pyglet.window.Window.__init__(self, visible=visible, width=int(width), height=int(height), resizable=True, caption=self.visualizer.input_sentence_string)
        glClearColor(1, 1, 1, 1)

    def determine_window_size(self, ps):
        left, right, depth = self.get_tree_size(ps, 0, 0, 0)
        width = (right - left) * self.x_grid + self.margins
        height = abs(depth * self.y_grid) + self.margins
        self.top_node_position = width / (abs(left) + abs(right)) * abs(left)
        self.x_offset = self.top_node_position  # Position of the highest node
        self.y_offset = height - 30 # How much extra room above the highest node (for highest label)
        return width, height

    def on_key_press(self, symbol, modifiers):
        move_x = 0
        move_y = 0
        if symbol == pyglet.window.key.S:
            self.save_image()
            print('Image saved.')
            return
        elif symbol == pyglet.window.key.R:
            if self.selected_node:
                self.visualizer.project_to_plane(self.selected_node.top())
        elif symbol == 65361 and self.selected_node:
            move_x = - 0.5
        elif symbol == 65363:
            move_x = + 0.5
        elif symbol == 65362:
            move_y = + 0.5
        elif symbol == 65364:
            move_y = - 0.5

        if move_x != 0 or move_y != 0:
            self.visualizer.move_node(move_x, move_y, self.selected_node)
            self.visualizer.lateral_stretch(self.selected_node.top())

    def on_draw(self):
        glClear(GL_COLOR_BUFFER_BIT)
        self.mouse_over_node = None
        self.show_in_window(self.phrase_structure)
        if not self.visualizer.stop_after_each_image:
            self.save_image()

    def save_image(self):
        pyglet.image.get_buffer_manager().get_color_buffer().save(self.visualizer.file_identifier)

    def update(self):
        pass

    def on_mouse_motion(self, x, y, button, modifiers):
        self.mouse_position_x = x
        self.mouse_position_y = y

    def on_mouse_press(self, x, y, button, modifiers):
        if self.mouse_over_node:
            self.selected_node = self.mouse_over_node
        else:
            self.selected_node = None

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        move_x = 0
        move_y = 0
        if self.selected_node:
            if buttons & pyglet.window.mouse.LEFT:
                move_x = dx/self.x_grid
                move_y = dy/self.y_grid
            if move_x != 0 or move_y != 0:
                self.visualizer.move_node(move_x, move_y, self.selected_node)
                self.visualizer.lateral_stretch(self.selected_node.top())

    # Recursive projection function
    def show_in_window(self, ps):

        # Mother position
        X1 = self.x_offset + ps.x * self.x_grid
        Y1 = self.y_offset + ps.y * self.y_grid

        if X1 < 0:
            X1 = 0
        if Y1 < 0:
            Y1 = 0

        # Textual
        head_text = self.determine_label_stack(ps)
        self.draw_node_label(ps, X1, Y1, head_text)
        self.draw_chain_subscript(ps, X1, Y1)
        self.draw_original_sentence()
        self.draw_selection()

        # Phrase structure geometry for daughters
        if ps.is_complex_head():
            self.draw_vertical_line(ps, X1, Y1)
            self.show_in_window(ps.right_const)
        else:
            if ps.left_const:
                self.draw_left_line(ps, X1, Y1)
                self.show_in_window(ps.left_const)
            if ps.right_const:
                self.draw_right_line(ps, X1, Y1)
                self.show_in_window(ps.right_const)
                if not self.visualizer.stop_after_each_image:
                    pyglet.app.exit()

    def draw_selection(self):
        if self.selected_node:
            x = self.x_offset + self.selected_node.x * self.x_grid
            y = self.y_offset + self.selected_node.y * self.y_grid + (self.y_grid - self.x_grid)
            glColor4f(0, 0, 0, 0)
            circle = shapes.Circle(x=x-1, y=y-14, radius=30, color=(50, 50, 50))
            circle.opacity = 2
            circle.draw()

    def determine_label_stack(self, ps):
        if self.visualizer.nolabels:
            if ps.get_pf():
                label_stack = ps.get_pf()
            else:
                label_stack = 'X'
        else:
            label_stack = ps.get_cats_string()

        if self.visualizer.show_words and ps.is_primitive():
            if ps.get_pf() != ps.get_cats_string():
                label_stack = label_stack + '§' + ps.get_pf()
                if self.visualizer.show_glosses:
                    if ps.gloss() != ps.get_cats_string() and ps.gloss() != ps.get_pf():
                        label_stack = label_stack + '§' + '\'' + ps.gloss() + '\''

        if self.visualizer.show_cases and ps.is_primitive():
            if ps.get_case():
                label_stack = label_stack + '§' + str(ps.get_case())

        return label_stack


    def draw_right_line(self, ps, X1, Y1):
        X2 = self.x_offset + ps.right_const.x * self.x_grid
        Y2 = self.y_offset + ps.right_const.y * self.y_grid + (self.y_grid - self.x_grid)
        glBegin(GL_LINES)
        glVertex2f(X1, Y1)
        glVertex2f(X2, Y2)
        # Adjuncts are marked by double line
        if ps.right_const.adjunct:
            glVertex2f(X1 + 5, Y1)
            glVertex2f(X2 + 5, Y2)

        glEnd()

    def draw_left_line(self, ps, X1, Y1):
        X2 = self.x_offset + ps.left_const.x * self.x_grid
        Y2 = self.y_offset + ps.left_const.y * self.y_grid + (self.y_grid - self.x_grid)
        if abs(ps.x - ps.left_const.x) > 1:
            glLineWidth(1)
        else:
            glLineWidth(2)
        glColor4f(0, 0, 0, 0)
        glBegin(GL_LINES)
        glVertex2f(X1, Y1)
        glVertex2f(X2, Y2)
        # Adjuncts are marked by double line
        if ps.left_const.adjunct:
            glVertex2f(X1 - 5, Y1 + 1)
            glVertex2f(X2 - 5, Y2 + 1)
        glEnd()

    def draw_vertical_line(self, ps, X1, Y1):
        X2 = X1
        Y2 = self.y_offset + ps.right_const.y * self.y_grid + (self.y_grid - self.x_grid)
        glBegin(GL_LINES)
        glVertex2f(X1, Y1 - 25)
        glVertex2f(X2, Y2)
        glEnd()

    def draw_original_sentence(self):
        if self.visualizer.show_sentences:
            label5 = pyglet.text.Label(self.visualizer.input_sentence_string,
                                       font_name='Times New Roman',
                                       font_size=20,
                                       italic = True,
                                       x=0, y=0,
                                       anchor_x='left', anchor_y='bottom',
                                       color=(1, 1, 1, 255))
            label5.draw()


    def draw_chain_subscript(self, ps, X1, Y1):
        if ps.identity:
            label = pyglet.text.Label(ps.identity, font_name='Times New Roman', font_size=10, x=X1+18, y=Y1+5,
                                          anchor_x='center', anchor_y='center',
                                          color=(1, 1, 1, 255))
            label.draw()

    def nearby(self, x1, y1, x2, y2):
        if abs(x1-x2) < 15 and abs(y1-y2) < 15:
            return True
        else:
            return False

    def draw_node_label(self, ps, X1, Y1, head_text):
        label_stack = head_text.split('§')
        line_position = 0
        if self.nearby(X1, Y1+12, self.mouse_position_x, self.mouse_position_y):
            bold = True
            self.mouse_over_node = ps
        else:
            bold = False

        for i, label in enumerate(label_stack):
            label_ = pyglet.text.Label(label,
                                      font_name='Times New Roman',
                                      font_size=20,
                                      bold=bold,
                                      x=X1, y=Y1 + 12 - line_position,
                                      anchor_x='center', anchor_y='center',
                                      color=(1, 1, 1, 255))
            line_position = line_position + 25
            label_.draw()

    def get_tree_size(self, ps, left, right, depth):
        if ps.x < left:
            left = ps.x
        if ps.x > right:
            right = ps.x
        if ps.y < depth:
            depth = ps.y
        if ps.left_const:
            left, right, depth = self.get_tree_size(ps.left_const, left, right, depth)
        if ps.right_const:
            left, right, depth = self.get_tree_size(ps.right_const, left, right, depth)

        return left, right, depth