from phrase_structure import PhraseStructure


class GPhraseStructure(PhraseStructure):
    """Phrase Structure class that has additional properties related to tree drawing"""

    application = None  # Application handle for settings

    def __init__(self, source=None, left=None, right=None, **kwargs):
        super().__init__(left, right, **kwargs)

        # Properties of regular constituents

        self.core = source.core
        self.adjunct = source.adjunct
        self.identity = source.identity
        self.copied = source.copied
        self.flip = False
        self.phrasal_zero = False
        self.custom_label = None
        self.shrink = source.shrink
        self.phrasal_zero_level = source.phrasal_zero_level

        if not source.terminal():

            # Create phrasal representations for complex words if so defined in the settings

            if GPhraseStructure.application.settings.retrieve('image_parameter_phrasal_complex_heads') and source.zero_level() and len(source.const) > 0:

                # Do not create them for DP is DP were set to be shrink

                if not (self.application.settings.retrieve('image_parameter_shrink_all_DPs', False) and source.head()('referential')):
                    self.create_constituents([GPhraseStructure(x) for x in self.complex_head_transform(source).const])
                    self.phrasal_zero_level = True
                    self.relabel()  # Create new custom labels (e.g., not phrases XP)
            else:
                self.create_constituents([GPhraseStructure(const) for const in source.const])

        # Special properties
        self.x = 0
        self.y = 0
        self.X = 0
        self.Y = 0
        self.Y_offset = 0
        self.subscript = None
        self.superscript = None
        self.custom_phonology = None
        self.custom_gloss = None
        self.custom_features = []
        self.custom_text = None
        self.source = source
        self.compressed = False
        self.label_stack = self.generate_label_stack()
        self.custom_arcs = []
        self.ellipsis = None
        self.ID = None
        self.highlight = False
        self.special_left_constituent_marking = []
        self.special_right_constituent_marking = []

    def complex_head_transform(self, X):
        M = X.M()
        C = None

        for x in X.affixes()[::-1]:
            x.const = []
            if not C:
                C = x
            else:
                C = PhraseStructure(C, x)
                if not GPhraseStructure.application.settings.retrieve('image_parameter_covert_complex_heads'):
                    if C.R().copied:
                        C.core.add_features(C.R().label())
                        C.core.add_features(C.R().index())
                        C.const = []
                    elif C.L().copied:
                        C.L().copied = False
        if M:
            if X.L():
                M.const = [M.R(), C]
            else:
                M.const = [C, M.L()]
            C.mother_ = M
        return C

    def relabel(self):
        if self.L():
            self.L().relabel()
        if self.R():
            self.R().relabel()
            self.custom_label = self.R().label() + '°'

    # Allows left-right flipping during image creation

    def L(self):
        if self.flip:
            return super().R()
        else:
            return super().L()

    def R(self):
        if self.flip:
            return super().L()
        else:
            return super().R()

    def dominating_nodes(self):
        x = self
        lst = []
        while x.mother_:
            lst.append(x.mother_)
            x = x.mother_
        return lst

    def map_into_gps(gX, X):
        """
        Finds recursively gX which maps into X
        """

        if gX.source == X:
            return gX

        if gX.affix():
            K = gX.affix().map_into_gps(X)
            if K:
                return K

        if gX.complex():
            K = gX.L().map_into_gps(X)
            if not K:
                K = gX.R().map_into_gps(X)
            return K

    def initialize_image_parameters(self):
        if self.complex():

            # Create compressed DPs

            if self.head()('referential') and self.application.settings.retrieve('image_parameter_DP_compression', False):
                self.compressed = True

            # Create shrink DPs

            if self.head()('referential') and self.application.settings.retrieve('image_parameter_shrink_all_DPs', False):
                self.shrink = True          # This will not draw any nodes below and currently created custom label DP
                self.compressed = False     # Compression (triangle format) and shrink cannot be applied simultaneously
                self.custom_label = 'DP'    # This could be generalized if we allow other types of shrunk constituents,
                                            # but the intention is that normally we should use compression (triangle format)

                # Copy phonological features from N into DP, if possible

                if 'N' in self.R().core.features():
                    self.custom_phonology = self.R().PF()

            self.L().initialize_image_parameters()
            self.R().initialize_image_parameters()

    def initialize_logical_space(self):
        """Projects the phrase structure object into a logical space"""
        if self.complex():
            self.L().x = self.x - 1
            self.L().y = self.y + 1
            self.L().initialize_logical_space()
            self.R().x = self.x + 1
            self.R().y = self.y + 1
            self.R().initialize_logical_space()

    def remove_overlap(self):
        if self.application.settings.retrieve('image_parameter_remove_overlap', True):
            self.remove_overlap_()

    def remove_overlap_(self):
        """Stretches child nodes apart if their offspring create overlap"""

        # Horizontal overlap

        if self.complex() and not self.L().shrink:
            if not self.L().compressed:
                self.L().remove_overlap_()
            if not self.R().compressed:
                self.R().remove_overlap_()

            # Remove horizontal overlap from each row

            overlap = 0

            LC_right_boundary = self.L().boundary_points()
            RC_left_boundary = self.R().boundary_points()
            for L_bp in LC_right_boundary:
                for R_bp in RC_left_boundary:
                    if L_bp[1] == R_bp[1]:
                        if L_bp[0] >= R_bp[0] and L_bp[0] - R_bp[0] >= overlap:
                            overlap = L_bp[0] - R_bp[0] + 1
            if overlap > 0:
                self.L().move_x(-overlap / 2)
                self.R().move_x(overlap / 2)

            # Remove vertical overlap from each column (i.e. high label stack overlaps with constituent below)
            # This brute force algorithm is inefficient (todo)

            if not self.L().compressed:
                lst = self.L().rich_labels()     # Find high labels from LEFT that can in principle overlap
                for node in lst:
                    if not self.R().compressed:
                        if self.R().vertical_overlap(node):     # find overlaps from RIGHT
                            self.L().move_x(-0.5)               # and if found, stretch
                            self.R().move_x(0.5)

    def boundary_points(self):
        boundary = set()
        if self.compressed:
            boundary.add((self.L().x, self.L().y))
            boundary.add((self.R().x, self.R().y))
        else:
            boundary.add((self.x, self.y))
            if self.complex():
                boundary = boundary | self.L().boundary_points()
                boundary = boundary | self.R().boundary_points()
        return boundary

    def find_boundaries(self, left_x, right_x, depth):
        if self.x < left_x:
            left_x = self.x
        if self.x > right_x:
            right_x = self.x
        if self.y > depth:
            depth = self.y
        if self.complex() and not self.compressed:
            left_x, right_x, depth = self.L().find_boundaries(left_x, right_x, depth)
            left_x, right_x, depth = self.R().find_boundaries(left_x, right_x, depth)
        return left_x, right_x, depth

    def rich_labels(self):
        lst = []
        if self.label_size() > 2:
            lst.append(self)
        return lst

    def vertical_overlap(self, node):
        if self.x == node.x and self.y == node.y + 1:
            return True

    def move_x(self, amount):
        """Moves a node and its offspring"""
        self.x = self.x + amount
        if self.L():
            self.L().move_x(amount)
        if self.R():
            self.R().move_x(amount)

    def move_y(self, amount):
        """Moves a node and its offspring"""
        self.y = self.y + amount
        if self.complex():
            self.L().move_y(amount)
            self.R().move_y(amount)

    def label_size(self):
        if self.compressed:     # Compressed triangles only have custom labels
            offset = 1
            if self.custom_phonology and self.custom_phonology != '$n/a$':
                offset += 1
            if self.custom_gloss and self.custom_phonology != '$n/a$':
                offset += 1
            if self.custom_features and self.custom_phonology != '$n/a$':
                offset += 1
            return offset
        if not self.terminal() and GPhraseStructure.application.settings.retrieve('image_parameter_phrasal_complex_heads'):
            return 0            # Complex heads [X Y]^0 do not generate label stacks
        return len(self.label_stack)

    def generate_label_stack(self):

        # Label stack is a list of label information that will be shown in connection with this node

        label_stack = []

        # Minimum label is the label itself

        if not self.custom_label == '$n/a$':

            # Custom label

            if self.custom_label:
                label_stack.append((self.custom_label, 'label'))

            # Linguistic label

            else:
                label_stack.append((self.label(), 'label'))

        # Empty label is currently represented as white space

        else:
            label_stack.append((' ', 'label'))

        # Phonological string

        if not self.custom_phonology == '$n/a$':
            if self.custom_phonology:
                label_stack.append((self.custom_phonology, 'PF'))
            elif not self.complex():
                if self.get_phonological_string() and self.get_phonological_string() != self.label():
                    label_stack.append((self.get_phonological_string(), 'PF'))

        # Gloss

        if not self.custom_gloss == '$n/a$':
            if self.custom_gloss:
                label_stack.append((f"ʻ{self.custom_gloss}ʼ", 'gloss'))
            elif not self.complex():
                if self.gloss() and self.gloss() != self.label() and self.gloss() != self.get_phonological_string():
                    label_stack.append((f"ʻ{self.gloss()}ʼ", 'gloss'))

        # Features

        if not '$n/a$' in self.custom_features:
            if self.custom_features:
                for feature in self.custom_features:
                    label_stack.append((feature, 'feature'))
            elif not self.complex():
                for feature in [x for x in self.core.features() if x in GPhraseStructure.draw_features]:
                    label_stack.append((f'{feature}', 'feature'))

        # Custom text

        if self.custom_text:
            label_stack.append((self.custom_text, 'gloss'))

        self.label_stack = label_stack
        return label_stack

    def itext(self):
        """Produces information concerning constituents when pointed at the screen by mouse"""
        itext = self.label() + '\n'
        if self.zero_level():
            i = 0
            for feature in sorted(self.core.features()):
                itext += feature + '\n'
        return itext

    def find_max_label_size(self, label_size):
        """Finds the maximal label size for a phrase structure (to determine canvas margins)"""
        if self.zero_level():
            ls = self.label_size() * len(self.affixes())
            if ls > label_size:
                return ls
            return label_size
        if self.complex():
            label_size = self.L().find_max_label_size(label_size)
            label_size = self.R().find_max_label_size(label_size)
        return label_size
