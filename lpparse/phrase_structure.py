from collections import namedtuple
from itertools import takewhile
from feature_processing import *
from support import log, set_logging

major_cats = ['√', 'n', 'N', 'Neg', 'Neg/fin', 'P', 'D', 'Qn', 'Num', 'φ', 'Top', 'C', 'a', 'A', 'v', 'V', 'Pass', 'VA/inf', 'T', 'Fin', 'Agr',
              'A/inf', 'MA/inf', 'ESSA/inf', 'E/inf', 'TUA/inf', 'KSE/inf', 'Inf',
              'FORCE', 'EXPL', 'Adv',
              '0', 'a', 'b', 'c', 'd', 'x', 'y', 'z', 'X', 'Y', 'Z']
Result = namedtuple('Result', 'match_occurred outcome')


class PhraseStructure:
    speaker_model = None
    access_experimental_functions = None
    spellout_heads = False      # This parameter, if set true, spells out PF-content of heads in all printouts; otherwise only labels are shown
    phase_heads = {'ph', 'φ'}   # Phase heads set for all calculations
    resources = {"Merge-1": {"ms": 0, "n": 0}}
    chain_index = 0
    transfer_operation = None
    instructions =        {'Head': {'type': 'Head Chain',
                                    'test integrity': lambda x: x.has_affix() and not x.right.find_me_elsewhere and not x.License_EHM(),
                                    'repair': lambda x: x.create_chain(),
                                    'selection': lambda x: True,
                                    'sustain': lambda x: True,
                                    'legible': lambda x, y: y.properly_selected() and not y.empty_finite_EPP() and y.right_sister() != x,
                                    'single operation': False,
                                    'prepare': lambda x: x.prepare_head_chain()},
                           'Phrasal': {'type': 'Phrasal Chain',
                                       'test integrity': lambda x: not x.find_me_elsewhere and x.complex() and x.is_left() and not x.expletive() and x.container() and x.container().EF(),
                                       'repair': lambda x: x.create_chain(),
                                       'selection': lambda x: x.primitive() and not x.finite(),
                                       'sustain': lambda x: not (x.primitive() and x.referential()),
                                       'legible': lambda x, y: x.Abar_legible(y),
                                       'prepare': lambda x: x.prepare_phrasal_chain()},
                           'Feature': {'type': 'Feature Inheritance',
                                       'test integrity': lambda x: x.check({'ARG?'}) or x.highest_finite_head() and not x.check({'-ΦPF'}),
                                       'repair': lambda x: x.feature_inheritance(),
                                       'single operation': False},
                           'A-chain':  {'type': 'Phrasal Chain',
                                        'repair': lambda x: x.create_chain(),
                                        'selection': lambda x: x.has_vacant_phrasal_position(),
                                        'legible': lambda x, y: True,
                                        'sustain': lambda x: not (x.primitive() and x.referential()),
                                        'test integrity': lambda x: not x.find_me_elsewhere and x.complex() and x.is_left() and x.container() and x.container().EF(),
                                        'prepare': lambda x: x.prepare_phrasal_chain()},
                           'Agree': {'type': 'Agree',
                                     'test integrity': lambda x: x.is_unvalued(),
                                     'repair': lambda x: PhraseStructure.speaker_model.Experimental_functions.Agree(x)},
                           'Extraposition': {'type': 'Extraposition',
                                             'test integrity': lambda x: x.primitive() and (x.top().contains_finiteness() or x.top().referential()) and x.induces_selection_violation() and x.sister() and not x.sister().adjunct,
                                             'repair': lambda x: x.extrapose()},
                           'Right Scramble': {'type': 'Right Scrambling',
                                              'test integrity': lambda x: not x.find_me_elsewhere and x.trigger_right_node_scrambling(),
                                              'repair': lambda x: x.right_scrambling()},
                           'Left Scramble': {'type': 'Left Scrambling',
                                             'test integrity': lambda x: x.complex() and not x.find_me_elsewhere and x.trigger_scrambling(),
                                             'repair': lambda x: x.reconstruct_scrambling()},
                           'Last Resort Extraposition': {'type': 'Last Resort Extraposition',
                                                         'test integrity': lambda x: (x.top().contains_finiteness() or x.top().referential()) and not PhraseStructure.speaker_model.LF.LF_legibility_test_detached(x.top()),
                                                         'repair': lambda x: x.last_resort_extrapose()}}
    transfer_sequence = [instructions['Head'],
                         instructions['Feature'],
                         instructions['Extraposition'],
                         instructions['Right Scramble'],
                         instructions['Left Scramble'],
                         instructions['Phrasal'],
                         instructions['Agree'],
                         instructions['Last Resort Extraposition']]

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
        self.adjunct = False
        self.find_me_elsewhere = False
        self.identity = ''
        self.internal = False
        self.rebaptized = False
        self.stop = False
        self.nn = None
        self.x = 0
        self.y = 0
        self.X = 0
        self.Y = 0
        self.canvas_ID = 0
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
        if self.mother and self.head() != self.mother.head():
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
            if x.is_right():
                if not x.geometrical_sister().adjunct:
                    return x.geometrical_sister()
                else:
                    x = x.mother
            else:
                if not x.geometrical_sister().adjunct:
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
        return self.max().container().licensed_phrasal_specifier() and \
               self.max() == self.max().container().licensed_phrasal_specifier()

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

    def local_edge(self):
        if self.edge():
            return self.edge()[0]

    def pro_edge(self):
        if self.NS():
            return self.edge() + [self.NS()]
        return self.edge()

    def identify_argument(self):
        return next((acquire(self) for acquire in [lambda x: x.pro(), lambda x: x.local_edge(), lambda x: x.control()] if acquire(self)), None)

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

    # Virtual pronouns -----------------------------------------------------------------------

    def pro(self):
        if self.sustains_reference():
            return self.NS()

    def NS(self):
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
        phi_set = self.complete_valued_phi_set()
        for f in phi_set:
            for g in phi_set:
                if f.split(':')[0] == g.split(':')[0] and f.split(':')[1] != g.split(':')[1]:
                    return False
        return True

    def complete_valued_phi_set(self):
        phi_sets = [phi[4:].split(',') for phi in self.features if phi.startswith('PHI:') and not phi.endswith('_')]
        return {phi for phi_set in phi_sets for phi in phi_set}

    # Condition for independent pro-element: constituent phi-features and values for NUM, PER, DEF
    def sustains_reference(self):
        return self.phi_consistent_head() and self.has_full_referential_phi_set()

    def has_full_referential_phi_set(self):
        return {phi[:3] for phi in self.complete_valued_phi_set()} & {'NUM', 'PER', 'DET'} == {'NUM', 'PER', 'DET'}

    # INACTIVATED
    def pro_legibility(self):
        if not self.sister() or self.adjunct or self.nominal() or self.preposition():
            return True
        iter = self.minimal_search_domain().minimal_search(lambda x: x.primitive(), lambda x: x.theta_predicate() or (not x.phase_head()) and not x.check({'PER'}))
        return next((x for x in iter if x.theta_predicate()), None)

    # Selection -------------------------------------------------------------------------------------------
    # Feature -SPEC:L
    def selection__negative_specifier(self, selected_feature_set):
        return not self.next(self.edge, lambda x: x.check(selected_feature_set) and not x.adjunct)

    # Feature !1EDGE
    def selection__negative_one_edge(self, selected_feature):
        return len(self.edge()) < 2

    # Feature !COMP:L
    def selection__positive_obligatory_complement(self, selected_feature_set):
        return self.selected_sister() and self.selected_sister().check(selected_feature_set)

    # Feature +COMP:L,K
    def selection__positive_disjunctive_complement(self, selected_feature_set):
        return self.selected_sister() and self.selected_sister().check_some(selected_feature_set)

    # Feature -COMP:L
    def selection__negative_complement(self, selected_feature_set):
        return not (self.proper_selected_complement() and self.proper_selected_complement().check_some(selected_feature_set))

    # Feature [!]
    def selection__positive_self_selection(self, selected_features):
        return self.check(set(selected_features.split(',')))

    # Feature [-]
    def selection__negative_self_selection(self, selected_features):
        return not self.check(set(selected_features.split(',')))

    # Feature [+]
    def selection__partial_self_selection(self, selected_features):
        return self.check_some(set(selected_features.split(',')))

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
                    pass

    def edge_feature_tests(self):
        if 'EF' not in self.features and self.edge() and not self.edge()[0].head().check({'Adv'}):
            if not ((self.edge()[0] == self.sister() and self.check_some({'!COMP:φ', 'COMP:φ'})) or self.check_some({'SPEC:φ', '!SPEC:φ'})):
                return True

    def w_selection(self):
        for feature in self.features:
            if feature.startswith('!wCOMP:') and \
                    not self.right.check(set(feature.split(':')[1].split(','))):
                return True
            elif feature.startswith('-wCOMP:') and \
                    self.right.check_some(set(feature.split(':')[1].split(','))):
                return True

    # Test whether a complex head satisfies conditions of the UG
    def Complex_Head_Integrity(self):
        if self.has_affix():
            x = self
            while x.right:
                if x.w_selection():
                    return True
                if x.right.find_me_elsewhere:
                    return x.License_EHM()      # [ε] blocks IHM
                else:
                    if not x.License_EHM():     # [ε] licenses EHM
                        return True
                x = x.right

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

    # Transfer --------------------------------------------------------------------------------------------------------------------

    # Transfers phrase structure SELF (which may be part of a larger structure)
    # and re-attaches the transferred SELF to its host
    def transfer_to_LF(self):
        ps, m = self.detached()
        for op in PhraseStructure.transfer_sequence:
            PhraseStructure.transfer_operation = op
            self.reconstruct(op)
        return ps.reattach(m)

    def reconstruct(self, op):
        for const in (x for x in [self.bottom()] + self.bottom().upward_path() if op['test integrity'](x)):
            op['repair'](const)
            PhraseStructure.speaker_model.consume_resources(op['type'], const)

    # Chain creation (part of transfer)
    def create_chain(self):
        head, target = PhraseStructure.transfer_operation['prepare'](self)
        head.form_chain(target)
        if PhraseStructure.transfer_operation['test integrity'](target):
            target.create_chain()   # Recursion, successive-cyclicity

    def prepare_head_chain(self):
        return self, self.right.copy_for_chain()

    def prepare_phrasal_chain(self):
        if self.A_bar_operator():
            self.prepare_A_bar_chain(self.container())
        else:
            PhraseStructure.transfer_operation = PhraseStructure.instructions['A-chain']    # Last Resort option
        return self.container(), self.copy_for_chain()

    def prepare_A_bar_chain(self, probe):
        if not self == probe.next(probe.edge):
            probe = self.project_phonologically_null_head()
        probe.copy_criterial_features(self)
        probe.features = PhraseStructure.speaker_model.lexicon.apply_redundancy_rules(probe.features)

    def project_phonologically_null_head(self):
        probe = self.sister().Merge(PhraseStructure.speaker_model.lexicon.PhraseStructure(), 'left').left
        probe.features |= probe.add_scope_information()
        return probe

    def form_chain(self, target):
        for head in self.minimal_search_domain().minimal_search(PhraseStructure.transfer_operation['selection'], PhraseStructure.transfer_operation['sustain']):
            if head != self and head.test_merge(target, PhraseStructure.transfer_operation['legible'], 'left'):
                break
            target.remove()
        else:
            if not self.top().bottom().test_merge(target, PhraseStructure.transfer_operation['legible'], 'right'):
                target.remove()
                if self.sister() and not target.scan_criterial_features('ΔOP'):
                    self.sister().Merge_inside(target, 'left')
                else:
                    self.top().bottom().Merge_inside(target, 'right')  # Last Resort option

    def has_vacant_phrasal_position(self):
        return self.gapless_head() or self.is_right()

    def scan_criterial_features(self, feature):
        criterial_features = self.scan_features(feature)
        if 'OP*' not in criterial_features:
            self.head().features = self.head().features | criterial_features
        for f in list(criterial_features):
            if 'OP' in f:
                return True

    def scan_features(self, feature):
        criterial_feature_set = set()
        if self.left and not self.left.find_me_elsewhere:
            criterial_feature_set = self.left.scan_features(feature)
        if not criterial_feature_set and self.right and not self.right.find_me_elsewhere and not {'T/fin', 'C'} & self.right.head().features:
            criterial_feature_set = self.right.scan_features(feature)
        if not criterial_feature_set and self.primitive():
            criterial_feature_set = {f for f in self.features if f.startswith(feature) and f[-1] != '_'}
        return criterial_feature_set

    def copy_criterial_features(self, specifier):
        for f in [g for g in specifier.head().features if g.startswith('Δ')]:
            self.features.add(f[1:])
            self.features.add('OP:_')

    def test_merge(self, target, legible, direction):
        self.specifier_sister().Merge_inside(target, direction)
        return legible(self, target)

    def Abar_legible(self, target):
        # Conditions for accepting [SpecXP] as landing site
        if target == self.next(self.edge) and \
                len(self.edge()) == 1 and \
                self.specifier_match(target) and \
                self.specifier_sister().tail_match(self.specifier_sister(), 'left'):
            return True
        # Effect of [CompXP] as landing site
        if target.is_right():
            target.adjunct = False
        # Conditions for accepting [CompXP] as landing site
        if self.sister() == target:
            if self.complement_match(target) and not (target.is_left() and self.specifier_mismatch(target)):
                return True

    def gapless_head(self):
        return self.primitive() and self.aunt() and self.aunt().primitive()

    def has_nonthematic_specifier(self):
        return self.EF() and next(iter(self.edge()), self).extended_subject()

    def add_scope_information(self):
        if not self.non_scopal():
            return {'Fin', 'C', 'PF:C'}
        return set()

    @staticmethod
    def baptize_chain():
        PhraseStructure.chain_index += 1
        return str(PhraseStructure.chain_index)

    # Scrambling ==========================================================================

    def trigger_scrambling(self):
        return not self.legible_adjunct() and \
               self.adjoinable() and \
               self.floatable() and \
               not self.operator_in_scope_position() and \
               not self.expletive() and \
               self.container()

    def trigger_right_node_scrambling(self):
        return self.focus_right_node().trigger_scrambling()

    def right_scrambling(self):
        if not self.focus_right_node().in_situ_scrambling_solution():
            self.focus_right_node().reconstruct_scrambling()

    def in_situ_scrambling_solution(self):
        self.head().externalize_structure()
        return self.legible_adjunct() or self.head().adverbial() or not self.top().contains_finiteness()

    def focus_right_node(self):
        if self.is_left():
            return self.geometrical_sister()
        return self

    def legible_adjunct(self):
        return self.head().tail_test() and (self.is_right() or (self.is_left() and not self.nonthematic()))

    def reconstruct_scrambling(self):
        starting_point = self.container()
        virtual_test_item = self.copy()
        scrambled_phrase = self

        node = starting_point
        for node in self.local_tense_edge().minimal_search(lambda x: True, lambda x: x.sustain_condition_for_scrambling(self, self.local_tense_edge())):
            node.merge_scrambled_phrase(virtual_test_item)
            if node.test_adjunction_solution(scrambled_phrase, virtual_test_item, starting_point, 'left'):
                break
        else:
            node.Merge_inside(virtual_test_item, 'right')
            virtual_test_item.adjunct = False
            node.test_adjunction_solution(scrambled_phrase, virtual_test_item, starting_point, 'right')

    def local_tense_edge(self):
        return next((node.mother for node in self.upward_path() if node.finite() or node.force()), self.top())

    def sustain_condition_for_scrambling(self, target, local_tense_edge):
        return not (self.mother == target or
                    self.mother.find_me_elsewhere or
                    (self.force() and self.container() != local_tense_edge.head()) or
                    (self.primitive() and self.referential()))

    def test_adjunction_solution(self, scrambled_phrase, virtual_test_item, starting_point, direction):
        if virtual_test_item.valid_reconstructed_adjunct(starting_point):
            virtual_test_item.remove()
            scrambled_phrase.externalize_structure()
            s = self.merge_scrambled_phrase(scrambled_phrase.copy_for_chain(), direction)
            PhraseStructure.speaker_model.narrow_semantics.pragmatic_pathway.unexpected_order_occurred(s, starting_point)
            return True
        virtual_test_item.remove()

    def merge_scrambled_phrase(self, reconstructed_floater, direction='left'):
        target_node = self
        if direction == 'left':
            if self.is_left():
                target_node = self.mother
            if reconstructed_floater.adverbial_adjunct():
                target_node.Merge_inside(reconstructed_floater, 'right')
            else:
                target_node.Merge_inside(reconstructed_floater, 'left')
        else:
            target_node.Merge_inside(reconstructed_floater, 'right')
            reconstructed_floater.adjunct = False
        return reconstructed_floater

    def externalize_structure(self):
        if self and self.head().is_adjoinable() and self.mother:
            if self.complex():
                self.externalize_and_transfer()
            else:
                self.externalize_head()

    def externalize_head(self):
        if self.isolated_preposition():
            self.externalize_and_transfer()
        elif self.externalize_with_specifier():
            self.mother.mother.externalize_and_transfer()
        else:
            self.mother.externalize_and_transfer()

    def externalize_and_transfer(self):
        if self.mother:
            self.adjunct = True
            self.add_tail_features_if_missing()
            self.transfer_adjunct()

    def transfer_adjunct(self):
        detached_phrase, m = self.detached()
        detached_phrase.transfer_to_LF()
        detached_phrase.mother = m
        return detached_phrase

    def add_tail_features_if_missing(self):
        if not self.head().get_tail_sets():
            if self.referential():
                self.head().features.add('TAIL:V')
            else:
                self.head().features.add('TAIL:T')
                self.head().features.add('Adv')

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
                    return True  # XP without container is accepted

    def externalize_with_specifier(self):
        return self.is_left() and self.predicate() and \
               ((self.tail_test() and self.has_nonthematic_specifier()) or
                (not self.tail_test() and self.edge() and not self.has_unlicensed_specifier()))

    # Agreement ---------------------------------------------------------------------------------------------

    def AgreeLF(self):
        self.value_from_goal(self.get_goal())

    def get_goal(self):
        # Executes minimal search from the search domain until a phase head is encountered and
        # locates the first suitable goal
        return next(self.minimal_search_domain().minimal_search(lambda x: x.goal_selection(),
                                                                lambda x: not x.phase_head()), None)

    def goal_selection(self):
        # A goal is a phrase at the canonical position that has a referential head
        # or which is a phase head itself
        return not self.find_me_elsewhere and (self.head().referential() or self.phase_head())

    def value_from_goal(self, goal):
        if goal:
            log(f'\n\t\tAgree({self}°, {goal.head()}): ')
            # Conditions for successful valuation are that
            # (i) the incoming phi-features are licensed,
            # (ii) agreement/EPP rule is satisfied
            if feature_licensing(goal.head().interpretable_phi_features(), self.phi_masks()) and self.agreement_EPP_rule(goal):
                self.value(goal)
            else:
                log(f'Failure. ')
                self.features.add('*')

    # Finds all pairs of phi-features where the goal can value a corresponding unvalued phi-feature at the probe
    # and performs valuation at the probe
    def value(self, goal):
        log(f'valued features ')

        # A valuing phi-feature must be interpretable and the probe must have a corresponding unvalued feature.
        for phi in (x for x in goal.head().features if x.startswith('iPHI') and
                                                       f'PHI:{x.split(":")[1]}:_' in self.features):
            log(f'[{phi[5:]}] ')
            self.features.discard(f'PHI:{phi.split(":")[1]}:_')
            self.features.add(f'{phi[1:]}')

        # Leave a record of AgreeLF and provide the index
        self.features.update({'ΦLF', 'dPHI:IDX:' + goal.head().get_id()})

    # The probe X satisfies the Agreement/EPP rule if
    # (i) X is a theta-hear OR
    # (ii) X does not require an identifiable arguments OR
    # (iii) X has strong agreement features OR
    # (iv) X has weak agreement features and something at its edge OR
    # (v) X satisfies the chain condition.
    def agreement_EPP_rule(self, goal):
        return self.theta_head() or not self.requires_identifiable_local_argument() or self.check({'strong'}) or \
               (self.check({'weak'}) and self.edge()) or self.chain_condition(goal)

    def requires_identifiable_local_argument(self):
        return self.check_some({'+ΦLF,ΦPF', '!ΦLF,ΦPF'})

    # Chain legibility for A-system (will be later generalized to A-bar system)
    def chain_condition(self, goal):
        return next(iter(self.edge()), self).head().get_id() == goal.head().get_id() or \
               (self.edge() and self.edge()[0].expletive())

    def argument_by_agreement(self):
        for f in self.features:
            if f.startswith('dPHI'):
                if self.sister():
                    idx = f.split(':')[2]
                    return next(self.sister().minimal_search(lambda x: idx in x.head().features, lambda x: not x.phase_head()), None)

    # Extraposition
    def cutoff_point_for_last_resort_extraposition(self):
        return self.primitive() and self.is_adjoinable() and self.aunt() and \
               (self.aunt().complex() or (self.aunt().primitive() and self.grandmother().induces_selection_violation()))

    def license_extraposition(self):
        return self.top().contains_finiteness() or self.top().referential()

    def extrapose(self):
        self.sister().head().externalize_structure()
        PhraseStructure.speaker_model.consume_resources('Extraposition', self)

    def last_resort_extrapose(self):
        if self.primitive() and self.cutoff_point_for_last_resort_extraposition():
            self.externalize_structure()
            PhraseStructure.speaker_model.consume_resources('Last Resort Extraposition', self)

    def feature_inheritance(self):
        if self.highest_finite_head() and not self.check({'-ΦPF'}):
            self.features.add('!PER')
        if self.check({'ARG?'}):
            self.features.discard('ARG?')
            if self.selected_by_SEM_internal_predicate():
                log(f'\n\t\t{self}° resolved into -ARG.')
                self.features.add('-ARG')
                self.features.add('-ΦPF,ΦPF')
            elif self.selected_by_SEM_external_predicate() or (self.selector() and self.selector().check({'Fin'})):
                log(f'\n\t\t{self}° resolved into ARG.')
                self.features.add('ARG')
                self.features.add('+ΦLF,ΦPF')
                self.features.add('PHI:NUM:_')
                self.features.add('PHI:PER:_')
            else:
                self.features.add('ARG')
                self.features.add('PHI:NUM:_')
                self.features.add('PHI:PER:_')

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
        return feature_set == {'*'} or feature_set <= self.head().features

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
        if not self.sustains_reference() and self.get_unvalued_phi():
            return self.get_unvalued_phi()

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
        self.Merge_inside(constituent_from_MB.copy(), direction)   # Test merge
        if direction == 'right':                                   # Presupposition
            self.geometrical_sister().adjunct = True
        result = self.geometrical_sister().head().tail_test()      # Test
        self.geometrical_sister().remove()                         # Remove trial unit
        return result

    # Recovery ---------------------------------------------------------------------------------------------------

    def is_possible_antecedent(self, antecedent):
        if antecedent:
            if antecedent.head().referential() or antecedent.head().sustains_reference():
                valued_phi_at_probe = [phi.split(':') for phi in self.features if (phi[:7] == 'PHI:NUM' or phi[:7] == 'PHI:PER') and not phi.endswith('_') and not ',' in phi]
                valued_phi_at_antecedent = [phi.split(':') for phi in antecedent.head().features if (phi[:7] == 'PHI:NUM' or phi[:7] == 'PHI:PER' or phi[:8] == 'iPHI:NUM' or phi[:8] == 'iPHI:PER') and not phi.endswith('_')]
                for P in valued_phi_at_probe:
                    for A in valued_phi_at_antecedent:
                        if P[1] == A[1] and P[2] != A[2]:
                            return False
                return True

    def control(self):
        unvalued_phi = self.get_unvalued_phi()
        if unvalued_phi & {'PHI:NUM:_', 'PHI:PER:_'} and not self.get_valued_phi() & {'PHI:NUM', 'PHI:PER'}:
            return self.standard_control()
        elif unvalued_phi & {'PHI:DET:_'}:
            return self.finite_control()

    def standard_control(self):
        search_path = [x for x in takewhile(lambda x: not x.head().check({'SEM:external'}), self.upward_path())]
        antecedent = next((x for x in search_path if self.is_possible_antecedent(x)), PhraseStructure())
        if not antecedent.features:
            antecedent.features = {"PF:generic 'one'", 'LF:generic', 'φ', 'D'}
        return antecedent

    def finite_control(self):
        antecedent = self.next(self.upward_path, lambda x: x.complex() and (self.is_possible_antecedent(x)))
        return antecedent

    # Structure building --------------------------------------------------------------------------

    def Merge_inside(self, C, direction=''):
        local_structure = (self.mother, self.is_left())         # Snapshot of the local structure
        X = self.asymmetric_merge(C, direction)                 # Create new constituent X
        X.substitute(local_structure)                           # Insert X back into the local structure
        return X

    # Asymmetric Merge is a generalization of the bottom-up Merge (__init__) that can be provided with directionality
    def asymmetric_merge(self, B, direction='right'):
        self.consume_resources('Merge-1', self)
        if direction == 'left':
            return PhraseStructure(B, self)
        return PhraseStructure(self, B)

    def substitute(self, local_structure):
        if local_structure[0]:                          # If N had a mother
            if not local_structure[1]:                  # If N was right...
                local_structure[0].right = self         # the new constituent will be right,
            else:                                       # otherwise the new constituent will be left.
                local_structure[0].left = self
            self.mother = local_structure[0]            # The new constituent will have the same mother as N had (substitution)

    def merge_around(self, reconstructed_object, legibility=lambda x: True):
        if not (self.Merge_inside(reconstructed_object, 'right') and legibility(reconstructed_object)):
            reconstructed_object.remove()
            if not (self.Merge_inside(reconstructed_object, 'left') and legibility(reconstructed_object)):
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

    def attach(self, site, terminal_lexical_item, transfer, address_label):
        if site.primitive() and site.bottom_affix().word_internal():
            const = self.head_attachment(terminal_lexical_item)
        else:
            const = self.phrasal_attachment(terminal_lexical_item, transfer)
        self.speaker_model.consume_resources("Merge", const)
        log(f'({address_label})\n')
        return const

    def head_attachment(self, terminal_lexical_item):
        return self.bottom_affix().sink(terminal_lexical_item)

    def phrasal_attachment(self, terminal_lexical_item, transfer):
        new_left_branch = self
        m = self.mother
        set_logging(False)
        if transfer:
            ps, m = self.detached()
            new_left_branch = self.transfer_to_LF()
            new_left_branch.mother = m
        set_logging(True)
        new_left_branch.mother = m
        new_constituent = new_left_branch.Merge_inside(terminal_lexical_item)
        return new_constituent

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
        ps_.active_in_syntactic_working_memory = self.active_in_syntactic_working_memory
        ps_.adjunct = self.adjunct
        ps_.internal = self.internal
        ps_.find_me_elsewhere = self.find_me_elsewhere
        ps_.identity = self.identity
        return ps_

    def secure_copy(self):
        if self:
            return self.copy()
        return None

    def detached(self):
        m = self.mother
        self.mother = None
        return self, m

    def reattach(self, m):
        self.top().mother = m
        return self.top()

    def __add__(self, incoming_constituent):
        return self.Merge_inside(incoming_constituent)

    def get_index(self, target):
        for i, node in enumerate(self.geometrical_minimal_search()):
            if target == node:
                return i

    def get_node(self, idx):
        for i, node in enumerate(self.geometrical_minimal_search()):
            if i == idx:
                return node

    def index(self):
        for x in self.features:
            if x.startswith('§'):
                return x

    def target_left_branch(self, target):
        new_ps = self.top().copy()
        return new_ps.get_node(self.top().get_index(target))

    # Support ----------------------------------------------------------------------

    def find_constituent_with_index(self, idx):
        if self.index() == idx:
            return self
        if self.complex():
            const = self.left.find_constituent_with_index(idx)
            if const:
                return const
            return self.right.find_constituent_with_index(idx)

    def find_constituent_with_identity(self, ps, identity):
        if self.identity == identity and self != ps:
            return self
        if self.complex():
            const = self.left.find_constituent_with_identity(ps, identity)
            if const:
                return const
            return self.right.find_constituent_with_identity(ps, identity)

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

    def PF(self):
        for f in self.features:
            if f.startswith('PF:'):
                return f.split(':')[1]
        return '?'

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
            self.identity = self.baptize_chain()
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

        # Chain notation
        if self.find_me_elsewhere:
            chain_index_str = chain_index_str + ''

        # Phonologically null complex constituents
        if self.features and 'null' in self.features and self.complex():
            if self.adjunct:
                return '<__>' + chain_index_str
            else:
                return '__' + chain_index_str

        # Primitive heads
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
        def show_affixes(self):
            i = ''
            if self.has_affix():
                if PhraseStructure.spellout_heads:
                    i = self.right.PF()
                else:
                    i = self.right.label()
                if self.right.right:
                    i = '(' + show_affixes(self.right) + ' ' + i + ')'
            else:
                i = ''
            return i

        pfs = [f[3:] for f in self.features if f[:2] == 'PF']
        if self.has_affix():
            if not self.right.find_me_elsewhere:
                affix_str = show_affixes(self)
                return '(' + affix_str + ' ' + ''.join(sorted(pfs)) + ')°'
        return ''.join(sorted(pfs))

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
            if f.startswith('§'):
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

    def theta_predicate(self):
        return self.check({'θ'}) and not self.check({'-ARG'}) and not self.check({'-θ'})

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

    def interpretable_phi_features(self):
        return {f[5:] for f in self.features if f.startswith('iPHI:')}

    def preposition(self):
        return self.check({'P'})

    def floatable(self):
        return not self.check({'nonfloat'})

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
        return self.adjunct or (self.head().check({'adjoinable'}) and not self.head().check({'nonadjoinable'}))

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
        return self.complex() and not self.find_me_elsewhere and self.head().get_tail_sets() and self.head().check({'adjoinable'}) and not self.head().check({'nonadjoinable'})

    def legitimate_criterial_feature(self):
        return self.referential() and not self.relative() and self.mother and self.mother.contains_features({'REL'}) and not self.mother.contains_features({'T/fin'})

    def interpretable_adjunct(self):
        return self.referential() and self.max() and self.max().adjunct and self.max().is_right() and self.max().mother and self.max().mother.referential()

    def word_internal(self):
        return self.bottom().bottom_affix().internal

    def impossible_sequence(self, w):
        return self.primitive() and 'T/fin' in self.head().features and 'T/fin' in w.features

    def is_word_internal(self):
        return self.mother and self.sister() and self.sister().primitive() and self.sister().word_internal()

    def phase_head(self):
        return self.primitive() and self.check_some(PhraseStructure.phase_heads) and not self.check_some(PhraseStructure.phase_heads_exclude)

    def extended_subject(self):
        return self.check_some({'GEN'})

    def highest_finite_head(self):
        return self.check({'Fin'}) and not self.check_some({'C', 'FORCE'}) and not (self.selector() and self.selector().check_some({'T', 'COPULA', 'Fin'}))

    def theta_head(self):
        return self.theta_predicate() and not self.check({'!Φ'})

    def expletive(self):
        return self.head().check({'EXPL'})

    def open_class(self):
        return self.head().check_some({'N', 'V', 'P', 'A'})

    def licensed_expletive(self, phrase):
        return phrase.expletive() and self.head().check_some({'SPEC:EXPL', '!SPEC:EXPL'})

    def theta_marks(self, target):
        if self.sister() == target:
            return self.theta_predicate()
        return self.check_some({'SPEC:φ', '!SPEC:φ'})

    def coreference_by_Agree(self, goal):
        return {f.split(':')[2] for f in goal.head().features if f.split(':')[0] == 'dPHI'} & self.head().features

    def get_dPHI(self):
        return {f for f in self.head().features if f.startswith('dPHI:')}

    def get_valued_phi(self):
        return {f[:7] for f in self.features if f[:4] == 'PHI:' and f[-1] != '_'}

    def get_unvalued_phi(self):
        return {phi for phi in self.features if phi[-1] == '_' and (phi[:7] == 'PHI:NUM' or phi[:7] == 'PHI:PER' or phi[:7] == 'PHI:DET')}

    def phi_masks(self):
        return [set(phi[4:].split(',')) for phi in self.features if valued_phi_feature(phi) and not phi.startswith('i') and not 'IDX' in phi]

    def type_match(self, phi, phi_):
        return phi.split(':')[1] == phi_.split(':')[1]

    def EF(self):
        return {x for x in self.features if x == 'EF'}

    def A_bar_operator(self):
        return self.scan_criterial_features('ΔOP')

    def appropriate_argument(self):
        return not self.head().check({'pro_'}) and (self.referential() or self.expletive())

    def License_EHM(self):
        return 'ε' in self.features

