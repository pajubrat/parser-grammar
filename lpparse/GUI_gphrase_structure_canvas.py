import tkinter as tk


class PhraseStructureCanvas(tk.Canvas):
    """Canvas for drawing and manipulating phrase structure objects"""
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.focus_set()
        self.application = parent.application
        self.title = None
        self.selected_objects = []   # selected (logical, phrase structure) objects
        self.selected_dependency = None
        self.parent = parent
        self.configure(scrollregion=(0, 0, 5000, 5000))
        self.ID_to_object = {}
        self.scaling_factor = 1
        self.info = None
        self.cursor = None
        self.feature_mappings = self.create_feature_mappings()

        # Text types for images

        self.label_style = {'label': (self.application.settings.retrieve('image_parameter_font', 'Times New Roman'), int(self.application.settings.retrieve('image_parameter_tsize'))),
                            'PFtrace': (self.application.settings.retrieve('image_parameter_font', 'Times New Roman'), int(self.application.settings.retrieve('image_parameter_tsize') / self.application.settings.retrieve('image_parameter_tshrink')), "italic", "overstrike"),
                            'PF': (self.application.settings.retrieve('image_parameter_font', 'Times New Roman'), int(self.application.settings.retrieve('image_parameter_tsize') / self.application.settings.retrieve('image_parameter_tshrink')), "italic"),
                            'gloss': (self.application.settings.retrieve('image_parameter_font', 'Times New Roman'), int(self.application.settings.retrieve('image_parameter_tsize') / self.application.settings.retrieve('image_parameter_tshrink'))),
                            'feature': (self.application.settings.retrieve('image_parameter_font', 'Times New Roman'), 0.8 * int(self.application.settings.retrieve('image_parameter_tsize') / self.application.settings.retrieve('image_parameter_tshrink'))),
                            'subscript': (self.application.settings.retrieve('image_parameter_font', 'Times New Roman'), int(self.application.settings.retrieve('image_parameter_tsize') * 0.5)),
                            'arrow_label': (self.application.settings.retrieve('image_parameter_font', 'Times New Roman'), int(self.application.settings.retrieve('image_parameter_tsize') * 0.75)),
                            'info': ("Courier", int(self.application.settings.retrieve('image_parameter_tsize') * 0.25))}
        self.bind('<Button-1>', self._on_mouse_click)
        self.bind('<Button-3>', self._on_right_click)
        self.bind('<Control-Button-1>', self._on_ctrl_mouse_click)
        self.bind('<KeyPress>', self._key_press)
        self.info_text = None

    def create_feature_mappings(self):

        # Creates feature mappings which transform features present in the phrase structure trees into
        # feature abbreviations as set up by the user in the study configuration file

        if self.application.settings.retrieve('image_parameter_visualization', set()):
            mappings = [item.strip().split('>') for item in self.application.settings.retrieve('image_parameter_visualization').split(';')]
            return {key: value for key, value in mappings}

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

    def _on_right_click(self, *_):
        if self.find_withtag('current'):
            cur = self.find_withtag('current')[0]
            tag = self.gettags('current')[0]
            if tag == 'node':
                self.selected_objects = [self.ID_to_object[str(cur)]]
                if self.selected_objects:
                    self.parent.inspect()

    def _on_mouse_click(self, *_):
        if self.parent.inspect_window:              #   If there is a inspector window,
            self.parent.inspect_window.destroy()    #   it will be destroyed
        if self.find_withtag('current'):
            cur = self.find_withtag('current')[0]
            tag = self.gettags('current')[0]
            if tag == 'node':
                self.addtag_withtag('selected', tk.CURRENT)
                self.selected_objects = [self.ID_to_object[str(cur)]]
                self.selected_dependency = None
                self.bind('<Motion>', self.drag_and_drop_node)
                self.bind('<ButtonRelease-1>', self.deselect)
            if tag == 'dependency':
                self.selected_dependency = self.ID_to_object[str(cur)]
                self.selected_objects = []
        else:
            self.selected_objects = []
            self.selected_dependency = None
            self.selected_canvas_object = None
            self.parent.update_contents(False)

    def deselect(self, event):
        self.unbind('<Motion>')
        self.dtag('selected')
        self.parent.update_contents(False)

    def drag_and_drop_node(self, event):
        x, y = event.x, event.y
        xc, yc = self.coords('selected')
        if x - xc > self.application.settings.retrieve('image_parameter_grid', 150) / 2:
            self.parent.move_right()
        if xc - x > self.application.settings.retrieve('image_parameter_grid', 150) / 2:
            self.parent.move_left()
        if y - yc > self.application.settings.retrieve('image_parameter_y_grid', 180) / 2:
            self.parent.move_down()
        if yc - y > self.application.settings.retrieve('image_parameter_y_grid', 180) / 2:
            self.parent.move_up()

    def _on_ctrl_mouse_click(self, *_):
        if self.find_withtag('current'):
            if self.gettags('current')[0] == 'node':
                self.selected_objects.append(self.ID_to_object[str(self.find_withtag('current')[0])])
        else:
            self.selected_objects = []
        self.parent.update_contents(False)

    def focus_item(self, *_):
        if self.find_withtag('current'):
            selected = self.find_withtag('current')[0]
            x1, y1 = self.coords(selected)
            self.coords(self.cursor, x1 - 50, y1 - 50, x1 + 50, y1 + 50)

    def unfocus_item(self, *_):
        if not self.selected_objects:
            self.coords(self.cursor, 0, 0, 0, 0)

    def create_cursor(self):
        self.cursor = self.create_rectangle(0, 0, 0, 0, outline='#DDDDDD')

    def update_status_bar(self, spx):
        if self.parent.index_of_analysis_shown and self.title:
            self.parent.status_label.configure(text='Current image: (' + str(self.parent.index_of_analysis_shown) + ')  ' + self.title)
        else:
            self.parent.status_label.configure(text='Current image:')

    def redraw(self, gps, recalculate=True, x_offset=0, y_offset=0):
        self.delete("all")
        if recalculate:
            gps.remove_overlap()
        spx, spy = self.parent.determine_position_of_highest_node(gps)
        self.create_cursor()
        self.draw_to_canvas(gps, spx + x_offset, spy + y_offset)

    def draw_to_canvas(self, gps, spx, spy):
        """
        Draws all elements to the canvas
        """

        # Status bar update

        self.update_status_bar(spx)

        # Project the phrase structure onto canvas

        self.project_into_canvas(gps, spx, spy)

        # Draws dependencies between nodes

        self.draw_dependencies()

        # Scales everything based on zoom

        self.scale("all", 0, 0, self.scaling_factor, self.scaling_factor)

    def project_into_canvas(self, gps, spx, spy):
        """Projects the logical phase structure object into canvas"""
        X1 = spx + gps.x * self.application.settings.retrieve('image_parameter_grid')
        Y1 = spy + gps.y * self.application.settings.retrieve('image_parameter_y_grid')
        gps.X = X1  # Memorize the point on the canvas for later chain marking
        gps.Y = Y1
        gps.generate_label_stack()

        if gps.complex():
            color = 'black'
            if gps in self.selected_objects:
                color = 'red'
            self.create_complex_node(gps, (X1, Y1), spx, spy, color)
        else:
            self.create_primitive_node(gps, X1, Y1)

        if gps.highlight:
            self.highlight(gps, X1, Y1)

    def highlight(self, gps, X, Y):
        if gps.M():
            if gps.is_R():
                self.create_line(X + 80, Y - 80, X + 30, Y - 30, arrowshape=(20, 20, 10), arrow='last', width=10)
            if gps.is_L():
                self.create_line(X - 80, Y - 80, X - 30, Y - 30, arrowshape=(20, 20, 10), arrow='last', width=10)
        else:
            self.create_line(X + 100, Y, X + 50, Y, arrowshape=(20, 20, 10), arrow='last', width=10)

    def create_primitive_node(self, gps, X1, Y1):
        Y_offset = 0    # Y_offset determines the lower boundary of the node + its label(s) when adding elements

        # Reproduce the head and all of its affixes

        for j, affix in enumerate(gps.affixes(), start=1):

            color = 'black'
            if affix in self.selected_objects:
                color = 'red'

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

                # Modify label font size based on scaling factor

                scaled_font = list(self.label_style[style])
                scaled_font[1] = int(self.label_style[style][1] * self.scaling_factor)
                scaled_font = tuple(scaled_font)

                # Create text

                if label_item[1] == 'label' and label_item[0].strip() == '':
                    text = '??'
                    color = 'white'

                ID = self.create_text((X1, Y1 + Y_offset),
                                      fill=color,
                                      activefill='grey',
                                      tag='node',
                                      text=text,
                                      anchor='center',
                                      font=scaled_font)

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
                    self.tag_bind(ID, '<Enter>', self.focus_item)
                    self.tag_bind(ID, '<Leave>', self.unfocus_item)

                # Add the node to the mapping from nodes to affixes

                self.ID_to_object[str(ID)] = affix
                affix.ID = str(ID)
                if gps in self.selected_objects:
                    self.addtag_withtag('selected', ID)

    def create_complex_node(self, gps, M_const_coord, spx, spy, color='black'):

        L_const_coord = (spx + gps.L().x * self.application.settings.retrieve('image_parameter_grid'),
                         spy + gps.L().y * self.application.settings.retrieve('image_parameter_y_grid'))
        R_const_coord = (spx + gps.R().x * self.application.settings.retrieve('image_parameter_grid'),
                         spy + gps.R().y * self.application.settings.retrieve('image_parameter_y_grid'))

        # Create text holding the complex label (e.g., XP)

        text = self.feature_conversion_for_images(gps.label_stack[0])
        ID = self.create_text(M_const_coord,
                              text=text,
                              fill=color,
                              activefill='grey',
                              tag='node',
                              font=(self.label_style['label'][0],
                                    int(self.label_style['label'][1] * self.scaling_factor)))

        self.ID_to_object[str(ID)] = gps
        gps.ID = ID
        self.tag_bind(ID, '<Enter>', self.focus_item)
        self.tag_bind(ID, '<Leave>', self.unfocus_item)
        if gps in self.selected_objects:
            self.addtag_withtag('selected', ID)

        # Phrasal zero-level node

        if gps.shrink:
            Y_offset = self.application.settings.retrieve('image_parameter_tsize') * self.application.settings.retrieve('image_parameter_text_spacing')
            for i, label_item in enumerate(gps.label_stack):

                # Font scaling

                scaled_font = list(self.label_style[label_item[1]])
                scaled_font[1] = int(self.label_style[label_item[1]][1] * self.scaling_factor)
                scaled_font = tuple(scaled_font)

                if label_item[1] != 'label':
                    text = self.feature_conversion_for_images(label_item)
                    self.create_text((spx + gps.x * self.application.settings.retrieve('image_parameter_grid'), spy + gps.y * self.application.settings.retrieve('image_parameter_y_grid') + Y_offset),
                                     fill=color,
                                     activefill='red',
                                     tag='node',
                                     text=text,
                                     anchor='center',
                                     font=scaled_font)
                    Y_offset += self.application.settings.retrieve('image_parameter_tsize') * self.application.settings.retrieve('image_parameter_text_spacing')

            return

        # Compressed node

        if gps.compressed:

            self.create_line(self.Y_frame(M_const_coord, 1), self.Y_frame(L_const_coord, 0.5), width=2, fill='black')
            self.create_line(self.Y_frame(M_const_coord, 1), self.Y_frame(R_const_coord, 0.5), width=2, fill='black')
            self.create_line(self.Y_frame(L_const_coord, 0.5), self.Y_frame(R_const_coord, 0.5), width=2, fill='black')
            Y_offset = self.application.settings.retrieve('image_parameter_tsize') * self.application.settings.retrieve('image_parameter_text_spacing')

            # Create text items from label stack

            for i, label_item in enumerate(gps.label_stack):

                # Font scaling

                scaled_font = list(self.label_style[label_item[1]])
                scaled_font[1] = int(self.label_style[label_item[1]][1] * self.scaling_factor)
                scaled_font = tuple(scaled_font)

                if label_item[1] != 'label':
                    text = self.feature_conversion_for_images(label_item)
                    self.create_text((M_const_coord[0], L_const_coord[1] + Y_offset),
                                     fill=color,
                                     activefill='red',
                                     tag='node',
                                     text=text,
                                     anchor='center',
                                     font=scaled_font)
                    Y_offset += self.application.settings.retrieve('image_parameter_tsize') * self.application.settings.retrieve('image_parameter_text_spacing')
        else:
            self.draw_constituent_line(gps.L(), L_const_coord, M_const_coord)
            self.draw_constituent_line(gps.R(), R_const_coord, M_const_coord)
            self.project_into_canvas(gps.L(), spx, spy)
            self.project_into_canvas(gps.R(), spx, spy)

    def draw_constituent_line(self, gps, D_coord, M_coord):
        if self.application.settings.retrieve('image_parameter_adjuncts', False) and gps and gps.adjunct:
            self.draw_adjunct_line(M_coord, D_coord)
        else:
            self.create_line(self.Y_frame(M_coord, 1), self.Y_frame(D_coord, -1), width=2, fill='black')
        self.add_special_constituent_marking(gps, self.Y_frame(M_coord, 1), self.Y_frame(D_coord, -1))

    def add_special_constituent_marking(self, gps, M_coord, D_coord):

        # Find middle point

        mx = M_coord[0] + (D_coord[0] - M_coord[0])/2
        my = M_coord[1] + (D_coord[1] - M_coord[1])/2

        # Add special markings at the middle point

        if gps.is_L():
            if 'cut' in gps.M().special_left_constituent_marking:
                self.create_line((mx - 15, my - 25, mx + 15, my + 25), fill='black', width=4)
                self.create_line((mx - 5, my - 35, mx + 25, my + 15), fill='black', width=4)
            if 'ball' in gps.M().special_left_constituent_marking:
                self.create_oval((mx - 10, my - 10, mx + 10, my + 10), fill='black')
        if gps.is_R():
            if 'cut' in gps.M().special_right_constituent_marking:
                self.create_line((mx + 15, my - 25, mx - 15, my + 25), fill='black', width=4)
                self.create_line((mx + 5, my - 35, mx - 25, my + 15), fill='black', width=4)
            if 'ball' in gps.M().special_right_constituent_marking:
                self.create_oval((mx-10, my-10, mx+10, my+10), fill='black')

    def draw_adjunct_line(self, M_coord, D_coord):
        closeness_to_mother = 10     # the larger the number, the closer
        size_of_circle = 18         # in pixels
        if D_coord[0] > M_coord[0]:
            MX = M_coord[0] + (D_coord[0] - M_coord[0]) / closeness_to_mother - size_of_circle/2
        else:
            MX = M_coord[0] - (M_coord[0] - D_coord[0]) / closeness_to_mother - size_of_circle/2
        MY = self.Y_frame(M_coord, 1)[1]
        self.create_oval(MX, MY, MX + size_of_circle, MY + size_of_circle, width=1, fill='black')
        self.create_line((MX + size_of_circle/2, MY + size_of_circle/2), self.Y_frame(D_coord, -1), width=2, fill='black')

    def Y_frame(self, coord, direction):
        return coord[0], coord[1] + direction * int(self.application.settings.retrieve('image_parameter_tsize') / self.application.settings.retrieve('image_parameter_label_padding'))

    def draw_dependencies(self):
        for dep in self.parent.inventory['dependencies']:

            # Do not draw dependencies if dominating nodes have been compressed for the source

            if not {x for x in dep.source_gps.dominating_nodes() if x.compressed}:

                # Do not draw dependencies if dominating nodes have been compressed for the target

                if not {x for x in dep.target_gps.dominating_nodes() if x.compressed}:

                    # Draw the dependency

                    self.draw_dependency(dep)

    def feature_conversion_for_images(self, label_item):
        text = label_item[0]
        if self.application.settings.retrieve('image_parameter_DP_hypothesis', False):
            if text == 'φ':
                return 'D'
            if text == 'φP':
                return 'DP'
        if label_item[1] == 'feature':
            if len(self.feature_mappings) > 0:
                text = self.feature_mappings.get(text, text)
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

        # Change the color if the dependency has been selected by the user

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

        # Value for compressed phrase

        for x in gps.dominating_nodes():
            if x.compressed:
                return x.Y

        # Value for shrink phrase

        if gps.shrink:
            return self.Y_coord_zero_level(gps)

        # Value for complex node

        if gps.complex():
            return self.Y_coord_complex_node(gps)

        return self.Y_coord_zero_level(gps)

    def Y_coord_complex_node(self, gps):
        return gps.L().Y + self.label_offset(gps)

    def Y_coord_zero_level(self, gps):
        x = gps
        complex_head_Y_offset = 0
        while x.affix() and not x.affix().copied:
            complex_head_Y_offset += x.affix().label_size() * self.application.settings.retrieve('image_parameter_tsize')
            x = x.affix()
        return gps.Y + \
               (self.application.settings.retrieve('image_parameter_text_spacing') * self.application.settings.retrieve('image_parameter_tsize') * gps.label_size()) + \
               (self.application.settings.retrieve('image_parameter_text_spacing') * complex_head_Y_offset)
