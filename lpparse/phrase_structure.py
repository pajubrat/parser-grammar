from collections import namedtuple
from itertools import takewhile
import itertools
from feature_processing import *
from support import log, set_logging

major_cats = ['√', 'n', 'N', 'Neg', 'Neg/fin', 'P', 'D', 'Qn', 'Num', 'φ', 'Top', 'C', 'a', 'A', 'v', 'V', 'Pass', 'VA/inf', 'T', 'Fin', 'Agr',
              'A/inf', 'MA/inf', 'ESSA/inf', 'E/inf', 'TUA/inf', 'KSE/inf', 'Inf',
              'FORCE', 'EXPL', 'Adv', 'Pr',
              '0', 'a', 'b', 'c', 'd', 'x', 'y', 'z', 'X', 'Y', 'Z']
Result = namedtuple('Result', 'match_occurred outcome')


class PhraseStructure:
    speaker_model = None
    access_experimental_functions = None
    spellout_heads = False      # This parameter, if set true, spells out PF-content of heads in all printouts; otherwise only labels are shown
    phase_heads = {'ph', 'φ'}   # Phase heads set for all calculations
    phase_heads_exclude = set()
    resources = {"Merge-1": {"ms": 0, "n": 0}}
    chain_index = 0
    node_identity = 0
    transfer_operation = None
    instructions =        {'Head': {'type': 'Head Chain',
                                    'test integrity': lambda x: x.affix() and not x.right().copied and not x.License_EHM(),
                                    'repair': lambda x: x.create_chain(),
                                    'selection': lambda x: True,
                                    'sustain': lambda x: True,
                                    'legible': lambda x, y: y.properly_selected() and not y.empty_finite_EPP() and y.right_sister() != x,
                                    'single operation': False,
                                    'prepare': lambda x: x.prepare_head_chain()},
                           'Phrasal': {'type': 'Phrasal Chain',
                                       'test integrity': lambda x: not x.copied and x.complex() and x.is_left() and not x.expletive() and x.container() and x.container().EF(),
                                       'repair': lambda x: x.create_chain(),
                                       'selection': lambda x: x.zero_level() and not x.finite(),
                                       'sustain': lambda x: not (x.zero_level() and x.referential()),
                                       'legible': lambda x, y: x.Abar_legible(y),
                                       'prepare': lambda x: x.prepare_phrasal_chain()},
                           'Feature': {'type': 'Feature Inheritance',
                                       'test integrity': lambda x: x.check({'ARG?'}) or x.highest_finite_head(),
                                       'repair': lambda x: x.feature_inheritance(),
                                       'single operation': False},
                           'A-chain':  {'type': 'Phrasal Chain',
                                        'repair': lambda x: x.create_chain(),
                                        'selection': lambda x: x.has_vacant_phrasal_position(),
                                        'legible': lambda x, y: True,
                                        'sustain': lambda x: not (x.zero_level() and x.referential()),
                                        'test integrity': lambda x: not x.copied and x.complex() and x.is_left() and x.container() and x.container().EF(),
                                        'prepare': lambda x: x.prepare_phrasal_chain()},
                           'Agree': {'type': 'Agree',
                                     'test integrity': lambda x: x.is_unvalued(),
                                     'repair': lambda x: PhraseStructure.speaker_model.Experimental_functions.Agree(x)},
                           'Extraposition': {'type': 'Extraposition',
                                             'test integrity': lambda x: x.zero_level() and (x.top().contains_finiteness() or x.top().referential()) and x.induces_selection_violation() and x.sister() and not x.sister().adjunct,
                                             'repair': lambda x: x.extrapose()},
                           'Right Scramble': {'type': 'Right Scrambling',
                                              'test integrity': lambda x: not x.copied and x.trigger_right_node_scrambling(),
                                              'repair': lambda x: x.right_scrambling()},
                           'Left Scramble': {'type': 'Left Scrambling',
                                             'test integrity': lambda x: x.complex() and not x.copied and x.trigger_scrambling(),
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

    def __init__(self, left=None, right=None):
        self.const = []
        if left and right:
            self.create_constituents([left, right])
        self.mother_ = None
        self.features = set()
        self.active_in_syntactic_working_memory = True
        self.adjunct = False
        self.copied = False
        self.identity = ''
        self.node_identity = self.create_node_identity()
        self.internal = False
        self.rebaptized = False
        self.stop = False
        self.nn = None
        if left and left.adjunct and left.zero_level():
            self.adjunct = True
            left.adjunct = False

    # Phrase structure geometry --------------------------------
    def left(X):
        if X.const:
            return X.const[0]

    def right(X):
        if X.const:
            return X.const[-1]

    def mother(X):
        return X.mother_

    def create_constituents(X, lst):
        X.const = lst
        for x in X.const:
            x.mother_ = X

    def terminal(X):
        return not X.const

    def complex(X):
        return len(X.const) > 1

    def zero_level(X):
        return len(X.const) < 2

    def is_left(X):
        return X.mother() and X.mother().left() == X

    def is_right(X):
        return X.mother() and X.mother().right() == X

    def affix(X):
        if X.left() == X.right():
            return X.left()

    def get_affix_list(X):
        lst = [X]
        while X.affix():
            lst.append(X.affix())
            X = X.affix()
        return lst

    def bottom(X):
        return list(X.minimal_search())[-1]

    def top(X):
        while X.mother():
            X = X.mother()
        return X

    def grandmother(X):
        if X.mother().mother():
            return X.mother().mother()

    def aunt(X):
        if X.mother():
            return X.mother().sister()

    def head(X):
        for x in [X] + X.const:
            if x.zero_level():
                return x
        return X.right_nonadjunct().head()

    def right_nonadjunct(X):
        if X.right().adjunct:
            return X.left()
        return X.right()

    def inside(X, head):
        return X.head() == head

    def container(X):
        if X.mother() and X.head() != X.mother().head():
            return X.mother().head()

    def max(X):
        x = X
        while x.mother() and x.mother().head() == X.head():
            x = x.mother()
        return x

    def minimal_search_domain(X):
        if not X.right_sister():
            return X
        return X.sister()

    def geometrical_sister(X):
        if X.is_left():
            return X.mother().right()
        return X.mother().left()

    def sister(X):
        while X.mother():
            if not X.geometrical_sister().adjunct:
                return X.geometrical_sister()
            X = X.mother()

    def right_sister(X):
        if X.sister() and X.sister().is_right():
            return X.sister()

    def proper_selected_complement(X):
        if X.zero_level():
            return X.right_sister()

    def selector(X):
        return X.next(X.upward_path, lambda x: x.zero_level())

    def selected_sister(X):
        if X.geometrical_sister() and X.zero_level():
            return X.geometrical_sister()

    def specifier_sister(X):
        if X.is_left():
            return X.mother()
        return X

    def extract_affix(X):
        affix = X.affix()
        X.const = []
        return affix

    def bottom_affix(X):
        if X.affix():
            while X.affix() and not X.affix().copied:
                X = X.affix()
        return X

    def is_licensed_specifier(X):
        return X.max().container().licensed_phrasal_specifier() and \
               X.max() == X.max().container().licensed_phrasal_specifier()

    def __iter__(X):
        X.nn = X
        return X

    def __next__(X):
        if not X.nn:
            raise StopIteration
        current = X.nn
        if X.nn.zero_level():
            X.nn = None
            return current
        elif X.nn.head() == X.nn.right().head() or X.nn.left().proper_selected_complement():
            X.nn = X.nn.right()
        else:
            X.nn = X.nn.left()
        return current.left()

    def minimal_search(X, selection_condition=lambda x: True, sustain_condition=lambda x: True):
        """Collect items that satisfy selection_condition as long as sustain_condition remains true"""
        return takewhile(sustain_condition, (x for x in X if selection_condition(x)))

    def upward_path(X):
        upward_path = []
        x = (X, X.mother())
        while x[1]:
            if x[1].left() and x[1].left() != x[0]:
                upward_path.append(x[1].left())
            x = (x[1], x[1].mother())
        return upward_path

    def next(X, memory_span, condition=lambda x: True):
        return next((x for x in memory_span() if condition(x)), None)

    def edge(X):
        return list(takewhile(lambda x: x.mother() and x.mother().inside(X), X.upward_path()))

    def local_edge(X):
        return next(iter(X.edge()), None)

    def pro_edge(X):
        if X.NS():
            return X.edge() + [X.NS()]
        return X.edge()

    def identify_argument(X):
        available_arguments = [acquire(X) for acquire in [lambda x: x.pro_argument(),
                                                          lambda x: x.argument_complement(),
                                                          lambda x: x.local_edge(),
                                                          lambda x: x.control()]]
        return next((argument for argument in available_arguments if argument), None)

    def argument_complement(X):
        if X.proper_selected_complement() and X.proper_selected_complement().referential():
            return X.proper_selected_complement()

    def contains_features(X, fset):
        if X.complex():
            for x in X.const:
                if x.contains_features(fset):
                    return True
        else:
            return X.check(fset)

    def geometrical_minimal_search(x):
        search_list = [x]
        while x.complex() and x.right():
            search_list.append(x.right())
            x = x.right()
        return search_list

    # Virtual pronouns -----------------------------------------------------------------------
    def pro_argument(X):
        if X.independent_pro_from_overt_agreement() or X.sustains_reference() or X.has_linked_argument():
            return X.NS()

    def NS(X):
        if X.predicate() and X.sustains_reference():
            pro = PhraseStructure()
            pro.features = X.valued_phi_features() | {'φ', 'PF:pro', 'pro'}
            return pro

    def sustains_reference(X):
        return X.phi_consistent_head() and X.has_minimal_phi_set_for_reference()

    def phi_consistent_head(X):
        for fpair in itertools.permutations(X.complete_valued_phi_set(), 2):
            if type_value_mismatch(*fpair):
                return False
        return True

    def has_minimal_phi_set_for_reference(X):
        return {'NUM', 'PER', 'DET'} <= {phi[:3] for phi in X.complete_valued_phi_set()}

    def complete_valued_phi_set(X):
        phi_sets = [phi[4:].split(',') for phi in X.features if phi.startswith('PHI:') and not phi.endswith('_')]
        return {phi for phi_set in phi_sets for phi in phi_set}

    # Selection -------------------------------------------------------------------------------------------
    # Feature -SPEC:L
    def selection__negative_specifier(X, selected_feature_set):
        return not X.next(X.edge, lambda x: x.check(selected_feature_set) and not x.adjunct)

    # Feature !1EDGE
    def selection__negative_one_edge(X, selected_feature):
        return len(X.edge()) < 2

    # Feature !COMP:L
    def selection__positive_obligatory_complement(X, selected_feature_set):
        return X.selected_sister() and X.selected_sister().check(selected_feature_set)

    # Feature +COMP:L,K
    def selection__positive_disjunctive_complement(X, selected_feature_set):
        return X.selected_sister() and X.selected_sister().check_some(selected_feature_set)

    # Feature -COMP:L
    def selection__negative_complement(X, selected_feature_set):
        return not (X.proper_selected_complement() and X.proper_selected_complement().check_some(selected_feature_set))

    # Feature [!]
    def selection__positive_self_selection(X, selected_features):
        return X.check(set(selected_features.split(',')))

    # Feature [-]
    def selection__negative_self_selection(X, selected_features):
        return not X.check(set(selected_features.split(',')))

    # Feature [+]
    def selection__partial_self_selection(X, selected_features):
        return X.check_some(set(selected_features.split(',')))

    def specifier_match(X, phrase):
        return phrase.head().check_some(X.licensed_specifiers())

    def specifier_mismatch(X, phrase):
        return phrase.head().check_some(X.nonlicensed_specifiers())

    def double_spec_filter(X):
        return not X.check({'2SPEC'}) and len({spec for spec in X.edge() if not spec.adjunct}) > 1

    def licensed_phrasal_specifier(X):
        if X.next(X.edge, lambda x: x.referential() and not x.adjunct):
            return X.next(X.edge, lambda x: x.referential() and not x.adjunct)
        return X.next(X.edge, lambda x: x.referential())

    def complement_match(X, const):
        return const.check_some(X.licensed_complements())

    def nonlicensed_complement(X):
        return X.proper_selected_complement() and X.proper_selected_complement().check_some(X.complements_not_licensed())

    def missing_mandatory_complement(X):
        return X.get_mandatory_comps() and (not X.proper_selected_complement() or not X.proper_selected_complement().check(X.get_mandatory_comps()))

    def complement_not_licensed(X):
        return X.proper_selected_complement() and not X.proper_selected_complement().check(X.licensed_complements())

    def properly_selected(X):
        return X.selector() and X.check_some(X.selector().licensed_complements())

    def does_not_accept_any_complements(X):
        return X.check({'-COMP:*'})

    def probe_goal_test(X):
        if X.sister():
            for ff in [(f, X.probe(f[7:])) for f in X.features if 'PROBE:' in f]:
                if (mandatory(ff[0]) and not ff[1]) or (illicit(ff[0]) and ff[1]):
                    return True

    def probe(X, G):
        return next((x for x in X.sister() if x.check({G})), None)

    def edge_feature_tests(X):
        if 'EF' not in X.features and X.edge() and not X.edge()[0].head().check({'Adv'}):
            if not ((X.edge()[0] == X.sister() and
                     X.check_some({'!COMP:φ', 'COMP:φ'})) or
                    X.check_some({'SPEC:φ', '!SPEC:φ'})):
                return True

    def w_selection(X):
        for feature in X.features:
            if feature.startswith('!wCOMP:') and \
                    not X.right().check(set(feature.split(':')[1].split(','))):
                return True
            elif feature.startswith('-wCOMP:') and \
                    X.right().check_some(set(feature.split(':')[1].split(','))):
                return True

    # Test whether a complex head satisfies conditions of the UG
    def Complex_Head_Integrity(X):
        if X.affix():
            x = X
            while x.affix():
                if x.w_selection():
                    return True
                if x.affix().copied:
                    return x.License_EHM()      # [ε] blocks IHM
                else:
                    if not x.License_EHM():     # [ε] licenses EHM
                        return True
                x = x.affix()

    # Projection principle ---------------------------------------------------------------------
    def nonthematic(X):
        if X.max().container():
            return X.max().container().EF() or \
                   (X.max().container().check_some({'-SPEC:*', '-SPEC:φ', '-SPEC:D'}) and
                    X == X.max().container().local_edge())

    def projection_principle_failure(X):
        return (X.max().projection_principle_applies() and
                not X.max().container_assigns_theta_role()) or \
               X.pro_projection_principle_violation()

    def pro_projection_principle_violation(X):
        """Each theta-predicate can be linked with only one pro, 
		since the latter is independent referential argument"""
        if X.zero_level() and \
                X.independent_pro_from_overt_agreement() and \
                X.right_sister():
            for x in X.right_sister().minimal_search(lambda x: x.zero_level(), lambda x: not x.check({'V', 'θ'})):
                if x.independent_pro_from_overt_agreement():
                    return True
                if x.nonthematic_verb():
                    if X.AgreeLF_has_occurred() or not X.nonreferential_pro():
                        return True

    def projection_principle_applies(X):
        return X.referential() and \
               not X.max().copied and \
               X.max().mother() and \
               not X.max().contains_features({'adjoinable', 'SEM:nonreferential'})

    def container_assigns_theta_role(X):
        Y = X.max().container()
        if Y:
            if Y.sister() == X or \
                    (Y.geometrical_sister() == X and
                     X.check_some(Y.licensed_complements())):
                return True
            return not Y.EF() and \
                   Y.check_some({'SPEC:φ', '!SPEC:φ'}) and \
                   X.is_licensed_specifier() and \
                   not (X.selector() and X.selector().check({'-ARG'}))

    # Transfer --------------------------------------------------------------------------------------------------------------------

    # Transfers phrase structure SELF (which may be part of a larger structure)
    # and re-attaches the transferred SELF to its host
    def transfer_to_LF(X):
        ps, m = X.detached()
        for op in PhraseStructure.transfer_sequence:
            PhraseStructure.transfer_operation = op
            X.reconstruct(op)
        return ps.reattach(m)

    def reconstruct(X, op):
        for const in (x for x in [X.bottom()] + X.bottom().upward_path() if op['test integrity'](x)):
            op['repair'](const)
            X.speaker_model.results.record_derivational_step(const.top(), f"{op['type']} ({const})")
            PhraseStructure.speaker_model.results.consume_resources(op['type'], const)

    # Chain creation (part of transfer)
    def create_chain(X):
        head, target = PhraseStructure.transfer_operation['prepare'](X)
        head.form_chain(target)
        if PhraseStructure.transfer_operation['test integrity'](target):
            target.create_chain()   # Recursion, successive-cyclicity

    def prepare_head_chain(X):
        return X, X.right().copy_for_chain()

    def prepare_phrasal_chain(X):
        if X.A_bar_operator():
            X.prepare_A_bar_chain(X.container())
        else:
            PhraseStructure.transfer_operation = PhraseStructure.instructions['A-chain']    # Last Resort option
        return X.container(), X.copy_for_chain()

    def prepare_A_bar_chain(X, probe):
        if not X == probe.next(probe.edge):
            probe = X.project_phonologically_null_head()
        probe.copy_criterial_features(X)
        probe.features = PhraseStructure.speaker_model.lexicon.apply_redundancy_rules(probe.features)

    def project_phonologically_null_head(X):
        probe = X.sister().Merge_inside(PhraseStructure(), 'left').left()
        probe.features |= probe.add_scope_information()
        return probe

    def form_chain(X, target):
        for head in X.minimal_search_domain().minimal_search(PhraseStructure.transfer_operation['selection'],
                                                             PhraseStructure.transfer_operation['sustain']):
            if head != X and head.test_merge(target, PhraseStructure.transfer_operation['legible'], 'left'):
                break
            target.remove()
        else:
            if not X.top().bottom().test_merge(target, PhraseStructure.transfer_operation['legible'], 'right'):
                target.remove()
                if X.sister() and not target.scan_criterial_features('ΔOP'):
                    X.sister().Merge_inside(target, 'left')
                else:
                    X.top().bottom().Merge_inside(target, 'right')  # Last Resort option

    def has_vacant_phrasal_position(X):
        return X.gapless_head() or X.is_right()

    def scan_criterial_features(X, feature):
        criterial_features = X.scan_features(feature)
        if 'OP*' not in criterial_features:
            X.head().features = X.head().features | criterial_features
        for f in list(criterial_features):
            if 'OP' in f:
                return True

    def scan_features(X, feature):
        if X.zero_level():
            return {f for f in X.features if f.startswith(feature) and f[-1] != '_'}
        else:
            for x in [x for x in X.const if not x.copied]:
                return x.scan_features(feature)

    def copy_criterial_features(X, specifier):
        for f in [g for g in specifier.head().features if g.startswith('Δ')]:
            X.features.add(f[1:])
            X.features.add('OP:_')

    def test_merge(X, target, legible, direction):
        X.specifier_sister().Merge_inside(target, direction)
        return legible(X, target)

    def Abar_legible(X, target):
        # Conditions for accepting [SpecXP] as landing site
        if target == X.next(X.edge) and \
                len(X.edge()) == 1 and \
                X.specifier_match(target) and \
                X.specifier_sister().tail_match(X.specifier_sister(), 'left'):
            return True
        # Effect of [CompXP] as landing site
        if target.is_right():
            target.adjunct = False
        # Conditions for accepting [CompXP] as landing site
        if X.sister() == target:
            if X.complement_match(target) and not (target.is_left() and X.specifier_mismatch(target)):
                return True

    def gapless_head(X):
        return X.zero_level() and X.aunt() and X.aunt().zero_level()

    def has_nonthematic_specifier(X):
        return X.EF() and next(iter(X.edge()), X).extended_subject()

    def add_scope_information(X):
        if not X.non_scopal():
            return {'Fin', 'C', 'PF:C'}
        return set()

    @staticmethod
    def baptize_chain():
        PhraseStructure.chain_index += 1
        return str(PhraseStructure.chain_index)

    # Scrambling ==========================================================================

    def trigger_scrambling(X):
        return not X.legible_adjunct() and \
               X.adjoinable() and \
               X.floatable() and \
               not X.operator_in_scope_position() and \
               not X.expletive() and \
               X.container()

    def trigger_right_node_scrambling(X):
        return X.focus_right_node().trigger_scrambling()

    def right_scrambling(X):
        if not X.focus_right_node().in_situ_scrambling_solution():
            X.focus_right_node().reconstruct_scrambling()

    def in_situ_scrambling_solution(X):
        X.head().externalize_structure()
        return X.legible_adjunct() or X.head().adverbial() or not X.top().contains_finiteness()

    def focus_right_node(X):
        if X.is_left():
            return X.geometrical_sister()
        return X

    def legible_adjunct(X):
        return X.head().tail_test() and (X.is_right() or (X.is_left() and not X.nonthematic()))

    def reconstruct_scrambling(X):
        starting_point = X.container()
        virtual_test_item = X.copy()
        scrambled_phrase = X

        node = starting_point
        for node in X.local_tense_edge().minimal_search(lambda x: True, lambda x: x.sustain_condition_for_scrambling(X, X.local_tense_edge())):
            node.merge_scrambled_phrase(virtual_test_item)
            if node.test_adjunction_solution(scrambled_phrase, virtual_test_item, starting_point, 'left'):
                break
        else:
            node.Merge_inside(virtual_test_item, 'right')
            virtual_test_item.adjunct = False
            node.test_adjunction_solution(scrambled_phrase, virtual_test_item, starting_point, 'right')

    def local_tense_edge(X):
        return next((node.mother() for node in X.upward_path() if node.finite() or node.force()), X.top())

    def sustain_condition_for_scrambling(X, target, local_tense_edge):
        return not (X.mother() == target or
                    X.mother().copied or
                    (X.force() and X.container() != local_tense_edge.head()) or
                    (X.zero_level() and X.referential()))

    def test_adjunction_solution(X, scrambled_phrase, virtual_test_item, starting_point, direction):
        if virtual_test_item.valid_reconstructed_adjunct(starting_point):
            virtual_test_item.remove()
            scrambled_phrase.externalize_structure()
            s = X.merge_scrambled_phrase(scrambled_phrase.copy_for_chain(), direction)
            PhraseStructure.speaker_model.narrow_semantics.pragmatic_pathway.unexpected_order_occurred(s, starting_point)
            return True
        virtual_test_item.remove()

    def merge_scrambled_phrase(X, reconstructed_floater, direction='left'):
        target_node = X
        if direction == 'left':
            if X.is_left():
                target_node = X.mother()
            if reconstructed_floater.adverbial_adjunct():
                target_node.Merge_inside(reconstructed_floater, 'right')
            else:
                target_node.Merge_inside(reconstructed_floater, 'left')
        else:
            target_node.Merge_inside(reconstructed_floater, 'right')
            reconstructed_floater.adjunct = False
        return reconstructed_floater

    def externalize_structure(X):
        if X and X.head().is_adjoinable() and X.mother():
            if X.complex():
                X.externalize_and_transfer()
            else:
                X.externalize_head()

    def externalize_head(X):
        if X.isolated_preposition():
            X.externalize_and_transfer()
        elif X.externalize_with_specifier():
            X.mother().mother().externalize_and_transfer()
        else:
            X.mother().externalize_and_transfer()

    def externalize_and_transfer(X):
        if X.mother():
            X.adjunct = True
            X.add_tail_features_if_missing()
            X.transfer_adjunct()

    def transfer_adjunct(X):
        detached_phrase, m = X.detached()
        detached_phrase.transfer_to_LF()
        detached_phrase.mother_ = m
        return detached_phrase

    def add_tail_features_if_missing(X):
        if not X.head().get_tail_sets():
            if X.referential():
                X.head().features.add('TAIL:V')
            else:
                X.head().features.add('TAIL:T')
                X.head().features.add('Adv')

    def valid_reconstructed_adjunct(X, starting_point_node):
        if X.head().tail_test() and (X.adverbial_adjunct() or X.non_adverbial_adjunct_condition(starting_point_node)):
            if not X.container():
                return True
            if X == X.container().local_edge():
                return X.container().specifier_match(X)
            if X == X.container().sister():
                return X.container().complement_match(X)

    def non_adverbial_adjunct_condition(X, starting_point_head):
        if not X.container():
            return True
        if X.nonthematic() or (X.referential() and X.projection_principle_failure()):
            return False
        return True

    def externalize_with_specifier(X):
        return X.is_left() and X.predicate() and \
               ((X.tail_test() and X.has_nonthematic_specifier()) or
                (not X.tail_test() and X.edge() and not X.has_unlicensed_specifier()))

    def has_unlicensed_specifier(X):
        if X.local_edge():
            return set(X.specifiers_not_licensed()) & X.local_edge().head().features

    # Agreement ---------------------------------------------------------------------------------------------

    def AgreeLF(X):
        X.value_from_goal(X.get_goal())

    def get_goal(X):
        return next(X.minimal_search_domain().minimal_search(lambda x: x.goal_selection(),
                                                             lambda x: not x.phase_head()), None)

    def goal_selection(X):
        return not X.copied and (X.head().referential() or X.phase_head())

    def value_from_goal(X, goal):
        if goal:
            log(f'\n\t\tAgree({X}°, {goal.head()}) ')
            if feature_licensing(goal.head().interpretable_phi_features(), X.phi_bundles()) and X.Condition_on_agreement_and_EPP(goal):
                X.value(goal)
            else:
                log(f'failed.')
                X.features.add('*')

    def value(X, goal):
        log(f'valued features ')
        for phi in (x for x in goal.head().features if x.startswith('iPHI') and f'PHI:{x.split(":")[1]}:_' in X.features):
            log(f'[{phi[5:]}] ')
            X.features.discard(f'PHI:{phi.split(":")[1]}:_')
            X.features.add(f'{phi[1:]}')
        X.features.update({'ΦLF'})
        X.features.add(f'PHI:IDX:{goal.head().get_id()}')

    def Condition_on_agreement_and_EPP(X, goal):
        return not X.EF() or \
               not X.PHI() or \
               X.check({'strong_pro'}) or \
               (X.local_edge() and (X.primary_rule(goal) or X.secondary_rule()))

    def primary_rule(X, goal):
        return X.local_edge().head().get_id() == goal.head().get_id()

    def secondary_rule(X):
        return X.check({'weak_pro'}) or X.local_edge().expletive()

    def argument_by_agreement(X):
        for f in [f for f in X.features if f.startswith('PHI:IDX:')]:
            if X.sister():
                idx = f.split(':')[2]
                return next(X.sister().minimal_search(lambda x: idx in x.head().features, lambda x: not x.phase_head()), None)

    # Extraposition
    def cutoff_point_for_last_resort_extraposition(X):
        return X.zero_level() and X.is_adjoinable() and X.aunt() and \
               (X.aunt().complex() or (X.aunt().zero_level() and X.grandmother().induces_selection_violation()))

    def license_extraposition(X):
        return X.top().contains_finiteness() or X.top().referential()

    def extrapose(X):
        X.sister().head().externalize_structure()
        PhraseStructure.speaker_model.results.consume_resources('Extraposition', X)

    def last_resort_extrapose(X):
        if X.zero_level() and X.cutoff_point_for_last_resort_extraposition():
            X.externalize_structure()
            PhraseStructure.speaker_model.results.consume_resources('Last Resort Extraposition', X)

    def feature_inheritance(X):
        if X.highest_finite_head():
            X.features.add('!PER')
        if X.check({'ARG?'}):
            X.features.discard('ARG?')
            if X.selected_by_SEM_internal_predicate():
                X.make_non_predicate()
            elif X.selected_by_SEM_internal_predicate():
                X.make_predicate()
                X.features.add('+ΦLF,ΦPF')
            else:
                X.make_predicate()  #   Neither internal nor external selector will leave the status of subject open

    def get_constituent_containing_selection_violation(X):
        return next((x for x in X if x.induces_selection_violation() and not x.sister().adjunct), None)

    def induces_selection_violation(X):
        return X.nonlicensed_complement() or X.missing_mandatory_complement()

    # Feature processing -----------------------------------------------------------------------------

    def check(X, feature_set):
        return feature_set == {'*'} or feature_set <= X.head().features

    def check_some(X, feature_set):
        return feature_set == {'*'} or feature_set & X.head().features

    def complements_not_licensed(X):
        return {f[6:] for f in X.features if f[:5] == '-COMP'}

    def licensed_specifiers(X):
        return {f[5:] for f in X.features if f[:4] == 'SPEC'} | {f[6:] for f in X.features if f[:5] == '!SPEC'}

    def nonlicensed_specifiers(X):
        return {f[6:] for f in X.features if f[:5] == '-SPEC'}

    def licensed_complements(X):
        return {f[5:] for f in X.features if f[:4] == 'COMP'} | {f[6:] for f in X.features if f[:5] == '!COMP'}

    def is_unvalued(X):
        for f in X.features:
            if unvalued(f):
                return True

    def valued_phi_features(X):
        return {f for f in X.features if 'PHI:' in f and f[-1] != '_'}

    def get_pf(X):
        return {feature[3:] for feature in X.features if feature[:3] == 'PF:'}

    def get_phi_set(X):
        return {f for f in X.features if f[:4] == 'PHI:' and len(f.split(':')) == 3}

    def get_tail_sets(X):
        return {frozenset(f[5:].split(',')) for f in X.head().features if f[:4] == 'TAIL'}

    def needs_valuation(X):
        if not X.sustains_reference() and X.get_unvalued_phi():
            return X.get_unvalued_phi()

    def phi_is_unvalued(X):
        for f in X.head().features:
            if f[-1] == '_':
                return True

    def get_mandatory_comps(X):
        return {f[6:] for f in X.features if f[:5] == '!COMP' and f != '!COMP:*'}

    def specifiers_not_licensed(X):
        return {f[6:] for f in X.features if f[:5] == '-SPEC'}

    def rare_specs(X):
        return {f[6:] for f in X.features if f[:5] == '%SPEC'}

    def semantic_match(X, b):
        a_head = X.head()
        b_head = b.head()
        pos_sem_a = {f[5:] for f in a_head.features if f.startswith('+SEM:')}
        neg_sem_a = {f[5:] for f in a_head.features if f.startswith('-SEM:')}
        pos_sem_b = {f[5:] for f in b_head.features if f.startswith('+SEM:')}
        neg_sem_b = {f[5:] for f in b_head.features if f.startswith('-SEM:')}
        return not ((pos_sem_a & neg_sem_b) or (pos_sem_b & neg_sem_a))

    def feature_conflict(X):
        def remove_exclamation(g):
            if g[0] == '!':
                return g[1:]
            else:
                return g
        for feature1 in X.features:
            if feature1 == '*':
                return True
            if feature1.startswith('-'):
                for feature2 in X.features:
                    if feature1[1:] == remove_exclamation(feature2):
                        log(f'\n\t\tFeature conflict +/{feature1}')
                        return True

    # Operators

    def checking_domain(X, narrow_domain):
        if narrow_domain:
            return X.head()
        return X

    def operator_in_scope_position(X):
        return X.container() and X.container().head().finite() and X.scan_features('ΔOP')

    # Tail-processing ---------------------------------------------------------------------------

    def tail_test(X):
        pos_tsets = {frozenset(positive_features(tset)) for tset in X.get_tail_sets() if positive_features(tset)}
        neg_tsets = {frozenset(negative_features(tset)) for tset in X.get_tail_sets() if negative_features(tset)}
        checked_pos_tsets = {tset for tset in pos_tsets if X.tail_condition(tset)}
        checked_neg_tsets = {tset for tset in neg_tsets if X.tail_condition(tset)}
        return pos_tsets == checked_pos_tsets and not checked_neg_tsets

    def tail_condition(X, tset):
        if X.referential() or X.preposition():
            for m in (x for x in X.upward_path() if x.zero_level() and x.check_some(tset)):
                return m.check(tset)
        if not X.referential():
            return X.check_container(tset) or X.check_aunt(tset)

    def check_container(X, tset):
        return X.max().container() and X.max().container().check(tset)

    def check_aunt(X, tset):
        return X.max().mother() and X.max().mother().sister() and X.max().mother().sister().check(tset)

    def tail_match(X, constituent_from_MB, direction):
        X.Merge_inside(constituent_from_MB.copy(), direction)   # Test merge
        if direction == 'right':                                   # Presupposition
            X.geometrical_sister().adjunct = True
        result = X.geometrical_sister().head().tail_test()      # Test
        X.geometrical_sister().remove()                         # Remove trial unit
        return result

    # Recovery ---------------------------------------------------------------------------------------------------

    def is_possible_antecedent(X, antecedent):
        if antecedent:
            if antecedent.head().referential():
                valued_phi_at_probe = [phi.split(':') for phi in X.features if (phi[:7] == 'PHI:NUM' or phi[:7] == 'PHI:PER') and not phi.endswith('_') and not ',' in phi]
                valued_phi_at_antecedent = [phi.split(':') for phi in antecedent.head().features if (phi[:7] == 'PHI:NUM' or phi[:7] == 'PHI:PER' or phi[:8] == 'iPHI:NUM' or phi[:8] == 'iPHI:PER') and not phi.endswith('_')]
                for P in valued_phi_at_probe:
                    for A in valued_phi_at_antecedent:
                        if P[1] == A[1] and P[2] != A[2]:
                            return False
                return True

    def control(X):
        unvalued_phi = X.get_unvalued_phi()
        if unvalued_phi & {'PHI:NUM:_', 'PHI:PER:_'} and not X.get_valued_phi() & {'PHI:NUM', 'PHI:PER'}:
            return X.standard_control()
        elif unvalued_phi & {'PHI:DET:_'}:
            return X.finite_control()

    def standard_control(X):
        log(' by standard control')
        search_path = [x for x in takewhile(lambda x: not x.head().check({'SEM:external'}), X.upward_path())]
        antecedent = next((x for x in search_path if X.is_possible_antecedent(x)), None)
        if not antecedent:
            antecedent = PhraseStructure()
            antecedent.features = {"PF:generic 'one'", 'LF:generic', 'φ', 'D'}
        return antecedent

    def finite_control(X):
        log(' by finite control')
        antecedent = X.next(X.upward_path, lambda x: x.complex() and X.is_possible_antecedent(x) and not x.copied)
        return antecedent

    # Structure building --------------------------------------------------------------------------

    def Merge_inside(X, C, direction=''):
        local_structure = (X.mother(), X.is_left())         # Snapshot of the local structure
        X = X.asymmetric_merge(C, direction)                 # Create new constituent X
        X.substitute(local_structure)                           # Insert X back into the local structure
        return X

    # Asymmetric Merge is a generalization of the bottom-up Merge (__init__) that can be provided with directionality
    def asymmetric_merge(X, B, direction='right'):
        X.consume_resources('Merge-1', X)
        if direction == 'left':
            return PhraseStructure(B, X)
        return PhraseStructure(X, B)

    def substitute(X, local_structure):
        if local_structure[0]:                                                              # If N had a mother
            if not local_structure[1]:                                                      # If N was right...
                local_structure[0].create_constituents([local_structure[0].left(), X])   # the new constituent will be right,
            else:                                                                           # otherwise the new constituent will be left.
                local_structure[0].create_constituents([X, local_structure[0].right()])
            X.mother_ = local_structure[0]                                                # The new constituent will have the same mother as N had (substitution)

    def merge_around(X, reconstructed_object, legibility=lambda x: True):
        if not (X.Merge_inside(reconstructed_object, 'right') and legibility(reconstructed_object)):
            reconstructed_object.remove()
            if not (X.Merge_inside(reconstructed_object, 'left') and legibility(reconstructed_object)):
                reconstructed_object.remove()
                return True

    def remove(X):
        if X.mother():
            mother_, sister, grandmother = X.context()
            sister.mother_ = sister.mother().mother()
            if mother_.is_right():
                grandmother.const = [grandmother.left(), sister]
            elif mother_.is_left():
                grandmother.const = [sister, grandmother.right()]
            X.mother_ = None

    def context(X):
        return X.mother(), X.geometrical_sister(), X.mother().mother()

    def sink(X, ps):
        bottom_affix = X.bottom().get_affix_list()[-1]   # If self is complex, we first take the right bottom node.
        bottom_affix.active_in_syntactic_working_memory = True
        bottom_affix.const = [ps]
        ps.mother_ = bottom_affix
        return X.top()

    def attach(X, site, terminal_lexical_item, transfer, address_label):
        if site.zero_level() and site.bottom_affix().word_internal():
            const = X.head_attachment(terminal_lexical_item)
        else:
            const = X.phrasal_attachment(terminal_lexical_item, transfer)
        X.speaker_model.results.consume_resources("Merge", const)
        log(f'{address_label}\n')
        return const

    def head_attachment(X, terminal_lexical_item):
        return X.bottom_affix().sink(terminal_lexical_item)

    def phrasal_attachment(X, terminal_lexical_item, transfer):
        new_left_branch = X
        m = X.mother()
        set_logging(False)
        if transfer:
            ps, m = X.detached()
            new_left_branch = X.transfer_to_LF()
            new_left_branch.mother_ = m
        set_logging(True)
        new_left_branch.mother_ = m
        new_constituent = new_left_branch.Merge_inside(terminal_lexical_item)
        return new_constituent

    def copy(X):
        ps_ = PhraseStructure()
        ps_.active_in_syntactic_working_memory = X.active_in_syntactic_working_memory
        ps_.adjunct = X.adjunct
        ps_.internal = X.internal
        ps_.copied = X.copied
        ps_.identity = X.identity
        ps_.node_identity = X.node_identity
        ps_.create_constituents([x.copy() for x in X.const])
        if X.features:
            ps_.features = X.features.copy()
        return ps_

    def secure_copy(X):
        if X:
            return X.copy()
        return None

    def detached(X):
        m = X.mother()
        X.mother_ = None
        return X, m

    def reattach(X, m):
        X.top().mother_ = m
        return X.top()

    def __add__(X, incoming_constituent):
        return X.Merge_inside(incoming_constituent)

    def get_index(X, target):
        for i, node in enumerate(X.geometrical_minimal_search()):
            if target == node:
                return i

    def get_node(X, idx):
        for i, node in enumerate(X.geometrical_minimal_search()):
            if i == idx:
                return node

    def index(X):
        for x in X.features:
            if x.startswith('§'):
                return x

    def target_left_branch(X, target):
        new_ps = X.top().copy()
        return new_ps.get_node(X.top().get_index(target))

    # Support ----------------------------------------------------------------------

    def find_constituent_with_index(X, idx):
        if X.index() == idx:
            return X
        if X.complex():
            for x in X.const:
                const = x.find_constituent_with_index(idx)
                if const:
                    return const

    def find_constituent_with_identity(X, ps, identity):
        if X.identity == identity and X != ps:
            return X
        if X.complex():
            for x in X.const:
                const = x.find_constituent_with_identity(ps, identity)
                if const:
                    return const

    def gloss(X):
        def LF_features(head):
            lfs = [f[3:] for f in head.features if f[:2] == 'LF']
            return '.'.join(sorted(lfs))

        pf = ''
        if X.complex():
            if 'null' in X.left().features:
                pf = pf + '_'
            else:
                pf = pf + X.left().gloss() + ' '
            if 'null' in X.right().features:
                pf = pf + '_'
            else:
                pf = pf + X.right().gloss() + ' '
        if X.zero_level():
            pf = pf + LF_features(X)
        return pf

    def PF(X):
        for f in X.features:
            if f.startswith('PF:'):
                return f.split(':')[1]
        return '?'

    def label(X):
        head = X.head()
        if X.complex():
            suffix = 'P'
        else:
            suffix = ''
        for cat in major_cats:
            if cat in head.features:
                return cat + suffix
        return 'X' + suffix

    def copy_for_chain(X, babtize='1'):
        def silence_phonologically(h):
            if not h.features:
                h.features = {'null'}
            else:
                h.features.add('null')      # Null is about what is printed out
                h.features.discard('Δp')    # This is the grammatical feature that operates in narrow syntax
            if h.left():
                silence_phonologically(h.left())
            if h.right():
                silence_phonologically(h.right())

        X.identity = X.baptize_chain()
        X_copy = X.copy()
        X_copy.node_identity = X.create_node_identity()
        X_copy.copied = False
        silence_phonologically(X_copy)
        X.copied = True
        X.features.add('CHAIN:' + str(X_copy.node_identity))
        return X_copy

    def for_LF_interface(X, features):
        set_of_features = set()
        for f in features:
            if f[0] == '!' or f[0] == '-':
                set_of_features.add(f)
        return set_of_features

    def illustrate(X):
        if X.zero_level():
            if not X.get_phonological_string():
                return '?'
            else:
                if X.adjunct:
                    return '<' + X.get_phonological_string() + '>'
                else:
                    return X.get_phonological_string()
        else:
            prefix = ''
            if X.adjunct:
                return f'<' + prefix \
                       + X.left().illustrate() + ' ' \
                       + X.right().illustrate() + '>'
            else:
                return f'[' + prefix \
                       + X.left().illustrate() + ' ' \
                       + X.right().illustrate() + ']'

    def phonological_content(X):
        exceptions = {'φ', 'D'}
        phon = ''
        if X.zero_level():
            if not set(X.get_phonological_string()) & exceptions:
                phon = X.get_phonological_string()
        else:
            str = X.left().phonological_content()
            if str:
                phon += ' ' + str
            if not X.right().adjunct:
                str = X.right().phonological_content()
                if str:
                    phon += ' ' + str
        return phon

    def __str__(X):
        if X.identity != '':
            chain_index_str = ':' + X.identity
        else:
            chain_index_str = ''

        # Phonologically null complex constituents
        if X.features and 'null' in X.features and X.complex():
            if X.adjunct:
                return '<__>' + chain_index_str
            else:
                return '__' + chain_index_str

        # Primitive heads
        if X.zero_level():
            if not X.get_phonological_string():
                return '?'
            else:
                if X.adjunct:
                    return '<' + X.get_phonological_string() + '>'
                else:
                    return X.get_phonological_string()
        else:
            if X.adjunct:
                return f'<{X.left()} {X.right()}>' + chain_index_str
            else:
                return f'[{X.left()} {X.right()}]' + chain_index_str

    def get_phonological_string(X):
        def show_affixes(self):
            i = ''
            if self.affix():
                if PhraseStructure.spellout_heads:
                    i = self.affix().PF()
                else:
                    i = self.affix().label()
                if self.affix().affix():
                    i = '(' + show_affixes(self.affix()) + ' ' + i + ')'
            else:
                i = ''
            return i

        pfs = [f[3:] for f in X.features if f[:2] == 'PF']
        if X.affix():
            if not X.affix().copied:
                affix_str = show_affixes(X)
                return '(' + affix_str + ' ' + ''.join(sorted(pfs)) + ')°'
        return ''.join(sorted(pfs))

    def tidy_names(X, counter):
        def rebaptize(h, old_name, new_name):
            if h.identity == old_name:
                if not h.rebaptized:
                    h.identity = new_name
                    h.rebaptized = True
            if h.left:
                rebaptize(h.left(), old_name, new_name)
            if h.right:
                rebaptize(h.right(), old_name, new_name)
            return

        if X.identity != '' and not X.rebaptized:
            rebaptize(X.top(), X.identity, str(counter))
            counter = counter + 1
        if X.left():
            counter = X.left().tidy_names(counter)
        if X.right():
            counter = X.right().tidy_names(counter)
        return counter

    def consume_resources(X, resource_key, target):
        PhraseStructure.resources[resource_key]['n'] += 1

    def get_id(X):
        for f in X.features:
            if f.startswith('§'):
                return f
        return '?'

    #  Definitions and abstractions for terms

    def make_predicate(X):
        X.features.add('ARG')
        X.features.add('PHI:NUM:_')
        X.features.add('PHI:PER:_')
        X.features.add('PHI:DET:_')

    def make_non_predicate(X):
        X.features.add('-ARG')
        X.features.add('-ΦLF,ΦPF')

    def empty_finite_EPP(X):
        return X.selector().finite_C() and X.EF() and not X.edge()

    def adverbial(X):
        return X.check({'Adv'})

    def nominal(X):
        return X.check({'N'})

    def nonverbal(X):
        return X.nominal() or X.referential() or X.adjectival()

    def adjectival(X):
        return X.check({'A'})

    def verbal(X):
        return X.check({'V'})

    def theta_predicate(X):
        return X.check({'θ'}) and not X.check({'-ARG'}) and not X.check({'-θ'})

    def nonthematic_verb(X):
        return X.verbal() and not X.theta_predicate()

    def light_verb(X):
        return X.check_some({'v', 'v*', 'impass', 'cau'})

    def force(X):
        return X.check({'FORCE'})

    def finite(X):
        return X.check_some({'Fin', 'T/fin', 'C/fin'})

    def copula(X):
        return X.check({'COPULA'})

    def finite_C(X):
        return X.check({'C/fin'})

    def relative(X):
        return X.check({'REF'})

    def nonfinite(X):
        return X.check({'Inf'})

    def concept_operator(X):
        return X.concept() and {feature for feature in X.features if feature[:2] == 'OP'}

    def finite_left_periphery(X):
        return X.finite() and X.check_some({'T', 'C'})

    def finite_tense(X):
        return X.check({'T/fin'}) or (X.finite() and X.check({'T'}))

    def contains_finiteness(X):
        return X.contains_features({'Fin'})

    def referential(X):
        return X.check_some({'φ', 'D'})

    def nonreferential_pro(X):
        return X.check({'nonreferential_pro'})

    def interpretable_phi_features(X):
        return {f[5:] for f in X.features if f.startswith('iPHI:')}

    def phi_features(X):
        return {f[4:] for f in X.features if f.startswith('PHI:') and not f.endswith('_')}

    def preposition(X):
        return X.check({'P'})

    def floatable(X):
        return not X.check({'nonfloat'})

    def non_scopal(X):
        return X.check_some({'Inf', 'P', 'D', 'φ'})

    def expresses_concept(X):
        return X.check_some({'N', 'Neg', 'P', 'D', 'φ', 'A', 'V', 'Adv', 'Q', 'Num', '0'}) and not X.check({'T/prt', 'COPULA'})

    def unrecognized_label(X):
        return X.check_some({'CAT:?', '?'})

    def predicate(X):
        return X.zero_level() and X.check({'ARG'}) and not X.check({'-ARG'})

    def adverbial_adjunct(X):
        return X.adverbial() or X.preposition()

    def is_adjoinable(X):
        return X.adjunct or (X.head().check({'adjoinable'}) and not X.head().check({'nonadjoinable'}))

    def concept(X):
        next((x for x in X.get_affix_list() if x.expresses_concept()), False)

    def semantic_complement(X):
        return X.proper_selected_complement() and not X.semantic_match(X.proper_selected_complement())

    def selected_by_SEM_internal_predicate(X):
        return X.selector() and X.selector().SEM_internal_predicate()

    def selected_by_SEM_external_predicate(X):
        return X.selector() and X.selector().SEM_external_predicate()

    def SEM_internal_predicate(X):
        return X.check({'SEM:internal'})

    def SEM_external_predicate(X):
        return X.check({'SEM:external'})

    def isolated_preposition(X):
        return X.preposition() and X.sister() and X.sister().zero_level()

    def adjoinable(X):
        return X.complex() and not X.copied and X.head().get_tail_sets() and X.head().check({'adjoinable'}) and not X.head().check({'nonadjoinable'})

    def legitimate_criterial_feature(X):
        return X.referential() and not X.relative() and X.mother_ and X.mother_.contains_features({'REL'}) and not X.mother_.contains_features({'T/fin'})

    def interpretable_adjunct(X):
        return X.referential() and X.max() and X.max().adjunct and X.max().is_right() and X.max().mother_ and X.max().mother_.referential()

    def word_internal(X):
        return X.bottom().bottom_affix().internal

    def impossible_sequence(X, w):
        return X.zero_level() and 'T/fin' in X.head().features and 'T/fin' in w.features

    def is_word_internal(X):
        return X.mother_ and X.sister() and X.sister().zero_level() and X.sister().word_internal()

    def phase_head(X):
        return X.zero_level() and X.check_some(PhraseStructure.phase_heads) and not X.check_some(PhraseStructure.phase_heads_exclude)

    def extended_subject(X):
        return X.check_some({'GEN'})

    def highest_finite_head(X):
        return X.check({'Fin'}) and not X.check_some({'C', 'FORCE'}) and not (X.selector() and X.selector().check_some({'T', 'COPULA', 'Fin'}))

    def theta_head(X):
        return X.theta_predicate() and not X.check({'!Φ'})

    def expletive(X):
        return X.head().check({'EXPL'})

    def open_class(X):
        return X.head().check_some({'N', 'V', 'P', 'A'})

    def licensed_expletive(X, phrase):
        return phrase.expletive() and X.head().check_some({'SPEC:EXPL', '!SPEC:EXPL'})

    def theta_marks(X, target):
        if X.sister() == target:
            return X.theta_predicate()
        return X.check_some({'SPEC:φ', '!SPEC:φ'})

    def independent_pro_from_overt_agreement(X):
        return X.check_some({'weak_pro', 'strong_pro'})

    def has_linked_argument(X):
        return {f for f in X.head().features if f.startswith('PHI:IDX:')}

    def get_valued_phi(X):
        return {f[:7] for f in X.features if f[:4] == 'PHI:' and f[-1] != '_'}

    def get_unvalued_phi(X):
        return {phi for phi in X.features if phi[-1] == '_' and (phi[:7] == 'PHI:NUM' or phi[:7] == 'PHI:PER' or phi[:7] == 'PHI:DET')}

    def phi_bundles(X):
        return [set(phi[4:].split(',')) for phi in X.features if valued_phi_feature(phi) and not phi.startswith('i') and not 'IDX' in phi]

    def type_match(X, phi, phi_):
        return phi.split(':')[1] == phi_.split(':')[1]

    def EF(X):
        return {x for x in X.features if x == 'EF'}

    def PHI(X):
        return X.check_some({'+ΦLF,ΦPF', '!ΦLF,ΦPF', '?ΦLF,ΦPF'})

    def AgreeLF_has_occurred(X):
        return X.check({'ΦLF'})

    def A_bar_operator(X):
        return X.scan_criterial_features('ΔOP')

    def License_EHM(X):
        return 'ε' in X.features

    def create_node_identity(X):
        PhraseStructure.node_identity += 1
        return PhraseStructure.node_identity

    def find_node_with_identity(X, identity):
        if X.node_identity == identity:
            return X
        if X.complex():
            for x in X.const:
                node = x.find_node_with_identity(identity)
                if node:
                    return node
