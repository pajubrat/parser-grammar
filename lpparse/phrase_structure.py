
from itertools import takewhile
from feature_processing import *
from phi import *
from support import log, set_logging


class PhraseStructure:
    speaker_model = None
    major_cats = ['@', '√', 'n', 'N', 'Neg', 'Neg/fin', 'P', 'D', 'Qn', 'Num', 'φ', 'Top', 'C', 'C/fin', 'a', 'A', 'v', 'V', 'Pass',
                  'VA/inf', 'T', 'Fin', 'Agr',
                  'A/inf', 'MA/inf', 'ESSA/inf', 'E/inf', 'TUA/inf', 'KSE/inf', 'Inf',
                  'FORCE', 'EXPL', 'Adv', 'Pr',
                  '0', 'a', 'b', 'c', 'd', 'x', 'y', 'z', 'X', 'Y', 'Z']
    access_experimental_functions = None
    spellout_heads = False      # This parameter, if set true, spells out PF-content of heads in all printouts; otherwise only labels are shown
    phase_heads = {'ph', 'φ'}   # Phase heads set for all calculations
    phase_heads_exclude = set()
    resources = {"Merge-1": {"ms": 0, "n": 0}}
    chain_index = 0
    node_identity = 0
    transfer_operation = None

    def __init__(self, left=None, right=None):
        self.const = []
        if left and right:
            self.create_constituents([left, right])
        self.mother_ = None
        self.features = set()
        self.active_in_syntactic_working_memory = True
        self.adjunct = False
        self.copied = False
        self.phrasal_zero = False
        self.identity = 0
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
        return len(X.const) < 2 or X.phrasal_zero

    def is_left(X):
        return X.mother() and X.mother().left() == X

    def is_right(X):
        return X.mother() and X.mother().right() == X

    def complex_head(X):
        return len(X.get_affix_list()) > 1

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
        return next((x for x in [X] + X.const if x.zero_level()), X.complex() and X.right_nonadjunct().head())

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

    def complement(X):
        if X.zero_level() and X.is_left():
            return X.sister()

    def selector(X):
        if X.max().sister() and X.max().sister().zero_level() and X.max().sister().is_left():
            return X.max().sister()

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
        elif X.nn.head() == X.nn.right().head() or X.nn.left().complement():
            X.nn = X.nn.right()
        else:
            X.nn = X.nn.left()
        return current.left()

    def minimal_search(X, intervention=lambda x: False):
        return takewhile(lambda x: not intervention(x), (x for x in X))

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
                                                          lambda x: x.complement_argument(),
                                                          lambda x: x.indexed_argument(),
                                                          lambda x: x.local_edge(),
                                                          lambda x: x.control()]]
        return next((argument for argument in available_arguments if argument), None)

    def complement_argument(X):
        if X.complement() and X.complement().referential():
            return X.complement()

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

    def predicate_composition(X):
        if X.complement():
            lst = [x for x in X.complement().minimal_search(lambda x: x.reference_head()) if x.zero_level()]
            lst = [X] + lst[:-1] + lst[-1].get_affix_list()
            return lst

    def reference_head(X):
        return {'π', 'D', 'φ'} & X.features

    # Virtual pronouns -----------------------------------------------------------------------
    def pro_argument(X):
        if X.independent_pro_from_overt_agreement() or X.complete_agreement_suffixes():
            return X.NS()

    def NS(X):
        if X.predicate() and X.complete_agreement_suffixes():
            pro = PhraseStructure()
            pro.features = X.valued_phi_features() | {'φ', 'PF:pro', 'pro'}
            return pro

    def complete_agreement_suffixes(X):
        return X.phi_consistent_head() and X.has_minimal_phi_set_for_reference() and 'ΦPF' in X.features

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

    # Auxiliary functions
    def get_selection_features(X, key):
        feats = [set(f.split(':')[1].split(',')) for f in X.features if f.startswith(key)]
        return set().union(*feats)

    def selection_violation(X):
        return not X.COMP_selection() or not X.SPEC_selection()

    def properly_selected(X):
        return X.selector() and X.selector().COMP_selection()

    def SPEC_selection(X):
        return X.minus_SPEC(X.get_selection_features('-SPEC')) and \
               X.plus_SPEC(X.get_selection_features('+SPEC'))

    def COMP_selection(X):
        return X.minus_COMP(X.get_selection_features('-COMP')) and \
               X.plus_COMP(X.get_selection_features('+COMP'))

    # -SPEC:L,K
    def minus_SPEC(X, fset):
        return len(fset) == 0 or \
               not X.local_edge() or \
               X.local_edge().adjunct or \
               not X.local_edge().head().check_some(fset)

    # +SPEC:L,K
    def plus_SPEC(X, fset):
        return len(fset) == 0 or \
               (not X.local_edge() and 'ø' in fset) or \
               (X.local_edge() and X.local_edge().head().check_some(fset))

    # +COMP:L,K
    def plus_COMP(X, fset):
        return not PhraseStructure.speaker_model.settings.retrieve('head_complement_selection', True) or \
               fset == 0 or\
               (not X.complement() and 'ø' in fset) or \
               (X.complement() and X.complement().head().check_some(fset))

    # -COMP:L,K
    def minus_COMP(X, fset):
        return not PhraseStructure.speaker_model.settings.retrieve('head_complement_selection', True) or \
               len(fset) == 0 or \
               not X.complement() or \
               not X.complement().head().check_some(fset)

    # -SELF
    def minus_SELF(X, fset):
        return not X.check_some(fset)

    # +SELF
    def plus_SELF(X, fset):
        return X.check_some(fset)

    # =SELF
    def conjunctive_minus_SELF(X, fset):
        return not X.check(fset)

    def double_spec_filter(X):
        if not X.check({'2SPEC'}) and len(X.edge()) > 1:
            for x in X.edge()[1:]:
                if not x.adjunct:
                    return True

    def get_constituent_containing_selection_violation(X):
        return next((x for x in X if x.selection_violation() and not x.sister().adjunct), None)

    def does_not_accept_any_complements(X):
        return X.check({'-COMP:*'})

    def w_selection(X):
        for feature in X.features:
            if feature.startswith('!wCOMP:') and \
                    not X.right().check(set(feature.split(':')[1].split(','))):
                return True
            elif feature.startswith('-wCOMP:') and \
                    X.right().check_some(set(feature.split(':')[1].split(','))):
                return True

    def complex_head_integrity(X):
        """Tests whether a complex head satisfies conditions of the UG"""
        if X.affix():
            x = X
            while x.affix():
                if x.w_selection() and PhraseStructure.speaker_model.settings.retrieve('w_selection', True):
                    return True
                if PhraseStructure.speaker_model.settings.retrieve('epsilon', True):
                    if x.affix().copied:
                        return x.EHM()      # [ε] blocks IHM
                    else:
                        if not x.EHM():     # [ε] licenses EHM
                            return True
                x = x.affix()

    def probe_goal_test(X):
        if X.sister():
            for ff in [(f, X.probe(f[7:])) for f in X.features if 'PROBE:' in f]:
                if (mandatory(ff[0]) and not ff[1]) or (illicit(ff[0]) and ff[1]):
                    return True

    def probe(X, G):
        return next((x for x in X.sister() if x.check({G})), None)

    # Projection principle ---------------------------------------------------------------------
    def thematic_head(X):
        return 'θ' in X.head().features

    def in_thematic_position(X):
        return (X.max().container() and X.max().container().thematic_head()) or \
               (X.max().container() and X.max().container().complement() == X.max())

    def projection_principle_failure(X):
        return (X.max().projection_principle_applies() and
                not X.max().container_assigns_theta_role(X.max().container())) or \
               X.pro_projection_principle_violation()

    def projection_principle_applies(X):
        return X.referential() and \
               not X.max().copied and \
               X.max().mother() and \
               not X.max().contains_features({'adjoinable', 'SEM:nonreferential'})

    def pro_projection_principle_violation(X):
        if X.zero_level() and X.independent_pro_from_overt_agreement() and X.right_sister():
            for x in X.right_sister().minimal_search(lambda y: y.thematic_head() and y.verbal()):
                if x.zero_level():
                    if x.independent_pro_from_overt_agreement():
                        return True
                    if x.nonthematic_verb():
                        if X.AgreeLF_has_occurred() or not X.nonreferential_pro():
                            return True

    def container_assigns_theta_role(X, Y):
        return Y and Y.thematic_head() and \
               ((X == Y.geometrical_sister() and not X.check_some(Y.get_selection_features('-COMP')) or
                 X == Y.local_edge()))

    # Transfer --------------------------------------------------------------------------------------------------------------------

    def transfer(X):
        Y, m = X.detached()
        for Z in (x for x in [Y.bottom()] + Y.bottom().upward_path()):
            Z.reconstruct(cyclic=False)
        return Y.reattach(m)

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
        return not X.head().tail_test() and X.adjoinable() and X.floatable() and \
               not X.operator_in_scope_position() and X.container()

    def reconstruct_scrambling(X):
        X.externalize_structure()
        for x in X.local_tense_edge().minimal_search():
            if x.tail_test(tail_sets=X.get_tail_sets()):
                return x.mother().Merge_left(X.copy_for_chain())
        return X.container().Merge_right(X.copy_for_chain())

    def local_tense_edge(X):
        return next((node.mother() for node in X.upward_path() if node.finite() or node.force()), X.top())

    def externalize_structure(X):
        if X and X.head().is_adjoinable() and X.mother():
            if X.complex():
                X.externalize_and_transfer()
            else:
                X.externalize_head()

    def externalize_head(X):
        if X.isolated_preposition():
            X.externalize_and_transfer()
        elif X.externalize_with_specifier() and X.mother() and X.mother().mother() and X.local_edge():
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
        detached_phrase.transfer()
        detached_phrase.mother_ = m
        return detached_phrase

    def add_tail_features_if_missing(X):
        if not X.head().get_tail_sets():
            if X.referential():
                X.head().features.add('TAIL:V')
            else:
                X.head().features.add('TAIL:T')
                X.head().features.add('Adv')

    def valid_reconstructed_adjunct(X):
        if X.head().tail_test() and (X.adverbial_adjunct() or X.non_adverbial_adjunct_condition()):
            if not X.container():
                return True
            if X == X.container().local_edge():
                return X.container().SPEC_selection()
            if X == X.container().sister():
                return X.container().COMP_selection()

    def non_adverbial_adjunct_condition(X):
        return not X.max().container() or X.in_thematic_position()

    def externalize_with_specifier(X):
        return X.is_left() and X.predicate() and \
               ((X.tail_test() and X.local_edge()) or
                (not X.tail_test() and X.SPEC_selection()))

    # Agreement ---------------------------------------------------------------------------------------------
    def AgreeLF(X):
        return X.Agree(X.get_goal())

    def get_goal(X):
        return next((x for x in X.minimal_search_domain().minimal_search(lambda x: x.phase_head())
                     if x.goal_selection()), None)

    def goal_selection(X):
        return not X.copied and (X.head().referential() or X.phase_head())

    def Agree(X, goal):
        if X.is_unvalued() and goal:
            if not goal.feature_mismatch_test(X.phi_bundles()):
                X.value(goal)
                return goal
            else:
                X.features.add('*')

    def feature_mismatch_test(X, PP):
        """
        X = goal
        PP = phi-bundles at the probe
        This function examines if there are unlicensed phi-features at the goal (G) that mismatch with
        phi-features at the probe. Unlicensed phi-features at the goal are those features which are not
        matched with phi-bundles at the probe.
        Note 1: The feature format is TYPE:VALUE with (i)PHI removed.
        """
        return mismatch(unlicensed_phi_features_at_goal(X.head().interpretable_phi_features(), PP), set().union(*PP))

    def interpretable_phi_features(X):
        return {f[5:] for f in X.features if f.startswith('iPHI:')}

    def value(X, goal):
        P = set().union(*X.phi_bundles())
        for phi in [goal_feature for goal_feature in goal.head().features if interpretable_phi_feature(goal_feature) and unvalued_counterparty(goal_feature, X) and (not P or X.feature_gate(goal_feature, P))]:
            X.features.discard(f'PHI:{phi.split(":")[1]}:_')
            X.features.add(f'{phi[1:]}')
        X.features.update({'ΦLF'})
        X.features.add(f'PHI:IDX:{goal.head().get_id()}')

    def feature_gate(X, goal_feature, P):
        """
        Feature A can be valued for B at probe head X iff
        (1) B is an unvalued feature of the same type as A
        (2) probe X contains overtly valued phi-bundle with the same type as A (gate condition)
        """
        for p in P:
            if goal_feature.split(":")[1] == p.split(':')[0]:          # Condition (2)
                return True

    def phi_bundles(X):
        return [set(phi[4:].split(',')) for phi in X.features if valued_phi_feature(phi) and not phi.startswith('i') and 'IDX' not in phi]

    def phi_level_violation(X):
        """
        Current implementation of the Agree/EPP system, tested as LF-legibility
        """
        if not X.check_some({'ASP', 'strong_pro'}):                         #   Condition 1. Amnesty for strong pro and theta heads
            if not X.check({'Φ*'}):                                         #   Condition 2. Φ-heads do not have EF
                return X.local_edge()
            if X.check({'-ΦPF'}):                                           #   Condition 3. Heads which cannot agree overtly are not subject to further conditions
                return False
            if X.check({'weak_pro'}):                                       #   Secondary rule
                return X.check({'ΦLF'}) and not X.local_edge()
            return (X.check({'ΦLF'}) and not X.primary_rule()) or \
                   (not X.check({'ΦLF'}) and not X.check_some({'?ΦLF', '-ΦLF'}) and
                    not (X.check({'ΦPF'}) and X.phi_consistent_head()))     #   Primary rule

    def primary_rule(X):
        return X.local_edge() and X.indexed_argument() and X.local_edge().head().get_id() == X.indexed_argument().head().get_id()

    def indexed_argument(X):
        idx = X.phi_index()
        if idx and X.sister():
            return next((x.max() for x in X.sister().minimal_search() if idx in x.head().features), None)

    def phi_index(X):
        return next((f.split(':')[2] for f in X.features if f.startswith('PHI:IDX:')), None)

    def license_extraposition(X):
        return X.top().contains_finiteness() or X.top().referential()

    def extrapose(X):
        if X.sister() and not X.COMP_selection():
            X.sister().head().externalize_structure()
        if not X.SPEC_selection():
            X.head().externalize_structure()
        return X

    def feature_inheritance(X):
        if X.highest_finite_head():
            X.features.add('!PER')
        if X.check({'Φ?'}):
            X.features.discard('Φ?')
            X.features.add('Φ*')
            X.features.add('Φ')
            if X.selected_by_SEM_internal_predicate():
                X.features.add('-ΦLF')
        return X

    # Feature processing -----------------------------------------------------------------------------

    def check(X, fset):
        return fset <= X.head().features

    def check_some(X, fset):
        return fset & X.head().features

    def is_unvalued(X):
        for f in X.features:
            if unvalued_phi_feature(f):
                return True

    def valued_phi_features(X):
        return {f for f in X.features if 'PHI:' in f and f[-1] != '_'}

    def get_pf(X):
        return {f[3:] for f in X.features if f[:3] == 'PF:'}

    def get_phi_set(X):
        return {f for f in X.features if f[:4] == 'PHI:' and len(f.split(':')) == 3}

    def get_tail_sets(X):
        return {frozenset(f[5:].split(',')) for f in X.head().features if f[:4] == 'TAIL'}

    def needs_valuation(X):
        if not X.complete_agreement_suffixes() and X.get_unvalued_minimal_phi():
            return X.get_unvalued_minimal_phi()

    def phi_is_unvalued(X):
        for f in X.head().features:
            if f[-1] == '_':
                return True

    def specifiers_not_licensed(X):
        return set().union(*{frozenset(f[6:].split(',')) for f in X.features if f.startswith('-SPEC:')})

    def specifiers_licensed(X):
        return set().union(*{frozenset(f[6:].split(',')) for f in X.features if f.startswith('+SPEC:')})

    def complements_not_licensed(X):
        return set().union(*{frozenset(f[6:].split(',')) for f in X.features if f.startswith('-COMP:')})

    def complements_licensed(X):
        return set().union(*{frozenset(f[6:].split(',')) for f in X.features if f.startswith('+COMP:')})

    def spec_selection(X, Y):
        return X.complex() and X.check(Y.specifiers_licensed())

    def comp_selection(X, Y):
        return X.zero_level() and Y.check_some(X.complements_licensed())

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

    def tail_test(X, **kwargs):
        tail_sets = kwargs.get('tail_sets', X.get_tail_sets())
        weak_test = kwargs.get('weak_test', X.referential() or X.preposition())
        direction = kwargs.get('direction', 'left')
        positive_tsets = {frozenset(positive_features(tset)) for tset in tail_sets if positive_features(tset)}
        negative_tsets = {frozenset(negative_features(tset)) for tset in tail_sets if negative_features(tset)}
        checked_pos_tsets = {tset for tset in positive_tsets if X.tail_condition(tset, weak_test, direction)}
        checked_neg_tsets = {tset for tset in negative_tsets if X.tail_condition(tset, weak_test, direction)}
        return positive_tsets == checked_pos_tsets and not checked_neg_tsets

    def tail_condition(X, tail_set, weak_test, direction):
        if weak_test:
            context = [x for x in X.upward_path() if x.zero_level()]
            if direction == 'right':
                context.insert(X)
            for m in context:
                if m.check_some(tail_set):
                    return m.check(tail_set)
        else:
            return X.check_container(tail_set) or X.check_aunt(tail_set)

    def check_container(X, tset):
        return X.max().container() and X.max().container().check(tset)

    def check_aunt(X, tset):
        return X.max().mother() and \
               X.max().mother().sister() and \
               X.max().mother().sister().check(tset)

    def tail_match(X, constituent_from_MB, direction):
        X.Merge_inside(constituent_from_MB.copy(), direction)   # Test merge
        if direction == 'right':                                # Presupposition
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
        unvalued_phi = X.get_unvalued_minimal_phi()
        if unvalued_phi & {'PHI:NUM:_', 'PHI:PER:_'} and not X.get_valued_phi_types() & {'PHI:NUM', 'PHI:PER'} and not X.check({'PHI:NUM:SG,PER:3'}):
            return X.standard_control()
        elif unvalued_phi & {'PHI:DET:_'}:
            return X.finite_control()

    def standard_control(X):
        search_path = [x for x in takewhile(lambda x: not x.head().check({'SEM:external'}), X.upward_path())]
        antecedent = next((x for x in search_path if X.is_possible_antecedent(x)), None)
        if not antecedent:
            antecedent = PhraseStructure()
            antecedent.features = {"PF:generic 'one'", 'LF:generic', 'φ', 'D'}
        return antecedent

    def finite_control(X):
        antecedent = X.next(X.upward_path, lambda x: x.complex() and X.is_possible_antecedent(x) and not x.copied)
        return antecedent

    # Structure building --------------------------------------------------------------------------

    def Merge_inside(X, C, direction=''):
        local_structure = (X.mother(), X.is_left())         # Snapshot of the local structure
        X = X.asymmetric_merge(C, direction)                # Create new constituent X
        X.substitute(local_structure)                       # Insert X back into the local structure
        return X

    # Asymmetric Merge is a generalization of the bottom-up Merge (__init__) that can be provided with directionality
    def asymmetric_merge(X, B, direction='right'):
        X.consume_resources('Merge-1', X)
        if direction == 'left':
            return PhraseStructure(B, X)
        return PhraseStructure(X, B)

    def Merge_right(X, Y):
        return X.Merge_inside(Y, 'right')

    def Merge_left(X, Y):
        return X.Merge_inside(Y, 'left')

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

    def sink(X, Y):
        bottom_affix = X.bottom().get_affix_list()[-1]
        bottom_affix.const = [Y]
        Y.mother_ = bottom_affix
        return X.top()

    def attach(X, N, W):
        if N.bottom_affix().word_internal() and (PhraseStructure.speaker_model.settings.retrieve('UG_parameter_middle_field_HM', True) or N.check({'C'}) or N.bottom_affix().EHM()):
            Y = X.head_attachment(W)
        else:
            Y = X.regular_attachment(W)
        X.speaker_model.results.consume_resources('Merge', Y, N, W)
        return Y

    def head_attachment(X, terminal_lexical_item):
        return X.bottom_affix().sink(terminal_lexical_item)

    def regular_attachment(X, terminal_lexical_item):
        return X.transfer_detached().Merge_inside(terminal_lexical_item)

    def transfer_detached(X):
        set_logging(False)
        ps, m = X.detached()
        new_left_branch = X.transfer()
        new_left_branch.mother_ = m
        set_logging(True)
        return new_left_branch

    def detached(X):
        m = X.mother()
        X.mother_ = None
        return X, m

    def Affect_a(X, Y, **kwargs):
        logg = kwargs.get('log', False)
        if Y and not Y.copied:
            if logg:
                log(f"\n\t\t{kwargs['type']}({Y})")
            if kwargs['type'] == 'A-chain':
                if Y.complex() and not Y.get_tail_sets() and not Y.operator_features() and not Y.sister().operator_features():
                    return Y
                else:
                    return None
            if kwargs['type'] == 'Ā-chain' and Y.container():
                Y.container().features = Y.container().features | Y.operator_features()
            return Y

    def reconstruct(X, **kwargs):

        trigger = {'A-chain': lambda x: x.zero_level() and x.EF() and not (x.internal and x.terminal()),
                   'Scrambling': lambda x: x.max().trigger_scrambling(),
                   'Agree': lambda x: x.zero_level() and x.is_left() and x.is_unvalued() and not x.check({'ΦLF'}),
                   'IHM': lambda x: x.complex_head() and not x.EHM() and not x.check({'C'}),
                   'Extrapose': lambda x: x.zero_level() and x.is_left() and x.selection_violation(),
                   'Ā-chain': lambda x: x.zero_level() and x.is_right() and x.thematic_head(),
                   'Feature inheritance': lambda x: x.check({'Φ?'}) or (x.highest_finite_head() and not x.check({'!PER'}))
                    }

        cyclic = kwargs.get('cyclic', True)
        Y = X

        type = 'Feature inheritance'
        if trigger[type](X) and X.Affect_a(X, type=type):
            X.Affect_a(X, type=type, log=True).feature_inheritance()

        type = 'A-chain'
        if cyclic and trigger[type](X) and X.Affect_a(X.sister(), type=type):
            Y = X.Merge_right(X.Affect_a(X.sister(), type=type, log=True).copy_for_chain()).right()

        type = 'Scrambling'
        if not cyclic and trigger[type](X):
            X.Affect_a(X.max(), type=type, log=True).reconstruct_scrambling()

        type = 'Agree'
        if trigger['Agree'](X) and X.Affect_a(X, type=type):
            X.Affect_a(X, type=type, log=True).AgreeLF()

        type = 'IHM'
        if trigger[type](X) and X.Affect_a(X.affix(), type=type):
            Y = Y.Merge_right(X.Affect_a(X.affix(), type=type, log=True).copy_for_chain()).right()

        type = 'Extrapose'
        if not cyclic and trigger[type](X) and X.Affect_a(X, type=type):
            Y = X.Affect_a(X, type=type, log=True).extrapose()

        type = 'Ā-chain'
        target = None
        if trigger[type](Y):
            if Y.sister().zero_level():
                target = next((x for x in Y.upward_path() if x.operator_features() and x.head().check_some(Y.get_selection_features('+SPEC')) and Y.tail_test(tail_sets=x.get_tail_sets())), None)
                if Y.Affect_a(target, type=type):
                    Y = Y.Merge_left(target.copy_for_chain()).right()
            if not cyclic and not Y.COMP_selection():
                target = next((x for x in Y.upward_path() if x.operator_features() and x.head().check_some(Y.get_selection_features('+COMP')) and Y.tail_test(tail_sets=x.get_tail_sets(), direction='right')), None)
                if Y.Affect_a(target, type=type):
                    Y = Y.Merge_right(target.copy_for_chain()).right()
            if target:
                Y.Affect_a(target, type=type, log=True)

        if cyclic:
            log(f'\n')

        return Y.top()

    def copy(X):
        ps_ = PhraseStructure()
        ps_.active_in_syntactic_working_memory = X.active_in_syntactic_working_memory
        ps_.adjunct = X.adjunct
        ps_.internal = X.internal
        ps_.copied = X.copied
        ps_.phrasal_zero = X.phrasal_zero
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

    def semantic_index(X, space):
        return next((f.split(':')[1].split(',')[0] for f in X.features if f.startswith('IDX') and space in f), None)

    def target_left_branch(X, target):
        new_ps = X.top().copy()
        return new_ps.get_node(X.top().get_index(target))

    # Support ----------------------------------------------------------------------
    def find_constituent_with_index(X, idx, Y):
        if X.index() == idx and X != Y:
            return X
        if X.complex():
            for x in X.const:
                const = x.find_constituent_with_index(idx, Y)
                if const:
                    return const

    def first_dominating_complex_node(X):
        while X.mother():
            if not X.mother().zero_level() and not X.mother().phrasal_zero and X.is_left():
                return X.sister()
            X = X.mother()

    def find_nonstandard_head_chain(self):
        if self.check({'create_head_chain_here'}) and self.first_dominating_complex_node():
            return self.first_dominating_complex_node().find_constituent_with_index(self.index(), self)

    def find_head_chain(self):
        if self.affix() and self.affix().index() and self.left() and self.sister():
            return self.sister().find_constituent_with_index(self.affix().index(), self)

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
            lfs = [f[3:] for f in head.features if f and f[:2] == 'LF']
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
        for cat in PhraseStructure.major_cats:
            if cat in head.features:
                return cat + suffix
        return '?' + suffix

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
        if X.identity != 0:
            chain_index_str = f':{X.identity}'
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
        stri = ''
        for i, affix in enumerate(X.get_affix_list()):
            if not affix.copied:
                if i > 0:
                    stri += '(' + ''.join(sorted([f[3:] for f in affix.features if f and f[:2] == 'PF'])) + ')'
                else:
                    stri += ''.join(sorted([f[3:] for f in affix.features if f and f[:2] == 'PF']))
        return stri

    def tidy_names(X, counter):
        def rebaptize(X, old_identity, new_identity):
            if X.identity == old_identity:
                if not X.rebaptized:
                    X.identity = new_identity
                    X.rebaptized = True
            if X.left():
                rebaptize(X.left(), old_identity, new_identity)
            if X.right():
                rebaptize(X.right(), old_identity, new_identity)
            return

        if X.identity != 0 and not X.rebaptized:
            rebaptize(X.top(), X.identity, counter)
            counter += 1
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

    def empty_finite_EPP(X):
        return X.selector().finite_C() and X.EF() and not X.edge()

    def finite_C(X):
        return 'C/fin' in X.head().features

    def adverbial(X):
        return X.check({'Adv'})

    def nominal(X):
        return X.check({'N'})

    def nonverbal(X):
        return X.nominal() or X.referential() or X.adjectival()

    def adjectival(X):
        return X.check({'A'})

    def verbal(X):
        return X.check({'ASP'})

    def theta_predicate(X):
        return X.check({'θ'}) and X.check_some({'Φ', 'Φ*'}) and not X.check({'-θ'})

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

    def relative(X):
        return X.check({'REF'})

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
        return X.zero_level() and X.check_some({'Φ', 'Φ*'})

    def adverbial_adjunct(X):
        return X.adverbial() or X.preposition()

    def is_adjoinable(X):
        return X.adjunct or (X.head().check({'adjoinable'}) and not X.head().check({'nonadjoinable'}))

    def concept(X):
        next((x for x in X.get_affix_list() if x.expresses_concept()), False)

    def semantic_complement(X):
        return X.complement() and not X.semantic_match(X.complement())

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

    def phase_head(X):
        return X.zero_level() and X.check_some(PhraseStructure.phase_heads) and not X.check_some(PhraseStructure.phase_heads_exclude)

    def extended_subject(X):
        return X.check({'GEN'})

    def highest_finite_head(X):
        return X.check({'Fin'}) and \
               not X.check_some({'C', 'FORCE'}) and \
               not (X.selector() and X.selector().check_some({'T', 'COPULA', 'Fin'}))

    def expletive(X):
        return X.head().check({'EXPL'})

    def theta_marks(X, target):
        if X.sister() == target:
            return X.theta_predicate()
        return X.check_some({'SPEC:φ', '!SPEC:φ'})

    def independent_pro_from_overt_agreement(X):
        return X.check_some({'weak_pro', 'strong_pro'})

    def get_valued_phi_types(X):
        return {f[:7] for f in X.features if valued_phi_feature(f)}

    def get_unvalued_minimal_phi(X):
        return {x for x in X.features if x[-1] == '_' and x[:7] in {'PHI:NUM', 'PHI:PER', 'PHI:DET'}}

    def phi_features(X):
        return {f[4:] for f in X.features if f.startswith('PHI:') and not f.endswith('_')}

    def EF(X):
        return X.check({'Φ*'})

    def AgreeLF_has_occurred(X):
        return X.check({'ΦLF'})

    def operator_features(X):
        return X.scan_features('ΔOP')

    def EHM(X):
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

    def has_linked_argument(X):
        return {f for f in X.head().features if f.startswith('PHI:IDX:')}

    def has_idx(X, space=''):
        return next((idx for idx, space_ in [tuple(f[4:].split(',')) for f in X.features if f.startswith('IDX:')] if space_ == space or space == ''), None)

    def get_idx_tuple(X, space):
        return next(((idx, space_) for idx, space_ in [tuple(f[4:].split(',')) for f in X.features if f.startswith('IDX:')] if space_ == space or space == ''), None)

    def get_referential_index(X, space):
        def index_(f):
            return f.split(':')[1].split(',')[0]

        def space_(f):
            return f.split(':')[1].split(',')[1]

        return next((index_(f) for f in X.head().features if f.startswith('IDX:') and space_(f) == space), None)

    def construct_semantic_working_memory(X, intervention_feature, assignment):
        sWM = set()
        for const in (x for x in X.upward_path() if x.head().has_idx() and x.head().get_idx_tuple('QND') and x.head() != X and not x.copied):
            sWM.add(assignment[const.head().get_referential_index('QND')])
            if intervention_feature and not const.copied and {intervention_feature}.issubset(const.head().features):
                break
        return sWM