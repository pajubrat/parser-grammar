import tkinter as tk
from g_phrase_structure import GPhraseStructure

class PhraseStructureCanvas(tk.Canvas):
    """Canvas for drawing and manipulating phrase structure objects"""
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.focus_set()
        self.application = parent.application
        self.title = None
        self.derivational_index = None
        self.selected_objects = []   # selected (logical, phrase structure) objects
        self.selected_dependency = None
        self.parent = parent
        self.configure(scrollregion=(0, 0, 5000, 5000))
        self.ID_to_object = {}
        self.info = None
        self.label_style = {'label': ("Times New Roman", int(self.application.settings.retrieve('image_parameter_tsize'))),
                            'PFtrace': ("Times New Roman", int(self.application.settings.retrieve('image_parameter_tsize') / self.application.settings.retrieve('image_parameter_tshrink')), "italic", "overstrike"),
                            'PF': ("Times New Roman", int(self.application.settings.retrieve('image_parameter_tsize') / self.application.settings.retrieve('image_parameter_tshrink')), "italic"),
                            'gloss': ("Times New Roman", int(self.application.settings.retrieve('image_parameter_tsize') / self.application.settings.retrieve('image_parameter_tshrink'))),
                            'feature': ("Times New Roman", int(self.application.settings.retrieve('image_parameter_tsize') / self.application.settings.retrieve('image_parameter_tshrink'))),
                            'subscript': ("Times New Roman", int(self.application.settings.retrieve('image_parameter_tsize') * 0.5)),
                            'arrow_label': ("Times New Roman", int(self.application.settings.retrieve('image_parameter_tsize') * 0.75)),
                            'info': ("Courier", int(self.application.settings.retrieve('image_parameter_tsize') * 0.25))}
        self.bind('<Button-1>', self._on_mouse_click)
        self.bind('<Control-Button-1>', self._on_ctrl_mouse_click)
        self.bind('<KeyPress>', self._key_press)
        self.info_text = None

    def _key_press(self, event):
        if self.selected_objects:
            for gps in self.selected_objects:
                if event.keysym == 'Left':
                    gps.move_x(-0.5)
                if event.keysym == 'Right':
                    gps.move_x(0.5)
                if event.keysym == 'Down':
                    gps.move_y(+0.5)
                if event.keysym == 'Up':
                    gps.move_y(-0.5)
        self.parent.update_contents(False)

    def _on_mouse_click(self, *_):
        if self.find_withtag('current'):
            cur = self.find_withtag('current')[0]
            tag = self.gettags('current')[0]
            if tag == 'node':
                self.selected_objects = [self.ID_to_object[str(cur)]]
                self.selected_dependency = None
            if tag == 'dependency':
                self.selected_dependency = self.ID_to_object[str(cur)]
                self.selected_objects = []
        else:
            self.selected_objects = []
            self.selected_dependency = None
            self.selected_canvas_object = None
        self.parent.update_contents(False)

    def _on_ctrl_mouse_click(self, *_):
        if self.find_withtag('current'):
            if self.gettags('current')[0] == 'node':
                self.selected_objects.append(self.ID_to_object[str(self.find_withtag('current')[0])])
        else:
            self.selected_objects = []
        self.parent.update_contents(False)

    def _show_info(self, *_):
        if self.find_withtag('current'):
            selected = self.find_withtag('current')[0]
            tag = self.gettags('current')[0]
            if tag == 'node':
                gps = self.ID_to_object[str(selected)]
                if gps.zero_level():
                    self.parent.infoframe.config(text=gps.itext(), anchor='nw', justify='left', state='active', bg='yellow')
                    self.info = self.create_window((2200, 700), height=1200, width=500, window=self.parent.infoframe)
        else:
            self.parent.infoframe.config(state='hidden')

    def _hide_info(self, *_):
        self.delete(self.info)

    def update_status_bar(self, spx):
        self.parent.status_label.configure(text='Current image: (' + str(self.derivational_index) + ')  ' + self.title)

    def redraw(self, gps, recalculate=True, x_offset=0, y_offset=0):
        self.delete("all")
        if recalculate:
            gps.remove_overlap()
        spx, spy = self.parent.determine_position_of_highest_node(gps)
        self.draw_to_canvas(gps, spx + x_offset, spy + y_offset)

    def draw_to_canvas(self, gps, spx, spy):
        self.update_status_bar(spx)
        self.info_text = self.create_text((2000, 300), state='hidden')  # Show information about selected objects
        self.project_into_canvas(gps, spx, spy)
        self.draw_dependencies()

    def project_into_canvas(self, gps, spx, spy):
        """Projects the logical phase structure object into canvas"""
        X1 = spx + gps.x * self.application.settings.retrieve('image_parameter_grid')
        Y1 = spy + gps.y * self.application.settings.retrieve('image_parameter_y_grid')
        gps.X = X1  # Memorize the point on the canvas for later chain marking
        gps.Y = Y1
        gps.generate_label_stack()

        color = 'black'
        if gps in self.selected_objects:
            color = 'red'
        if gps.complex() and not gps.compressed_into_head:
            self.create_complex_node(gps, (X1, Y1), spx, spy, color)
        else:
            self.create_primitive_node(gps, X1, Y1, color)

    def create_complex_node(self, gps, M_const_coord, spx, spy, color='black'):

        L_const_coord = (spx + gps.left().x * self.application.settings.retrieve('image_parameter_grid'), spy + gps.left().y * self.application.settings.retrieve('image_parameter_y_grid'))
        R_const_coord = (spx + gps.right().x * self.application.settings.retrieve('image_parameter_grid'), spy + gps.right().y * self.application.settings.retrieve('image_parameter_y_grid'))

        # Create text holding the complex label (e.g., XP)
        ID = self.create_text(M_const_coord,
                              text=gps.label_stack[0][0],
                              fill=color,
                              activefill='red',
                              tag='node',
                              font=("Times New Roman", self.application.settings.retrieve('image_parameter_tsize')))

        self.ID_to_object[str(ID)] = gps
        gps.ID = ID
        self.tag_bind(ID, '<Enter>', self._show_info)
        self.tag_bind(ID, '<Leave>', self._hide_info)
        if gps.compressed:
            self.create_line(self.Y_frame(M_const_coord, 1), self.Y_frame(L_const_coord, 0.5), width=2, fill='black')
            self.create_line(self.Y_frame(M_const_coord, 1), self.Y_frame(R_const_coord, 0.5), width=2, fill='black')
            self.create_line(self.Y_frame(L_const_coord, 0.5), self.Y_frame(R_const_coord, 0.5), width=2, fill='black')
            Y_offset = self.application.settings.retrieve('image_parameter_tsize') * self.application.settings.retrieve('image_parameter_text_spacing')
            for i, label_item in enumerate(gps.label_stack):
                if label_item[1] != 'label':
                    text = self.feature_conversion_for_images(label_item)
                    self.create_text((M_const_coord[0], L_const_coord[1] + Y_offset), fill=color, activefill='red', tag='node', text=text, anchor='center', font=self.label_style[label_item[1]])
                    Y_offset += self.application.settings.retrieve('image_parameter_tsize') * self.application.settings.retrieve('image_parameter_text_spacing')
        else:
            self.draw_constituent_line(gps.left(), L_const_coord, M_const_coord)
            self.draw_constituent_line(gps.right(), R_const_coord, M_const_coord)
            self.project_into_canvas(gps.left(), spx, spy)
            self.project_into_canvas(gps.right(), spx, spy)

    def draw_constituent_line(self, gps, D_coord, M_coord):
        if self.application.settings.retrieve('image_parameter_adjuncts', False) and gps and gps.adjunct:
            self.draw_adjunct_line(M_coord, D_coord)
        else:
            self.create_line(self.Y_frame(M_coord, 1), self.Y_frame(D_coord, -1), width=2, fill='black')

    def draw_adjunct_line(self, M_coord, D_coord):
        MX = M_coord[0] - abs(D_coord[0] - M_coord[0]) / 5 - 18 / 2
        MY = M_coord[1] + abs(D_coord[1] - M_coord[1] + int(self.application.settings.retrieve('image_parameter_tsize') / self.application.settings.retrieve('image_parameter_label_padding'))) / 5 - 18 / 2
        self.create_oval(MX, MY, MX + 18, MY + 18, width=1, fill='black')
        self.create_line((MX + 18 / 2, MY + 18 / 2), self.Y_frame(D_coord, -1), width=2, fill='black')

    def Y_frame(self, coord, direction):
        return coord[0], coord[1] + direction * int(self.application.settings.retrieve('image_parameter_tsize') / self.application.settings.retrieve('image_parameter_label_padding'))

    def create_primitive_node(self, gps, X1, Y1, color='black'):
        Y_offset = 0    # Y_offset determines the lower boundary of the node + its label(s) when adding elements

        # Reproduce the head and all of its affixes
        for j, affix in enumerate(gps.get_affix_list(), start=1):
            # Do not reproduce affixes if blocked by settings
            if (affix.zero_level() and affix.copied and not self.application.settings.retrieve('image_parameter_covert_complex_heads', False)) or \
                    (j > 1 and not self.application.settings.retrieve('image_parameter_complex_heads', True)):
                break

            # Generate the label text (label + phonological exponent + gloss)
            for i, label_item in enumerate(affix.label_stack):
                text = self.feature_conversion_for_images(label_item)

                # Do not reproduce items if blocked by settings
                if (label_item[1] == 'gloss' and not self.application.settings.retrieve('image_parameter_glosses', True)) or \
                        (label_item[1] == 'PF' and not self.application.settings.retrieve('image_parameter_words', True)):
                    continue

                # Elliptic phonology
                if label_item[1] == 'PF' and gps.ellipsis:
                    style = 'PFtrace'
                else:
                    style = label_item[1]

                # Create text
                ID = self.create_text((X1, Y1 + Y_offset),
                                      fill=color,
                                      activefill='red',
                                      tag='node',
                                      text=text,
                                      anchor='center',
                                      font=self.label_style[style])
                # Subscript and superscript
                if label_item[1] == 'label' and affix.subscript:
                    self.create_text((X1 + (len(text)-1) * 15 + self.application.settings.retrieve('image_parameter_grid') / 6, Y1 + Y_offset + self.application.settings.retrieve('image_parameter_tsize') / 4),
                                     fill=color,
                                     activefill='red',
                                     tag='subscript',
                                     text=affix.subscript,
                                     anchor='w',
                                     font=self.label_style['subscript'])
                if label_item[1] == 'label' and affix.superscript:
                    self.create_text((X1 + (len(text)-1) * 15 + self.application.settings.retrieve('image_parameter_grid') / 6, Y1 - Y_offset - self.application.settings.retrieve('image_parameter_tsize') / 4),
                                     fill=color,
                                     activefill='red',
                                     tag='superscript',
                                     text=affix.superscript,
                                     anchor='w',
                                     font=self.label_style['subscript'])

                # Update the offset
                Y_offset += self.application.settings.retrieve('image_parameter_tsize') * self.application.settings.retrieve('image_parameter_text_spacing')

                # Add events to the first element (i == 0 when producing the label)
                if i == 0:
                    self.tag_bind(ID, '<Enter>', self._show_info)
                    self.tag_bind(ID, '<Leave>', self._hide_info)

                # Add the node to the mapping from nodes to affixes
                self.ID_to_object[str(ID)] = affix
                affix.ID = str(ID)

    def draw_dependencies(self):
        for dep in self.parent.inventory['dependencies']:
            if not {x for x in dep.source_gps.dominating_nodes() if x.compressed_into_head or x.compressed}:
                if not {x for x in dep.target_gps.dominating_nodes() if x.compressed_into_head or x.compressed}:
                    self.draw_dependency(dep)

    def feature_conversion_for_images(self, label_item):
        text = label_item[0]
        if self.application.settings.retrieve('image_parameter_DP_hypothesis', False):
            if text == 'φ':
                text = 'D'
            if text == 'φP':
                text = 'DP'
        if label_item[1] == 'feature':
            return '[' + text + ']'
        return text

    def get_lowered_Y_coord_for_arrow(self, dep):
        Y_offset = self.application.settings.retrieve('image_parameter_Y_offset_for_arrow')
        if self.calculate_Y_coord(dep.target_gps) > self.calculate_Y_coord(dep.source_gps):
            return self.calculate_Y_coord(dep.target_gps) + Y_offset + dep.Y_offset
        return self.calculate_Y_coord(dep.source_gps) + Y_offset + dep.Y_offset

    def draw_dependency(self, dep):
        coords = [(dep.source_gps.X + dep.spx + dep.source_X_offset, self.calculate_Y_coord(dep.source_gps) + dep.spy),
                  (dep.source_gps.X + dep.spx + dep.source_X_offset, self.get_lowered_Y_coord_for_arrow(dep)),
                  (dep.target_gps.X + dep.epx + dep.target_X_offset, self.get_lowered_Y_coord_for_arrow(dep)),
                  (dep.target_gps.X + dep.epx + dep.target_X_offset, self.calculate_Y_coord(dep.target_gps) + dep.epy)]
        if self.selected_dependency == dep:
            color = 'red'
        else:
            color = 'black'
        ID = self.create_line(*coords,
                              splinesteps=50,
                              dash=self.parent.line_style['arrow']['dash'],
                              arrow=dep.arrow_type,
                              activefill='red',
                              tag='dependency',
                              arrowshape=(2, 20, 20),
                              width=self.parent.line_style['arrow']['width'],
                              smooth=dep.smooth,
                              fill=color)
        if dep.label:
            mX = abs(dep.source_gps.X + dep.target_gps.X) / 2
            mY = self.get_lowered_Y_coord_for_arrow(dep) + 30
            self.create_text((mX, mY),
                             fill='black',
                             activefill='red',
                             tag='label_text',
                             text=dep.label,
                             anchor='c',
                             font=self.label_style['arrow_label'])
        self.ID_to_object[str(ID)] = dep

    def label_offset(self, gps):
        if gps.compressed:
            return gps.label_size() * self.application.settings.retrieve('image_parameter_tsize') * self.application.settings.retrieve('image_parameter_text_spacing')
        return self.application.settings.retrieve('image_parameter_text_spacing') * self.application.settings.retrieve('image_parameter_tsize') * gps.label_size()

    def calculate_Y_coord(self, gps):
        for x in gps.dominating_nodes():
            if x.compressed:
                return x.Y  # GPS is inside compressed node
        if gps.complex():
            return self.Y_coord_complex_node(gps)
        return self.Y_coord_zero_level(gps)

    def Y_coord_complex_node(self, gps):
        return gps.left().Y + self.label_offset(gps)

    def Y_coord_zero_level(self, gps):
        x = gps
        complex_head_Y_offset = 0
        while x.affix() and not x.affix().copied:
            complex_head_Y_offset += x.affix().label_size() * self.application.settings.retrieve('image_parameter_tsize')
            x = x.affix()
        return gps.Y + \
               (self.application.settings.retrieve('image_parameter_text_spacing') * self.application.settings.retrieve('image_parameter_tsize') * gps.label_size()) + \
               (self.application.settings.retrieve('image_parameter_text_spacing') * complex_head_Y_offset)
