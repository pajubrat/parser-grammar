# This class defines basic linguistic competence, i.e. phrase structures and operations on phrase structure
from support import log
from LF import LF
from collections import namedtuple

major_category = {'N', 'Neg', 'Neg/fin', 'P', 'D', 'C', 'A', 'v', 'V', 'ADV', 'Q', 'NUM', 'T', 'TO/inf', 'VA/inf', 'A/inf', 'FORCE', '0', 'a', 'b', 'c', 'd', 'x', 'y', 'z'}

# Definitions and methods for phrase structure
class PhraseStructure:

    # Constituent constructor, Merge[A B]
    def __init__(self, left_constituent=None, right_constituent=None):
        self.left_const = left_constituent
        self.right_const = right_constituent
        if self.left_const:
            self.left_const.mother = self
        if self.right_const:
            self.right_const.mother = self
        self.mother = None
        self.features = set()
        self.morphology = ''
        self.internal = False
        self.adjunct = False
        self.incorporated = False
        self.find_me_elsewhere = False
        self.identity = ''
        self.rebaptized = False
        self.x = 0
        self.y = 0
        if left_constituent and left_constituent.externalized() and left_constituent.is_primitive():
            self.adjunct = True
            left_constituent.adjunct = False

    #
    #
    # Block 1. Definitions for basic grammatical relations
    #
    #
    # Definition of primitive constituent
    def is_primitive(self):
        return not (self.right_const and self.left_const)

    # Definition for complex constituent
    def is_complex(self):
        return not self.is_primitive()

    # Definition of left
    def is_left(self):
        return self.mother and self.mother.left_const == self

    # Definition of right
    def is_right(self):
        return self.mother and self.mother.right_const == self

    # Definition for affix
    def has_affix(self):
        return self.right_const and not self.left_const

    # Definition for terminal head (that has no constituents of any kind)
    def terminal_node(self):
        return self.is_primitive() and not self.has_affix()

    # Definition for complex head
    def is_complex_head(self):
        return self.is_primitive() and self.has_affix()

    # Definition for geometrical sister
    def geometrical_sister(self):
        if self.is_left():
            return self.mother.right_const
        if self.is_right():
            return self.mother.left_const

    # Definition for externalization
    def externalized(self):
        return self.adjunct

    def adjoinable(self):
        return 'adjoinable' in self.features and '-adjoinable' not in self.features

    # Definition of functional (vs. lexical)
    def is_functional(self):
        return '!COMP:*' in self.features

    # Definition for left primitive head
    def left_primitive(self):
        return self.left_const and self.left_const.is_primitive()

    # Definition for left complex head
    def left_complex(self):
        return self.left_const and self.is_complex()

    # Opposite of externalization
    def visible(self):
        return not self.externalized()

    def is_selected(self):
        if self.max().sister() and self.max().sister().is_primitive():
            return True

    # Definition for adjoinable phrase
    def is_adjoinable(self):
        for edge in self.head().edge():
            if edge.contains_feature('OP:REL'):
                return True
        return self.externalized() or ('adjoinable' in self.head().features and '-adjoinable' not in self.head().features)

    # Definition for sisterhood
    def sister(self):
        while self.mother:
            if self.is_left():
                if self.geometrical_sister().visible():
                    return self.geometrical_sister()
                else:
                    self = self.mother
            if self.is_right():
                if self.visible():
                    return self.geometrical_sister()
                else:
                    return None
        return None

    # Definition for strong complement (=right sister)
    def proper_complement(self):
        if self.sister() and self.sister().is_right():
            return self.sister()

    # Definition of bottom node
    def bottom(self):
        while not self.is_primitive():
            self = self.right_const
        return self

    # Definition for head (also label) of a phrase structure
    def head(self):
        if self.is_primitive():
            return self
        if self.left_const.is_primitive():
            return self.left_const
        if self.right_const.is_primitive():
            return self.right_const
        if self.right_const.externalized():
            return self.left_const.head()
        return self.right_const.head()

    def max(self):
        ps_ = self
        while ps_ and ps_.mother and ps_.mother.head() == self.head():
            ps_ = ps_.mother
        return ps_

    # Definition for minimal search
    def minimal_search(self):
        return [node for node in self]

    # Definition for geometrical minimal search
    def geometrical_minimal_search(self):
        search_list = [self]
        while self.is_complex() and self.right_const:
            search_list.append(self.right_const)
            self = self.right_const
        return search_list

    def __getitem__(self, position):
        iterator_ = 0
        ps_ = self
        while ps_:
            if iterator_ == position:
                return ps_
            if ps_.is_primitive():
                raise IndexError
            else:
                if ps_.head() == ps_.right_const.head():    # [_YP XP YP] = YP
                     ps_ = ps_.right_const
                else:
                    if ps_.left_const.is_complex():         # [_XP XP <YP>] = XP
                        ps_ = ps_.left_const
                    else:
                        if ps_.right_const.externalized():  # [X <YP>] = X
                            ps_ = ps_.left_const
                        else:
                            ps_ = ps_.right_const           # [X Y] = Y
            iterator_ = iterator_ + 1

    # Definition for upstream search
    # Notes. This version excludes the starting node
    def upstream_search(self):
        path = []
        while self.mother:
            path.append(self.mother)
            self = self.mother
        return path

    # Definition for edge
    def edge(self):
        edge = []
        # -------------- minimal upstream path ---------------------------------------------#
        for node in self.upstream_search():
            if node.head() != self:
                break
            if node.left_const and node.left_const.is_complex() and node.left_const.head() != self:
                edge.append(node.left_const)
        #------------------------------------------------------------------------------------#
        if not edge and self.extract_pro():
            edge.append(self.extract_pro())
        return edge

    # Definition for local edge
    def local_edge(self):
        if self.edge():
            return self.edge()[0]

    def phrasal_edge(self):
        return [edge for edge in self.edge() if edge.is_complex()]

    # Definition for licensed specifier (for a head)
    def licensed_specifier(self):
        edge = self.phrasal_edge()
        # If there is only one phrasal edge, return it
        if len(edge) == 1:
            return edge[0]
        # If there are many phrases in the edge
        elif len(edge) > 1:
            # Return the first non-externalized phrase, if any,
            licensed_edge = [edge for edge in self.phrasal_edge() if not edge.externalized()]
            if licensed_edge:
                return licensed_edge[0]
            # if everything has been externalized, return the closest phrase that has not been moved away
            else:
                licensed_edge = [edge for edge in self.phrasal_edge() if not edge.find_me_elsewhere]
                if licensed_edge:
                    return licensed_edge[0]

    # Definition for container head
    def container_head(self):
        if self.mother:
            return self.mother.head()

    # Definition for upstream walk
    def walk_upstream(self):
        while self.mother:
            self = self.mother
            if self.right_const.visible():
                return self

    # Definition for selector
    def selector(self):
        if len(self.feature_vector()) > 1:
            return self.feature_vector()[1]

    def top(self):
        if not self.mother:
            return self
        else:
            return self.upstream_search()[-1]

    def missing_complement(self):
        return self.is_primitive() and not self.proper_complement() and self.licensed_complements()

    def wrong_complement(self):
        return self.is_left() and self.proper_complement() and self.has_mismatching_complement()

    def complement_match(self, const):
        return self.licensed_complements() & const.head().features

    def licensed_complements(self):
        return {f[5:] for f in self.features if f[:4] == 'COMP'} | {f[6:] for f in self.features if f[:5] == '!COMP'}

    def complements_not_licensed(self):
        return {f[6:] for f in self.features if f[:5] == '-COMP'}

    def has_mismatching_complement(self):
        return not (self.licensed_complements() & self.proper_complement().head().features)

    def get_mandatory_comps(self):
        return  {f[6:] for f in self.features if f[:5] == '!COMP' and f != '!COMP:*'}

    def get_theta_assigner(self):
        if self.sister() and self.sister().is_primitive():
            return self.sister
        if self.container_head() and self.container_head().licensed_specifier():
            if self == self.container_head().licensed_specifier():
                return self.container_head()

    def get_position_on_geometric_right_edge(self):
        ps_ = self.top()
        position = 0
        while ps_:
            if ps_ == self:
                return position
            if ps_.right_const:
                position = position + 1
                ps_ = ps_.right_const
            else:
                return None
        return None

    def node_at(self, position):
        ps_ = self.top()
        for pos in range(0, position):
            ps_ = ps_.right_const
        return ps_

    def identify_equivalent_node(self, site):
        return self.node_at(site.get_position_on_geometric_right_edge())

    #
    # Block 2. Structure building operations
    #
    #
    # Definition for asymmetric countercyclic Merge-1 operation (nontrivial)
    def merge_1(self, C, direction=''):
        local_structure = self.local_structure()                # [X...self...Y]
        new_constituent = self.asymmetric_merge(C, direction)   # A = [self H] or [H self]
        new_constituent.substitute(local_structure)             # [X...A...Y]
        return new_constituent.top()

    # Definition for standard Merge with symmetry breaking
    def asymmetric_merge(self, B, direction='right'):
        if direction == 'left':
            new_constituent = PhraseStructure(B, self)
        else:
            new_constituent = PhraseStructure(self, B)
        return new_constituent

    # Substitute self into local_structure
    def substitute(self, local_structure):
        if local_structure.mother:
            if not local_structure.left:
                local_structure.mother.right_const = self
            else:
                local_structure.mother.left_const = self
            self.mother = local_structure.mother

    def local_structure(self):
        local_structure = namedtuple('local_structure', 'mother left')
        local_structure.mother = self.mother
        local_structure.left = self.is_left()
        return local_structure

    # Abbreviation for X.Merge_1(Y, right)
    def __add__(self, incoming_constituent):
        return self.merge_1(incoming_constituent)

    # Definition for an operation that removes an element from the phrase structure
    # and seals the hole left behind (does not do anything if H is topmost constituent)
    def remove(self):
        if self.mother:
            mother = self.mother                    # {H, X}
            sister = self.geometrical_sister()      # X
            grandparent = self.mother.mother        # {Y {H, X}}
            sister.mother = sister.mother.mother    # Y
            if mother.is_right():
                grandparent.right_const = sister    # {Y X} (removed H)
            elif mother.is_left():
                grandparent.left_const = sister     # {X Y} (removed H)
            self.mother = None                      # detach H

    # Definition for sinking
    # X.sink(ps) = adds ps to X as the bottom affix
    def sink(self, ps):
        bottom_affix = self.get_affix_list()[-1]
        bottom_affix.right_const = ps
        ps.mother = bottom_affix
        bottom_affix.left_const = None
        return self.top()

    def copy(self):
        ps_ = PhraseStructure()
        if self.left_const:
            ps_.left_const = self.left_const.copy()
            ps_.left_const.mother = ps_
        if self.right_const:
            ps_.right_const = self.right_const.copy()
            ps_.right_const.mother = ps_
        if self.features:
            ps_.features = self.features.copy()
        ps_.morphology = self.morphology
        ps_.internal = self.internal
        ps_.adjunct = self.adjunct
        ps_.find_me_elsewhere = self.find_me_elsewhere
        ps_.identity = self.identity
        return ps_

    # Separate phrase structure from its host and return the mother (for later reattachment)
    def detach(self):
        if self.mother:
            original_mother = self.mother
            self.mother = None
        else:
            original_mother = None
        return original_mother

    def get_specifier_sister(self):
        if self.is_left():
            return self.mother
        else:
            return self

    # Definition for selected sister
    # A sister, excluding left primitive heads and adjuncts
    def selected_sister(self):
        if self.sister():
            if self.sister().is_primitive() and self.sister().is_right():
                    return self.sister()
            if self.sister().is_complex():
                return self.sister()

    #
    # Block 3. Nonlocal dependencies and operations
    #
    # Definition for feature vector
    def feature_vector(self):
        return [self] + [node.left_const for node in self.upstream_search() if
                         node.left_const and node.left_const.is_primitive() and node.left_const != self]

    # Definition for probe-goal dependency
    def probe(self, feature, G):
        if self.sister():
            # --------------------- minimal search --------------------------------
            for node in self.sister():
                if G in node.inside_path().features:
                    return True
                if G[:4] == 'TAIL' and G[5:] in node.left_const.scan_criterial_features():
                    return True
                if node.intervention(feature):
                    break
            # -------------------------------------------------------------------------------------------

    # Definition for path visibility
    def inside_path(self):
        if self.is_primitive():
            return self
        if self.is_complex:
            return self.left_const.head()

    # Definition for intervention
    def intervention(self, feature):
        feature.issubset(self.inside_path().features)

    def external_tail_head_test(self):
        tail_sets = self.get_tail_sets()
        tests_checked = set()
        for tail_set in tail_sets:
            # Strong tail condition: Must be inside the projection
            if self.strong_tail_condition(tail_set):
                tests_checked.add(tail_set)
            # Weak tail condition: Must find an upstream path
            if self.weak_tail_condition(tail_set):
                tests_checked.add(tail_set)
        return tests_checked & tail_sets == tail_sets

    def internal_tail_head_test(self):
        tail_sets = self.get_tail_sets()
        tests_checked = set()
        if tail_sets:
            for tail_set in tail_sets:
                if self.weak_tail_condition(tail_set, 'internal'):
                    tests_checked.add(tail_set)
            return tests_checked & tail_sets == tail_sets
        return True

    def strong_tail_condition(self, tail_set):
        if self.precondition_for_strong_condition():
            if self.max() and self.max().mother:
                if self.max().mother.head().match_features(tail_set) == 'complete match':
                    return True
                # Licenses HP at [V [DP <H XP>]] by V
                if self.max().mother.sister() and self.max().mother.sister().match_features(tail_set) == 'complete match':
                    return True

    def precondition_for_strong_condition(self):
        # APs are excluded
        if 'A' in self.head().features:
            return False
        # Left DPs are excluded with the exception of genitive marked DPs
        if 'D' in self.head().features and self.max().is_left() and 'GEN' not in self.head().features:
            return False
        return True

    def weak_tail_condition(self, tail_set, variation='external'):
        if  'ADV' not in self.features and len(self.feature_vector()) > 1:
            for const in self.feature_vector()[1:]:
                for m in const.get_affix_list():
                    test = m.match_features(tail_set)
                    if test == 'complete match':
                        return True
                    elif test == 'partial match':
                        return False
                    elif test == 'negative match':
                        return False
        # What to do when reaching the top
        if variation=='external' and not self.negative_features(tail_set):
            return False    # Strong test: reject (tail set must be checked)
        else:
            return True     # Weak test: accept still (only look for violations)

    def bind_to_operator(self, operator):
        # --------------- upstream path --------------------------------------------------------------------------- #
        for node in self.upstream_search():
            if node.inside_path().match_features({operator}) == 'complete match' and 'FIN' in node.inside_path().features:
                return node
        # --------------------------------------------------------------------------------------------------------- #

    def match_features(self, features_to_check):
        positive_features = self.positive_features(features_to_check)
        negative_features = self.negative_features(features_to_check)
        if negative_features & self.features:
            return 'negative match'
        elif positive_features:
            if positive_features & self.features == positive_features:
                return 'complete match'
            elif positive_features & self.features:
                return 'partial match'

    def negative_features(self, features_to_check):
        return {feature[1:] for feature in features_to_check if feature[0] == '*'}

    def positive_features(self, features_to_check):
        return {feature for feature in features_to_check if feature[0] != '*'}

    # Definition for tail sets
    def get_tail_sets(self):
        return {frozenset((feature[5:].split(','))) for feature in self.head().features if feature[:4] == 'TAIL'}

    # Recursive definition for contains-feature-F for a phrase
    def contains_feature(self, feature):
        if self.left_const and self.left_const.contains_feature(feature):
            return True
        if self.right_const and self.right_const.contains_feature(feature):
            return True
        if self.is_primitive:
            if feature in self.features:
                return True
        return False

    #
    #
    # Block 4. Functions which return properties from inside a head
    #
    #
    def EPP(self):
        return 'SPEC:*' in self.features or '!SPEC:*' in self.features

    # Return a list of affixes inside a grammatical head (including the head itself)
    def get_affix_list(self):
        lst = [self]
        while self.right_const and not self.left_const:
            lst.append(self.right_const)
            self = self.right_const
        return lst

    def features_of_complex_word(h):
        return {feature for affix in h.get_affix_list() for feature in affix.features}

    # Definition for pro-extraction
    def extract_pro(self):
        # Internal functions
        def valued_phi(h):
            return {f for f in h.features if f[:4] == 'PHI:' and f[-1] != '_'}
        def all_phi(h):
            return {f for f in h.features if f[:4] == 'PHI:'}
        def phi_conflict(h):
            for f in self.features:
                if f[:4] == 'PHI:' and f[-1] != '_':  # Check only valued phi-features
                    for g in h.features:
                        if g[:4] == 'PHI:' and g[-1] != '_':  # Check only valued phi-features
                            f_type = f.split(':')[1]
                            g_type = g.split(':')[1]
                            f_value = f.split(':')[2]
                            g_value = g.split(':')[2]
                            # If there is a feature type T with two difference values, we have feature conflict
                            if f_type == g_type and f_value != g_value:
                                return True
            return False

        # Main function
        if 'ARG' in self.features:
            if 'VAL' in self.features:
                phi_set = valued_phi(self)
            else:
                phi_set = all_phi(self)
            if phi_set:
                pro = PhraseStructure()
                pro.features = pro.features | phi_set
                pro.features.add('D')
                pro.features.add('PF:pro')
                pro.features.add('pro')
                if not phi_conflict(pro):
                    return pro
        return None

    # Definition for unvalued phi-features
    def is_unvalued(self):
        return {f for f in self.features if f[:4] == 'PHI:' and f[-1] == '_'}

    # Definition for valued phi-features
    def get_valued_features(self):
        return {f for f in self.features if f[:4] == 'PHI:' and f[-1] != '_'}

    # Definition for the notion of phi-set for head H
    def get_phi_set(self):
        return {f for f in self.head().features if f[:4] == 'PHI:' and len(f.split(':')) == 3}

    # Return a list of unvalued features
    def get_unvalued_features(self):
        return {f for f in self.features if f[:4] == 'PHI:' and f[-1] == '_'}

    def has_op_feature(self):
        return {feature for feature in self.features if feature[:2] == 'OP'}

    # Recursive definition for criterial features (type ABAR:_) inside phrase
    def scan_criterial_features(self):
        set_ = set()
        if self.left_const and not self.left_const.find_me_elsewhere:
            set_ = set_ | self.left_const.scan_criterial_features()
        if self.right_const and not self.right_const.externalized() and not 'T/fin' in self.right_const.head().features:
            set_ = set_ | self.right_const.scan_criterial_features()
        if self.is_primitive():
            set_ |= {feature for feature in self.features if feature[:3] == 'OP:'}
        return set_

    # Definition for positive specifier selection
    def licensed_specifiers(self):
        return {f[5:] for f in self.features if f[:4] == 'SPEC'} | {f[6:] for f in self.features if f[:5] == '!SPEC'}

    # Definition for negative specifier selection
    def specifiers_not_licensed(self):
        return {f[6:] for f in self.features if f[:5] == '-SPEC'}

    # Definition for rate specifier selection (not used)
    def rare_specs(self):
        return {f[6:] for f in self.features if f[:5] == '%SPEC'}

    # Returns features without !
    def convert_features_for_parsing(self, features):
        return {f[1:] if f.startswith('!') else f for f in features}

    def is_clitic(self):
        if 'CL' in self.features:
            return True
        if 'CL' in self.head().features:
            if not self.head().has_affix() and self.head().internal:
                return True

    def quasi_auxiliary(self):
        return 'SEM:internal' in self.features_of_complex_word() and \
                'ASP' not in self.features_of_complex_word()

    def incorporation_features(self, direction):
        if direction == 'left':
            return {frozenset(feature[5:].split(",")) for feature in self.head().features if feature[:5] == 'LEFT:'}
        if direction == 'right':
            return {frozenset(feature[6:].split(",")) for feature in self.head().features if feature[:6] == 'RIGHT:'}

    def get_pf(self):
        return {feature[3:] for feature in self.features if feature[:3] == 'PF:'}

    # Return the phonological form of the constituent if any
    # Does some additional formatting
    def get_phonological_string(self):
        def show_affix(self):
            i = ''
            if self.is_primitive() and self.right_const:
                i = self.right_const.get_cats_string()
                if self.right_const.right_const:
                    i = i + ',' + show_affix(self.right_const)
            else:
                i = ''
            return i

        # Main function
        # We return phonological features but not inflectional features
        pfs = [f[3:] for f in self.features if f[:2] == 'PF']
        if self.has_affix():
            affix_str = show_affix(self)
            return '.'.join(sorted(pfs)) + '(' + affix_str + ')'
        else:
            return '.'.join(sorted(pfs))

    # Definition for semantic features (access keys to concepts)
    def LF_features(self):
        lfs = [f[3:] for f in self.features if f[:2] == 'LF']
        return '.'.join(sorted(lfs))

    def gloss(self):
        pf = ''
        if self.left_const:
            if 'null' in self.left_const.features:
                pf = pf + '__'
            else:
                pf = pf + self.left_const.gloss() + ' '
        if self.right_const:
            if 'null' in self.right_const.features:
                pf = pf + '__'
            else:
                pf = pf + self.right_const.gloss() + ' '
        if self.is_primitive():
            pf = pf + self.LF_features()
        return pf

    # This function tries to create "informative" representation of the categories of the constituent ps
    def get_cats_string(self):
        major_cats = ''.join(sorted([feature for feature in self.head().features if feature in major_category]))
        if major_cats == 'Neg/fin':
            major_cats = 'Neg'
        if self.is_complex():
            suffix = 'P'
        else:
            suffix = ''
        if not major_cats:
            major_cats = 'X'
        return major_cats + suffix

    #
    #
    # Block 5. Unclassified functions
    #
    #

    # Copies a constituent and does all other operations required for reconstruction
    def copy_from_memory_buffer(self, babtize='1'):

        # Internal functions
        def remove_tail_features(ps):
            if not ps.is_primitive():
                remove_tail_features(ps.left_const)
                remove_tail_features(ps.right_const)
            else:
                remove_set = set()
                for f in ps.features:
                    if f[:4] == 'TAIL':
                        remove_set.add(f)
                ps.features = ps.features.difference(remove_set)

        def silence_phonologically(h):
            if not h.features:
                h.features = {'null'}
            else:
                h.features.add('null')
            if h.left_const:
                silence_phonologically(h.left_const)
            if h.right_const:
                silence_phonologically(h.right_const)

        # Main function
        if self.identity == '':
            self.identity = babtize

        # Copy
        self_copy = self.copy()              # Copy the constituent
        self_copy.find_me_elsewhere = False  # Copy is marked for being where it is
        silence_phonologically(self_copy)    # Silence the new constituent phonologically
        self.find_me_elsewhere = True        # Mark that the constituent has been copied
                                             # Neutralize the original
        remove_tail_features(self)           # Remove tail-features from the original

        return self_copy

    # Definition of features that are used at LF-interface (only obligatory selection counts)
    def for_LF_interface(self, features):
        set_of_features = set()
        for f in features:
            if f[0] == '!' or f[0] == '-':
                set_of_features.add(f)
        return set_of_features

    def bottom_affix(self):
        if not self.is_primitive:
            return None
        ps_ = self
        while ps_.right_const:
            ps_ = ps_.right_const
        return ps_

    def illustrate(self):
        if self.is_primitive():
            if not self.get_phonological_string():
                return '?'
            else:
                if self.adjunct:
                    return '<' + self.get_phonological_string() + '>'
                else:
                    return self.get_phonological_string()

        prefix= ''

        if 'null' in self.features:
            if self.adjunct:
                return '<' + prefix + self.left_const.illustrate() + ' ' \
                       + self.right_const.illustrate() + '>'
            else:
                return '['+ prefix + self.left_const.illustrate() + ' ' \
                   + self.right_const.illustrate() + ']'
        else:
            if self.adjunct:
                return f'<' + prefix \
                       + self.left_const.illustrate() + ' ' \
                       + self.right_const.illustrate() + '>'
            else:
                return f'[' + prefix\
                       + self.left_const.illustrate() + ' ' \
                       + self.right_const.illustrate() + ']'

    def illustrate_spellout(self):

        if self.identity != '':
            id_str = ':' + self.identity
        else:
            id_str = ''

        if self.is_primitive():
            if not self.get_phonological_string():
                return '?'
            else:
                if self.adjunct:
                    return '<' + self.get_phonological_string() + '>'
                else:
                    return self.get_phonological_string()

        prefix= ''

        if 'null' in self.features:
            if self.adjunct:
                return '<__>' + id_str
            else:
                return '__' + id_str
        else:
            if self.adjunct:
                return f'<' + prefix \
                       + self.left_const.illustrate_spellout() + ' ' \
                       + self.right_const.illustrate_spellout() + '>' + id_str
            else:
                return f'[' + prefix\
                       + self.left_const.illustrate_spellout() + ' ' \
                       + self.right_const.illustrate_spellout() + ']' + id_str

    #   Standard output function that shows the phrase structure
    def __str__(self):
        # This adds a unique name to the constituent if it has one, so we can trace chains in the output
        if self.identity != '':
            index_str = ':'+self.identity
        else:
            index_str = ''
        # By writing something here you can track which elements are copied in the final solution
        if self.find_me_elsewhere:
            index_str = index_str + ''
        if self.features and 'null' in self.features:
            if self.adjunct:
                return '<__>' + index_str       # Adjuncts are represented as <,>
            else:
                return '__' + index_str
                # return '(' + self.get_cats_string() + ')' + index_str   # Regular constituents as [,]
        if self.is_primitive():
            if not self.get_phonological_string():
                return '?'
            else:
                if self.adjunct:
                    return '<' + self.get_phonological_string() + '>'
                else:
                    if self.extract_pro():
                        return self.get_phonological_string()
                        # return self.get_pro_type() + '.' + self.get_pf()
                    else:
                        return self.get_phonological_string()
        else:
            if self.adjunct:
                return f'<{self.left_const} {self.right_const}>' + index_str
            else:
                return f'[{self.left_const} {self.right_const}]' + index_str


    # This function tidies the names for constituents
    def tidy_names(self, counter):

        # Internal function
        def rebaptize(h, old_name, new_name):
            if h.identity == old_name:
                if not h.rebaptized:
                    h.identity = new_name
                    h.rebaptized = True
            if h.left_const:
                rebaptize(h.left_const, old_name, new_name)
            if h.right_const:
                rebaptize(h.right_const, old_name, new_name)
            return

        if self.identity != '' and not self.rebaptized:
            rebaptize(self.top(), self.identity, str(counter))
            counter = counter + 1
        if self.left_const:
            counter = self.left_const.tidy_names(counter)
        if self.right_const:
            counter = self.right_const.tidy_names(counter)
        return counter

    def size(self):
        size_ = 1
        if self.left_const:
            size_ = size_ + self.left_const.size()
        if self.right_const:
            size_ = size_ + self.right_const.size()
        return size_