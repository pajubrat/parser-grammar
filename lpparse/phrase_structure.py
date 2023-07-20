from collections import namedtuple
from itertools import takewhile
from support import log
from feature_processing import *

# New list (ordered hierarchically)
major_cats = ['N', 'Neg', 'Neg/fin', 'P', 'D', 'φ', 'C', 'A', 'v', 'V', 'T', 'Fin', 'Adv', 'Q', 'Num', 'Agr', 'Inf', 'FORCE', 'EXPL', '0', 'a', 'b', 'c', 'd', 'x', 'y', 'z']

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
        if left_constituent and left_constituent.adjunct and left_constituent.primitive():
            self.adjunct = True
            left_constituent.adjunct = False

    # Phrase structure geometry --------------------------------

    def complex(self):
        return self.right and self.left

    def primitive(self):
        return not self.complex()

    def is_left(self):
        return self.mother and self.mother.left == self

    def is_right(self):
        return self.mother and self.mother.right == self

    def has_affix(self):
        return self.right and not self.left

    def get_affix_list(x):
        lst = [x]
        while x.right and not x.left:
            lst.append(x.right)
            x = x.right
        return lst

    def bottom(x):
        return list(x.minimal_search())[-1]

    def top(x):
        while x.mother:
            x = x.mother
        return x

    def grandmother(self):
        if self.mother.mother:
            return self.mother.mother

    def aunt(self):
        if self.mother:
            return self.mother.sister()

    def head(self):
        if self.primitive():
            return self
        if self.left.primitive():
            return self.left
        if self.right.adjunct:
            return self.left.head()
        if self.right.primitive():
            return self.right
        return self.right.head()

    def inside(self, head):
        return self.head() == head

    def container(self):
        if self.mother:
            return self.mother.head()

    def max(self):
        x = self
        while x.mother and x.mother.head() == self:
            x = x.mother
        return x

    def minimal_search_domain(self):
        if not self.right_sister():
            return self
        return self.sister()


    def geometrical_sister(self):
        if self.is_left():
            return self.mother.right
        return self.mother.left

    def sister(x):
        while x.mother:
            if x.is_left():
                if not x.geometrical_sister().adjunct:
                    return x.geometrical_sister()
                else:
                    x = x.mother
            if x.is_right():
                if not x.adjunct:
                    return x.geometrical_sister()
                else:
                    return None

    def right_sister(self):
        if self.sister() and self.sister().is_right():
            return self.sister()

    def proper_selected_complement(self):
        if self.primitive():
            return self.right_sister()

    def selector(self):
        return self.next(self.upward_path, lambda x: x.primitive())

    def selected_sister(self):
        if self.sister() and not self.sister().proper_selected_complement():
            return self.sister()

    def specifier_sister(self):
        if self.is_left():
            return self.mother
        return self

    def extract_affix(self):
        affix = self.right
        self.right = None
        return affix

    def bottom_affix(x):
        if x.primitive():
            while x.right and not x.right.find_me_elsewhere:
                x = x.right
        return x

    def is_licensed_specifier(self):
        return self.max().container().licensed_phrasal_specifier() and self.max() == self.max().container().licensed_phrasal_specifier()

    def __iter__(self):
        self.nn = self
        return self

    def __next__(self):
        if not self.nn:
            raise StopIteration
        current = self.nn
        if self.nn.primitive():
            self.nn = None
            return current
        elif self.nn.head() == self.nn.right.head() or self.nn.left.proper_selected_complement():
            self.nn = self.nn.right
        else:
            self.nn = self.nn.left
        return current.left

    def minimal_search(self, selection_condition=lambda x: True, sustain_condition=lambda x: True):
        return takewhile(sustain_condition, (const for const in self if selection_condition(const)))

    def upward_path(self):
        upward_path = []
        x = self.mother
        while x:
            if x.left.head() != self:
                upward_path.append(x.left)
            x = x.mother
        return upward_path

    def next(self, memory_span, condition=lambda x: True):
        return next((x for x in memory_span() if condition(x)), None)

    def edge(self):
        return list(takewhile(lambda x: x.mother and x.mother.inside(self), self.upward_path()))

    def pro_edge(self):
        if self.extract_pro():
            return self.edge() + [self.extract_pro()]
        return self.edge()

    def contains_features(self, feature_set):
        if self.complex():
            if self.left.contains_features(feature_set) or self.right.contains_features(feature_set):
                return True
        else:
            return self.check(feature_set)

    def return_constituent_with(self, feature):
        constituent = None
        if self.complex():
            constituent = self.left.return_constituent_with(feature)
            if constituent:
                return constituent
            constituent = self.right.return_constituent_with(feature)
        if self.primitive() and feature in self.features:
            constituent = self
        return constituent

    def geometrical_minimal_search(x):
        search_list = [x]
        while x.complex() and x.right:
            search_list.append(x.right)
            x = x.right
        return search_list

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
        return phi_consistency({f for f in self.features if f[:4] == 'PHI:'})

    # Condition for independent pro-element
    def sustains_reference(self):
        return self.phi_consistent_head() and self.has_full_phi_set()

    def pro_legibility(self):
        iter = self.minimal_search_domain().minimal_search(lambda x: x.primitive(), lambda x: x.root_predicate() or (not x.phase_head()) and not x.check({'PER'}))
        return next((x for x in iter if x.root_predicate()), None)

    # Selection -------------------------------------------------------------------------------------------

    # Feature -SPEC:L
    def selection__negative_specifier(self,  selected_feature):
        return not self.next(self.edge, lambda x: x.check({selected_feature}) and not x.adjunct)

    # Feature !1EDGE
    def selection__negative_one_edge(self, selected_feature):
        return len(self.edge()) < 2

    # Feature !COMP:L
    def selection__positive_obligatory_complement(self, selected_feature):
        return self.selected_sister() and self.selected_sister().check({selected_feature})

    # Feature -COMP:L
    def selection__negative_complement(self, selected_feature):
        return not (self.proper_selected_complement() and self.proper_selected_complement().check({selected_feature}))

    # Feature [!SELF]
    def selection__positive_self_selection(self, selected_features):
        selected_features_set = set(selected_features.split(','))
        return self.check(selected_features_set)

    # Feature [-SELF]
    def selection__negative_self_selection(self, selected_features):
        selected_features_set = set(selected_features.split(','))
        return not self.check(selected_features_set)

    # Feature [?SELF]
    def selection__partial_self_selection(self, selected_features):
        selected_features_set = set(selected_features.split(','))
        return self.check_some(selected_features_set)

    # Feature [!p]
    def selection__p_test(self, feature):
        return self.edge() or self.check({'strong_agr'})

    def specifier_match(self, phrase):
        return phrase.head().check_some(self.licensed_specifiers())

    def specifier_mismatch(self, phrase):
        return phrase.head().check_some(self.nonlicensed_specifiers())

    def double_spec_filter(self):
        return not self.check({'2SPEC'}) and len({spec for spec in self.edge() if not spec.adjunct}) > 1

    def licensed_phrasal_specifier(self):
        if self.next(self.edge, lambda x: x.referential() and not x.adjunct):
            return self.next(self.edge, lambda x: x.referential() and not x.adjunct)
        return self.next(self.edge, lambda x: x.referential())

    def complement_match(self, const):
        return const.check_some(self.licensed_complements())

    def nonlicensed_complement(self):
        return self.proper_selected_complement() and self.proper_selected_complement().check_some(self.complements_not_licensed())

    def missing_mandatory_complement(self):
        return self.get_mandatory_comps() and (not self.proper_selected_complement() or not self.proper_selected_complement().check(self.get_mandatory_comps()))

    def complement_not_licensed(self):
        return self.proper_selected_complement() and not self.proper_selected_complement().check(self.licensed_complements())

    def properly_selected(self):
        return self.selector() and self.check_some(self.selector().licensed_complements())

    def does_not_accept_any_complements(self):
        return self.check({'-COMP:*'})

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
                if node.check({G}) or (G[:4] == 'TAIL' and G[5:] in node.scan_features('OP')[0]):
                    return True
                if node.check(intervention_features):
                    break

    def edge_feature_tests(self):
        if 'EF' not in self.features and self.edge() and not self.edge()[0].head().check({'Adv'}):
            if not ((self.edge()[0] == self.sister() and self.check_some({'!COMP:φ', 'COMP:φ'})) or self.check_some({'SPEC:φ', '!SPEC:φ'})):
                return True

    # Projection principle and thematic roles ---------------------------------------------------------------------
    def nonthematic(self):
        if self.max().container():
            return self.max().container().EF() or \
                   (self.max().container().check_some({'-SPEC:*', '-SPEC:φ', '-SPEC:D'}) and
                    self == next((const for const in self.max().container().edge()), None))

    def projection_principle_failure(self):
        return self.max().projection_principle_applies() and \
               not self.max().container_assigns_theta_role()

    def projection_principle_applies(self):
        return self.referential() and \
               self.max() and \
               not self.max().find_me_elsewhere and \
               self.max().mother and \
               not self.max().contains_features({'adjoinable', 'SEM:nonreferential'})

    # Configuration [A <XP>] is unclear, currently it satisfies Projection Principle if A licenses XP because Finnish reconstructed arguments
    # satisfy this configuration, but the assumption is unintuitive. Perhaps <XP> has to be returned to the primary plane
    # when it is reconstructed to this position
    def container_assigns_theta_role(self):
        assigner = self.max().container()
        return assigner and \
               (assigner.sister() == self or
                (self.referential() and assigner.geometrical_sister() == self and self.check_some(assigner.licensed_complements())) or
                self.is_licensed_specifier() and assigner.specifier_theta_role_assigner())

    def specifier_theta_role_assigner(self):
        if self.EF():
            return False
        if self.check_some({'SPEC:φ', '!SPEC:φ'}) and not (self.selector() and self.selector().check({'-ARG'})):
            return True

    # Reconstruction -----------------------------------------------------------------------------------
    def EF(self):
        for f in self.features:
            if f.startswith('!EF') or f.startswith('EF') or f == '!SEF':
                return True

    # Used by post-LF predicates module (experimental)
    def p_associate_check(self, goal):
        if goal and self.check({'!p'}) and not self.check({'strong_agr'}) and not self.check({'!SELF:PER'}) and not self.theta_head():
            return self != goal and not (next(iter(self.edge()), self).head().get_id() == goal.head().get_id())

    def create_chain(self, transfer, inst):
        for target in self.select_targets(inst):
            inst, target = self.prepare_chain(target, inst, transfer)
            self.form_chain(target, inst)
            transfer.brain_model.consume_resources(inst['type'], self)

            # Successive-cyclicity
            if target.primitive() and inst['test integrity'](target):
                target.create_chain(transfer, inst)
            elif target.max().container() and inst['test integrity'](target.max().container()):
                target.max().container().create_chain(transfer, inst)

    def select_targets(self, instructions):
        if instructions['type'] == 'Phrasal Chain':
            return [x for x in self.edge() if not x.find_me_elsewhere and not self.licensed_expletive(x)]
        return [self.right]

    def prepare_chain(probe, specifier, inst, transfer):
        if inst['type'] == 'Phrasal Chain':
            if probe.scan_criterial_features(specifier, 'ΔOP'):
                if not specifier.supported_by(probe):
                    probe = specifier.sister().Merge(transfer.access_lexicon.PhraseStructure(), 'left').left
                    probe.features |= probe.add_scope_information()
                    log(f'\n\t\tCreated {probe}° ')
            else:
                inst['selection'] = lambda x: x.has_vacant_phrasal_position()
                inst['legible'] = lambda x, y: True
                log(f'\n\t\t{probe} triggers A-movement ')
            probe.copy_criterial_features(specifier)
            probe.features = transfer.access_lexicon.apply_redundancy_rules(probe.features)
        return inst, specifier.copy_for_chain(transfer.babtize())

    def form_chain(self, target, inst):

        # Core engine
        for head in self.minimal_search_domain().minimal_search(inst['selection'], inst['sustain']):
            if head != self and head.test_merge(target, inst['legible'], 'left'):
                break
            target.remove()

        # Last resort options
        else:
            if not self.top().bottom().test_merge(target, inst['legible'], 'right'):
                target.remove()
                if self.sister():
                    self.sister().Merge(target, 'left')

    def scan_criterial_features(self, specifier, feature):
        criterial_features = specifier.scan_features(feature)
        if 'OP*' not in criterial_features:
            specifier.head().features = specifier.head().features | criterial_features
        for f in list(criterial_features):
            if 'OP' in f:
                return True

    def scan_features(self, feature):
        criterial_feature_set = set()
        if self.left and not self.left.find_me_elsewhere:
            criterial_feature_set = self.left.scan_features(feature)
        if not criterial_feature_set and self.right and not self.right.find_me_elsewhere and not {'T/fin', 'C'} & self.right.head().features:
            criterial_feature_set= self.right.scan_features(feature)
        if not criterial_feature_set and self.primitive():
            criterial_feature_set = {f for f in self.features if f.startswith(feature) and f[-1] != '_'}
        return criterial_feature_set

    def copy_criterial_features(self, specifier):
        for f in [g for g in specifier.head().features if g.startswith('Δ')]:
            self.features.add(f[1:])
            self.features.add('OP:_')
            log(f'[{f[1:]}] ')

    def index(self):
        for f in self.features:
            if f.startswith('#'):
                return f[1:]

    def supported_by(self, probe):
        return self == probe.next(probe.edge)

    def test_merge(self, obj, legible, direction):
        self.specifier_sister().Merge(obj, direction)
        return legible(self, obj)

    def Abar_legible(self, y):
        if y == self.next(self.edge):
            if len(self.edge()) < 2 and self.specifier_match(y) and self.specifier_sister().tail_match(self.specifier_sister(), 'left'):
                return True
        if y.is_right():
            y.adjunct = False
        if self.sister() == y:
            if self.complement_match(y) and not (y.is_left() and self.specifier_mismatch(y)):
                return True

    def VP_for_fronting(self):
        return self == self.container().next(self.container().upward_path, lambda x: x.mother.inside(self.container()) and x.head().check_some({'VA/inf', 'A/inf'}))

    def has_legitimate_specifier(self):
        return self.predicate() and not self.head().check_some({'-EF:φ', '-EDGE:*'}) and self.edge() and not self.has_unlicensed_specifier()

    def unlicensed_specifier(self):
        return self.complex() and not self.adjunct and self.container() and self != self.container().licensed_phrasal_specifier()

    def has_vacant_phrasal_position(self):
        return self.gapless_heads() or self.is_right()

    def gapless_heads(self):
        return self.primitive() and self.aunt() and self.aunt().primitive()

    def has_nonthematic_specifier(self):
        return self.EF() and next(iter(self.edge()), self).extended_subject()

    def add_scope_information(self):
        if not self.non_scopal():
            return {'Fin', 'C', 'PF:C'}
        return set()

    def AgreeLF(self):
        self.value_features_from(self.get_goal())

    def get_goal(self):
        return next(self.minimal_search_domain().minimal_search(lambda x: (x.head().referential() and not x.find_me_elsewhere) or
                                                                          x.phase_head() or x.check({'PER'}), lambda x: not x.phase_head()), None)

    def value_features_from(self, goal):
        if goal:
            log(f'\n\t\tAgree({self}°, {goal.head()})')
            for phi, phi_ in [(i(phi), self.unvalued_counterparty(i(phi))) for phi in sorted(list(goal.head().features)) if self.target_phi_feature(phi, goal)]:
                log(f' {phi}')
                if self.feature_licensing(phi, goal):
                    self.features.discard(phi_)
                    self.features.add(phi)
            self.features.update({'ΦLF', 'dPHI:IDX:' + goal.head().get_id()})
            self.induce_p()

    def target_phi_feature(self, phi, goal):
        if valued_phi_feature(phi):
            if goal.has_interpretable_phi_features():
                if self == goal:
                    return not interpretable_phi_feature(phi)
                else:
                    return interpretable_phi_feature(phi)
            return True

    def unvalued_counterparty(self, phi):
        return next((phi_ for phi_ in self.head().features if unvalued(phi_) and phi.startswith(phi_[:-1])), None)

    # Check if types match, then there must be a licensing feature with identical value.
    def feature_licensing(self, phi, goal):
        if goal.nonverbal():
            probe_type_matched_phi = {phi_ for phi_ in self.get_phi_set() if valued_phi_feature(phi_) and self.type_match(phi, phi_)}
            if not probe_type_matched_phi or {x for x in probe_type_matched_phi if x == phi}:
                return True
        log(f'(*)')
        self.features.add('*')

    def has_interpretable_phi_features(self):
        return next((phi for phi in self.head().features if phi.startswith('iPHI:')), None)

    def argument_by_agreement(self):
        for f in self.features:
            if f.startswith('dPHI'):
                if self.sister():
                    idx = f.split(':')[2]
                    return next(self.sister().minimal_search(lambda x: idx in x.head().features, lambda x: not x.phase_head()), None)

    def cutoff_point_for_last_resort_extraposition(self):
        return self.primitive() and self.is_adjoinable() and self.aunt() and \
               (self.aunt().complex() or (self.aunt().primitive() and self.grandmother().induces_selection_violation()))

    def license_extraposition(self):
        return self.top().contains_finiteness() or self.top().referential()

    def extrapose(self, transfer):
        transfer.brain_model.adjunct_constructor.externalize_structure(self.sister().head())
        transfer.brain_model.consume_resources('Extraposition', self)

    def last_resort_extrapose(self, transfer):
        transfer.brain_model.adjunct_constructor.externalize_structure(self.bottom().next(self.bottom().upward_path, lambda x: x.cutoff_point_for_last_resort_extraposition()))

    def feature_inheritance(self):

        if self.highest_finite_head() and not self.check({'-ΦPF'}):
            log(f'\n\t\t{self} acquired φ-completeness.')
            self.features.add('!SELF:PER')

        if self.check({'?ARG'}):
            self.features.discard('?ARG')
            if self.selected_by_SEM_internal_predicate():
                log(f'\n\t\t{self}° resolved into -ARG.')
                self.features.add('-ARG')
                self.features.add('-SELF:ΦPF,ΦPF')
                self.features.add('opaque')
            elif self.selected_by_SEM_external_predicate() or (self.selector() and self.selector().check({'Fin'})):
                log(f'\n\t\t{self}° resolved into ARG.')
                self.features.add('ARG')
                self.features.add('?SELF:ΦLF,ΦPF')
                self.features.add('PHI:NUM:_')
                self.features.add('PHI:PER:_')
            else:
                self.features.add('ARG')
                self.features.add('PHI:NUM:_')
                self.features.add('PHI:PER:_')

    def valid_reconstructed_adjunct(self, starting_point_node):
        if self.head().tail_test():
            if self.adverbial_adjunct() or self.non_adverbial_adjunct_condition(starting_point_node):
                if self.container():
                    h = self.container()
                    if self == h.next(h.edge):
                        return h.specifier_match(self)
                    if self == h.sister():
                        return h.complement_match(self)
                else:
                    return True     # XP without container is accepted

    def trigger_adjunct_reconstruction(self):
        return not self.legible_adjunct() and self.adjoinable() and self.floatable() and not self.operator_in_scope_position() and not self.expletive()

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
        local_edge = self.next(self.edge)
        if local_edge:
            return set(self.specifiers_not_licensed()) & local_edge.head().features

    def get_constituent_containing_selection_violation(self):
        return next((x for x in self if x.induces_selection_violation() and not x.sister().adjunct), None)

    def induces_selection_violation(self):
        return self.nonlicensed_complement() or self.missing_mandatory_complement()

    def non_adverbial_adjunct_condition(self, starting_point_head):
        if not self.container():
            return True
        if self.container() == starting_point_head or self.nonthematic() or (self.referential() and self.projection_principle_failure()):
            return False
        return True

    # Feature processing -----------------------------------------------------------------------------

    def check(self, feature_set):
        return feature_set == {'*'} or feature_set & self.head().features == feature_set

    def check_some(self, feature_set):
        return feature_set == {'*'} or feature_set & self.head().features

    def complements_not_licensed(self):
        return {f[6:] for f in self.features if f[:5] == '-COMP'}

    def licensed_specifiers(self):
        return {f[5:] for f in self.features if f[:4] == 'SPEC'} | {f[6:] for f in self.features if f[:5] == '!SPEC'}

    def nonlicensed_specifiers(self):
        return {f[6:] for f in self.features if f[:5] == '-SPEC'}

    def licensed_complements(self):
        return {f[5:] for f in self.features if f[:4] == 'COMP'} | {f[6:] for f in self.features if f[:5] == '!COMP'}

    def is_unvalued(self):
        for f in self.features:
            if unvalued(f):
                return True

    def valued_phi_features(self):
        return {f for f in self.features if 'PHI:' in f and f[-1] != '_'}

    def get_pf(self):
        return {feature[3:] for feature in self.features if feature[:3] == 'PF:'}

    def get_phi_set(self):
        return {f for f in self.features if f[:4] == 'PHI:' and len(f.split(':')) == 3}

    def get_tail_sets(self):
        return {frozenset(f[5:].split(',')) for f in self.head().features if f[:4] == 'TAIL'}

    def needs_valuation(self):
        return not self.sustains_reference() and self.has_unvalued_phi()

    def phi_is_unvalued(self):
        for f in self.head().features:
            if f[-1] == '_':
                return True

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
            if feature1 == '*':
                return True
            if feature1.startswith('-'):
                for feature2 in self.features:
                    if feature1[1:] == remove_exclamation(feature2):
                        log(f'\n\t\tFeature conflict +/{feature1}')
                        return True

    # Operators

    def checking_domain(self, narrow_domain):
        if narrow_domain:
            return self.head()
        return self

    def operator_in_scope_position(self):
        return self.container() and self.container().head().finite() and self.scan_features('ΔOP')

    # Tail-processing ---------------------------------------------------------------------------

    def tail_test(self):
        pos_tsets = {frozenset(positive_features(tset)) for tset in self.get_tail_sets() if positive_features(tset)}
        neg_tsets = {frozenset(negative_features(tset)) for tset in self.get_tail_sets() if negative_features(tset)}
        checked_pos_tsets = {tset for tset in pos_tsets if self.tail_condition(tset)}
        checked_neg_tsets = {tset for tset in neg_tsets if self.tail_condition(tset)}
        return pos_tsets == checked_pos_tsets and not checked_neg_tsets

    def tail_condition(self, tset):
        if not self.referential() and \
                self.max() and \
                self.max().container() and \
                (self.max().container().check(tset) or
                 (self.max().mother.sister() and
                  self.max().mother.sister().check(tset))):
            return True
        if self.referential() or self.preposition():
            for m in (affix for node in self.upward_path() if node.primitive() for affix in node.get_affix_list()):
                if m.check_some(tset):
                    return m.check(tset)

    def tail_match(self, constituent_from_MB, direction):
        self.Merge(constituent_from_MB.copy(), direction)        # Test merge
        if direction == 'right':                                   # Presupposition
            self.geometrical_sister().adjunct = True
        result = self.geometrical_sister().head().tail_test()      # Test
        self.geometrical_sister().remove()                         # Remove trial unit
        return result

    # Recovery ---------------------------------------------------------------------------------------------------

    def is_possible_antecedent(self, antecedent):
        if antecedent:
            if not self.self_referencing(antecedent) and {phi for phi in antecedent.head().features if (phi.startswith("iPHI:") or phi.startswith("PHI:")) and not phi.endswith('_')}:
                if antecedent.head().referential() or antecedent.head().sustains_reference():
                    valued_phi_at_probe = [phi.split(':') for phi in self.features if (phi[:7] == 'PHI:NUM' or phi[:7] == 'PHI:PER') and not phi.endswith('_')]
                    valued_phi_at_antecedent = [phi.split(':') for phi in antecedent.head().features if (phi[:7] == 'PHI:NUM' or phi[:7] == 'PHI:PER' or phi[:8] == 'iPHI:NUM' or phi[:8] == 'iPHI:PER') and not phi.endswith('_')]
                    for P in valued_phi_at_probe:
                        for A in valued_phi_at_antecedent:
                            if P[1] == A[1] and P[2] != A[2]:
                                return False
                    return True

    def control(self):
        unvalued_phi = self.needs_valuation()
        if unvalued_phi & {'PHI:NUM:_', 'PHI:PER:_'} and not self.get_valued_phi() & {'PHI:NUM', 'PHI:PER'}:
            return self.standard_control()
        elif unvalued_phi & {'PHI:DET:_'}:
            return self.finite_control()

    def standard_control(self):
        search_path = [x for x in takewhile(lambda x: not x.head().check({'SEM:external'}), self.upward_path())]
        antecedent = next((x for x in search_path if not x.find_me_elsewhere and self.is_possible_antecedent(x)), PhraseStructure())
        if not antecedent.features:
            antecedent.features = {"PF:generic 'one'", 'LF:generic', 'φ', 'D'}
        log(f'\n\t\t\tAntecedent search for {self} provides {antecedent} (standard control). ')
        return antecedent

    def finite_control(self):
        antecedent = self.next(self.upward_path, lambda x: x.complex() and (self.is_possible_antecedent(x) or x.expletive()) and not x.find_me_elsewhere)
        log(f'\n\t\t\tAntecedent search for {self} provides {antecedent} (finite control). ')
        return antecedent

    # Structure building --------------------------------------------------------------------------

    def Merge(self, C, direction=''):
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

    def merge_around(self, reconstructed_object, legibility=lambda x: True):
        if not (self.Merge(reconstructed_object, 'right') and legibility(reconstructed_object)):
            reconstructed_object.remove()
            if not (self.Merge(reconstructed_object, 'left') and legibility(reconstructed_object)):
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
        self.internal = False
        return self.top()

    def belong_to_same_word(self, site):
        return self.bottom_affix().internal and site.primitive()

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
        return self.Merge(incoming_constituent)

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
        if self.left and self.right:
            if 'null' in self.right.features:
                pf = pf + '_'
            else:
                pf = pf + self.right.gloss() + ' '
        if self.primitive():
            pf = pf + LF_features(self)
        return pf

    def label(self):
        head = self.head()
        if self.complex():
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
                h.features.add('null')      # Null is about what is printed out
                h.features.discard('Δp')    # This is the grammatical feature that operates in narrow syntax
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
        if self.primitive():
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
        if self.primitive():
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
        if self.features and 'null' in self.features and self.complex():
            if self.adjunct:
                return '<__>' + chain_index_str
            else:
                return '__' + chain_index_str
        if self.primitive():
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
            if f.startswith('#'):
                return f
        return '?'

    #  Definitions and abstractions for terms

    def adverbial(self):
        return self.check({'Adv'})

    def nominal(self):
        return self.check({'N'})

    def nonverbal(self):
        return self.nominal() or self.referential() or self.adjectival()

    def adjectival(self):
        return self.check({'A'})

    def root_predicate(self):
        return not self.check({'-ARG'}) and (self.light_verb() or self.check({'V'}) or self.check({'N'}) or self.check({'φ'}))

    def light_verb(self):
        return self.check_some({'v', 'v*', 'impass', 'cau'})

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

    def interpretable_phi(self):
        return {f for f in self.features if f.startswith('iPHI:')}

    def preposition(self):
        return self.check({'P'})

    def floatable(self):
        return not self.check({'-float'})

    def non_scopal(self):
        return self.check_some({'Inf', 'P', 'D', 'φ'})

    def expresses_concept(self):
        return self.check_some({'N', 'Neg', 'P', 'D', 'φ', 'A', 'V', 'Adv', 'Q', 'Num', '0'}) and not self.check({'T/prt', 'COPULA'})

    def unrecognized_label(self):
        return self.check_some({'CAT:?', '?'})

    def predicate(self):
        return self.primitive() and self.check({'ARG'}) and not self.check({'-ARG'})

    def adverbial_adjunct(self):
        return self.adverbial() or self.preposition()

    def is_adjoinable(self):
        return self.adjunct or (self.head().check({'adjoinable'}) and not self.head().check({'-adjoinable'}))

    def clitic(self):
        return self.check({'CL'}) or self.head().check({'CL'}) and not self.head().has_affix() and self.head().internal

    def concept(self):
        next((x for x in self.get_affix_list() if x.expresses_concept()), False)

    def semantic_complement(self):
        return self.proper_selected_complement() and not self.semantic_match(self.proper_selected_complement())

    def selected_by_SEM_internal_predicate(self):
        return self.selector() and self.selector().SEM_internal_predicate()

    def selected_by_SEM_external_predicate(self):
        return self.selector() and self.selector().SEM_external_predicate()

    def SEM_internal_predicate(self):
        return self.check({'SEM:internal'})

    def SEM_external_predicate(self):
        return self.check({'SEM:external'})

    def isolated_preposition(self):
        return self.preposition() and self.sister() and self.sister().primitive()

    def adjoinable(self):
        return self.complex() and not self.find_me_elsewhere and self.head().get_tail_sets() and self.check({'adjoinable'}) and not self.check({'-adjoinable'})

    def legitimate_criterial_feature(self):
        return self.referential() and not self.relative() and self.mother and self.mother.contains_features({'REL'}) and not self.mother.contains_features({'T/fin'})

    def interpretable_adjunct(self):
        return self.referential() and self.max() and self.max().adjunct and self.max().is_right() and self.max().mother and self.max().mother.referential()

    def word_internal(self):
        return self.bottom().bottom_affix().internal

    def impossible_sequence(self, w):
        return self.primitive() and 'T/fin' in self.head().features and 'T/fin' in w.features

    def is_word_internal(self):
        return self.mother and self.sister() and self.sister().primitive() and self.sister().internal

    def phase_head(self):
        return self.primitive() and not self.check_some({'opaque', 'φ'})

    def extended_subject(self):
        return self.check_some({'GEN'})

    def highest_finite_head(self):
        return self.check({'Fin'}) and not self.check_some({'C', 'FORCE'}) and not (self.selector() and self.selector().check_some({'T', 'COPULA', 'Fin'}))

    def theta_assigner(self):
        return self.check_some({'SPEC:φ', 'SPEC:D', 'COMP:φ', 'COMP:D', '!SPEC:φ', '!SPEC:D', '!COMP:φ', '!COMP:D'})

    def theta_head(self):
        return self.check_some({'COMP:φ', '!COMP:φ', 'v', 'V'}) and not self.check({'!SELF:Φ'})

    def expletive(self):
        return self.head().check({'EXPL'})

    def open_class(self):
        return self.head().check_some({'N', 'V', 'P', 'A'})

    def licensed_expletive(self, phrase):
        return phrase.expletive() and self.head().check_some({'SPEC:EXPL', '!SPEC:EXPL'})

    def theta_marks(self, target):
        if self.sister() == target:
            return self.check_some({'SPEC:φ', '!SPEC:φ', 'COMP:φ', '!COMP:φ'})
        return self.check_some({'SPEC:φ', '!SPEC:φ'})

    def coreference_by_Agree(self, goal):
        return {f.split(':')[2] for f in goal.head().features if f.split(':')[0] == 'dPHI'} & self.head().features

    def self_referencing(self, goal):
        return goal.head().get_id() == self.get_id()

    def requires_SUBJECT(self):
        return self.check({'?SELF:ΦLF,ΦPF'})

    def get_dPHI(self):
        return {f for f in self.head().features if f.startswith('dPHI:')}

    def get_valued_phi(self):
        return {f[:7] for f in self.features if f[:4] == 'PHI:' and f[-1] != '_'}

    def has_full_phi_set(self):
        return len({'PHI:NUM', 'PHI:PER', 'PHI:DET'} & self.get_valued_phi()) == 3

    def has_unvalued_phi(self):
        return {phi for phi in self.features if phi[-1] == '_' and (phi[:7] == 'PHI:NUM' or phi[:7] == 'PHI:PER' or phi[:7] == 'PHI:DET')}

    def type_match(self, phi, phi_):
        return phi.split(':')[1] == phi_.split(':')[1]

    def induce_p(self):
        if self.check_some({'?SELF:ΦLF,ΦPF', '!SELF:ΦLF,ΦPF'}):
            self.features.add('!p')

