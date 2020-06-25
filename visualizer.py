#####################################################################
# phrase_structure_graphics
# Provides support for drawing the phrase structure objects visually
######################################################################
import pyglet
from pyglet.gl import GL_POINTS, GL_LINES, glBegin, glEnd, glVertex2f, gl, glLineWidth, glColor4f, glClearColor, \
    glClear, GL_COLOR_BUFFER_BIT

import phrase_structure
import time


# Definition for the visualizer
# Gets a phrase structure object as input
# file_identifier will be used in the filename for the image
class Visualizer:
    def __init__(self):
        self.file_identifier = ''
        self.lateral_stretch_needed = True
        self.stop_after_each_image = False
        pass

    # Definition for the drawing function
    def draw(self, ps):
        self.lateral_stretch_needed = True
        ps.x = 0
        ps.y = 0
        self.determine_plane_topology(ps)
        while self.lateral_stretch_needed:
            self.lateral_stretch_needed = False
            self.lateral_stretch(ps)
        win = ProduceGraphicOutput(ps, self.file_identifier, self.stop_after_each_image)
        pyglet.app.run()
        if not self.stop_after_each_image:
            win.close()

    def determine_plane_topology(self, ps):
            if ps.left_const:
                ps.left_const.x = ps.x - 1
                ps.left_const.y = ps.y - 1
                self.determine_plane_topology(ps.left_const)
            if ps.right_const:
                ps.right_const.x = ps.x + 1
                ps.right_const.y = ps.y - 1
                self.determine_plane_topology(ps.right_const)

    # Definition for lateral stretch for constituent N (should be the top node)
    # Examines each node N = [A B] in the phrase structure and makes sure that the subtrees A and B do not overlap
    def lateral_stretch(self, N):

        #
        # Internal functions
        #
        # Function 1. Returns the amount of lateral conflict observed for N
        def check_lateral_conflicts(N):

            # Retrieve the lateral positions as lists for both [A B] = N
            left_branch_laterals, right_branch_laterals = get_laterals(N)

            # The maximum overlap, which determines the amount of lateral stretching needed
            max_k = 1

            for count, left_lateral in enumerate(left_branch_laterals):
                # Stop if right branch has no more corresponding elements
                if len(right_branch_laterals) > count:
                    # If the current overlap is bigger than any other overlap detected thus far,
                    if right_branch_laterals[count] - left_lateral < max_k:
                        max_k = right_branch_laterals[count] - left_lateral
                else:
                    break

            # Return the maximum overlap, which we will use to move the branch
            return max_k

        # Function 2. Moves N laterally by k
        def move_laterally(k, N):
            N.x = N.x + k
            if N.is_complex():
                move_laterally(k, N.left_const)
                move_laterally(k, N.right_const)

        # Function 3. Returns the laterals in two lists
        def get_laterals(N):

            left_laterals = []
            right_laterals = []

            # Get laterals from the left branch
            iterator_ = N.left_const
            while iterator_.is_complex():
                left_laterals.append(iterator_.x)
                iterator_ = iterator_.right_const
            left_laterals.append(iterator_.x)

            # Get laterals from the right branch
            iterator_ = N.right_const
            while iterator_.is_complex():
                right_laterals.append(iterator_.x)
                iterator_ = iterator_.left_const
            right_laterals.append(iterator_.x)

            return left_laterals, right_laterals

        #
        # MAIN FUNCTION BEGINS HERE
        #
        # Primitive constituents do not need stretching
        if N.is_primitive():
            return
        else:
            # Checks if the the branches conflict and return the amount of lateral overlap
            # k = 0:    some N at some y occupy the same x (repair  k-1)
            # k < 0:    some N at some y overlap with the amount -k (repair (k-1)
            # k > 0:    the smallest space between some N at some y is +k (do not repair)
            k = check_lateral_conflicts(N)
            if k <= 0:
                # Move K laterally by the amount k
                move_laterally(k-1, N.left_const)
                self.lateral_stretch_needed = True

            # Check lateral stretch for the two constituents, recursively
            self.lateral_stretch(N.left_const)
            self.lateral_stretch(N.right_const)


# Definition for the output window behavior
class ProduceGraphicOutput(pyglet.window.Window):

    def __init__(self, ps, save_image_file_name, stop):

        # Define the grid
        self.x_grid = 50
        self.y_grid = 75

        # Define the margins
        self.margins = 35

        self.top_node_position = 0

        self.file_identifier = save_image_file_name

        self.stop_after_each_image = stop

        # Phrase structure that will be projected to the 2D window
        self.phrase_structure = ps

        # Determines how big the tree is and calculates appropriate window size
        left, right, depth = self.get_tree_size(ps, 0, 0, 0)
        width = (right - left) * self.x_grid + self.margins * 2
        height = abs(depth * self.y_grid) + self.margins * 2
        self.top_node_position = width/(abs(left) + abs(right)) * abs(left)
        pyglet.window.Window.__init__(self, width=width, height=height)
        glClearColor(1, 1, 1, 1)

    def on_draw(self):

        glClear(GL_COLOR_BUFFER_BIT)

        # Recursive projection function
        def project_into_plane(ps):

            # Top node position
            X1 = x_offset + ps.x * self.x_grid
            Y1 = y_offset + ps.y * self.y_grid

            # Get the label for ps
            head = ps.get_cats_string()

            # Create label for the node
            label = pyglet.text.Label(head,
                                      font_name='Times New Roman',
                                      font_size=20,
                                      x=X1, y=Y1 + 12,
                                      anchor_x='center', anchor_y='center',
                                      color=(1, 1, 1, 255))
            label.draw()

            # Add subscript if the phrase is a member of a chain
            subscript = ps.identity
            if subscript:
                label2 = pyglet.text.Label(subscript,
                                          font_name='Times New Roman',
                                          font_size=10,
                                          x=X1+18, y=Y1+5,
                                          anchor_x='center', anchor_y='center',
                                          color=(1, 1, 1, 255))
                label2.draw()

            # Left branch line
            if ps.left_const:

                X2 = x_offset + ps.left_const.x * self.x_grid
                Y2 = y_offset + ps.left_const.y * self.y_grid + (self.y_grid-self.x_grid)
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
                    glVertex2f(X1-5, Y1+1)
                    glVertex2f(X2-5, Y2+1)
                glEnd()
                project_into_plane(ps.left_const)

            # Right branch line
            if ps.right_const:
                X2 = x_offset + ps.right_const.x * self.x_grid
                Y2 = y_offset + ps.right_const.y * self.y_grid + (self.y_grid-self.x_grid)
                glBegin(GL_LINES)
                glVertex2f(X1, Y1)
                glVertex2f(X2, Y2)
                # Adjuncts are marked by double line
                if ps.right_const.adjunct:
                    glVertex2f(X1+5, Y1)
                    glVertex2f(X2+5, Y2)

                glEnd()
                project_into_plane(ps.right_const)
                if not self.stop_after_each_image:
                    pyglet.app.exit()

        #
        # Main function begins here
        #
        #
        x_offset = self.top_node_position
        y_offset = self.height - 50

        # Create the image
        project_into_plane(self.phrase_structure)

        # Save to file
        pyglet.image.get_buffer_manager().get_color_buffer().save(self.file_identifier)

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





