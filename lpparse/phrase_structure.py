
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
    identity = 0
    noncyclic_derivation = False

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
        self.focus = False
        self.nn = None
        if left and left.adjunct and left.zero_level():
            self.adjunct = True
            left.adjunct = False

    # Phrase structure geometry --------------------------------
    def L(X):
        if X.const:
            return X.const[0]

    def R(X):
        if X.const:
            return X.const[-1]

    def M(X):
        return X.mother_

    def create_constituents(X, lst):
        X.const = lst
        for x in X.const:
            x.mother_ = X
        return X

    def terminal(X):
        return not X.const

    def complex(X):
        return len(X.const) > 1

    def zero_level(X):
        return len(X.const) < 2 or X.phrasal_zero

    def is_L(X):
        return X.M() and X.M().L() == X

    def is_R(X):
        return X.M() and X.M().R() == X

    def complex_head(X):
        return len(X.affixes()) > 1

    def affix(X):
        if X.L() == X.R():
            return X.L()

    def affixes(X):
        lst = [X]
        while X.affix():
            lst.append(X.affix())
            X = X.affix()
        return lst

    def bottom(X):
        return list(X.top().minimal_search())[-1]

    def top(X):
        while X.M():
            X = X.M()
        return X

    def GM(X):
        if X.M().M():
            return X.M().M()

    def aunt(X):
        if X.M():
            return X.M().sister()

    def H(X):
        return next((x for x in [X] + X.const if x.zero_level()), X.complex() and X.right_nonadjunct().H())

    def right_nonadjunct(X):
        if X.R().adjunct:
            return X.L()
        return X.R()

    def inside(X, head):
        return X.H() == head

    def container(X):
        if X.M() and X.H() != X.M().H():
            return X.M().H()

    def max(X):
        x = X
        while x.M() and x.M().H() == X.H():
            x = x.M()
        return x

    def minimal_search_domain(X):
        if not X.right_sister():
            return X
        return X.sister()

    def geometrical_sister(X):
        if X.is_L():
            return X.M().R()
        return X.M().L()

    def sister(X):
        while X.M():
            if not X.geometrical_sister().adjunct:
                return X.geometrical_sister()
            X = X.M()

    def right_sister(X):
        if X.sister() and X.sister().is_R():
            return X.sister()

    def complement(X):
        if X.zero_level() and X.is_L():
            return X.sister()

    def proper_complement(X):
        if X.complement() and X.complement().is_R():
            return X.complement()

    def selector(X):
        if X.max().sister() and X.max().sister().zero_level() and X.max().sister().is_L():
            return X.max().sister()

    def specifier_sister(X):
        if X.is_L():
            return X.M()
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
        elif X.nn.H() == X.nn.R().H() or X.nn.H().proper_complement():
            X.nn = X.nn.R()
        else:
            X.nn = X.nn.L()
        return current.L()

    def minimal_search(X, **kwargs):
        return takewhile(lambda x: not kwargs.get('intervention', lambda x: False)(x), (x for x in X))

    def path(X):
        path = []
        x = (X, X.M())
        while x[1]:
            if x[1].L() and x[1].L() != x[0]:
                path.append(x[1].L())
            x = (x[1], x[1].M())
        return path

    def self_path(X):
        return [X] + X.path()

    def next(X, memory_span, condition=lambda x: True):
        return next((x for x in memory_span() if condition(x)), None)

    def edge(X):
        return list(takewhile(lambda x: x.M() and x.M().inside(X), X.path()))

    def local_edge(X):
        return next(iter(X.edge()), None)

    def pro_edge(X):
        if X.NS():
            return X.edge() + [X.NS()]
        return X.edge()

    def identify_argument(X):
        arguments = [acquire(X) for acquire in [lambda x: x.pro_argument(),
                                                lambda x: x.complement_argument(),
                                                lambda x: x.indexed_argument(),
                                                lambda x: x.local_edge(),
                                                lambda x: x.control()]]
        return next((x for x in arguments if x), None)

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
        while x.complex() and x.R():
            search_list.append(x.R())
            x = x.R()
        return search_list

    def predicate_composition(X):
        if X.complement():
            lst = [x for x in X.complement().minimal_search(intervention=lambda x: x.reference_head()) if x.zero_level()]
            if lst:
                lst = [X] + lst[:-1] + lst[-1].affixes()
            return lst

    def reference_head(X):
        return {'π', 'D', 'φ'} & X.features

    def new_focus(X):
        return next((x for x in X.const[::-1] if X.complex() and x.zero_level()), X)

    def reconstruct(X):
        """
        Reconstruction cycle for element X (head or phrase).
        OP = contains all reconstruction operations and their properties
        T = element that will be targeted (head or phrase, can be X itself, can be a chain copy)
        """
        for type, calculate in PhraseStructure.speaker_model.OP.items():
            if not X.copied and calculate['TRIGGER'](X):
                T = calculate['TARGET'](X)
                if T:
                    log(f'\n\t{type}({T.illustrate()})')
                    X = calculate['TRANSFORM'](X, T).new_focus()
                    log(f'\n\t = {X.top()}')
        return X.top()

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
               not X.local_edge().H().check_some(fset)

    # +SPEC:L,K
    def plus_SPEC(X, fset):
        return len(fset) == 0 or \
               (not X.local_edge() and 'ø' in fset) or \
               (X.local_edge() and X.local_edge().H().check_some(fset))

    # +COMP:L,K
    def plus_COMP(X, fset):
        return not PhraseStructure.speaker_model.settings.retrieve('head_complement_selection', True) or \
               fset == 0 or\
               (not X.proper_complement() and 'ø' in fset) or \
               (X.proper_complement() and X.proper_complement().H().check_some(fset))

    # -COMP:L,K
    def minus_COMP(X, fset):
        return not PhraseStructure.speaker_model.settings.retrieve('head_complement_selection', True) or \
               len(fset) == 0 or \
               not X.proper_complement() or \
               not X.proper_complement().H().check_some(fset)

    # -SELF
    def minus_SELF(X, fset):
        return not X.check_some(fset)

    # +SELF
    def plus_SELF(X, fset):
        return X.check_some(fset)

    # =SELF
    def conjunctive_minus_SELF(X, fset):
        return not X.check(fset)

    def get_constituent_containing_selection_violation(X):
        return next((x for x in X if x.selection_violation() and not x.sister().adjunct), None)

    def w_selection(X):
        for feature in X.features:
            if feature.startswith('!wCOMP:') and not X.affix().check(set(feature.split(':')[1].split(','))):
                return True
            elif feature.startswith('-wCOMP:') and X.affix().check_some(set(feature.split(':')[1].split(','))):
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
        return X.check({'θ'})

    def in_thematic_position(X):
        return (X.max().container() and X.max().container().thematic_head()) or \
               (X.max().container() and X.max().container().complement() == X.max())

    def projection_principle_failure(X):
        if X.max() != X.top():
            return (X.max().projection_principle_applies() and
                    not X.max().container_assigns_theta_role(X.max().container())) or \
                   X.pro_projection_principle_violation()

    def projection_principle_applies(X):
        return X.referential() and \
               not X.max().copied and \
               X.max().M() and \
               not X.max().contains_features({'adjoinable', 'SEM:nonreferential'})

    def pro_projection_principle_violation(X):
        if X.zero_level() and X.independent_pro_from_overt_agreement() and X.right_sister():
            for x in X.right_sister().minimal_search(intervention=lambda y: y.thematic_head() and y.verbal()):
                if x.zero_level():
                    if x.independent_pro_from_overt_agreement():
                        return True
                    if x.nonthematic_verb():
                        if X.AgreeLF_has_occurred() or not X.nonreferential_pro():
                            return True

    def container_assigns_theta_role(X, Y):
        return Y and Y.thematic_head() and not (X == Y.local_edge() and Y.EPP()) and \
               (X == Y.geometrical_sister() or X == Y.local_edge())

    # Transfer --------------------------------------------------------------------------------------------------------------------

    def transfer(X):
        Y, m = X.detach()
        for Z in Y.bottom().self_path():
            Z.reconstruct()
        return Y.reattach(m)

    def scan_feature(X, feature):
        if X.zero_level():
            if {f for f in X.features if f.startswith(feature) and f[-1] != '_'}:
                return True
        else:
            for x in [x for x in X.const if not x.copied]:
                if x.scan_feature(feature):
                    return True

    @staticmethod
    def baptize_chain():
        PhraseStructure.chain_index += 1
        return str(PhraseStructure.chain_index)

    # Ā-Chain creation =====================================================================
    def reconstruct_operator(X):
        for x in X.container().sister().minimal_search():
            if x.tail_test(tails_sets=X.get_tail_sets()):
                if not x.local_edge() and X.check_some(x.get_selection_features('+SPEC')):
                    return X.chaincopy() * x.M()
                if X.check_some(x.get_selection_features('+COMP')) and not x.complement():
                    return x * X.chaincopy()
        return X

    # Scrambling ==========================================================================

    def tail_fit(X, Y, direction='left'):
        return X.tail_test(tail_sets=Y.get_tail_sets(),
                           weak_test=Y.referential() or Y.preposition(),
                           direction=direction)

    def scrambling_reconstruct(XP, YP):
        """
        Reconstructs scrambled phrases.
        XP = the original phrase which was marked for scrambling.
        YP = target copy (may contain additional material such as Specs)
        """

        # In situ scrambling: if the extrenalized XP is in correct position, leave it there
        if XP.tail_test() and not (XP.container() and XP.container().EPP()):
            XP.copied = False
            XP.identity = 0
            return XP.top()

        # Search for a new position
        for x in XP.local_tense_edge().minimal_search(intervention=lambda x: 'φ' in x.features or x == XP.H()):
            # Specifier positions
            if x.tail_fit(YP, 'left') and YP.spec_selection(x):
                if x.is_L():
                    return YP * x.M()    #   [a X(P)] = [YP [a X(P)]]
                return YP * x            #   [X(P) a] = [X(P) [YP a]]
            # Complement positions
            if x.zero_level() and not x.proper_complement() and x.tail_fit(YP, 'right') and x.comp_selection(YP):
                return x * YP            #   [X(P) a] = [X(P) [a YP]] or [a <XP>] = [[a YP] <XP>]

        XP.copied = False
        XP.identity = 0
        return XP.top()     # If nothing is found, do nothing

    def local_tense_edge(X):
        return next((node.M() for node in X.path() if node.finite() or node.force()), X.top())

    def scrambling_target(X):
        """
        Returns the phrase to be scrambled. Heads H which must or may have
        specifiers will return [SPEC + HP] if SPEC is present (Condition 1); otherwise HP (Condition 2)
        """
        if X.H().check_some({'EF', 'EF*'}) and X.H().local_edge():
            return X.H().local_edge().M()   # Condition 1
        return X.H().M()    # Condition 2

    def transfer_adjunct(X):
        detached_phrase, m = X.detach()
        detached_phrase.transfer()
        detached_phrase.mother_ = m
        return detached_phrase

    # Agreement ---------------------------------------------------------------------------------------------
    def AgreeLF(X):
        return X.Agree(X.get_goal())

    def get_goal(X):
        return next((x for x in X.minimal_search_domain().minimal_search(intervention=lambda x: x.phase_head())
                     if x.goal_selection()), None)

    def goal_selection(X):
        return not X.copied and (X.H().referential() or X.phase_head())

    def Agree(X, goal):
        if X.is_unvalued() and goal:
            if not goal.feature_mismatch_test(X.phi_bundles()):
                X.value(goal)
            else:
                X.features.add('*')
        else:
            log(f' did not find suitable goal.')
        return X

    def feature_mismatch_test(X, PP):
        """
        X = goal
        PP = phi-bundles at the probe
        This function examines if there are unlicensed phi-features at the goal (G) that mismatch with
        phi-features at the probe. Unlicensed phi-features at the goal are those features which are not
        matched with phi-bundles at the probe.
        Note 1: The feature format is TYPE:VALUE with (i)PHI removed.
        """
        return mismatch(unlicensed_phi_features_at_goal(X.H().interpretable_phi_features(), PP), set().union(*PP))

    def interpretable_phi_features(X):
        return {f[5:] for f in X.features if f.startswith('iPHI:')}

    def value(X, goal):
        log(' values ')
        P = set().union(*X.phi_bundles())
        for phi in [goal_feature for goal_feature in goal.H().features if interpretable_phi_feature(goal_feature) and unvalued_counterparty(goal_feature, X) and (not P or X.feature_gate(goal_feature, P))]:
            X.features.discard(f'PHI:{phi.split(":")[1]}:_')
            X.features.add(f'{phi[1:]}')
            log(f'[{phi[5:]}]')
        log(f' from goal {goal.max()}.')
        X.features.update({'ΦLF'})
        X.features.add(f'PHI:IDX:{goal.H().get_id()}')

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

    def EPP_violation(X):
        """
        Current implementation of the Agree/EPP system, tested as LF-legibility
        """
        if not X.check_some({'ASP', 'strong_pro', 'C/fin'}):                #   Amnesty for strong pro, theta heads and C/fin
            if not X.check_some({'EF*', 'EF'}):                             #   If X does not have EF, it cannot have local edge
                return X.local_edge()
            if X.check({'-ΦPF'}) or not X.EPP():                            #   Amnesty for non-agreeing heads and heads without EPP
                return False
            if X.check({'weak_pro'}):                                       #   Secondary rule:
                return X.check({'ΦLF'}) and not X.local_edge()              #       If Agree(X, Y), SpecXP cannot be empty
            if X.check({'ΦLF'}):                                            #   Primary rule:
                return not X.primary_rule()                                 #       If Agree(X, Y), YP = SpecXP
            # If Agree(X, Y) does not occur, then violation can be avoided if X is specifically marked to not require Agree
            # or there is phi-consistent overt agreement suffices at X
            elif not X.check_some({'?ΦLF', '-ΦLF'}) and not (X.check({'ΦPF'}) and X.phi_consistent_head()):
                return True

    def primary_rule(X):
        return X.local_edge() and X.indexed_argument() and X.local_edge().H().get_id() == X.indexed_argument().H().get_id()

    def indexed_argument(X):
        idx = X.phi_index()
        if idx and X.sister():
            return next((x.max() for x in X.sister().minimal_search() if idx in x.H().features), None)

    def phi_index(X):
        return next((f.split(':')[2] for f in X.features if f.startswith('PHI:IDX:')), None)

    def feature_inheritance(X):
        if X.highest_finite_head():
            X.features.add('!PER')
        if X.check({'EF?'}):
            X.features.discard('EF?')
            X.features.add('EF*')
            if X.selected_by_SEM_internal_predicate():
                X.features.add('-ΦLF')
        return X

    # Feature processing -----------------------------------------------------------------------------

    def check(X, fset):
        return fset <= X.H().features

    def check_some(X, fset):
        return fset & X.H().features

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
        return {frozenset(f[5:].split(',')) for f in X.H().features if f[:4] == 'TAIL'}

    def needs_valuation(X):
        if not X.complete_agreement_suffixes() and X.get_unvalued_minimal_phi():
            return X.get_unvalued_minimal_phi()

    def phi_is_unvalued(X):
        for f in X.H().features:
            if f[-1] == '_':
                return True

    def specifiers_licensed(X):
        return set().union(*{frozenset(f[6:].split(',')) for f in X.features if f.startswith('+SPEC:')})

    def spec_selection(X, W):
        return X.complex() and X.check_some(W.specifiers_licensed())

    def comp_selection(X, W):
        return X.zero_level() and W.check_some(X.complements_licensed())

    def complements_licensed(X):
        return set().union(*{frozenset(f[6:].split(',')) for f in X.features if f.startswith('+COMP:')})

    def semantic_match(X, b):
        a_head = X.H()
        b_head = b.H()
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
            return X.H()
        return X

    def operator_in_scope_position(X):
        return X.complex() and X.container() and not X.copied and X.container().H().finite() and 'ΔOP' in X

    # Tail-processing ---------------------------------------------------------------------------

    def tail_test(X, **kwargs):
        tail_sets = kwargs.get('tail_sets', X.get_tail_sets())
        if not tail_sets:
            return True
        weak_test = kwargs.get('weak_test', True)
        direction = kwargs.get('direction', 'left')
        positive_tsets = {frozenset(positive_features(tset)) for tset in tail_sets if positive_features(tset)}
        negative_tsets = {frozenset(negative_features(tset)) for tset in tail_sets if negative_features(tset)}
        checked_pos_tsets = {tset for tset in positive_tsets if X.tail_condition(tset, weak_test, direction)}
        checked_neg_tsets = {tset for tset in negative_tsets if X.tail_condition(tset, weak_test, direction)}
        return positive_tsets == checked_pos_tsets and not checked_neg_tsets

    def tail_condition(X, tail_set, weak_test, direction):
        if weak_test:
            context = [x for x in X.path() if x.zero_level()]
            if direction == 'right':
                context.insert(0, X)
            for m in context:
                if m.check_some(tail_set):
                    return m.check(tail_set)
        else:
            return X.check_container(tail_set) or X.check_aunt(tail_set)

    def check_container(X, tset):
        return X.max().container() and X.max().container().check(tset)

    def check_aunt(X, tset):
        return X.max().M() and \
               X.max().M().sister() and \
               X.max().M().sister().check(tset)

    # Recovery ---------------------------------------------------------------------------------------------------

    def is_possible_antecedent(X, antecedent):
        if antecedent:
            if antecedent.H().referential():
                valued_phi_at_probe = [phi.split(':') for phi in X.features if (phi[:7] == 'PHI:NUM' or phi[:7] == 'PHI:PER') and not phi.endswith('_') and not ',' in phi]
                valued_phi_at_antecedent = [phi.split(':') for phi in antecedent.H().features if (phi[:7] == 'PHI:NUM' or phi[:7] == 'PHI:PER' or phi[:8] == 'iPHI:NUM' or phi[:8] == 'iPHI:PER') and not phi.endswith('_')]
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
        search_path = [x for x in takewhile(lambda x: not x.H().check({'SEM:external'}), X.path())]
        antecedent = next((x for x in search_path if X.is_possible_antecedent(x)), None)
        if not antecedent:
            antecedent = PhraseStructure()
            antecedent.features = {"PF:generic 'one'", 'LF:generic', 'φ', 'D'}
        return antecedent

    def finite_control(X):
        antecedent = X.next(X.path, lambda x: x.complex() and X.is_possible_antecedent(x) and not x.copied)
        return antecedent

    # Structure building --------------------------------------------------------------------------

    def insert_left(X, Y):
        return X.create_constituents([Y, X.R()]).L()

    def insert_right(X, Y):
        return X.create_constituents([X.L(), Y]).R()

    def __call__(Xa, Y, dir=''):
        if Xa.is_L():
            return Xa.M().insert_left(Xa.Merge(Y, dir))
        elif Xa.is_R():
            return Xa.M().insert_right(Xa.Merge(Y, dir))
        return Xa.Merge(Y, dir)

    def Merge(X, Y, dir):
        if dir == 'left':
            return Y + X
        return X + Y

    def __add__(X, Y):
        return PhraseStructure(X, Y)

    def __mul__(X, Y):
        X.consume_resources('Merge-1', X)
        if X.M():
            return X(Y, 'right')
        elif Y.M():
            return Y(X, 'left')
        return X + Y

    def __contains__(X, f):
        return X.scan_feature(f)

    def __pow__(X, Y):
        return X.affixes()[-1].create_constituents([Y])

    def attach(X, W):
        X.speaker_model.results.consume_resources('Merge', X, W)
        if X.w_internal() and (PhraseStructure.speaker_model.settings.retrieve('UG_parameter_middle_field_HM', True) or X.check({'C'}) or X.bottom_affix().EHM()):
            return X ** W   #   EHM
        return X * W        #   Phrasal Merge (asymmetric)

    def detach(X):
        m = X.M()
        X.mother_ = None
        return X, m

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

    def reattach(X, m):
        X.mother_ = m
        return X

    def __getitem__(X, idx):
        for i, X in enumerate(X.geometrical_minimal_search()):
            if i == idx:
                return X
        return None

    def get_index(X, target):
        for i, node in enumerate(X.geometrical_minimal_search()):
            if target == node:
                return i

    def index(X):
        for x in X.features:
            if x.startswith('§'):
                return x

    def semantic_index(X, space):
        return next((f.split(':')[1].split(',')[0] for f in X.features if f.startswith('IDX') and space in f), None)

    def target_left_branch(X, N):
        return X.top().copy()[X.top().get_index(N)]

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
        while X.M():
            if not X.M().zero_level() and not X.M().phrasal_zero and X.is_L():
                return X.sister()
            X = X.M()

    def find_nonstandard_head_chain(self):
        if self.check({'create_head_chain_here'}) and self.first_dominating_complex_node():
            return self.first_dominating_complex_node().find_constituent_with_index(self.index(), self)

    def find_head_chain(self):
        if self.affix() and self.affix().index() and self.L() and self.sister():
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
            if 'null' in X.L().features:
                pf = pf + '_'
            else:
                pf = pf + X.L().gloss() + ' '
            if 'null' in X.R().features:
                pf = pf + '_'
            else:
                pf = pf + X.R().gloss() + ' '
        if X.zero_level():
            pf = pf + LF_features(X)
        return pf

    def PF(X):
        for f in X.features:
            if f.startswith('PF:'):
                return f.split(':')[1]
        return '?'

    def label(X):
        head = X.H()
        if X.complex():
            suffix = 'P'
        else:
            suffix = ''
        for cat in PhraseStructure.major_cats:
            if cat in head.features:
                return cat + suffix
        return '?' + suffix

    def chaincopy(X, babtize='1', **kwargs):
        def silence_phonologically(h):
            if not h.features:
                h.features = {'null'}
            else:
                h.features.add('null')      # Null is about what is printed out
                h.features.discard('Δp')    # This is the grammatical feature that operates in narrow syntax
            if h.L():
                silence_phonologically(h.L())
            if h.R():
                silence_phonologically(h.R())

        if kwargs.get('externalize', False):
            X.transfer()
            X.adjunct = True
        X.identity = X.baptize_chain()
        X_copy = X.copy()
        X_copy.identity = X.identity
        X_copy.copied = False
        silence_phonologically(X_copy)
        X.copied = True
        X.features.add('CHAIN:' + str(X_copy.identity))
        if X.referential():
            X_copy.adjunct = False
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
                       + X.L().illustrate() + ' ' \
                       + X.R().illustrate() + '>'
            else:
                return f'[' + prefix \
                       + X.L().illustrate() + ' ' \
                       + X.R().illustrate() + ']'

    def phonological_content(X):
        exceptions = {'φ', 'D'}
        phon = ''
        if X.zero_level():
            if not set(X.get_phonological_string()) & exceptions:
                phon = X.get_phonological_string()
        else:
            str = X.L().phonological_content()
            if str:
                phon += ' ' + str
            if not X.R().adjunct:
                str = X.R().phonological_content()
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
                return f'<{X.L()} {X.R()}>' + chain_index_str
            else:
                return f'[{X.L()} {X.R()}]' + chain_index_str

    def get_phonological_string(X):
        stri = ''
        for i, affix in enumerate(X.affixes()):
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
            if X.L():
                rebaptize(X.L(), old_identity, new_identity)
            if X.R():
                rebaptize(X.R(), old_identity, new_identity)
            return

        if X.identity != 0 and not X.rebaptized:
            rebaptize(X.top(), X.identity, counter)
            counter += 1
        if X.L():
            counter = X.L().tidy_names(counter)
        if X.R():
            counter = X.R().tidy_names(counter)
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
        return X.selector().finite_C() and X.EPP() and not X.edge()

    def finite_C(X):
        return 'C/fin' in X.H().features

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
        return X.check({'θ'}) and X.check_some({'EF', 'EF*'}) and not X.check({'-θ'})

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
        return X.zero_level() and X.check_some({'EF', 'EF*'})

    def adverbial_adjunct(X):
        return X.adverbial() or X.preposition()

    def is_adjoinable(X):
        return X.adjunct or (X.H().check({'adjoinable'}) and not X.H().check({'nonadjoinable'}))

    def concept(X):
        next((x for x in X.affixes() if x.expresses_concept()), False)

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
        return X.complex() and not X.copied and X.H().get_tail_sets() and X.H().check({'adjoinable'}) and not X.H().check({'nonadjoinable'})

    def legitimate_criterial_feature(X):
        return X.referential() and not X.relative() and X.mother_ and X.mother_.contains_features({'REL'}) and not X.mother_.contains_features({'T/fin'})

    def interpretable_adjunct(X):
        return X.referential() and X.max() and X.max().adjunct and X.max().is_R() and X.max().mother_ and X.max().mother_.referential()

    def w_internal(X):
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
        return X.H().check({'EXPL'})

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

    def EPP(X):
        return X.check({'EF*'})

    def AgreeLF_has_occurred(X):
        return X.check({'ΦLF'})

    def operator_features(X):
        return 'ΔOP' in X

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
        return {f for f in X.H().features if f.startswith('PHI:IDX:')}

    def has_idx(X, space=''):
        return next((idx for idx, space_ in [tuple(f[4:].split(',')) for f in X.features if f.startswith('IDX:')] if space_ == space or space == ''), None)

    def get_idx_tuple(X, space):
        return next(((idx, space_) for idx, space_ in [tuple(f[4:].split(',')) for f in X.features if f.startswith('IDX:')] if space_ == space or space == ''), None)

    def get_referential_index(X, space):
        def index_(f):
            return f.split(':')[1].split(',')[0]

        def space_(f):
            return f.split(':')[1].split(',')[1]

        return next((index_(f) for f in X.H().features if f.startswith('IDX:') and space_(f) == space), None)

    def construct_semantic_working_memory(X, intervention_feature, assignment):
        sWM = set()
        for const in (x for x in X.path() if x.H().has_idx() and x.H().get_idx_tuple('QND') and x.H() != X and not x.copied):
            sWM.add(assignment[const.H().get_referential_index('QND')])
            if intervention_feature and not const.copied and {intervention_feature}.issubset(const.H().features):
                break
        return sWM