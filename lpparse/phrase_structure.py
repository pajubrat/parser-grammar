# This class defines basic linguistic competence, i.e. phrase structures and operations on phrase structure
from collections import namedtuple
from itertools import takewhile
from support import log

major_category = {'N', 'Neg', 'Neg/fin', 'P', 'D', 'φ', 'C', 'A', 'v', 'V', 'ADV', 'Q', 'NUM', 'T', 'TO/inf', 'VA/inf', 'A/inf', 'FORCE', '0', 'a', 'b', 'c', 'd', 'x', 'y', 'z'}

Result = namedtuple('Result', 'match_occurred outcome')

#class phrase structure
class PhraseStructure:
    resources = {"Asymmetric Merge": {"ms":0, "n":0},
                 "Sink": {"ms":0, "n":0}
                 }

    def __init__(self, left_constituent=None, right_constituent=None):
        self.left_const = left_constituent
        self.right_const = right_constituent
        if self.left_const:
            self.left_const.mother = self
        if self.right_const:
            self.right_const.mother = self
        self.mother = None
        self.features = set()
        self.active_in_syntactic_working_memory = True
        self.morphology = ''
        self.internal = False
        self.adjunct = False
        self.incorporated = False
        self.find_me_elsewhere = False
        self.identity = ''
        self.rebaptized = False
        self.x = 0
        self.y = 0
        if left_constituent and left_constituent.adjunct and left_constituent.is_primitive():
            self.adjunct = True
            left_constituent.adjunct = False

    #
    # Phrase structure geometry
    #
    def is_primitive(self):
        if not (self.right_const and self.left_const):
            return True

    def is_complex(self):
        return self.right_const and self.left_const

    def head(self):
        if self.is_primitive():
            return self
        if self.left_const.is_primitive():
            return self.left_const
        if self.right_const.is_primitive():
            return self.right_const
        if self.right_const.adjunct:
            return self.left_const.head()
        return self.right_const.head()

    def is_left(self):
        return self.mother and self.mother.left_const == self

    def is_right(self):
        return self.mother and self.mother.right_const == self

    def geometrical_sister(self):
        if self.is_left():
            return self.mother.right_const
        if self.is_right():
            return self.mother.left_const

    def proper_complement(self):
        if self.sister() and self.sister().is_right():
            return self.sister()

    def container_head(self):
        if self.mother:
            return self.mother.head()

    def is_adjoinable(self):
        return self.adjunct or ('adjoinable' in self.head().features and '-adjoinable' not in self.head().features)

    def max(probe):
        return [probe, *probe.edge()][-1].mother

    def sister(self):
        while self.mother:
            if self.is_left():
                if not self.geometrical_sister().adjunct:
                    return self.geometrical_sister()
                else:
                    self = self.mother
            if self.is_right():
                if not self.adjunct:
                    return self.geometrical_sister()
                else:
                    return None

    def selected_sister(self):
        if self.sister() and (self.sister().is_complex() or (self.sister().is_primitive() and self.sister().is_right())):
            return self.sister()

    def bottom(self):
        while not self.is_primitive():
            self = self.right_const
        return self

    def top(self):
        while self.mother:
            self = self.mother
        return self

    #
    # Definitions for heads and terminal elements
    #
    def get_id(self):
        for f in self.features:
            if f[0] == '#':
                return f

    def has_affix(self):
        return self.right_const and not self.left_const

    def complex_head(self):
        return self.is_primitive() and self.has_affix()

    def EPP(self):
        return 'SPEC:*' in self.features or '!SPEC:*' in self.features

    def get_affix_list(self):
        lst = [self]
        while self.right_const and not self.left_const:
            lst.append(self.right_const)
            self = self.right_const
        return lst

    def features_of_complex_word(h):
        return {feature for affix in h.get_affix_list() for feature in affix.features}

    def get_valued_features(self):
        return {f for f in self.features if f[:4] == 'PHI:' and f[-1] != '_'}

    def get_phi_set(self):
        return {f for f in self.head().features if f[:4] == 'PHI:' and len(f.split(':')) == 3}

    def licensed_specifiers(self):
        return {f[5:] for f in self.features if f[:4] == 'SPEC'} | {f[6:] for f in self.features if f[:5] == '!SPEC'}

    def specifiers_not_licensed(self):
        return {f[6:] for f in self.features if f[:5] == '-SPEC'}

    def rare_specs(self):
        return {f[6:] for f in self.features if f[:5] == '%SPEC'}

    def convert_features_for_parsing(self, features):
        return {f[1:] if f.startswith('!') else f for f in features}

    def is_clitic(self):
        if 'CL' in self.features:
            return True
        if 'CL' in self.head().features and not self.head().has_affix() and self.head().internal:
            return True

    def bottom_affix(self):
        if self.is_primitive:
            while self.right_const:
                self = self.right_const
            return self

    #
    # Structure building
    #
    def merge_1(self, C, direction=''):
        local_structure = self.local_structure()                # [X...self...Y]
        new_constituent = self.asymmetric_merge(C, direction)   # A = [self H] or [H self]
        new_constituent.substitute(local_structure)             # [X...A...Y]
        return new_constituent.top()

    def asymmetric_merge(self, B, direction='right'):
        self.consume_resources('Asymmetric Merge')
        if direction == 'left':
            new_constituent = PhraseStructure(B, self)
        else:
            new_constituent = PhraseStructure(self, B)
        return new_constituent

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

    def sink(self, ps):
        self.consume_resources('Sink')
        bottom_affix = self.bottom().get_affix_list()[-1]   # If self is complex, we first take the right bottom node.
        bottom_affix.active_in_syntactic_working_memory = True
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
        ps_.active_in_syntactic_working_memory = self.active_in_syntactic_working_memory
        ps_.adjunct = self.adjunct
        ps_.find_me_elsewhere = self.find_me_elsewhere
        ps_.identity = self.identity
        return ps_

    def detach(self):
        is_right = self.is_right()
        original_mother = self.mother
        self.mother = None
        return original_mother, is_right

    #
    # Properties relating lexical features with phrase structure geometry
    #
    def complement_match(self, const):
        return self.licensed_complements() & const.head().features

    def licensed_complements(self):
        return {f[5:] for f in self.features if f[:4] == 'COMP'} | {f[6:] for f in self.features if f[:5] == '!COMP'}

    def licensed_specifiers(self):
        return {f[5:] for f in self.features if f[:4] == 'SPEC'} | {f[6:] for f in self.features if f[:5] == '!SPEC'}

    def complements_not_licensed(self):
        return {f[6:] for f in self.features if f[:5] == '-COMP'}

    def probe(self, feature, G):
        def inside_path(node):
            if node.is_primitive():
                return node
            return node.left_const.head()

        if self.sister():
            # --------------------- minimal search --------------------------------
            for node in self.sister():
                if G in inside_path(node).features:
                    return True
                if G[:4] == 'TAIL' and G[5:] in node.left_const.scan_criterial_features():
                    return True
                if feature.issubset(inside_path(node).features):
                    break
            # -------------------------------------------------------------------------

    def contains_feature(self, feature):
        if self.left_const and self.left_const.contains_feature(feature):
            return True
        if self.right_const and self.right_const.contains_feature(feature):
            return True
        if self.is_primitive:
            if feature in self.features:
                return True

    def find_occurrences_from(self, ps):
        def find_(identity, ps):
            chain = []
            if ps.is_complex():
                chain = chain + find_(identity, ps.left_const)
                chain = chain + find_(identity, ps.right_const)
            else:
                if identity in ps.features:
                    return [ps]
                if ps.complex_head():
                    chain = chain + find_(identity, ps.right_const)
            return chain

        identity = self.get_id()  # Returns the identity symbol (#1, ...)
        return find_(identity, ps)

    def __add__(self, incoming_constituent):
        return self.merge_1(incoming_constituent)

    #
    # Working memory related operations
    #
    def __getitem__(self, position):
        iter_ = 0
        ps_ = self
        while iter_ != position:
            if ps_.is_primitive():
                raise IndexError
            if ps_.head() == ps_.right_const.head():
                ps_ = ps_.right_const
            else:
                if ps_.left_const.is_complex():
                    ps_ = ps_.left_const
                else:
                    if ps_.right_const.adjunct:
                        ps_ = ps_.left_const
                    else:
                        ps_ = ps_.right_const
            iter_ = iter_ + 1
        return ps_

    def working_memory_path(probe):
        node = probe.mother
        working_memory = []
        #=============================================
        while node:
            if node.left_const.head() != probe:
                working_memory.append(node.left_const)
            node = node.walk_upwards()
        #==============================================
        return working_memory

    def walk_upwards(self):
        node = self.mother
        if self.is_left():
            while node and node.right_const.adjunct:
                node = node.mother
        return node

    def edge(probe):
        return list(takewhile(lambda x:x.mother.head() == probe, probe.working_memory_path()))

    def selector(self):
        return next((const for const in self.working_memory_path() if const.is_primitive()), None)

    def licensed_phrasal_specifier(self):
        return next((spec for spec in self.edge()
                     if 'φ' in spec.head().features and not spec.adjunct),
                    next((spec for spec in self.edge()
                          if 'φ' in spec.head().features and not spec.find_me_elsewhere), None))

    #
    # Tail processing
    #

    def tail_test(self):
        checked = {tail_set for tail_set in self.get_tail_sets() if self.strong_tail_condition(tail_set) or self.weak_tail_condition(tail_set)}
        return self.get_tail_sets() == checked

    def internal_tail_test(self):
        checked = {tail_set for tail_set in self.get_tail_sets() if self.weak_tail_condition(tail_set, 'internal')}
        return checked == self.get_tail_sets()

    def strong_tail_condition(self, tail_set):
        if self.precondition_for_strong_condition():
            if self.max() and self.max().mother:
                if self.max().mother.head().match_features(tail_set).outcome:
                    return True
                if self.max().mother.sister() and self.max().mother.sister().match_features(tail_set).outcome:
                    return True

    def precondition_for_strong_condition(self):
        if 'A' in self.head().features:
            return False
        if 'φ' in self.head().features and 'GEN' not in self.head().features:
            return False
        return True

    def weak_tail_condition(self, tail_set, variation='external'):
        if 'ADV' not in self.features:
            for m in (affix for node in self.working_memory_path() if node.is_primitive() for affix in node.get_affix_list()):
                test = m.match_features(tail_set)
                if test.match_occurred:
                    return test.outcome
        if variation=='external' and not self.negative_features(tail_set):
            return False    # Strong test: reject (tail set must be checked)
        else:
            return True     # Weak test: accept still (only look for violations)

    def match_features(self, features_to_check):
        if self.negative_features(features_to_check) & self.features:
            return Result(True, False)  # Match occurred, outcome negative
        if self.positive_features(features_to_check) & self.features:
            return Result(True, self.positive_features(features_to_check).issubset(
                self.features))  # Match occurred, outcome negative (partial match)/positive (full match)
        return Result(False, None)  # No match occurred, no outcome (usually evaluates into False)

    def negative_features(self, features_to_check):
        return {feature[1:] for feature in features_to_check if feature[0] == '*'}

    def positive_features(self, features_to_check):
        return {feature for feature in features_to_check if feature[0] != '*'}

    def get_tail_sets(self):
        return {frozenset(feature[5:].split(',')) for feature in self.head().features if feature[:4] == 'TAIL'}

    def extract_pro(self):
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

        #-----------------Main function--------------------------
        if 'ARG' in self.features:
            if 'VAL' in self.features:
                phi_set = {f for f in self.features if f[:4] == 'PHI:' and f[-1] != '_'}
            else:
                phi_set = {f for f in self.features if f[:4] == 'PHI:'}
            if phi_set:
                pro = PhraseStructure()
                pro.features = pro.features | phi_set
                pro.features.add('φ')
                pro.features.add('D')
                pro.features.add('PF:pro')
                pro.features.add('pro')
                if not phi_conflict(pro):
                    return pro
    #
    # Support functions
    #
    def get_pf(self):
        return {feature[3:] for feature in self.features if feature[:3] == 'PF:'}

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

        pfs = [f[3:] for f in self.features if f[:2] == 'PF']
        if self.has_affix():
            affix_str = show_affix(self)
            return '.'.join(sorted(pfs)) + '(' + affix_str + ')'
        else:
            return '.'.join(sorted(pfs))

    def info(self):
        info = [f[5:] for f in self.features if f[:5] == 'INFO:']
        return '.'.join(sorted(info))

    def gloss(self):
        def LF_features(head):
            lfs = [f[3:] for f in head.features if f[:2] == 'LF']
            return '.'.join(sorted(lfs))
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
            pf = pf + LF_features(self)
        return pf

    def get_cats_string(self):

        # Decide which labels to show if there are several
        features_to_consider = set(self.head().features)
        if 'φ' in features_to_consider:
            if {'D', 'NUM', 'D/REL', 'n', 'DET', 'QN'} & features_to_consider:
                features_to_consider.remove('φ')

        # Create the label string
        major_cats = ''.join(sorted([feature for feature in features_to_consider if feature in major_category]))
        if major_cats == 'Neg/fin':
            major_cats = 'Neg'
        if self.is_complex():
            suffix = 'P'
        else:
            suffix = ''
        if not major_cats:
            major_cats = 'X'
        return major_cats + suffix

    def copy_from_memory_buffer(self, babtize='1'):
        def silence_phonologically(h):
            if not h.features:
                h.features = {'null'}
            else:
                h.features.add('null')
            if h.left_const:
                silence_phonologically(h.left_const)
            if h.right_const:
                silence_phonologically(h.right_const)

        if self.identity == '':
            self.identity = babtize
        self_copy = self.copy()              # Copy the constituent
        self_copy.find_me_elsewhere = False  # Copy is marked for being where it is
        silence_phonologically(self_copy)    # Silence the new constituent phonologically
        self.find_me_elsewhere = True        # Mark that the constituent has been copied
        return self_copy

    def for_LF_interface(self, features):
        set_of_features = set()
        for f in features:
            if f[0] == '!' or f[0] == '-':
                set_of_features.add(f)
        return set_of_features

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
                return f'[' + prefix \
                       + self.left_const.illustrate() + ' ' \
                       + self.right_const.illustrate() + ']'

    def __str__(self):
        if self.identity != '':
            index_str = ':'+self.identity
        else:
            index_str = ''
        if self.find_me_elsewhere:
            index_str = index_str + ''
        if self.features and 'null' in self.features:
            if self.adjunct:
                return '<__>' + index_str
            else:
                return '__' + index_str
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
                if self.active_in_syntactic_working_memory:
                    return f'[{self.left_const} {self.right_const}]' + index_str
                else:
                    return f'[{self.left_const} {self.right_const}]' + index_str

    def tidy_names(self, counter):
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

    def consume_resources(self, resource_key):
        PhraseStructure.resources[resource_key]['n'] += 1