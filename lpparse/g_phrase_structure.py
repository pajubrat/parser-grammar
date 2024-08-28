from phrase_structure import PhraseStructure


class GPhraseStructure(PhraseStructure):
    """Phrase Structure class that has additional properties related to tree drawing"""

    draw_features = {}

    def __init__(self, source=None, left=None, right=None):
        super().__init__(left, right)

        # Properties of regular constituents
        self.features = source.features
        self.adjunct = source.adjunct
        self.identity = source.identity
        self.copied = source.copied
        self.flip = False
        if not source.terminal():
            self.create_constituents([GPhraseStructure(const) for const in source.const])

        # Special properties
        self.x = 0
        self.y = 0
        self.X = 0
        self.Y = 0
        self.Y_offset = 0
        self.custom_label = None
        self.subscript = None
        self.superscript = None
        self.custom_phonology = None
        self.custom_gloss = None
        self.custom_features = []
        self.custom_text = None
        self.head_chain_target = None
        self.Agree_target = None
        self.source = source
        self.node_identity = source.node_identity
        self.compressed = False
        self.label_stack = self.generate_label_stack()
        self.custom_arcs = []
        self.custom_arrows = []
        self.ellipsis = None
        self.ID = None

    # Allows left-right flipping during image creation
    def left(self):
        if self.flip:
            return super().right()
        else:
            return super().left()

    def right(self):
        if self.flip:
            return super().left()
        else:
            return super().right()

    def dominating_nodes(self):
        x = self
        lst = []
        while x.mother_:
            lst.append(x.mother_)
            x = x.mother_
        return lst

    def find_head_chain(self):
        if self.zero_level() and self.is_left() and self.affix() and self.affix().copied and self.mother_:
            return self.mother_.right().find_constituent_with_index(self.affix().index())

    def find_Agree(self):
        if self.zero_level() and self.is_left() and 'ΦLF' in self.features:
            pass

    def initialize_logical_space(self):
        """Projects the phrase structure object into a logical space"""
        self.head_chain_target = self.find_head_chain()
        if self.complex():
            self.left().x = self.x - 1
            self.left().y = self.y + 1
            self.left().initialize_logical_space()
            self.right().x = self.x + 1
            self.right().y = self.y + 1
            self.right().initialize_logical_space()

    def boundary_points(self):
        boundary = set()
        boundary.add((self.x, self.y))
        if self.complex() and (not self.mother() or not self.mother().compressed):
            boundary = boundary | self.left().boundary_points()
            boundary = boundary | self.right().boundary_points()
        return boundary

    def find_boundaries(self, left_x, right_x, depth):
        if self.x < left_x:
            left_x = self.x
        if self.x > right_x:
            right_x = self.x
        if self.y > depth:
            depth = self.y
        if self.complex() and (not self.mother() or not self.mother().compressed):
            left_x, right_x, depth = self.left().find_boundaries(left_x, right_x, depth)
            left_x, right_x, depth = self.right().find_boundaries(left_x, right_x, depth)
        return left_x, right_x, depth

    def remove_overlap(self):
        """Stretches child nodes apart if their offspring create overlap"""
        if self.complex():
            self.left().remove_overlap()
            self.right().remove_overlap()
            overlap = 0
            LC_right_boundary = self.left().boundary_points()
            RC_left_boundary = self.right().boundary_points()
            for L_bp in LC_right_boundary:
                for R_bp in RC_left_boundary:
                    if L_bp[1] == R_bp[1]:
                        if L_bp[0] >= R_bp[0] and L_bp[0] - R_bp[0] >= overlap:
                            overlap = L_bp[0] - R_bp[0] + 1
            if overlap > 0:
                self.left().move_x(-overlap/2)
                self.right().move_x(overlap/2)

    def move_x(self, amount):
        """Moves a node and its offspring"""
        self.x = self.x + amount
        if self.complex():
            self.left().move_x(amount)
            self.right().move_x(amount)

    def move_y(self, amount):
        """Moves a node and its offspring"""
        self.y = self.y + amount
        if self.complex():
            self.left().move_y(amount)
            self.right().move_y(amount)

    def label_size(self):
        return len(self.label_stack)

    def generate_label_stack(self):
        """Determines the content for primitive labels"""
        def feature_conversion(feature):
            return feature

        label_stack = []

        # Minimum label is the label itself
        if not self.custom_label == '$n/a$':
            if self.custom_label:
                label_stack.append((self.custom_label, 'label'))
            else:
                label_stack.append((self.label(), 'label'))

        if self.zero_level():

            # Phonological string
            if not self.custom_phonology == '$n/a$':
                if self.custom_phonology:
                    label_stack.append((self.custom_phonology, 'PF'))
                else:
                    if self.get_phonological_string() and self.get_phonological_string() != self.label():
                        label_stack.append((self.get_phonological_string(), 'PF'))

            # Gloss
            if not self.custom_gloss == '$n/a$':
                if self.custom_gloss:
                    label_stack.append((f"ʻ{self.custom_gloss}ʼ", 'gloss'))
                else:
                    if self.gloss() and self.gloss() != self.label() and self.gloss() != self.get_phonological_string():
                        label_stack.append((f"ʻ{self.gloss()}ʼ", 'gloss'))

            # Features
            if not '$n/a$' in self.custom_features:
                if self.custom_features:
                    for feature in self.custom_features:
                        label_stack.append((feature, 'feature'))
                else:
                    for feature in [x for x in self.features if x in GPhraseStructure.draw_features]:
                        label_stack.append((f'{feature_conversion(feature)}', 'feature'))

            # Custom text
            if self.custom_text:
                label_stack.append((self.custom_text, 'gloss'))

        self.label_stack = label_stack
        return label_stack

    def itext(self):
        """Produces information concerning constituents when pointed at the screen by mouse"""
        itext = self.label() + '\n\n'

        if self.complex():

            itext += f'Identity: {self.node_identity}\n'
            itext += f'Reconstructed: {self.copied}\n'
            itext += f'Adjunct Merge: {self.adjunct}\n'
            itext += ' '.join(self.features)
            return itext

        if self.zero_level():

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

            if self.affix() and not self.right().copied:
                itext += f'\nComplex head with structure '
                for c in self.get_affix_list():
                    itext += f'{c} '

        return itext

    def find_max_label_size(self, label_size):
        """Finds the maximal label size for a phrase structure (to determine canvas margins)"""
        if self.zero_level():
            ls = self.label_size() * len(self.get_affix_list())
            if ls > label_size:
                return ls
            return label_size
        if self.complex():
            label_size = self.left().find_max_label_size(label_size)
            label_size = self.right().find_max_label_size(label_size)
        return label_size

    def hasChain(self):
        for f in self.features:
            if f and f.startswith('CHAIN:'):
                return int(f.split(':')[1])

