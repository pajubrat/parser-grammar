# This class defines basic linguistic competence, i.e. phrase structures and operations on phrase structure
from support import log
from LF import LF

major_category = {'N', 'Neg', 'Neg/fin', 'P', 'D', 'C', 'A', 'v', 'V', 'ADV', 'Q', 'NUM', 'T', 'TO/inf', 'A/inf', 'FORCE', '0', 'a', 'b', 'c', 'd', 'x', 'y', 'z'}
case_features = {'NOM', 'ACC', 'PAR', 'GEN', '0_ACC', 'n_ACC', 't_ACC', 'DAT', 'POSS'}

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
        self.internal = False   # Tells if the constituent is word-internal; a more intuitive implementation is required
        self.adjunct = False    # Whether the constituent is stored in the secondary working space (i.e. is an adjunct)
        self.incorporated = False  # Tells if the constituent was incorporated
        self.find_me_elsewhere = False
        self.identity = ''      # A unique handler/name for the constituent
        self.rebaptized = False  # Support variable used in the creation of chain numbering
        self.x = 0
        self.y = 0

    #
    #
    # BLock 1. Other structure building operations
    #
    #

    def combine_with(self, ps, direction):

        if direction == 'left':
            new_ps = PhraseStructure(ps, self)
        else:
            new_ps = PhraseStructure(self, ps)
            if self.adjunct and self.is_primitive():
                new_ps.adjunct = True
                self.adjunct = False
        return new_ps

    def substitute(self, new_ps, old_mother, left):
        if not left:
            old_mother.right_const = new_ps
        else:
            old_mother.left_const = new_ps
        new_ps.mother = old_mother

    def merge(self, ps, direction='right'):

        old_mother = self.mother
        if self.is_left():
            left = True
        else:
            left = False

        new_constituent = self.combine_with(ps, direction)
        if old_mother:
            self.substitute(new_constituent, old_mother, left)

        return new_constituent.top()

    # Simpler notation for Merge
    def __add__(self, other):
        return self.merge(other, 'right')

    # Definition for an operation that removes an element from the phrase structure
    def remove(self):
        mother = self.mother
        sister = self.geometrical_sister()
        grandparent = self.mother.mother

        sister.mother = sister.mother.mother
        if mother.is_right():
            grandparent.right_const = sister
            self.mother = None
        elif mother.is_left():
            grandparent.left_const = sister
            self.mother = None

    def sink(self, ps):
        bottom = self.bottom_affix()
        bottom.right_const = ps
        ps.mother = bottom
        bottom.left_const = None
        return self.top()

    def get_specifier_anchor(self):
        if self.is_left():
            return self.mother
        else:
            return self

    def visible_head(self):
        if self.is_primitive():
            return self
        elif self.left_const.is_primitive():
            return self.left_const
        else:
            return None

    def walk_downstream_geometrically(self):
        ps_ = self
        if ps_.is_complex() and ps_.right_const:
            return ps_.right_const
        else:
            return None

    def spec_match(self, spec):
        if 'SPEC:*' in self.features or '!SPEC:*' in self.features:
            return True
        for feature_in_head in self.for_parsing(self.specs()):
            for feature_in_spec in spec.head().features:
                if feature_in_head == feature_in_spec:
                    return True
        return False


    #
    #
    # Block 2. Definitions for basic grammatical relations
    #
    #
    # Definition for head (also label) of a phrase structure
    def head(self):

        if self.is_primitive():
            return self
        else:
            if self.left_const.is_primitive():
                return self.left_const
            if self.right_const.is_primitive():
                return self.right_const
            if not self.left_const.is_primitive() and not self.right_const.is_primitive():
                if self.right_const.adjunct:
                    return self.left_const.head()
                return self.right_const.head()

    # Definition for sisterhood
    def sister(self):
        ps_ = self
        while ps_.mother:
            if ps_.is_right() and ps_.adjunct:
                return None
            if ps_.is_left() and not ps_.mother.right_const.adjunct:
                return ps_.mother.right_const
            if ps_.is_right():
                return ps_.mother.left_const
            ps_ = ps_.mother
        return None

    def selected_sister(self):
        if self.is_primitive() and not self.sister():
            return None
        if self.sister().is_complex():
            if self.sister().is_left():
                return self.sister()
            elif self.sister().is_right() and not self.sister().adjunct:
                return self.sister()
        else:
            if self.sister().is_right():
                return self.sister()
            else:
                return None

    def size(self):
        size_ = 1
        if self.left_const:
            size_ = size_ + self.left_const.size()
        if self.right_const:
            size_ = size_ + self.right_const.size()
        return size_

    # Definition for complex constituent
    def is_complex(self):
        return not self.is_primitive()

    # XP in [XP [H YP]] and [XP H]
    def local_phrasal_specifier(self):
        if self.is_primitive() and \
                self.is_left() and \
                self.mother.sister() and \
                not self.mother.adjunct and \
                self.mother.sister().is_left() and \
                self.mother.sister().is_complex() and \
                self.mother.mother.head() == self.head():
            return self.mother.sister()
        if self.is_primitive() and self.is_right() and self.sister() and self.sister().is_complex():
            return self.sister()

    # Definition for the relation of local specifier or local edge
    def local_edge(self):
        if self.local_phrasal_specifier():
            return self.local_phrasal_specifier()
        if self.extract_pro():
            return self.extract_pro()

    # Definition for the notion of edge (also generalized specifier)
    def edge(self):

        if self.is_complex():
            return None
        if self.is_right():
            ps_ = self
        else:
            ps_ = self.mother

        list = []

        # Condition 1. Collect all complex left sisters for which there exists an upstream path from H
        while ps_ and ps_.sister() and (ps_.sister().is_left() and ps_.sister().is_complex()):
            list.append(ps_.sister())
            ps_ = ps_.walk_upstream()

        # Condition 2. If nothing is found, try to extract the pro-element
        if not list:
            if self.extract_pro():
                list.append(self.extract_pro())

        return list

    # Definition for complement
    def complement(self):
        if self.sister() and self.sister().is_right():
            return self.sister()
        else:
            return None

    # Definition for geometrical sister
    def geometrical_sister(self):
        if self.mother:
            if self.is_left():
                return self.mother.right_const
            if self.is_right():
                return self.mother.left_const
        return None

    def Abar_movable(self):
        if self.scan_criterial_features():
            return True
        elif 'A/inf' in self.head().features:
            return True
        else:
            return False

    def must_have_head(self):
        if self.adjunct and not self.scan_criterial_features():
            return False
        else:
            return True

    def get_phrasal_left_sister(self):
        if self.sister() and not self.sister().is_primitive() and self.sister().is_left():
            return self.sister()
        else:
            return None

    # Definition for selector
    def selector(self):
        feature_vector = self.feature_vector()
        if len(feature_vector) == 1:
            return None
        else:
            return feature_vector[1]

    # Definition for property X has a theta assigner P
    def get_theta_assigner(self):
        if self.sister() and self.sister().is_primitive():
            return self.sister
        if self.container_head() and self in self.container_head().edge():
            return self.container_head()

    # Definition of max
    def max(self):
        ps_ = self
        last = self
        while ps_ and ps_.head() == self.head():
            last = ps_
            ps_ = ps_.walk_upstream()
        return last

    # Definition of left
    def is_left(self):
        if self.mother and self.mother.left_const == self:
            return True
        else:
            return False

    # Definition of right
    def is_right(self):
        if self.mother and self.mother.right_const == self:
            return True
        else:
            return False

    # Definition of primitive constituent
    def is_primitive(self):
        if self.right_const and self.left_const:
            return False
        else:
            return True

    def bottom_affix(self):
        ps_ = self
        while ps_.right_const:
            ps_ = ps_.right_const
        return ps_

    # Definition of bottom node
    def bottom(self):
        ps_ = self
        while not ps_.is_primitive():
            ps_ = ps_.right_const
        return ps_


    def causes_intervention(self, feature, phrase_structure):
        if self != phrase_structure.minimal_search()[0]:                    # Ignore the first node
            if feature in self.sister().features:
                log(f'\t\t\t\t\tFeature {feature} causes HM intervention.')
                return True
            else:
                return False

    def detect(self, property=''):
        if property == 'complex head':
            complex_head = None
            if self.is_primitive() and self.has_affix():
                complex_head = self
            elif self.left_const and self.left_const.is_primitive() and self.left_const.has_affix():
                complex_head = self.left_const
            return complex_head
        return None

    def minimal_search(self):
        return [node for node in self]

    def is_primitive_head(self):
        if self.is_primitive() and not self.has_affix():
            return True
        else:
            return False

    def is_complex_head(self):
        if self.is_primitive() and self.has_affix():
            return True
        else:
            return False

    # Definition for geometrical upstream walk
    def walk_upstream_geometrically(self):
        if self.mother:
            return self.mother
        else:
            return None

    # Definition for upstream walk
    def walk_upstream(self):
        if self.mother:
            ps_ = self.mother

            # Dodge right adjuncts
            while ps_.right_const.adjunct:
                if ps_.mother:
                    ps_ = ps_.mother
                else:
                    return ps_
            return ps_
        else:
            return None

    def top(self):
        result = self
        while result.mother:
            result = result.mother
        return result

    def node_at(self, position):
        ps_ = self.top()
        for pos in range(0, position):
                ps_ = ps_.right_const
        return ps_

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

    # Block 3. Nonlocal dependencies and operations
    #
    def probe(self, probe_label, goal_feature):
        if self.is_primitive() and self.is_right() or not self.sister():
            return None
        ps_ = self.sister()
        # --------------------- minimal top-down search --------------------------------
        for node in ps_:
            if node.is_primitive():
                if goal_feature in node.features:
                    return node
                else:
                    return None
            else:
                if node.left_const.head().features and goal_feature in node.left_const.head().features:
                    return node.left_const
                elif goal_feature[:4] == 'TAIL' and goal_feature[5:] in node.left_const.scan_criterial_features():
                    return node.left_const
            if node.left_const.is_primitive() and node.left_const.features and probe_label.issubset(node.left_const.features):
                return None
        # -------------------------------------------------------------------------------------------

    def primitive_left_sister(self):
        if self.geometrical_sister() and \
                self.geometrical_sister().is_primitive() and \
                self.geometrical_sister().is_left() and not \
                self.geometrical_sister() == self.complement():
            return self.geometrical_sister()

    def feature_vector(self):
        feature_vector = [self]
        iterator = self
        while iterator and iterator.mother:
            if iterator.primitive_left_sister():
                feature_vector.append(iterator.geometrical_sister())
            iterator = iterator.walk_upstream_geometrically()
        return feature_vector

    def external_tail_head_test(self):
        tail_sets = self.get_tail_sets()
        if not tail_sets:
            return True
        else:
            tests_checked = set()
            for tail_set in tail_sets:
                if self.locality_condition(tail_set):   # Strong test for any tail feature
                    tests_checked.add(tail_set)
                if 'ADV' not in self.features:
                    if self.path_condition(tail_set):   # Weaker test for everything except ADV
                        tests_checked.add(tail_set)
                    else:
                        return False
            if tests_checked & tail_sets == tail_sets:  # Check that all tail sets have been checked
                return True
            else:
                return False

    def internal_tail_head_test(self):
        tail_sets = self.get_tail_sets()
        if not tail_sets:
            return True
        else:
            for tail_set in tail_sets:
                if self.path_condition(tail_set, 'internal'):
                    return True
                else:
                    return False
        return True

    def get_max(self):
        ps_ = self
        while ps_.mother and ps_.mother.head() == self.head():
            ps_ = ps_.walk_upstream()
        return ps_

    def locality_condition(self, tail_set):
        if self.get_max() and self.get_max().mother:
            if self.get_max().mother.head().match_features(tail_set) == 'complete match' and self.mysterious_property():
                return True
            elif self.get_max().mother.sister() and self.get_max().mother.sister().match_features(tail_set) == 'complete match':
                return True

    def path_condition(self, tail_set, variation='external'):
        for const in self.feature_vector():
            if const is not self:
                for m in const.get_affix_list():
                    test = m.match_features(tail_set)
                    if test == 'complete match':
                        return True
                    elif test == 'partial match':
                        return False
                    elif test == 'negative match':
                        return False

        # Feature were not checked against anything
        if variation=='external' and not self.negative_features(tail_set):
            return False    # Strong test: reject (tail set must be checked)
        else:
            return True     # Weak test: accept still (only look for violations)

    def negative_features(self, features_to_check):
        return {feature[1:] for feature in features_to_check if feature[0] == '*'}

    def positive_features(self, features_to_check):
        return {feature for feature in features_to_check if feature[0] != '*'}

    # Definition for feature match
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

    # Recursive definition for contains-feature-F for a phrase
    def contains_feature(self, feature):
        if self.left_const and self.left_const.contains_feature(feature):
            return True
        if self.right_const and self.right_const.contains_feature(feature):
            return True
        if self.is_primitive:
            if feature in self.features:
                return True
            else:
                return False

        return False

    #
    #
    # Block 4. Functions which return properties from inside a head
    #
    #
    def EPP(self):
        if 'SPEC:*' in self.features or '!SPEC:*' in self.features:
            return True
        else:
            return False

    def adjoinable(self):
        if 'adjoinable' in self.features and '-adjoinable' not in self.features:
            return True
        else:
            return False


    def finite(self):
        if 'FIN' in self.features or 'T/fin' in self.features or 'Neg/fin' in self.features:
            return True
        else:
            return False

    # Returns the union of features of head and all its affixes
    def get_all_features_of_complex_word(self):
        if self.is_complex():
            head = self.head()
        else:
            head = self
        complex_word_features = head.features
        for affix in head.get_affix_list():
            complex_word_features = complex_word_features | affix.features
        return complex_word_features

    # Return a list of affixes inside a grammatical head (including the head itself)
    def get_affix_list(self):
        lst = [self]
        iterator_ = self
        while iterator_:
            if iterator_.right_const:
                iterator_ = iterator_.right_const
                lst.append(iterator_)
            else:
                iterator_ = None
        return lst

    # Returns the highest affix (if available)
    def get_affix(self):
        if not self.left_const and self.is_primitive():
            return self.right_const
        else:
            return None

    # Returns a set of unvalued phi-features
    def get_unvalued_features(self):
        return {f for f in self.features if f[:4] == 'PHI:' and f[-1] == '_'}

    # Definition for pro-extraction
    def extract_pro(self):
        if 'ARG' in self.features:
            if 'VAL' in self.features:
                phi_set = self.valued_phi()
            else:
                phi_set = self.all_phi()
            if phi_set:
                pro = PhraseStructure()
                pro.features = pro.features | phi_set
                pro.features.add('D')
                pro.features.add('PF:pro')
                pro.features.add('pro')
                if not pro.phi_conflict():
                    return pro
        return None

    def valued_phi(self):
        return {f for f in self.features if f[:4] == 'PHI:' and f[-1] != '_'}

    def all_phi(self):
        return {f for f in self.features if f[:4] == 'PHI:'}

    # Definition for affix
    def has_affix(self):
        if self.right_const and not self.left_const:
            return True
        else:
            return False

    # Definition for the concept of word internal
    def is_word_internal(self):
        return self.internal

    # Definition for adjoinable phrase
    def is_adjoinable(self):
        if self.adjunct:
            return True
        if 'adjoinable' in self.head().features:
            return True
        else:
            return False

    # This involves empirical issues that I don't understand
    def mysterious_property(self):
        if 'D' in self.features and not 'TAIL:INF,A/HEAD' in self.features:
            return False
        else:
            return True

    # Definition for well-formed phi-set
    def get_phi_set(self):
        head_ = self.head()
        return {f for f in head_.features if f[:4] == 'PHI:' and len(f.split(':')) == 3}

    # Definition of bottom affix
    def get_bottom_affix(self):
        if not self.is_primitive:
            return None

        ps_ = self
        while ps_.right_const:
            ps_ = ps_.right_const

        return ps_

    # Definition for tail sets
    def get_tail_sets(self):

        tail_features = set()
        constituent_ = self.head()

        for f in constituent_.features:
            if f[:4] == 'TAIL':
                tail_features.add(frozenset((f[5:].split(','))))

        if tail_features:
            return tail_features
        else:
            return None

    # Definition for scope-operator that can bind a variable at LF
    def is_scope_operator(self):
        operator_features = {feature for feature in self.features if feature[:2] == 'OP'}
        if 'FIN' in self.features and operator_features:
            return True
        else:
            return False

    def has_op_feature(self):
        return {feature for feature in self.features if feature[:2] == 'OP'}

    # Recursive definition for criterial features (type ABAR:_) inside phrase
    def scan_criterial_features(self):

        set_ = set()

        if self.left_const and not self.left_const.find_me_elsewhere:
            set_ = set_ | self.left_const.scan_criterial_features()

        if self.right_const and not self.right_const.adjunct and not 'T/fin' in self.right_const.head().features:
            set_ = set_ | self.right_const.scan_criterial_features()

        if self.is_primitive():
            set_ |= {feature for feature in self.features if feature[:3] == 'OP:'}
        return set_

    def is_functional(self):
        if '!COMP:*' in self.features:
            return True

    # Definition for phase (used by Agree-1)
    def is_phase(self):
        if 'v' in self.features or 'C' in self.features or 'FORCE' in self.features or 'COPULA' in self.features:
            return True
        else:
            return False

    # Definition for mandatory complement selection
    def get_mandatory_comps(self):
        return  {f[6:] for f in self.features if f[:5] == '!COMP' and f != '!COMP:*'}

    # Definition for complement selection
    def get_comps(self):
        return {f[5:] for f in self.features if f[:4] == 'COMP'} | {f[6:] for f in self.features if f[:5] == '!COMP'}

    # Definition for complements selection for a complex head
    def get_affix_comps(self):
        set_ = set()
        affixes = self.get_affix_list()
        for affix in affixes:
            for f in affix.features:
                if f[:4] == 'COMP':
                    set_.add(f[5:])
                if f[:5] == '!COMP':
                    set_.add(f[6:])

        return set_

    def get_case(self):
        for label in self.features:
            if label in case_features:
                return '['+label+']'
        return ''

    # Definition for negative complement selection
    def get_not_comps(self):
        return {f[6:] for f in self.features if f[:5] == '-COMP'}

    # Definition for positive specifier selection
    def specs(self):
        return {f[5:] for f in self.features if f[:4] == 'SPEC'} | {f[6:] for f in self.features if f[:5] == '!SPEC'}

    # Definition for negative specifier selection
    def get_not_specs(self):
        return {f[6:] for f in self.features if f[:5] == '-SPEC'}

    # Definition for rate specifier selection (not used)
    def get_rare_specs(self):
        return {f[6:] for f in self.features if f[:5] == '%SPEC'}

    # Returns features without !
    def for_parsing(self, features):
        return {f[1:] if f.startswith('!') else f for f in features}

    # Return the phonological form of the constituent if any
    # Does some additional formatting
    def get_pf(self):

        # We return phonological features but not inflectional features
        pfs = [f[3:] for f in self.features if f[:2] == 'PF']
        if self.has_affix():
            affix_str = self.show_affix()
            return '.'.join(sorted(pfs)) + '(' + affix_str + ')'
        else:
            return '.'.join(sorted(pfs))

    # Definition for semantic features (access keys to concepts)
    def get_lf(self):
        lfs = [f[3:] for f in self.features if f[:2] == 'LF']
        return '.'.join(sorted(lfs))

    #
    #
    # Block 5. Unclassified functions
    #
    #
    # Returns the node 'item' at the right edge
    # E.g. ps[3] = 3rd node at the right edge
    def __getitem__(self, position):

        iterator_ = 0
        ps_ = self

        while ps_:
            if iterator_ == position:
                return ps_

            # No more constituents to travel
            if ps_.is_primitive():
                raise IndexError

            # ps_ = [X(P) Y(P)], selection must be made
            else:
                # Take Y if labelling takes Y (ignore left specifiers, adjuncts)
                if ps_.head() == ps_.right_const.head():
                     ps_ = ps_.right_const
                # Labelling picks X in [X Y]
                else:
                    # If X is complex, pick it
                    if ps_.left_const.is_complex():
                        ps_ = ps_.left_const
                    else:
                        # If X is primitive, take Y if it is not adjunct
                        if ps_.right_const.adjunct:
                            ps_ = ps_.left_const
                        # If y is primitive and Y is selected sister, continue with Y
                        else:
                            ps_ = ps_.right_const

            iterator_ = iterator_ + 1

    # Copies a constituent and does all other operations required for reconstruction
    def copy_from_memory_buffer(self, babtize='1'):

        # Removes tail-features (if any) from a constituent
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

        # --- Main function begins here --- #

        if self.identity == '':
            self.identity = babtize

        # Copy
        self_copy = self.copy()              # Copy the constituent
        self_copy.find_me_elsewhere = False  # Copy is marked for being where it is
        self_copy.silence_phonologically()   # Silence the new constituent phonologically
        self.find_me_elsewhere = True        # Mark that the constituent has been copied
                                             # Neutralize the original
        remove_tail_features(self)           # Remove tail-features from the original

        return self_copy

    # Counts the number of (in situ non-adjunct) specifiers
    def count_specifiers(self):
        ps_ = self.mother
        count = 0
        # ---------------- while loop begins ----------------------#
        while ps_ and ps_.sister() and \
                (ps_.sister().is_left() and \
                not ps_.sister().is_primitive()) and \
                not ps_.sister().find_me_elsewhere and \
                not ps_.sister().adjunct:
            count = count + 1
            ps_ = ps_.walk_upstream()
        # ---------------- while loop ends --------------------------#
        return count

    def container_head(self):
        if self.mother:
            return self.mother.head()
        else:
            return self.head()

    # Definition for phi-feature conflict
    def phi_conflict(self):
        for f in self.features:
            if f[:4] == 'PHI:' and f[-1] != '_':  # Check only valued phi-features
                for g in self.features:
                    if g[:4] == 'PHI:' and g[-1] != '_':  # Check only valued phi-features
                        f_type = f.split(':')[1]
                        g_type = g.split(':')[1]
                        f_value = f.split(':')[2]
                        g_value = g.split(':')[2]
                        # If there is a feature type T with two difference values, we have feature conflict
                        if f_type == g_type and f_value != g_value:
                            return True
        return False

    # Definition for LF-legibility
    def LF_legibility_test(self):

        def detached(ps):
            ps.mother = None
            return ps

        lf = LF()
        lf.test(detached(self.copy()))
        return lf

    # Separate phrase structure from its host and return the mother (for later reattachment)
    def detach(self):

        if self.mother:
            original_mother = self.mother
            self.mother = None
        else:
            original_mother = None

        return original_mother

    # Definition for finiteness (trivial)
    def is_finite(self):
        head = self.head()
        if 'FIN' in head.features:
            return True
        else:
            return False

    # Definition of features that are used at LF-interface (only obligatory selection counts)
    def for_LF_interface(self, features):
        set_of_features = set()
        for f in features:
            if f[0] == '!' or f[0] == '-':
                set_of_features.add(f)
        return set_of_features

    # Definition for selection match, i.e. whether self (label) selects for head (label)
    # This duplicates functionality in the LF class, all this must be unified
    def selects(self, selectee):
        selector = self
        if selector.has_affix():
            selector = selector.get_bottom_affix()

        # Search positive selection feature
        if selectee.features & selector.get_comps():
            return True
        else:
            return False

    # Recursive definition for phonological silencing
    def silence_phonologically(self):

        # Add feature [null]
        if not self.features:
            self.features = {'null'}
        else:
            self.features.add('null')

        # Silence also constituents
        if self.left_const:
            self.left_const.silence_phonologically()
        if self.right_const:
            self.right_const.silence_phonologically()

    #
    #
    # Block 6. Support functions
    #
    #
    def get_valued_phi_set(self):

        phi_set = set()

        if self.is_complex():
            if self.left_const:
                phi_set = self.left_const.get_valued_phi_set()
            if self.right_const:
                phi_set = phi_set | self.right_const.get_valued_phi_set()
        else:
            if 'PHI:NUM:SG' in self.features and 'PHI:PER:1' in self.features:
                phi_set.add(f'{self}.1sg')
            elif 'PHI:NUM:SG' in self.features and 'PHI:PER:2' in self.features:
                phi_set.add(f'{self}.2sg')
            elif 'PHI:NUM:SG' in self.features and 'PHI:PER:3' in self.features:
                phi_set.add(f'{self}.3sg')
            elif 'PHI:NUM:PL' in self.features and 'PHI:PER:1' in self.features:
                phi_set.add(f'{self}.1pl')
            elif 'PHI:NUM:PL' in self.features and 'PHI:PER:2' in self.features:
                phi_set.add(f'{self}.2pl')
            elif 'PHI:NUM:PL' in self.features and 'PHI:PER:3' in self.features:
                phi_set.add(f'{self}.3pl')

        if 'PHI:DET:GEN' in self.features:
            phi_set.add(f'{self}.generic')

        return phi_set

    def show_affix(self):
        i = ''
        if self.is_primitive() and self.right_const:
            i = self.right_const.get_cats_string()
            if self.right_const.right_const:
                i = i + ',' + self.right_const.show_affix()
        else:
            i = ''
        return i

    def show_primitive_constituents(self):
        def sorted_by_relevance(set):
            first_class = {feature for feature in set if feature[:2] == 'PF' or feature[:2] == 'LF'}
            second_class = {feature for feature in set if feature in major_category}
            third_class = {feature for feature in set if feature in {'VAL', '-VAL', 'ARG', '-ARG', 'ASP', 'INF'}}
            fourth_class = {feature for feature in set if feature[:3] == 'PHI'}
            fifth_class = {feature for feature in set if feature[:3] == 'SEM'}
            sixth_class = {feature for feature in set if feature[:4] == 'TAIL'}
            residuum = set - first_class - second_class - third_class - fourth_class - fifth_class - sixth_class
            return sorted(first_class) + \
                   sorted(second_class) + \
                   sorted(third_class) + \
                   sorted(fourth_class) + \
                   sorted(fifth_class) + \
                   sorted(sixth_class) + \
                   sorted(residuum)

        reply = ''
        if not self.is_primitive():
            reply += self.left_const.show_primitive_constituents()
            reply += self.right_const.show_primitive_constituents()
        else:
            reply += f'{self.get_pf():<10} {sorted_by_relevance(self.features)}\n'
        return reply

    def spellout(self):
        pf = ''
        if self.left_const:
            if 'null' in self.left_const.features:
                pf = pf + '__'
            else:
                pf = pf + self.left_const.spellout()

        if self.right_const:

            if 'null' in self.right_const.features:
                pf = pf + '__'
            else:
                pf = pf + self.right_const.spellout()

        if self.is_primitive():
            pf = pf + self.get_pf() + ' '

        return pf

    def gloss(self):

        pf = ''
        if self.left_const:
            if 'null' in self.left_const.features:
                pf = pf + '__'
            else:
                pf = pf + self.left_const.gloss()

        if self.right_const:
            if 'null' in self.right_const.features:
                pf = pf + '__'
            else:
                pf = pf + self.right_const.gloss()

        if self.is_primitive():
            pf = pf + self.get_lf()

        return pf

    def show_all_vectors(self):
        if not self.is_primitive():
            return self.left_const.show_all_vectors() + self.right_const.show_all_vectors()
        return f'{self}: {self.feature_vector()};  '

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

    def show(self, start=True, label_only=False):

        s = f'{self.get_cats_string()} = ' if start else ''

        if self.identity != '':
            id_str = ':'+self.identity
        else:
            id_str = ''

        if self.features and 'null' in self.features:
            return s + '__' + id_str
        elif self.is_primitive():
            if not self.get_pf():
                return s + '?'
            else:
                return s + self.get_cats_string()
        elif label_only:
            if self.adjunct:
                return f'{s}{self.get_cats_string()}' + id_str
            else:
                return f'{s}{self.get_cats_string()}' + id_str
        else:
            if self.right_const.adjunct:
                left = self.left_const.show(start=False)
                right = self.right_const.show(start=False, label_only=True)
            else:
                left = self.left_const.show(start=False, label_only=True)
                right = self.right_const.show(start=False)

            return f'{s}[{left} {right}]' + id_str

    def illustrate(self):

        if self.is_primitive():
            if not self.get_pf():
                return '?'
            else:
                if self.adjunct:
                    return '<'+self.get_pf()+'>'
                else:
                    return self.get_pf()

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
            if not self.get_pf():
                return '?'
            else:
                if self.adjunct:
                    return '<'+self.get_pf()+'>'
                else:
                    return self.get_pf()

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
            if not self.get_pf():
                return '?'
            else:
                if self.adjunct:
                    return '<'+self.get_pf()+'>'
                else:
                    if self.extract_pro():
                        return self.get_pf()
                        # return self.get_pro_type() + '.' + self.get_pf()
                    else:
                        return self.get_pf()
        else:
            if self.adjunct:
                return f'<{self.left_const} {self.right_const}>' + index_str
            else:
                return f'[{self.left_const} {self.right_const}]' + index_str

    # This function returns the type of pro-element depending on the valuation of (uD, up) probe
    # PRO = control pro
    # pro/x = antecedent requiring pro
    # pro = little-pro
    def get_pro_type(self):
        if 'PHI:NUM:_' in self.features and 'PHI:PER:_' in self.features and 'PHI:DET:_' in self.features:
            return '\N{GREEK CAPITAL LETTER PHI}'
        if 'PHI:NUM:_' not in self.features and 'PHI:PER:_' not in self.features and 'PHI:DET:_' in self.features:
            return '\N{GREEK SMALL LETTER PHI}/x'
        return '\N{GREEK SMALL LETTER PHI}'

    # More detailed output function
    def __repr__(self):
        if self.is_primitive():
            if not self.get_pf():
                return '?'
            else:
                return self.get_cats_string()
        else:
            return f'[{repr(self.left_const)} {repr(self.right_const)}]'

    def simple_tree(self):
        if self.is_primitive():
            pf_part = self.get_pf() or '?'
            id_part = f':{self.identity}' if self.identity else ''
            if self.adjunct:
                return f'<{pf_part}{id_part}>'
            else:
                return pf_part + id_part
        if self.adjunct:
            opener = '<'
            closer = '>'
        else:
            opener = '['
            closer = ']'
        if self.identity:
            id_part = f'{self.head().get_pf()}:{self.identity}'
        else:
            id_part = self.head().get_pf()
        return f'{opener}.{id_part} {self.left_const.simple_tree()} {self.right_const.simple_tree()}{closer}'

    def rebaptize(self, old_name, new_name):
        if self.identity == old_name:
            if not self.rebaptized:
                self.identity = new_name
                self.rebaptized = True
        if self.left_const:
            self.left_const.rebaptize(old_name, new_name)
        if self.right_const:
            self.right_const.rebaptize(old_name, new_name)
        return

    # This function tidies the names for constituents
    def tidy_names(self, counter):
        if self.identity != '' and not self.rebaptized:
            self.top().rebaptize(self.identity, str(counter))
            counter = counter + 1
        if self.left_const:
            counter = self.left_const.tidy_names(counter)
        if self.right_const:
            counter = self.right_const.tidy_names(counter)
        return counter