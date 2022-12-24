from collections import namedtuple
from itertools import takewhile
from support import log
from feature_processing import unvalued, feature_check, negative_features, positive_features

# New list (ordered hierarchically)
major_cats = ['N', 'Neg', 'Neg/fin', 'P', 'D', 'φ', 'C', 'A', 'v', 'V', 'T', 'Adv', 'Q', 'Num', 'Agr', 'Inf', 'FORCE', '0', 'a', 'b', 'c', 'd', 'x', 'y', 'z']

Result = namedtuple('Result', 'match_occurred outcome')


class PhraseStructure:
    resources = {"Merge-1": {"ms": 0, "n": 0}}

    def __init__(self, left_constituent=None, right_constituent=None):
        self.left = left_constituent
        self.right = right_constituent
        if self.left:
            self.left.mother = self
        if self.right:
            self.right.mother = self
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
        self.stop = False
        self.nn = None
        self.x = 0
        self.y = 0
        if left_constituent and left_constituent.adjunct and left_constituent.is_primitive():
            self.adjunct = True
            left_constituent.adjunct = False

    # Phrase structure geometry --------------------------------

    def is_complex(self):
        return self.right and self.left

    def is_primitive(self):
        return not self.is_complex()

    def is_left(self):
        return self.mother and self.mother.left == self

    def is_right(self):
        return self.mother and self.mother.right == self

    def has_affix(self):  # Definition for complex head
        return self.right and not self.left

    def head(self):
        if self.is_primitive():
            return self
        if self.left.is_primitive():
            return self.left
        if self.right.adjunct:
            return self.left.head()
        if self.right.is_primitive():
            return self.right
        return self.right.head()

    def inside(self, head):
        return self.head() == head

    def container(self):
        if self.mother:
            return self.mother.head()

    def max(self):
        probe = self
        while probe.mother and probe.mother.head() == self:
            probe = probe.mother
        return probe

    def search_domain(self):
        if not self.right_sister():
            return self
        else:
            return self.sister()

    def geometrical_sister(self):
        if self.is_left():
            return self.mother.right
        if self.is_right():
            return self.mother.left

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

    def proper_complement(self):
        if self.is_primitive() and self.sister() and self.sister().is_right():
            return self.sister()

    def select_right(self):
        return self.is_primitive() and self.is_left() and not self.geometrical_sister().adjunct

    def selected(self):
        return self.max().sister() and self.max().sister().is_primitive()

    def bottom(self):
        while not self.is_primitive():
            self = self.right
        return self

    def top(self):
        while self.mother:
            self = self.mother
        return self

    def selected_sister(self):
        if self.sister() and not (self.sister().is_primitive() and self.sister().is_left()):
            return self.sister()

    def right_sister(self):
        if self.sister() and self.sister().is_right():
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

    def get_affix_list(self):
        lst = [self]
        while self.right and not self.left:
            lst.append(self.right)
            self = self.right
        return lst

    def extract_affix(self):
        affix = self.right
        self.right = None
        return affix

    def bottom_affix(self):
        if self.is_primitive:
            while self.right and not self.right.find_me_elsewhere:
                self = self.right
            return self

    def is_licensed_specifier(self):
        return self.max().container().licensed_phrasal_specifier() and self.max() == self.max().container().licensed_phrasal_specifier()

    def selector(self):
        return self.next(self.upward_path, lambda x: x.is_primitive())

    def features_of_complex_word(h):
        return {feature for affix in h.get_affix_list() for feature in affix.features}

    #  Definitions and abstractions for terms

    def adverbial(self):
        return self.check({'Adv'})

    def force(self):
        return self.check({'FORCE'})

    def finite(self):
        return self.check_some({'Fin', 'T/fin', 'C/fin'})

    def copula(self):
        return self.check({'COPULA'})

    def finite_C(self):
        return self.check({'C/fin'})

    def relative(self):
        return self.check({'REF'})

    def nonfinite(self):
        return self.check({'Inf'})

    def concept_operator(self):
        return self.concept() and {feature for feature in self.features if feature[:2] == 'OP'}

    def finite_left_periphery(self):
        return self.finite() and self.check_some({'T', 'C'})

    def finite_tense(self):
        return self.check({'T/fin'}) or (self.finite() and self.check({'T'}))

    def contains_finiteness(self):
        return self.contains_features({'Fin'})

    def referential(self):
        return self.check_some({'φ', 'D'})

    def preposition(self):
        return self.check({'P'})

    def floatable(self):
        return not self.check({'-float'})

    def SEM_internal_predicate(self):
        return self.check({'SEM:internal'})

    def SEM_external_predicate(self):
        return self.check({'SEM:external'})

    def non_scopal(self):
        return self.check_some({'Inf', 'P', 'D', 'φ'})

    def expresses_concept(self):
        return self.check_some({'N', 'Neg', 'P', 'D', 'φ', 'A', 'V', 'Adv', 'Q', 'Num', '0'}) and not self.check({'T/prt', 'COPULA'})

    def unrecognized_label(self):
        return self.check_some({'CAT:?', '?'})

    def predicate(self):
        return self.is_primitive() and self.check({'ARG'}) and not self.check({'-ARG'})

    def adverbial_adjunct(self):
        return self.adverbial() or self.preposition()

    def is_adjoinable(self):
        return self.adjunct or (self.head().check({'adjoinable'}) and not self.head().check({'-adjoinable'}))

    def clitic(self):
        return self.check({'CL'}) or (
                    self.head().check({'CL'}) and not self.head().has_affix() and self.head().internal)

    def concept(self):
        next((x for x in self.get_affix_list() if x.expresses_concept()), False)

    def semantic_complement(self):
        return self.proper_complement() and not self.semantic_match(self.proper_complement())

    def selected_by_SEM_internal_predicate(self):
        return self.selector() and self.selector().SEM_internal_predicate()

    def selected_by_SEM_external_predicate(self):
        return self.selector() and self.selector().SEM_external_predicate()

    def isolated_preposition(self):
        return self.preposition() and self.sister() and self.sister().is_primitive()

    def adjoinable(self):
        return self.is_complex() and not self.find_me_elsewhere and self.head().get_tail_sets() and self.check({'adjoinable'}) and not self.check({'-adjoinable'})

    def legitimate_criterial_feature(self):
        return self.referential() and not self.relative() and self.mother and self.mother.contains_features({'REL'}) and not self.mother.contains_features({'T/fin'})

    def interpretable_adjunct(self):
        return self.referential() and self.max() and self.max().adjunct and self.max().is_right() and self.max().mother and self.max().mother.referential()

    def word_internal(self):
        return self.bottom().bottom_affix().internal

    def impossible_sequence(self, w):
        return self.is_primitive() and 'T/fin' in self.head().features and 'T/fin' in w.features

    def is_word_internal(self):
        return self.mother and self.sister() and self.sister().is_primitive() and self.sister().internal

    # Minimal search and upward path -------------------------------------------

    def __next__(self):
        if not self.nn:
            raise StopIteration
        current = self.nn
        if self.nn.is_primitive():
            self.nn = None
            return current
        elif self.nn.head() == self.nn.right.head() or self.nn.left.select_right():
            self.nn = self.nn.right
        else:
            self.nn = self.nn.left
        return current.left

    def __iter__(self):
        self.nn = self
        return self

    def minimal_search(self, selection_condition=lambda x: True, sustain_condition=lambda x: True):
        return takewhile(sustain_condition, (const for const in self if selection_condition(const)))

    def symmetric_minimal_search(self, condition=lambda x: x == x, stop_condition=lambda x: x == x):
        lst = []
        for node in self.top().minimal_search():
            if condition(node):
                lst.append(node)
                if stop_condition(node):
                    break
            if node.sister() and condition(node.sister()):
                lst.append(node.sister())
                if stop_condition(node.sister()):
                    break
        return lst

    def upward_path(self):
        upward_path = []
        x = self.mother
        while x:
            if not x.right.adjunct and x.left.head() != self:
                upward_path.append(x.left)
            x = x.mother
        return upward_path

    def next(self, memory_span, condition=lambda x: x == x):
        return next((x for x in memory_span() if condition(x)), None)

    def edge(self):
        return list(takewhile(lambda x: x.mother and x.mother.inside(self), self.upward_path()))

    def contains_features(self, feature_set):
        if self.is_complex():
            if self.left.contains_features(feature_set) or self.right.contains_features(feature_set):
                return True
        elif feature_set & self.features == feature_set:
            return True

    def geometrical_minimal_search(self):
        search_list = [self]
        ps = self
        while ps.is_complex() and ps.right:
            search_list.append(ps.right)
            ps = ps.right
        return search_list

    # Virtual pronouns -----------------------------------------------------------------------

    def extract_pro(self):
        if self.check({'ARG'}) and self.phi_consistent_head():
            if self.sustains_reference():
                phi_set_for_pro = {f for f in self.features if f[:4] == 'PHI:' and f[-1] != '_'}
            else:
                phi_set_for_pro = {f for f in self.features if f[:4] == 'PHI:'}
                phi_set_for_pro.add('pro_')
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

    # Selection -------------------------------------------------------------------------------------------

    # Feature !EF:φ
    def selection__positive_SUBJECT_edge(self, lexical_feature):
        return next((x for x in self.pro_list() if x.referential() and not x.check({'pro_'}) and (not x.get_tail_sets() or x.is_extended_subject())), None)

    # Feature -EF:*
    def selection__unselective_negative_edge(self, lexical_feature):
        return not self.edge()

    # Feature -EF:φ
    def selection__negative_SUBJECT_edge(self, lexical_feature):
        return not self.next(self.edge, lambda x: x.referential() and x.is_extended_subject())

    def is_extended_subject(self):
        return {'EF:φ', '!EF:φ'} & {f for feature_set in self.get_tail_sets() for f in feature_set} or 'pro' in self.head().features

    # Feature !SEF
    def selection__positive_shared_edge(self, lexical_feature):
        return not (not self.licensed_phrasal_specifier() and self.referential_complement_criterion())

    # Feature !1EDGE
    @staticmethod
    def selection__negative_one_edge(self, lexical_feature):
        return len(self.edge()) < 2

    # Feature [!EF:*] ~ not used for calculation of any data
    def selection__unselective_edge(self, lexical_feature):
        return self.edge()

    # Feature !SPEC
    def selection__positive_selective_specifier(self, lexical_feature):
        return next((x for x in self.pro_list() if x.check(lexical_feature[6:])), None)

    def pro_list(self):
        lst = self.edge()
        if self.extract_pro():
            lst.append(self.extract_pro())
        return lst

    # Feature -SPEC
    def selection__negative_specifier(self,  lexical_feature):
        return not self.next(self.edge, lambda x: x.check({lexical_feature[6:]}) and not x.adjunct)

    # Feature !COMP
    def selection__positive_obligatory_complement(self, lexical_feature):
        return self.selected_sister() and (lexical_feature[6] == '*' or self.selected_sister().check({lexical_feature[6:]}))

    # Feature -COMP
    def selection__negative_complement(self, lexical_feature):
        return not (self.is_left() and self.proper_complement() and
                    (self.proper_complement().check({lexical_feature[6:]}) or lexical_feature[6:] == '*'))

    # Feature [!SEF]
    def referential_complement_criterion(probe):
        return probe.proper_complement() and (probe.proper_complement().head().referential() or
                                              (probe.proper_complement().head().licensed_phrasal_specifier() and
                                               probe.proper_complement().head().licensed_phrasal_specifier().head().referential()))

    def complement_match(self, const):
        return self.licensed_complements() & const.head().features

    def probe_goal_test(self):
        for f in sorted(self.features):
            if f.startswith('!PROBE:'):
                if not self.probe(self.features, f[7:]):
                    return True
            if f.startswith('-PROBE:'):
                if self.probe(self.features, f[7:]):
                    return True

    def probe(self, intervention_features, G):
        if self.sister():
            for node in self.sister().minimal_search():
                if node.check({G}) or (G[:4] == 'TAIL' and G[5:] in node.scan_operators()):
                    return True
                if node.check(intervention_features):
                    break


    def double_spec_filter(self):
        return not self.check({'2SPEC'}) and len({spec for spec in self.edge() if not spec.adjunct}) > 1

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
        return self.selector() and self.selector().licensed_complements() & self.features

    def specifier_match(self, phrase):
        return phrase.head().check_some(self.licensed_specifiers())

    def licensed_phrasal_specifier(self):
        return next((spec for spec in self.edge()
                     if spec.referential() and not spec.adjunct),
                    next((spec for spec in self.edge()
                          if spec.referential() and not spec.find_me_elsewhere), None))

    def does_not_accept_any_complementizers(self):
        return self.is_primitive() and self.check({'-COMP:*'})

    # Projection principle and thematic roles ---------------------------------------------------------------------

    def nonthematic(self):
        return self.container() and (self.container().EF() and self.container().finite()) or \
               (self.container().check_some({'-SPEC:*', '-SPEC:φ', '-SPEC:D'}) and self == next((const for const in self.container().edge()), None))

    def specifier_theta_role_assigner(self):
        return not self.EF() and \
               not (self.selector() and not self.selector().check({'ARG'})) and \
               self.check_some({'SPEC:φ', 'COMP:φ', '!SPEC:φ', '!COMP:φ'}) and not self.max().container().check({'-SPEC:φ'})

    def projection_principle(self):
        return self.projection_principle_applies() and not self.container_assigns_theta_role()

    def projection_principle_applies(self):
        return self.referential() and self.max() and not self.max().find_me_elsewhere and self.max().mother and not self.max().contains_features({'adjoinable', 'SEM:nonreferential'})

    def container_assigns_theta_role(self):
        return self.max().container() and (self.selected() or (self.is_licensed_specifier() and self.max().container().specifier_theta_role_assigner()))

    # Reconstruction -----------------------------------------------------------------------------------

    def EF(self):
        for f in self.features:
            if f.startswith('!EF:') or f.startswith('EF:') or f == '!SEF':
                return True

    def create_chain(self, transfer, inst):
        for i, target in enumerate(self.select_objects_from_edge(inst)):
            inst, target = target.prepare_chain(self, inst, i > 0, target.scan_operators(), transfer)
            self.form_chain(target, inst)
            transfer.brain_model.consume_resources(inst['type'], self)
            if inst['need repair'](target):
                target.create_chain(transfer, inst)

    def prepare_chain(self, probe, inst, new_head_needed, op_features, transfer):
        if inst['type'] == 'Phrasal Chain':
            if not op_features and inst['last resort A-chain conditions'](self):
                inst['selection'] = lambda x: x.has_vacant_phrasal_position()
                inst['legible'] = lambda x, y: True
            elif new_head_needed and (op_features or self.unlicensed_specifier()):
                probe = self.sister().merge_1(transfer.access_lexicon.PhraseStructure(), 'left').left
            probe.features |= transfer.access_lexicon.apply_parameters(transfer.access_lexicon.apply_redundancy_rules({'OP:_'} | self.checking_domain('OP*' in op_features).scan_operators() | probe.add_scope_information()))
        return inst.copy(), self.copy_for_chain(transfer.babtize())

    def form_chain(self, target, inst):
        for head in self.search_domain().minimal_search(inst['selection'], inst['sustain']):
            if head.test_merge(target, inst['legible'], 'left'):
                break
            target.remove()
        else:
            if not head.test_merge(target, inst['legible'], 'right'):
                target.remove()
                self.sister().merge_1(target, 'left')

    def test_merge(self, obj, legible, direction):
        self.specifier_sister().merge_1(obj, direction)
        return legible(self, obj)

    def select_objects_from_edge(self, instructions):
        if instructions['type'] == 'Phrasal Chain':
            return [spec for spec in self.edge() if not spec.find_me_elsewhere]
        return [self.right]

    def VP_for_fronting(self):
        return self == self.container().next(self.container().upward_path, lambda x: x.mother.inside(self.container()) and x.head().check_some({'VA/inf', 'A/inf'}))

    def has_legitimate_specifier(self):
        return self.predicate() and not self.head().check_some({'-EF:φ', '-EDGE:*'}) and self.edge() and not self.has_unlicensed_specifier()

    def unlicensed_specifier(self):
        return self.is_complex() and not self.adjunct and self.container() and self != self.container().licensed_phrasal_specifier()

    def has_vacant_phrasal_position(self):
        return self.gapless_heads() or self.is_right()

    def gapless_heads(self):
        return self.is_primitive() and self.aunt().is_primitive()

    def has_nonthematic_specifier(self):
        return self.EF() and self.edge() and self.edge()[0].is_extended_subject()

    def add_scope_information(self):
        if not self.non_scopal():
            return {'Fin', 'C', 'PF:C'}
        return set()

    def Agree(self, transfer):
        if self.sister():
            goal, phi = self.Agree_from_sister()
            if phi:
                transfer.brain_model.narrow_semantics.predicate_argument_dependencies.append((self, goal))
                if self.adverbial() or self.check({'VA/inf'}):  # Complementary distribution of phi and overt subject in this class
                    self.features.add('-pro')
                if not self.referential():
                    self.features.add('BLOCK_NS')               # Block semantic object projection
                for p in phi:
                    self.value(goal, p)
                if not self.is_unvalued():
                    return

        goal2, phi = self.Agree_from_edge()
        if goal2:
            for p in phi:
                if {f for f in self.features if unvalued(f) and f[:-1] == p[:len(f[:-1])]}:
                    self.value(goal2, p)
            if not self.referential() and not goal2.check({'pro'}):
                self.features.add('BLOCK_NS')  # Block semantic object projection

    def Agree_from_sister(self):
        for goal in self.sister().minimal_search(lambda x: x.is_complex()):
            if self.agreement_condition(goal):
                return goal.head(), sorted({f for f in goal.head().features if f[:4] == 'PHI:' and f[:7] != 'PHI:DET' and not unvalued(f)})
            else:
                break
        return None, None

    def Agree_from_edge(self):
        return next(((const.head(), sorted({f for f in const.head().features if f[:4] == 'PHI:' and not unvalued(f)}))
                     for const in [const for const in self.edge()] + [self.extract_pro()] if
                     const and self.agreement_condition(const)), (None, {}))

    def agreement_condition(self, goal):
        if goal.head().referential():
            if not goal.head().check({'LANG:FI'}):
                return True
            else:
                if goal.head().check({'pro'}):
                    return True
                else:
                    # To be replaced with the head-case model
                    if self.finite() and goal.head().check({'NOM'}):
                        return True
                    if self.nonfinite() and goal.head().check({'GEN'}):
                        return True

    def value(self, goal, phi):
        if self.valued_phi_features() and self.valuation_blocked(phi):
            log(f'Valuation of {self} was blocked for {phi}...')
            self.features.add(phi + '*')

        if {f for f in self.features if unvalued(f) and f[:-1] == phi[:len(f[:-1])]}:
            self.features = self.features - {f for f in self.features if unvalued(f) and f[:-1] == phi[:len(f[:-1])]}
            self.features.add(phi)
            if goal.mother:
                log(f'\n\t\t{self} acquired ' + str(phi) + f' from {goal.mother.illustrate()}...')
            else:
                log(f'\n\t\t{self} acquired ' + str(phi) + f' from {goal.illustrate()}...')
            self.features.add('PHI_CHECKED')

    def valuation_blocked(self, f):
        # We do not check violation, only that if types match there must be a licensing feature with identical value.
        valued_input_feature_type = f.split(':')[1]
        # Find type matches
        valued_phi_in_h = {phi for phi in self.get_phi_set() if
                           not unvalued(phi) and phi.split(':')[1] == valued_input_feature_type}
        if valued_phi_in_h:
            # Find if there is a licensing element
            if {phi for phi in valued_phi_in_h if phi == f}:
                return False
            log(f'Feature {f} cannot be valued into {self}.')
            return True

    def cutoff_point_for_last_resort_extraposition(self):
        return self.is_primitive() and self.is_adjoinable() and self.aunt() and \
               (self.aunt().is_complex() or (self.aunt().is_primitive() and self.grandmother().induces_selection_violation()))

    def license_extraposition(self):
        return self.top().contains_finiteness() or self.top().referential()

    def extrapose(self, transfer):
        transfer.brain_model.adjunct_constructor.externalize_structure(self.sister().head())

    def last_resort_extrapose(self, transfer):
        transfer.brain_model.adjunct_constructor.externalize_structure(self.bottom().next(self.bottom().upward_path, lambda x: x.cutoff_point_for_last_resort_extraposition()))

    def resolve_neutralized_feature(self):
        self.features.discard('?ARG')
        if self.selected_by_SEM_internal_predicate():
            log(f'{self} resolved into -ARG due to {self.selector()}...')
            self.features.add('-EF:φ')
            self.features.discard('EF:φ')
            self.features.add('-ARG')
        else:
            log(f'{self} resolved into +ARG...')
            self.features.add('ARG')
            self.features.add('!EF:φ')
            self.features.add('EF:φ')
            self.features.add('PHI:NUM:_')
            self.features.add('PHI:PER:_')

    def valid_reconstructed_adjunct(self, starting_point_node):
        return self.head().tail_test() and (self.adverbial_adjunct() or self.non_adverbial_adjunct_condition(starting_point_node))

    def trigger_adjunct_reconstruction(self):
        return self and not self.legible_adjunct() and self.adjoinable() and self.floatable() and not self.operator_in_scope_position()

    def legible_adjunct(self):
        return self.head().tail_test() and (self.is_right() or (self.is_left() and not self.nonthematic()))

    def local_tense_edge(self):
        return next((node.mother for node in self.upward_path() if node.finite() or node.force()), self.top())

    def externalize_with_specifier(self):
        return self.is_left() and self.predicate() and \
               ((self.tail_test() and self.has_nonthematic_specifier()) or
                (not self.tail_test() and self.has_legitimate_specifier()))

    def empty_finite_EPP(self):
        return self.selector().finite_C() and self.EF() and not self.edge()

    def has_unlicensed_specifier(self):
        return set(self.specifiers_not_licensed()) & set(next((const for const in self.edge()), None).head().features)

    def get_constituent_containing_selection_violation(self):
        return next((x for x in self if x.induces_selection_violation() and not x.sister().adjunct), None)

    def induces_selection_violation(self):
        return self.nonlicensed_complement() or self.missing_mandatory_complement()

    def non_adverbial_adjunct_condition(self, starting_point_head):
        return not self.container() or \
               (not (self.check({'GEN'}) and self.container().referential()) and
               not self.container() == starting_point_head and
               not self.nonthematic() and not (self.referential() and self.head().projection_principle()))

    def move_upwards(self):
        if self.mother:
            return self.mother.sister()

    # Feature processing -----------------------------------------------------------------------------

    def check(self, feature_set):
        return feature_set & self.head().features == feature_set

    def check_some(self, f):
        return f & self.head().features

    def is_unvalued(self):
        for f in self.features:
            if unvalued(f):
                return True

    def valued_phi_features(self):
        return {f for f in self.features if f[:4] == 'PHI:' and f[-1] != '_'}

    def get_phi_set(self):
        return {f for f in self.features if f[:4] == 'PHI:' and len(f.split(':')) == 3}

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

    def semantic_match(self, b):
        a_head = self.head()
        b_head = b.head()
        pos_sem_a = {f[5:] for f in a_head.features if f.startswith('+SEM:')}
        neg_sem_a = {f[5:] for f in a_head.features if f.startswith('-SEM:')}
        pos_sem_b = {f[5:] for f in b_head.features if f.startswith('+SEM:')}
        neg_sem_b = {f[5:] for f in b_head.features if f.startswith('-SEM:')}
        return not ((pos_sem_a & neg_sem_b) or (pos_sem_b & neg_sem_a))

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

    def match_features(self, features_to_check):
        if negative_features(features_to_check) & self.features:
            return Result(True, True)  # Match occurred, outcome positive
        if positive_features(features_to_check) & self.features:
            return Result(True, positive_features(features_to_check).issubset(self.features))  # Match occurred, outcome negative (partial match)/positive (full match)
        return Result(False, None)  # No match occurred, no outcome (usually evaluates into False)

    # Operators

    def checking_domain(self, narrow_domain):
        if narrow_domain:
            return self.head()
        return self

    def scan_operators(self):  # Note: we only take the first operator
        set_ = set()
        if self.left and not self.left.find_me_elsewhere:
            set_ = self.left.scan_operators()
        if not set_ and self.right and not self.right.find_me_elsewhere and not {'T/fin', 'C'} & self.right.head().features:
            set_ = self.right.scan_operators()
        if not set_ and self.is_primitive():
            set_ = {f for f in self.features if f[:2] == 'OP' and f[-1] != '_'}
        return set_

    def operator_in_scope_position(self):
        return self.scan_operators() and self.container() and self.container().head().finite()

    def find_occurrences_from(self, ps):
        def find_(identity, ps):
            chain = []
            if ps.is_complex():
                chain = chain + find_(identity, ps.left)
                chain = chain + find_(identity, ps.right)
            else:
                if identity in ps.features:
                    return [ps]
                if ps.has_affix():
                    chain = chain + find_(identity, ps.right)
            return chain

        identity = self.get_id()  # Returns the identity symbol (#1, ...)
        return find_(identity, ps)

    # Tail-processing ---------------------------------------------------------------------------

    def get_tail_sets(self):
        return {frozenset(f[5:].split(',')) for f in self.head().features if f[:4] == 'TAIL'}

    def tail_test(self):
        pos_features = {f for f in self.get_tail_sets() if positive_features(f)}
        neg_features = {f for f in self.get_tail_sets() if negative_features(f)}
        checked_positive_features = {tail_set for tail_set in pos_features if self.strong_tail_condition(tail_set) or
                                     self.weak_tail_condition(tail_set)}
        checked_negative_features = {tail_set for tail_set in neg_features if self.strong_tail_condition(tail_set) or
                                     self.weak_tail_condition(tail_set)}
        return pos_features == checked_positive_features and not checked_negative_features

    def strong_tail_condition(self, tail_set):
        if '$NO_S' not in tail_set and self.max() and self.max().mother:
            return self.max().container().match_features(tail_set).outcome or \
                   (self.max().mother.sister() and self.max().mother.sister().match_features(tail_set).outcome)

    def weak_tail_condition(self, tail_set):
        if '$NO_W' not in tail_set:
            if self.referential() or 'P' in self.features:
                for m in (affix for node in self.upward_path() if node.is_primitive() for affix in node.get_affix_list()):
                    test = m.match_features(tail_set)
                    if test.match_occurred:
                        return test.outcome
            if negative_features(tail_set):    # Unchecked negative features will pass the test
                return False

    def tail_match(self, constituent_from_MB, direction):
        self.merge_1(constituent_from_MB.copy(), direction)        # Test merge
        if direction == 'right':                                          # Presupposition
            self.geometrical_sister().adjunct = True
        result = self.geometrical_sister().head().tail_test()      # Test
        self.geometrical_sister().remove()                         # Remove trial unit
        return result

    # Recovery ---------------------------------------------------------------------------------------------------

    def is_possible_antecedent(self, antecedent):
        if not antecedent.find_me_elsewhere:
            phi_to_check = {phi for phi in self.features if phi[:7] == 'PHI:NUM' or phi[:7] == 'PHI:PER'}
            phi_checked = {phi2 for phi1 in antecedent.head().valued_phi_features() for phi2 in phi_to_check if feature_check(phi1, phi2)}
            return phi_to_check == phi_checked

    def special_rule(self, x):
        if self.finite() and self.edge() and x == self.next(self.upward_path):
            if not x.referential():
                self.features.add('PHI:DET:GEN')
            return x

    def control(self):
        return next((x for x in [self.sister()] + list(takewhile(lambda x: 'SEM:external' not in x.features, self.upward_path())) if self.is_possible_antecedent(x)), None)

    def finite_control(self):
        return self.next(self.upward_path, lambda x: self.is_possible_antecedent(x) or self.special_rule(x))

    def get_antecedent(self):
        unvalued_phi = self.phi_needs_valuation()
        if {'PHI:NUM:_', 'PHI:PER:_'} & unvalued_phi:
            return self.control()
        elif {'PHI:DET:_'} & unvalued_phi:
            return self.finite_control()

    # Structure building --------------------------------------------------------------------------

    def merge_1(self, C, direction=''):
        local_structure = self.local_structure()                # [X...self...Y]
        new_constituent = self.asymmetric_merge(C, direction)   # A = [self H] or [H self]
        new_constituent.substitute(local_structure)             # [X...A...Y]
        return new_constituent

    def asymmetric_merge(self, B, direction='right'):
        self.consume_resources('Merge-1', self)
        if direction == 'left':
            new_constituent = PhraseStructure(B, self)
        else:
            new_constituent = PhraseStructure(self, B)
        return new_constituent

    def substitute(self, local_structure):
        if local_structure.mother:
            if not local_structure.left:
                local_structure.mother.right = self
            else:
                local_structure.mother.left = self
            self.mother = local_structure.mother

    def local_structure(self):
        local_structure = namedtuple('local_structure', 'mother left')
        local_structure.mother = self.mother
        local_structure.left = self.is_left()
        return local_structure

    def merge_to_right(self, node, spec, name):
        if not node.right_sister():
            if node == self:
                node.merge_1(spec.copy_for_chain(name), 'right')
            else:
                node.merge_1(spec.copy_for_chain(name), 'left')
        else:
            node.mother.merge_1(spec.copy_for_chain(name), 'left')

    def merge_around(self, reconstructed_object, legibility=lambda x: True):
        if not (self.merge_1(reconstructed_object, 'right') and legibility(reconstructed_object)):
            reconstructed_object.remove()
            if not (self.merge_1(reconstructed_object, 'left') and legibility(reconstructed_object)):
                reconstructed_object.remove()
                return True

    def remove(self):
        if self.mother:
            mother = self.mother                    # {H, X}
            sister = self.geometrical_sister()      # X
            grandparent = self.mother.mother        # {Y {H, X}}
            sister.mother = sister.mother.mother    # Y
            if mother.is_right():
                grandparent.right = sister           # {Y X} (removed H)
            elif mother.is_left():
                grandparent.left = sister            # {X Y} (removed H)
            self.mother = None                          # detach H

    def sink(self, ps):
        bottom_affix = self.bottom().get_affix_list()[-1]   # If self is complex, we first take the right bottom node.
        bottom_affix.active_in_syntactic_working_memory = True
        bottom_affix.right = ps
        ps.mother = bottom_affix
        bottom_affix.left = None
        return self.top()

    def belong_to_same_word(self, site):
        return self.bottom_affix().internal and site.is_primitive()

    def sink_into_complex_head(self, terminal_lexical_item):
        return self.bottom_affix().sink(terminal_lexical_item)

    def copy(self):
        ps_ = PhraseStructure()
        if self.left:
            ps_.left = self.left.copy()
            ps_.left.mother = ps_
        if self.right:
            ps_.right = self.right.copy()
            ps_.right.mother = ps_
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

    def __add__(self, incoming_constituent):
        return self.merge_1(incoming_constituent)

    def get_index(self, target):
        for i, node in enumerate(self.geometrical_minimal_search()):
            if target == node:
                return i

    def get_node(self, idx):
        for i, node in enumerate(self.geometrical_minimal_search()):
            if i == idx:
                return node

    def target_left_branch(self, target):
        new_ps = self.top().copy()
        return new_ps.get_node(self.top().get_index(target))


    # Support ----------------------------------------------------------------------

    def get_pf(self):
        return {feature[3:] for feature in self.features if feature[:3] == 'PF:'}

    def info(self):
        info = [f[5:] for f in self.features if f[:5] == 'INFO:']
        return '.'.join(sorted(info))

    def gloss(self):
        def LF_features(head):
            lfs = [f[3:] for f in head.features if f[:2] == 'LF']
            return '.'.join(sorted(lfs))

        pf = ''
        if self.left:
            if 'null' in self.left.features:
                pf = pf + '_'
            else:
                pf = pf + self.left.gloss() + ' '
        if self.right:
            if 'null' in self.right.features:
                pf = pf + '_'
            else:
                pf = pf + self.right.gloss() + ' '
        if self.is_primitive():
            pf = pf + LF_features(self)
        return pf

    def label(self):
        head = self.head()
        if self.is_complex():
            suffix = 'P'
        else:
            suffix = ''
        for cat in major_cats:
            if cat in head.features:
                return cat + suffix
        return 'X' + suffix

    def copy_for_chain(self, babtize='1'):
        def silence_phonologically(h):
            if not h.features:
                h.features = {'null'}
            else:
                h.features.add('null')
            if h.left:
                silence_phonologically(h.left)
            if h.right:
                silence_phonologically(h.right)

        if self.identity == '':
            self.identity = babtize
        self_copy = self.copy()                 # Copy the constituent
        self_copy.find_me_elsewhere = False     # Copy is marked for being where it is
        silence_phonologically(self_copy)       # Silence the new constituent phonologically
        self.find_me_elsewhere = True           # Mark that the constituent has been copied
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
                return '<' + prefix + self.left.illustrate() + ' ' \
                       + self.right.illustrate() + '>'
            else:
                return '[' + prefix + self.left.illustrate() + ' ' \
                       + self.right.illustrate() + ']'
        else:
            if self.adjunct:
                return f'<' + prefix \
                       + self.left.illustrate() + ' ' \
                       + self.right.illustrate() + '>'
            else:
                return f'[' + prefix \
                       + self.left.illustrate() + ' ' \
                       + self.right.illustrate() + ']'

    def phonological_content(self):
        exceptions = {'φ', 'D'}
        phon = ''
        if self.is_primitive():
            if not set(self.get_phonological_string()) & exceptions:
                phon = self.get_phonological_string()
        else:
            str = self.left.phonological_content()
            if str:
                phon += ' ' + str
            if not self.right.adjunct:
                str = self.right.phonological_content()
                if str:
                    phon += ' ' + str
        return phon

    def __str__(self):
        if self.identity != '':
            chain_index_str = ':' + self.identity
        else:
            chain_index_str = ''
        if self.find_me_elsewhere:
            chain_index_str = chain_index_str + ''
        if self.features and 'null' in self.features and self.is_complex():
            if self.adjunct:
                return '<__>' + chain_index_str
            else:
                return '__' + chain_index_str
        if self.is_primitive():
            if not self.get_phonological_string():
                return '?'
            else:
                if self.adjunct:
                    return '<' + self.get_phonological_string() + '>'
                else:
                    return self.get_phonological_string()
        else:
            if self.adjunct:
                return f'<{self.left} {self.right}>' + chain_index_str
            else:
                if self.active_in_syntactic_working_memory:
                    return f'[{self.left} {self.right}]' + chain_index_str
                else:
                    return f'[{self.left} {self.right}]' + chain_index_str

    def get_phonological_string(self):
        def show_affix(self):
            i = ''
            if self.has_affix():
                i = self.right.label()
                if self.right.right:
                    i = i + ',' + show_affix(self.right)
            else:
                i = ''
            return i

        pfs = [f[3:] for f in self.features if f[:2] == 'PF']
        if self.has_affix():
            if self.right.find_me_elsewhere:
                affix_str = ''
            else:
                affix_str = '(' + show_affix(self) + ')'
            return '.'.join(sorted(pfs)) + affix_str
        else:
            return '.'.join(sorted(pfs))

    def tidy_names(self, counter):
        def rebaptize(h, old_name, new_name):
            if h.identity == old_name:
                if not h.rebaptized:
                    h.identity = new_name
                    h.rebaptized = True
            if h.left:
                rebaptize(h.left, old_name, new_name)
            if h.right:
                rebaptize(h.right, old_name, new_name)
            return

        if self.identity != '' and not self.rebaptized:
            rebaptize(self.top(), self.identity, str(counter))
            counter = counter + 1
        if self.left:
            counter = self.left.tidy_names(counter)
        if self.right:
            counter = self.right.tidy_names(counter)
        return counter

    def consume_resources(self, resource_key, target):
        PhraseStructure.resources[resource_key]['n'] += 1

    def get_id(self):
        for f in self.features:
            if f[0] == '#':
                return f
