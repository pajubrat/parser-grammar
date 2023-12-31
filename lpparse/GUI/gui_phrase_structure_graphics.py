import tkinter as tk

class PhraseStructureGraphics:
    def __init__(self, root_window, speaker_model_used_in_analysis, height=1000, width=1000):
        self.speaker_model_used_in_analysis = speaker_model_used_in_analysis
        self.GraphicsChildWindow = tk.Toplevel(root_window)
        self.GraphicsChildWindow.geometry(str(height)+'x'+str(width))
        self.GraphicsChildWindow.title("Phrase Structure Graphics")
        self.GraphicsChildWindow.focus()
        self.GraphicsChildWindow.grid()
        self.canvas = tk.Canvas(self.GraphicsChildWindow, width=1000, height=1000, background='white')
        self.ps = self.get_result_to_draw()
        self.canvas.grid()
        self.s = {'sp': (width/2, height/10), 'grid': 50}
        self.draw(self.ps)


    def get_result_to_draw(self):
        """Returns the phrase structure object to be drawn, None otherwise"""
        if self.speaker_model_used_in_analysis.result_list and self.speaker_model_used_in_analysis.result_list[0]:
            return self.speaker_model_used_in_analysis.result_list[0][0].top()

    def draw(self, ps):
        ps.x = 0
        ps.y = 0
        spx = self.s["sp"][0]
        spy = self.s["sp"][1]
        grid = self.s["grid"]
        self.project_into_logical_plane(ps)
        self.remove_overlap(ps)
        self.project_into_canvas(ps, spx, spy, grid)

    def project_into_logical_plane(self, ps):
        if ps.complex():
            ps.left.x = ps.x - 1
            ps.left.y = ps.y + 1
            self.project_into_logical_plane(ps.left)
            ps.right.x = ps.x + 1
            ps.right.y = ps.y + 1
            self.project_into_logical_plane(ps.right)

    def remove_overlap(self, ps):
        if ps.complex():
            self.remove_overlap(ps.left)
            self.remove_overlap(ps.right)
            overlap = 0
            LC_right_boundary = self.right_boundary(ps.left)
            RC_left_boundary = self.left_boundary(ps.right)
            for L_bp in LC_right_boundary:
                for R_bp in RC_left_boundary:
                    if L_bp[1] == R_bp[1]:
                        if L_bp[0] >= R_bp[0] and L_bp[0] - R_bp[0] >= overlap:
                            overlap = L_bp[0] - R_bp[0] + 1
            if overlap > 0:
                self.move_x(ps.left, -overlap/2)
                self.move_x(ps.right, overlap/2)

    def left_boundary(self, ps):
        boundary = set()
        boundary.add((ps.x, ps.y))
        if ps.complex():
            boundary = boundary | self.left_boundary(ps.left)
        return boundary

    def right_boundary(self, ps):
        boundary = set()
        boundary.add((ps.x, ps.y))
        if ps.complex():
            boundary = boundary | self.left_boundary(ps.right)
        return boundary

    def move_x(self, ps, amount):
        ps.x = ps.x + amount
        if ps.complex():
            self.move_x(ps.left, amount)
            self.move_x(ps.right, amount)

    def project_into_canvas(self, ps, spx, spy, grid):
        X1 = spx + ps.x * grid
        Y1 = spy + ps.y * grid
        if ps.complex():
            X2 = spx + ps.left.x * grid
            Y2 = spy + ps.left.y * grid
            X3 = spx + ps.right.x * grid
            Y3 = spy + ps.right.y * grid
            self.canvas.create_text((X1, Y1), text=ps.label(), font=("Times New Roman", 16))
            self.canvas.create_line((X1, Y1+10), (X2, Y2-10),  width=1, fill='black')
            self.project_into_canvas(ps.left, spx, spy, grid)
            self.canvas.create_line((X1, Y1+10), (X3, Y3-10), width=1, fill='black')
            self.project_into_canvas(ps.right, spx, spy, grid)
        if ps.primitive():
            self.primitive_label(ps, X1, Y1)

    def primitive_label(self, ps, X1, Y1):
        self.canvas.create_text((X1, Y1), text=ps.label(), anchor='center', font=("Times New Roman", 16))
        if ps.PF() != ps.label():
            self.canvas.create_text((X1, Y1+20), text=ps.PF(), anchor='center', font=("Times New Roman", 16))







