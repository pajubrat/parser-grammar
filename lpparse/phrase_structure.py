from collections import namedtuple
from itertools import takewhile


# New list (ordered hierarchically)
major_cats = ['N', 'Neg', 'Neg/fin', 'P', 'D', 'φ', 'C', 'A', 'v', 'V', 'Adv', 'Q', 'Num', 'Agr', 'Inf', 'T', 'FORCE', '0', 'a', 'b', 'c', 'd', 'x', 'y', 'z']

Result = namedtuple('Result', 'match_occurred outcome')

class PhraseStructure:
    resources = {"Merge-1": {"ms": 0, "n": 0}}

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

    # 1. BASIC PHRASE STRUCTURE GEOMETRY =======================================================

    def is_primitive(self):
        return not (self.right_const and self.left_const)

    def is_complex(self):
        return self.right_const and self.left_const

    def is_left(self):
        return self.mother and self.mother.left_const == self

    def is_right(self):
        return self.mother and self.mother.right_const == self

    def geometrical_sister(self):
        if self.is_left():
            return self.mother.right_const
        if self.is_right():
            return self.mother.left_const

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

    def specifier_sister(self):
        if self.is_left():
            return self.mother
        else:
            return self

    def grandmother(self):
        if self.mother.mother:
            return self.mother.mother

    def aunt(self):
        if self.mother:
            return self.mother.sister()

    def head(self):
        if self.is_primitive():
            return self
        if self.left_const.is_primitive():
            return self.left_const
        if self.right_const.adjunct:
            return self.left_const.head()
        if self.right_const.is_primitive():
            return self.right_const
        return self.right_const.head()

    def minimal_search(self):
        return [const.left_const if const.is_complex() else const for const in self]

    def proper_complement(self):
        if self.is_primitive() and self.sister() and self.sister().is_right():
            return self.sister()

    def selected(self):
        return self.max().sister() and self.max().sister().is_primitive()

    def container(self):
        if self.mother:
            return self.mother.head()

    def bottom(self):
        while not self.is_primitive():
            self = self.right_const
        return self

    def top(self):
        while self.mother:
            self = self.mother
        return self

    def max(probe):
        p = probe
        while p.mother and p.mother.head() == probe:
            p = p.mother
        return p

    def has_affix(self):
        return self.right_const and not self.left_const

    def complex_head(self):
        return self.has_affix()

    def get_affix_list(self):
        lst = [self]
        while self.right_const and not self.left_const:
            lst.append(self.right_const)
            self = self.right_const
        return lst

    def bottom_affix(self):
        if self.is_primitive:
            while self.right_const:
                self = self.right_const
            return self

    def non_complex_head(self):
        return self.is_complex() or not self.complex_head()

    def features_of_complex_word(h):
        return {feature for affix in h.get_affix_list() for feature in affix.features}

    def is_licensed_specifier(self):
        return self.max().container().licensed_phrasal_specifier() and self.max() == self.max().container().licensed_phrasal_specifier()

    def working_memory_path(probe, intervention_feature=''):
        node = probe.mother
        working_memory = []
        #=============================================
        while node:
            if node.left_const.head() != probe:
                working_memory.append(node.left_const)
                if intervention_feature and probe.intervention(node, intervention_feature):
                    break
            node = node.walk_upwards()
        #==============================================
        return working_memory

    def walk_upwards(self):
        node = self.mother
        if self.is_left():
            while node and node.right_const.adjunct:
                node = node.mother
        return node

    def intervention(self, node, intervention_feature):
        return intervention_feature in node.left_const.features

    @staticmethod
    def scan_next(working_memory, func=lambda x: x == x):
        return next((const for const in working_memory if func(const)), None)

    @staticmethod
    def scan_all(working_memory, func=lambda x: x == x):
        return [const for const in working_memory if func(const)]

    @staticmethod
    def scan_until(working_memory, func=lambda x: x == x):
        return list(takewhile(func, working_memory))

    def edge_specifiers(probe):
        return list(takewhile(lambda x: x.mother.head() == probe, probe.working_memory_path()))

    def complete_edge(self):
        return [const for const in self.edge_specifiers() + [self.extract_pro()] if const]

    def filtered_edge(self):
        return self.scan_all(self.complete_edge(), lambda x: not (x.check('pro') and not x.head().sustains_reference()))

    def local_tense_edge(self):
        return next((node.mother for node in self.working_memory_path('FORCE') if node.finite() or node.force()), self.top())

    def scan_down(self, func=lambda x: x == x):
        return next((const for const in self if func(const)), None)

    def selector(self):
        return next((const for const in self.working_memory_path() if const.is_primitive()), None)

    def contains_feature(self, feature):
        if self.left_const and self.left_const.contains_feature(feature):
            return True
        if self.right_const and self.right_const.contains_feature(feature):
            return True
        if self.is_primitive:
            if feature in self.features:
                return True

    def contains_features(self, feature_set):
        if self.left_const and self.left_const.contains_features(feature_set):
            return True
        if self.right_const and self.right_const.contains_features(feature_set):
            return True
        if self.is_primitive:
            if feature_set & self.features == feature_set:
                return True

    def cutoff_point_for_last_resort_extraposition(self):
        return self.is_primitive() and self.is_adjoinable() and self.aunt() and \
               (self.aunt().is_complex() or (self.aunt().is_primitive() and self.grandmother().contains_selection_violation()))

    # 2. PROPERTIES DEFINED BY LEXICAL FEATURES =====================================================================

    def adverbial(self):
        return self.check('Adv')

    def force(self):
        return self.check('FORCE')

    def finite(self):
        return self.check_some({'Fin', 'T/fin', 'C/fin'})

    def copula(self):
        return self.check('COPULA')

    def candidate_for_VP_fronting(self):
        return self == self.scan_next(self.container().edge_specifiers(), lambda x: {'A/inf', 'VA/inf'} & x.head().features)

    def finite_C(self):
        return self.check('C/fin')

    def relative(self):
        return self.check('REF')

    def nonfinite(self):
        return self.check('Inf')

    def legible_adjunct(self):
        return self.head().tail_test() and (self.is_right() or (self.is_left() and not self.nonthematic()))

    def finite_left_periphery(self):
        return self.finite() and self.check_some({'T', 'C'})

    def finite_tense(self):
        return self.check('T/fin') or (self.finite() and self.check('T'))

    def contains_finiteness(self):
        return self.contains_feature('Fin')

    def referential(self):
        return self.check_some({'φ', 'D'})

    def preposition(self):
        return self.check('P')

    def SEM_internal_predicate(self):
        return self.check('SEM:internal')

    def SEM_external_predicate(self):
        return self.check('SEM:external')

    def selected_by_SEM_internal_predicate(self):
        return self.selector() and self.selector().SEM_internal_predicate()

    def selected_by_SEM_external_predicate(self):
        return self.selector() and self.selector().SEM_external_predicate()

    def predicate(self):
        return self.is_primitive() and self.check('ARG') and not self.check('-ARG')

    def adjunct_is_correct_position(self):
        return self.tail_test()

    def has_legitimate_specifier(self):
        return self.predicate() and not self.edgeless() and self.edge_specifiers() and not self.has_unlicensed_specifier()

    def has_vacant_phrasal_position(self):
        return (self.is_complex() and self.left_const.is_primitive() and self.sister().is_primitive()) or self.is_primitive()

    def has_nonthematic_specifier(self):
        return self.EF() and self.edge_specifiers()

    def externalize_with_specifier(self):
        return self.is_left() and self.predicate() and \
               ((self.adjunct_is_correct_position() and self.has_nonthematic_specifier()) or
                (not self.adjunct_is_correct_position() and self.has_legitimate_specifier()))

    def isolated_preposition(self):
        return self.preposition() and self.sister() and self.sister().is_primitive()

    def edgeless(self):
        return self.head().check_some({'-EF:φ', '-EDGE:*'})

    def license_extraposition(self):
        return self.top().contains_finiteness() or self.top().referential()

    def has_unlicensed_specifier(self):
        return set(self.specifiers_not_licensed()) & set(next((const for const in self.edge_specifiers()), None).head().features)

    def non_scopal(self):
        return self.check_some({'Inf', 'P', 'D', 'φ'})

    def add_scope_information(self):
        if not self.non_scopal():
            return {'Fin', 'C', 'PF:C'}
        return set()

    def adjoinable_and_floatable(self):
        return self.is_complex() and not self.find_me_elsewhere and \
               self.head().get_tail_sets() and self.check('adjoinable') and \
               not self.check('-adjoinable') and not self.check('-float')

    def adverbial_adjunct(self):
        return self.adverbial() or self.preposition()

    def unrecognized_label(self):
        return self.check_some({'CAT:?', '?'})

    def get_head_violating_selection(self):
        return self.scan_down(lambda x: x.contains_selection_violation() and not x.right_const.head().adjunct)

    # Feature !EF:φ
    def selection__positive_SUBJECT_edge(self, lexical_feature):
        return self.scan_next(self.filtered_edge(), lambda x: x.referential() and (not x.has_tail_features() or x.is_extended_subject()))

    # Feature -EF:*
    def selection__unselective_negative_edge(self, lexical_feature):
        return not self.filtered_edge()

    # Feature -EF:φ
    def selection__negative_SUBJECT_edge(self, lexical_feature):
        return not self.scan_next(self.filtered_edge(), lambda x: x.referential() and x.is_extended_subject())

    # Feature !SEF
    def selection__positive_shared_edge(self, lexical_feature):
        return not (not self.licensed_phrasal_specifier() and self.referential_complement_criterion())

    # Feature !1EDGE
    @staticmethod
    def selection__negative_one_edge(self, lexical_feature):
        return len(self.edge_specifiers()) < 2

    # Feature [!EF:*] ~ not used for calculation of any data
    def selection__unselective_edge(self, lexical_feature):
        return self.filtered_edge()

    # Feature !SPEC
    def selection__positive_selective_specifier(self, lexical_feature):
        return self.scan_next(self.complete_edge(), lambda x: x.check(lexical_feature[6:]))

    # Feature -SPEC
    def selection__negative_specifier(self,  lexical_feature):
        return not self.scan_next(self.edge_specifiers(), lambda x: x.check(lexical_feature[6:]) and not x.adjunct)

    # Feature !COMP
    def selection__positive_obligatory_complement(self, lexical_feature):
        return self.selected_sister() and (lexical_feature[6] == '*' or self.selected_sister().check(lexical_feature[6:]))

    # Feature -COMP
    def selection__negative_complement(self, lexical_feature):
        return not (self.is_left() and self.proper_complement() and
                    (self.proper_complement().check(lexical_feature[6:]) or lexical_feature[6:] == '*'))

    def EF(self):
        return next((True for f in self.features if 'EF:' in f and '-' not in f), False)

    def trigger_phrasal_chain(self):
        return self.EF()

    def empty_finite_EPP(self):
        return self.selector().finite_C() and self.EF() and not self.edge_specifiers()

    def is_extended_subject(self):
        return {'EF:φ', '!EF:φ'} & {feature for feature_set in self.get_tail_sets() for feature in feature_set} or 'pro' in self.head().features

    def nonthematic(self):
        return self.container() and (self.container().EF() and self.container().finite()) or \
               (self.container().check('-SPEC:*') and self == next((const for const in self.container().edge_specifiers()), None))

    # Feature [!SEF]
    def referential_complement_criterion(probe):
        return probe.proper_complement() and (probe.proper_complement().head().referential() or
                                              (probe.proper_complement().head().licensed_phrasal_specifier() and
                                               probe.proper_complement().head().licensed_phrasal_specifier().head().referential()))

    def legitimate_head_position(self):
        return self.properly_selected() and not self.empty_finite_EPP()

    def specifier_theta_role_assigner(self):
        return not self.EF() and \
               not (self.selector() and not self.selector().check('ARG')) and \
               self.check_some({'SPEC:φ', 'COMP:φ', '!SPEC:φ', '!COMP:φ'}) and not self.max().container().check('-SPEC:φ')

    def is_adjoinable(self):
        return self.adjunct or ('adjoinable' in self.head().features and '-adjoinable' not in self.head().features)

    def contains_selection_violation(self):
        return self.is_complex() and (self.left_const.nonlicensed_complement() or self.left_const.missing_mandatory_complement())

    def has_tail_features(self):
        return self.head().get_tail_sets()

    def get_valued_features(self):
        return {f for f in self.features if f[:4] == 'PHI:' and f[-1] != '_'}

    def get_phi_set(self):
        return {f for f in self.head().features if f[:4] == 'PHI:' and len(f.split(':')) == 3}

    def phi_needs_valuation(self):
        return {phi for phi in self.features if phi[-1] == '_' and (phi[:7] == 'PHI:NUM' or phi[:7] == 'PHI:PER' or phi[:7] == 'PHI:DET')}

    def get_mandatory_comps(self):
        return {f[6:] for f in self.features if f[:5] == '!COMP' and f != '!COMP:*'}

    def licensed_specifiers(self):
        return {f[5:] for f in self.features if f[:4] == 'SPEC'} | {f[6:] for f in self.features if f[:5] == '!SPEC'}

    def specifiers_not_licensed(self):
        return {f[6:] for f in self.features if f[:5] == '-SPEC'}

    def rare_specs(self):
        return {f[6:] for f in self.features if f[:5] == '%SPEC'}

    def double_spec_filter(self):
        return not self.check('2SPEC') and len({spec for spec in self.edge_specifiers() if not spec.adjunct}) > 1

    def convert_features_for_parsing(self, features):
        return {f[1:] if f.startswith('!') else f for f in features}

    def is_clitic(self):
        return self.check('CL') or (self.head().check('CL') and not self.head().has_affix() and self.head().internal)

    def check(self, f):
        return f in self.head().features

    def check_all(self, feature_set):
        return feature_set & self.head().features == feature_set

    def check_some(self, f):
        return f & self.head().features

    def complement_match(self, const):
        return self.licensed_complements() & const.head().features

    def licensed_complements(self):
        return {f[5:] for f in self.features if f[:4] == 'COMP'} | {f[6:] for f in self.features if f[:5] == '!COMP'}

    def nonlicensed_complement(self):
        return self.proper_complement() and (self.complements_not_licensed() & self.proper_complement().head().features)

    def missing_mandatory_complement(self):
        return self.get_mandatory_comps() and (not self.proper_complement() or not (self.get_mandatory_comps() & self.proper_complement().head().features))

    def complement_not_licensed(self):
        return self.proper_complement() and not (self.licensed_complements() & self.proper_complement().head().features)

    def licensed_specifiers(self):
        return {f[5:] for f in self.features if f[:4] == 'SPEC'} | {f[6:] for f in self.features if f[:5] == '!SPEC'}

    def complements_not_licensed(self):
        return {f[6:] for f in self.features if f[:5] == '-COMP'}

    def properly_selected(self):
        return self.selector().bottom_affix().licensed_complements() & self.features

    def specifier_match(self, phrase):
        return self.licensed_specifiers() & phrase.head().features

    def licensed_phrasal_specifier(self):
        return next((spec for spec in self.edge_specifiers()
                     if spec.check('φ') and not spec.adjunct),
                    next((spec for spec in self.edge_specifiers()
                          if spec.check('φ') and not spec.find_me_elsewhere), None))

    def projection_principle(self):
        return self.projection_principle_applies() and not self.container_assigns_theta_role()

    def non_adverbial_adjunct_condition(self, starting_point_head):
        return not self.container() or \
               (self.check('GEN') and not self.container().referential()) and \
               not self.container() == starting_point_head and \
               not self.nonthematic() and not (self.referential() and self.head().projection_principle())

    def valid_reconstructed_adjunct(self, starting_point_node):
        return self.head().tail_test() and (self.adverbial_adjunct() or self.non_adverbial_adjunct_condition(starting_point_node))

    def projection_principle_applies(self):
        return self.referential() and self.max() and not self.max().find_me_elsewhere and self.max().mother and not self.max().contains_features({'adjoinable', 'SEM:nonreferential'})

    def container_assigns_theta_role(self):
        return self.max().container() and (self.selected() or (self.is_licensed_specifier() and self.max().container().specifier_theta_role_assigner()))

    def semantic_complement(self):
        return self.proper_complement() and not self.semantic_match(self.proper_complement())

    def semantic_match(self, b):
        a_head = self.head()
        b_head = b.head()
        pos_sem_a = {f[5:] for f in a_head.features if f.startswith('+SEM:')}
        neg_sem_a = {f[5:] for f in a_head.features if f.startswith('-SEM:')}
        pos_sem_b = {f[5:] for f in b_head.features if f.startswith('+SEM:')}
        neg_sem_b = {f[5:] for f in b_head.features if f.startswith('-SEM:')}
        return not ((pos_sem_a & neg_sem_b) or (pos_sem_b & neg_sem_a))

    def legitimate_criterial_feature(self):
        return self.referential() and not self.relative() and self.mother and self.mother.contains_feature('REL') and not self.mother.contains_feature('T/fin')

    def interpretable_adjunct(self):
        return self.referential() and self.max() and self.max().adjunct and self.max().is_right() and self.max().mother and self.max().mother.referential()

    def concept(self):
        for m in self.get_affix_list():
            if m.expresses_concept():
                return True

    def expresses_concept(self):
        return self.check_some({'N', 'Neg', 'P', 'D', 'φ', 'A', 'V', 'Adv', 'Q', 'Num', '0'}) and not self.copula() and not self.check('T/prt')

    def feature_conflict(self):
        def remove_exclamation(g):
            if g[0] == '!':
                return g[1:]
            else:
                return g
        for feature1 in self.features:
            if feature1[0] == '-':
                for feature2 in self.features:
                    if feature1[1:] == remove_exclamation(feature2):
                        return True

    def probe_goal_test(self):
        for f in sorted(self.features):
            if f.startswith('!PROBE:'):
                if not self.probe(self.features, f[7:]):
                    return True
            if f.startswith('-PROBE:'):
                if self.probe(set(self.features), f[7:]):
                    return True

    def probe(self, intervention_feature, G):
        if self.sister():
            # --------------------- minimal search --------------------------------
            for node in self.sister().minimal_search():
                if node.check(G) or (G[:4] == 'TAIL' and G[5:] in node.left_const.scan_criterial_features()):
                    return True
                if intervention_feature.issubset(node.features):
                    break
            # -------------------------------------------------------------------------

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

    def get_tail_sets(self):
        return {frozenset(f[5:].split(',')) for f in self.features if f[:4] == 'TAIL'}

    def tail_test(self):
        positive_features = {f for f in self.get_tail_sets() if self.positive_features(f)}
        negative_features = {f for f in self.get_tail_sets() if self.negative_features(f)}
        checked_positive_features = {tail_set for tail_set in positive_features if self.strong_tail_condition(tail_set) or
                                     self.weak_tail_condition(tail_set)}
        checked_negative_features = {tail_set for tail_set in negative_features if self.strong_tail_condition(tail_set) or
                                     self.weak_tail_condition(tail_set)}
        return positive_features == checked_positive_features and not checked_negative_features

    def strong_tail_condition(self, tail_set):
        if '$NO_S' not in tail_set and self.max() and self.max().mother:
            return self.max().container().match_features(tail_set).outcome or \
                   (self.max().mother.sister() and self.max().mother.sister().match_features(tail_set).outcome)

    def weak_tail_condition(self, tail_set):
        if '$NO_W' not in tail_set:
            if self.referential() or 'P' in self.features:
                for m in (affix for node in self.working_memory_path() if node.is_primitive() for affix in node.get_affix_list()):
                    test = m.match_features(tail_set)
                    if test.match_occurred:
                        return test.outcome
            if self.negative_features(tail_set):    # Unchecked negative features will pass the test
                return False

    def match_features(self, features_to_check):
        if self.negative_features(features_to_check) & self.features:
            return Result(True, True)  # Match occurred, outcome positive
        if self.positive_features(features_to_check) & self.features:
            return Result(True, self.positive_features(features_to_check).issubset(self.features))  # Match occurred, outcome negative (partial match)/positive (full match)
        return Result(False, None)  # No match occurred, no outcome (usually evaluates into False)

    def negative_features(self, features_to_check):
        return {feature[1:] for feature in features_to_check if feature[0] == '*'}

    def positive_features(self, features_to_check):
        return {feature for feature in features_to_check if feature[0] != '*' and feature[0] != '$'}

    def extract_pro(self):
        if self.check('ARG') and self.phi_consistent_head():
            if self.sustains_reference():
                phi_set_for_pro = {f for f in self.features if f[:4] == 'PHI:' and f[-1] != '_'}
            else:
                phi_set_for_pro = {f for f in self.features if f[:4] == 'PHI:'}
            pro = PhraseStructure()
            pro.features = pro.features | phi_set_for_pro | {'φ', 'D', 'PF:pro', 'pro'}
            return pro

    def phi_consistent_head(self):
        def is_valued_phi_feature(f):
            return f[:4] == 'PHI:' and f[-1] != '_'
        def phi_conflict(f, g):
            def deconstruct_phi_feature(f):
                return f.split(':')[1], f.split(':')[2]
            f_type, f_value = deconstruct_phi_feature(f)
            g_type, g_value = deconstruct_phi_feature(g)
            if f_type == g_type and f_value != g_value:
                return True
        def phi_consistency(phi_set):
            for f in phi_set:
                if is_valued_phi_feature(f):
                    for g in phi_set:
                        if is_valued_phi_feature(g):
                            if phi_conflict(f, g):
                                return False
            return True
        return phi_consistency({f for f in self.features if f[:4] == 'PHI:'})

    def sustains_reference(self):
        return self.phi_consistent_head() and {'PHI:NUM', 'PHI:PER'} & {f[:7] for f in self.features if f[:4] == 'PHI:' and f[-1] != '_'}

    # 3. STRUCTURE BUILDING ========================================================================================

    def merge_1(self, C, direction=''):
        local_structure = self.local_structure()                # [X...self...Y]
        new_constituent = self.asymmetric_merge(C, direction)   # A = [self H] or [H self]
        new_constituent.substitute(local_structure)             # [X...A...Y]
        return new_constituent

    def asymmetric_merge(self, B, direction='right'):
        self.consume_resources('Merge-1')
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

    def __add__(self, incoming_constituent):
        return self.merge_1(incoming_constituent)

    # 4. SUPPORT

    def get_pf(self):
        return {feature[3:] for feature in self.features if feature[:3] == 'PF:'}

    def get_phonological_string(self):
        def show_affix(self):
            i = ''
            if self.has_affix():
                i = self.right_const.major_category_label()
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

    def major_category_label(self):
        head = self.head()
        if self.is_complex():
            suffix = 'P'
        else:
            suffix = ''
        for cat in major_cats:
            if cat in head.features:
                return cat + suffix
        return 'X' + suffix

    def copy_for_reconstruction(self, babtize='1'):
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
        self_copy = self.copy()  # Copy the constituent
        self_copy.find_me_elsewhere = False  # Copy is marked for being where it is
        silence_phonologically(self_copy)  # Silence the new constituent phonologically
        self.find_me_elsewhere = True  # Mark that the constituent has been copied
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

        prefix = ''

        if 'null' in self.features:
            if self.adjunct:
                return '<' + prefix + self.left_const.illustrate() + ' ' \
                       + self.right_const.illustrate() + '>'
            else:
                return '[' + prefix + self.left_const.illustrate() + ' ' \
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
            index_str = ':' + self.identity
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

    def get_id(self):
        for f in self.features:
            if f[0] == '#':
                return f
