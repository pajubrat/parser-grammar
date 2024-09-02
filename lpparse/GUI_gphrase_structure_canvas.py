import tkinter as tk


class PhraseStructureCanvas(tk.Canvas):
    """Canvas for drawing and manipulating phrase structure objects"""
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.focus_set()
        self.S = parent.S
        self.title = None
        self.derivational_index = None
        self.selected_objects = []   # selected (logical, phrase structure) objects
        self.parent = parent
        self.configure(scrollregion=(0, 0, 5000, 5000))
        self.node_to_gps = {}
        self.info = None
        self.label_style = {'label': ("Times New Roman", int(self.S['tsize'])),
                            'PFtrace': ("Times New Roman", int(self.S['tsize'] / self.S['tshrink']), "italic", "overstrike"),
                            'PF': ("Times New Roman", int(self.S['tsize'] / self.S['tshrink']), "italic"),
                            'gloss': ("Times New Roman", int(self.S['tsize'] / self.S['tshrink'])),
                            'feature': ("Times New Roman", int(self.S['tsize'] / self.S['tshrink'])),
                            'subscript': ("Times New Roman", int(self.S['tsize'] * 0.5)),
                            'arrow_label': ("Times New Roman", int(self.S['tsize'] * 0.75)),
                            'info': ("Courier", int(self.S['tsize'] * 0.25))}
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
            self.selected_objects = [self.node_to_gps[str(cur)]]
        else:
            self.selected_objects = []
            self.selected_canvas_object = None
        self.parent.update_contents(False)

    def _on_ctrl_mouse_click(self, *_):
        if self.find_withtag('current'):
            if self.gettags('current')[0] == 'node':
                self.selected_objects.append(self.node_to_gps[str(self.find_withtag('current')[0])])
        else:
            self.selected_objects = []
        self.parent.update_contents(False)

    def _show_info(self, *_):
        if self.find_withtag('current'):
            selected = self.find_withtag('current')[0]
            tag = self.gettags('current')[0]
            if tag == 'node':
                gps = self.node_to_gps[str(selected)]
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

    def project_into_canvas(self, gps, spx, spy, S):
        """Projects the logical phase structure object into canvas"""
        X1 = spx + gps.x * S['grid']
        Y1 = spy + gps.y * S['y_grid']
        gps.X = X1  # Memorize the point on the canvas for later chain marking
        gps.Y = Y1
        gps.generate_label_stack()

        # Determine the color of label and node information
        color = 'black'
        if gps in self.selected_objects:
            color = 'red'

        if gps.complex():
            self.create_complex_node(gps, X1, Y1, spx, spy, S, color)
        else:
            self.create_primitive_node(gps, X1, Y1, S, color)

    def draw_to_canvas(self, gps, spx, spy):
        self.update_status_bar(spx)
        self.info_text = self.create_text((2000, 300), state='hidden')  # Show information about selected objects
        self.project_into_canvas(gps, spx, spy, self.S)
        self.draw_dependencies(gps)

    def draw_dependencies(self, gps):
        # head chains
        if self.parent.settings.retrieve('image_parameter_head_chains', True) and gps.head_chain_target:
            if gps.sister() != gps.head_chain_target or self.parent.settings.retrieve(
                    'image_parameter_trivial_head_chains', False) or not gps.nonverbal():
                self.draw_dependency('head_chain', gps, gps.head_chain_target)
        # phrasal chains
        if self.parent.settings.retrieve('image_parameter_phrasal_chains', True):
            if gps.hasChain() and gps.sister():
                target = gps.sister().find_node_with_identity(gps.hasChain())
                if target:
                    self.draw_dependency('phrasal_chain', gps, target)
        # custom arcs
        if len(gps.custom_arcs) > 0:
            for endpoint, label in gps.custom_arcs:
                self.draw_dependency('custom', gps, endpoint, label)
        # custom arrows
        if len(gps.custom_arrows) > 0:
            for target, label, arrow_type in gps.custom_arrows:
                self.draw_arrow(gps, target, label, arrow_type)
        if gps.complex() and not gps.compressed:
                self.draw_dependencies(gps.left())
                self.draw_dependencies(gps.right())

    def create_complex_node(self, gps, X1, Y1, spx, spy, S, color):

        X2 = spx + gps.left().x * S['grid']
        Y2 = spy + gps.left().y * S['y_grid']
        X3 = spx + gps.right().x * S['grid']
        Y3 = spy + gps.right().y * S['y_grid']

        text = self.feature_conversion_for_images(gps.label_stack[0][0])

        # Create text holding the complex label (e.g., XP)
        ID = self.create_text((X1, Y1),
                              text=text,
                              fill=color,
                              activefill='red',
                              tag='node',
                              font=("Times New Roman", S['tsize']))

        # Map node to the underlying constituent
        self.node_to_gps[str(ID)] = gps
        gps.ID = ID

        # Bind events to the node
        self.tag_bind(ID, '<Enter>', self._show_info)
        self.tag_bind(ID, '<Leave>', self._hide_info)

        if gps.compressed:
            # Compressed complex node will create a triangle without constituents
            Y_offset = int(S['tsize'] / S['text_spacing'])
            self.create_line((X1, Y1 + Y_offset), (X2, Y2 + 0), width=2, fill='black')
            self.create_line((X1, Y1 + Y_offset), (X3, Y3 + 0), width=2, fill='black')
            self.create_line((X2, Y2 + 0), (X3, Y3 + 0), width=2, fill='black')
            text_items = 0
            X = (X2 + X3) / 2

            # Add custom text below the triangle, if applicable
            if gps.custom_phonology and gps.custom_phonology != '$n/a$':
                text_items += 1
                Y = Y2 + text_items * S['tsize'] * S['text_spacing'] / 1.5
                ID = self.create_text((X, Y),
                                      text=gps.custom_phonology,
                                      fill=color,
                                      activefill='red',
                                      tag='node',
                                      anchor='center',
                                      font=self.label_style['PF'])
            if gps.custom_gloss and gps.custom_gloss != '$n/a$':
                text_items += 1
                Y = Y2 + text_items * S['tsize'] * S['text_spacing'] / 1.5
                ID = self.create_text((X, Y),
                                      text=f'ʻ{gps.custom_gloss}ʼ',
                                      fill=color,
                                      activefill='red',
                                      tag='node',
                                      anchor='center',
                                      font=self.label_style['gloss'])
            if gps.custom_features and '$n/a$' not in gps.custom_features:
                text_items += 1
                Y = Y2 + text_items * S['tsize'] * S['text_spacing'] / 1.5
                ID = self.create_text((X, Y),
                                      text=' '.join(gps.custom_features),
                                      fill=color,
                                      activefill='red',
                                      tag='node',
                                      anchor='center',
                                      font=self.label_style['feature'])
            if gps.custom_text:
                text_items += 1
                Y = Y2 + text_items * S['tsize'] * S['text_spacing'] / 1.5
                ID = self.create_text((X, Y),
                                      text=gps.custom_text,
                                      fill=color,
                                      activefill='red',
                                      tag='node',
                                      anchor='center',
                                      font=self.label_style['gloss'])
        else:
            # Draw left constituent
            if gps.left() and self.parent.settings.retrieve('image_parameter_adjuncts', False) and gps.left().adjunct:
                # Adjunct attachment
                size = 18
                MX = X1 - abs(X2 - X1) / 5 - size/2
                MY = Y1 + abs(Y2 - Y1 + int(S['tsize'] / S['label_padding'])) / 5 - size / 2
                self.create_oval(MX, MY, MX + size, MY + size, width=1, fill='black')
                self.create_line((MX + size/2, MY + size/2), (X2, Y2 - int(S['tsize'] / S['label_padding'])), width=2, fill='black')
            else:
                # Regular attachment
                self.create_line((X1, Y1 + int(S['tsize'] / S['label_padding'])), (X2, Y2 - int(S['tsize'] / S['label_padding'])), width=2, fill='black')
            # Draw right constituent
            if gps.left() and self.parent.settings.retrieve('image_parameter_adjuncts', False) and gps.right().adjunct:
                # Adjunct attachment
                size = 18
                MX = X1 + abs(X3 - X1) / 5 - size/2
                MY = Y1 + abs(Y3 - Y1 + int(S['tsize'] / S['label_padding'])) / 5 - size / 2
                self.create_oval(MX, MY, MX + size, MY + size, width=1, fill='black')
                self.create_line((MX + size/2, MY + size/2), (X3, Y3 - int(S['tsize'] / S['label_padding'])), width=2, fill='black')
            else:
                # Regular attachment
                self.create_line((X1, Y1 + int(S['tsize'] / S['label_padding'])), (X3, Y3 - int(S['tsize'] / S['label_padding'])), width=2, fill='black')
            # Recursive calls (for non-compressed complex nodes)
            self.project_into_canvas(gps.left(), spx, spy, S)
            self.project_into_canvas(gps.right(), spx, spy, S)
        return ID

    def create_primitive_node(self, gps, X1, Y1, S, color):
        Y_offset = 0    # Y_offset determines the lower boundary of the node + its label(s) when adding elements

        # Reproduce the head and all of its affixes
        for j, affix in enumerate(gps.get_affix_list(), start=1):
            # Do not reproduce affixes if blocked by settings
            if (affix.copied and not self.parent.settings.retrieve('image_parameter_covert_complex_heads', False)) or \
                    (j > 1 and not self.parent.settings.retrieve('image_parameter_complex_heads', True)):
                break

            # Generate the label text (label + phonological exponent + gloss)
            for i, label_item in enumerate(affix.label_stack):
                text = self.feature_conversion_for_images(label_item)

                # Do not reproduce items if blocked by settings
                if (label_item[1] == 'gloss' and not self.parent.settings.retrieve('image_parameter_glosses', True)) or \
                        (label_item[1] == 'PF' and not self.parent.settings.retrieve('image_parameter_words', True)):
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
                    self.create_text((X1 + (len(text)-1) * 15 + S['grid'] / 6, Y1 + Y_offset + S['tsize'] / 4),
                                     fill=color,
                                     activefill='red',
                                     tag='subscript',
                                     text = affix.subscript,
                                     anchor='w',
                                     font=self.label_style['subscript'])
                if label_item[1] == 'label' and affix.superscript:
                    self.create_text((X1 + (len(text)-1) * 15 + S['grid'] / 6, Y1 - Y_offset - S['tsize'] / 4),
                                     fill=color,
                                     activefill='red',
                                     tag='superscript',
                                     text=affix.superscript,
                                     anchor='w',
                                     font=self.label_style['subscript'])

                # Update the offset
                Y_offset += S['tsize'] * S['text_spacing']

                # Add the node to the mapping from nodes to affixes
                self.node_to_gps[str(ID)] = affix
                affix.ID = str(ID)

                # Add events to the first element (i == 0 when producing the label)
                if i == 0:
                    self.tag_bind(ID, '<Enter>', self._show_info)
                    self.tag_bind(ID, '<Leave>', self._hide_info)

    def feature_conversion_for_images(self, label_item):
        text = label_item[0]
        if self.parent.settings.retrieve('image_parameter_DP_hypothesis', False):
            if text == 'φ':
                text = 'D'
            if text == 'φP':
                text = 'DP'
        if label_item[1] == 'feature':
            return '[' + text + ']'
        return text

    def get_lowered_Y_coord_for_arrow(self, source, target):
        Y_offset = self['Y_offset_for_arrow']
        if self.get_Y_coord(target) > self.get_Y_coord(source):
            return self.get_Y_coord(target) + Y_offset
        return self.get_Y_coord(source) + Y_offset

    def draw_arrow(self, source, target, label, arrow_type):
        coords = [(source.X, self.get_Y_coord(source)),
                  (source.X, self.get_lowered_Y_coord_for_arrow(source, target)),
                  (target.X, self.get_lowered_Y_coord_for_arrow(source, target)),
                  (target.X, self.get_Y_coord(target))]
        self.create_line(*coords,
                         dash=self.parent.line_style['arrow']['dash'],
                         arrow=arrow_type,
                         arrowshape=(2, 20, 20),
                         width=self.parent.line_style['arrow']['width'], smooth=False, tag='arrow',
                         fill=self.parent.line_style['arrow']['fill'])
        if label:
            mX = abs(X1 + X4)/2
            mY = Yb + 30
            self.create_text((mX, mY),
                             fill='black',
                             activefill='red',
                             tag='label_text',
                             text=label,
                             anchor='c',
                             font=self.label_style['arrow_label'])

    def label_offset(self, gps):
        if gps.compressed:
            return self.S['tsize'] * 1.2 * self.compressed_node_label_stack(gps)
        return self.S['text_spacing'] * self.S['tsize'] * gps.label_size()

    def get_Y_coord(self, gps):
        for x in gps.dominating_nodes():
            if x.compressed:
                return x.Y  # GPS is inside compressed node
        if gps.complex():
            return self.Y_coord_complex_node(gps)
        return self.Y_coord_zero_level(gps)

    def Y_coord_complex_node(self, gps):
        return gps.left().Y + self.S['text_spacing'] * self.S['tsize'] * gps.label_size()

    def Y_coord_zero_level(self, gps):
        x = gps
        complex_head_Y_offset = 0
        while x.affix() and not x.affix().copied:
            complex_head_Y_offset += x.affix().label_size() * self.S['tsize']
            x = x.affix()
        return gps.Y + \
               (self.S['text_spacing'] * self.S['tsize'] * gps.label_size()) + \
               (self.S['text_spacing'] * complex_head_Y_offset)

    def draw_dependency(self, style, source_gps, target_gps, text=''):
        coords = [(source_gps.X, self.get_Y_coord(source_gps)),
                  (source_gps.X + abs(source_gps.X - target_gps.X)/2, target_gps.Y + int(self.S['grid'] * self.S['arc_curvature'])),
                  (target_gps.X, self.get_Y_coord(target_gps))]
        self.create_line(*coords,
                         splinesteps=50,
                         dash=self.parent.line_style[style]['dash'],
                         width=self.parent.line_style[style]['width'],
                         smooth=True,
                         tag=style,
                         fill=self.parent.line_style[style]['fill'])
