
from itertools import takewhile
from feature_processing import *
from support import log
from phrase_structure_inner_core import PhraseStructureCore, mandatory, illicit

class PhraseStructure:
    speaker_model = None
    major_cats = ['@', '√', 'n', 'N', 'Neg', 'Neg/fin', 'P', 'D', 'Qn', 'Num', 'φ', 'Top', 'C', 'C/fin', 'a', 'A', 'v', 'V', 'Pass',
                  'VA/inf', 'T', 'Fin', 'Agr',
                  'A/inf', 'MA/inf', 'ESSA/inf', 'E/inf', 'TUA/inf', 'KSE/inf', 'Inf',
                  'FORCE', 'EXPL', 'Adv',
                  '0', 'a', 'b', 'c', 'd', 'x', 'y', 'z', 'X', 'Y', 'Z']
    access_experimental_functions = None
    spellout_heads = False      # This parameter, if set true, spells out PF-content of heads in all printouts; otherwise only labels are shown
    phase_heads = {'ph', 'φ'}   # Phase heads set for all calculations
    phase_heads_exclude = set()
    resources = {"Merge-1": {"ms": 0, "n": 0}}
    chain_index = 0
    identity = 0
    cyclic = False

    def __init__(self, left=None, right=None, **kwargs):
        # Internal properties
        self.core = PhraseStructureCore(features=kwargs.get('features', []))
        # External properties (geometry)
        self.const = []
        if left and right:
            self.create_constituents([left, right])
        self.mother_ = None
        # External properties (other)
        self.active_in_syntactic_working_memory = True
        self.adjunct = False
        self.copied = None
        self.phrasal_zero = False
        self.identity = 0
        self.internal = False
        self.clitic = False
        self.rebaptized = False
        # Auxiliary properties (not part of the theory)
        self.stop = False
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
        if X.complement() and X.complement().H().core.referential():
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
        return X.zero_level() and X.check_some({'π', 'D', 'φ'})

    def denotes_event(X):
        return X.H().core.event()

    def new_focus(X):
        return next((x for x in X.const[::-1] if X.complex() and x.zero_level()), X)

    def reconstruct(X, OPs):
        """
        Reconstruction cycle for element X (head or phrase).
        OPs = dictionary of reconstruction operations to be applied
        T = element that will be targeted (head or phrase, can be X itself, can be a chain copy)
        """
        for type, calculate in OPs.items():
            if not X.copied and calculate['TRIGGER'](X):
                T = calculate['TARGET'](X)
                if T:
                    log(f'\n\t{type}({T.illustrate()})')
                    X = calculate['TRANSFORM'](X, T).new_focus()
                    log(f'\n\t = {X.top()}')
        return X.top()

    def transfer(X):
        Y, m = X.detach()
        PhraseStructure.exit = True
        for type, calculation in PhraseStructure.speaker_model.OPs.items():
            Z = None
            while not Z or (type == 'IHM' and Y.top().size() != Z.top().size()):
                Z = Y.top().copy()
                for x in Y.bottom().self_path():
                    x.reconstruct({type: calculation})
        return Y.reattach(m)

    # Virtual pronouns -----------------------------------------------------------------------

    def pro_argument(X):
        if X.core.independent_pro_from_overt_agreement() or X.core.complete_agreement_suffixes():
            return X.NS()

    def NS(X):
        if X.predicate() and X.core.complete_agreement_suffixes():
            return PhraseStructure(features=X.core.pro_features())

    def selection_violation(X):
        return not X.COMP_selection() or not X.SPEC_selection()

    def properly_selected(X):
        return X.selector() and X.selector().COMP_selection()

    def SPEC_selection(X):
        return X.minus_SPEC(X.core.get_selection_features('-SPEC')) and \
               X.plus_SPEC(X.core.get_selection_features('+SPEC'))

    def COMP_selection(X):
        return X.minus_COMP(X.core.get_selection_features('-COMP')) and \
               X.plus_COMP(X.core.get_selection_features('+COMP'))

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
        for f in X.core.features():
            if f.startswith('!wCOMP:') and not X.affix().check(set(f.split(':')[1].split(','))):
                return True
            elif f.startswith('-wCOMP:') and X.affix().check_some(set(f.split(':')[1].split(','))):
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
                        return x.core.EHM()      # [ε] blocks IHM
                    else:
                        if not x.core.EHM():     # [ε] licenses EHM
                            return True
                x = x.affix()

    def probe_goal_test(X):
        if X.sister():
            for ff in [(f, X.probe(f[7:])) for f in X.core.probe_features()]:
                if (mandatory(ff[0]) and not ff[1]) or (illicit(ff[0]) and ff[1]):
                    return True

    def probe(X, G):
        return next((x for x in X.sister() if x.check({G})), None)

    # Projection principle ---------------------------------------------------------------------

    def in_thematic_position(X):
        return (X.max().container() and X.max().container().core.thematic_head()) or \
               (X.max().container() and X.max().container().complement() == X.max())

    def projection_principle_failure(X):
        if X.max() != X.top():
            return (X.max().projection_principle_applies() and
                    not X.max().container_assigns_theta_role(X.max().container())) or \
                   X.pro_projection_principle_violation()

    def projection_principle_applies(X):
        return X.core.referential() and \
               not X.max().copied and \
               X.max().M() and \
               not X.max().contains_features({'adjoinable', 'SEM:nonreferential'})

    def pro_projection_principle_violation(X):
        if X.zero_level() and X.core.independent_pro_from_overt_agreement() and X.right_sister():
            for x in X.right_sister().minimal_search(intervention=lambda y: y.core.thematic_head() and y.core.verbal()):
                if x.zero_level():
                    if x.core.independent_pro_from_overt_agreement():
                        return True
                    if x.nonthematic_verb():
                        if X.core.AgreeLF_has_occurred() or not X.core.nonreferential_pro():
                            return True

    def container_assigns_theta_role(X, Y):
        return Y and Y.core.thematic_head() and not (X == Y.local_edge() and Y.core.EF()) and \
               (X == Y.geometrical_sister() or X == Y.local_edge())

    def unrecognized_label(X):
        return ['CAT:?', '?'] in X.core

    def scan_feature(X, feature):
        if X.zero_level():
            if {f for f in X.core.features() if f.startswith(feature)}:
                return True
        else:
            for x in [x for x in X.const if not x.copied]:
                if x.scan_feature(feature):
                    return True

    @staticmethod
    def baptize_chain():
        PhraseStructure.chain_index += 1
        return str(PhraseStructure.chain_index)

    def create_feature_chain(X):
        X.local_container().core.add_features(PhraseStructure.speaker_model.lexicon.lexical_redundancy(X.scan_strong_features()))

    def local_container(X):
        # Local container of zero-level X is:
        if X.zero_level():
            if X.M().zero_level():
                # (1) Y if Y(X...)
                return X.M()
            # otherwise (2) create Y such that Y(X...)
            M = X.M()
            return M.create_constituents([PhraseStructure(features={'C', 'C/fin', 'Fin', 'PF:C', 'LF:C', 'OP'}) ** X, M.R()]).L()
        else:
            # Local container of XP is:
            if X.container() and X.container().local_edge() == X:
                # (1) Y if [XP [Y..]]
                return X.container()
            # otherwise (2) create Y such that [XP [Y...]]
            return (PhraseStructure(features={'C', 'C/fin', 'PF:C', 'LF:C', 'Fin', 'EF'}) * X.sister()).L()

    def scan_strong_features(X):
        fset = X.core.strong_features()
        if fset:
            return {f[2:] for f in fset}    # Remove strength diacritic
        if X.complex():
            for x in X.const:
                fset = x.scan_strong_features()
                if fset:
                    return fset
        return set()

    # Ā-Chain creation =====================================================================
    def reconstruct_operator(X, T):
        for x in X.sister().minimal_search():
            if T.zero_level() and T.core.finite():
                #   Sentence operator, null head, V2
                T = X.chaincopy()
                if x.complex():
                    return T * x.sister()       # [T [XP [T' YP]]], XP = x
                return T * x                    # [T [T' [K YP]]], K = x
            if x.tail_test(tails_sets=T.get_tail_sets()):
                # New SPEC
                if T.complex() and not x.local_edge() and T.check_some(x.core.get_selection_features('+SPEC')):
                    return T.chaincopy() * x.M()
                # New COMP
                if T.check_some(x.core.get_selection_features('+COMP')):     # (2.1) No complement = [T....[x T']]
                    if not x.complement():
                        return x * T.chaincopy()
                # LHM
                if T.zero_level() and T.affix() and T.affix().check_some(x.core.get_selection_features('+COMP')):
                    return T.affix().chaincopy() * x.sister()
        return X

    def head_reconstruction(X, T):
        if not X.is_L():
            if not ('OP:' in X and X.core.finite()):
                return X * T.chaincopy()
            return X
        if PhraseStructure.cyclic:
            return X.sister() * T.chaincopy()
        return T.chaincopy() * X.sister()

    # Scrambling ==========================================================================
    def tail_fit(X, Y, direction='left'):
        return X.tail_test(tail_sets=Y.get_tail_sets(),
                           weak_test=Y.core.referential() or Y.core.preposition(),
                           direction=direction)

    def scrambling_reconstruct(XP, YP):
        """
        Reconstructs scrambled phrases.
        XP = the original phrase which was marked for scrambling.
        YP = target copy (may contain additional material such as Specs)
        """

        # In situ scrambling: if the extrenalized XP is in correct position, leave it there
        if XP.tail_test() and not (XP.container() and XP.container().core.EF()):
            XP.copied = False
            XP.identity = 0
            return XP.top()

        # Search for a new position
        for x in XP.local_tense_edge().minimal_search(intervention=lambda x: 'φ' in x.core or x == XP.H()):
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
        return next((X.M() for X in X.path() if X.core.finite() or X.core.force()), X.top())

    def scrambling_target(X):
        """
        Returns the phrase to be scrambled. Heads H which must or may have
        specifiers will return [SPEC + HP] if SPEC is present (Condition 1); otherwise HP (Condition 2)
        """
        if X.H().core.EF() and X.H().local_edge() and ['T', 'V'] not in X.H().local_edge().H().core:
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

    def Agree(X, goal):
        if X.core.is_unvalued() and goal:
            if not goal.core.feature_mismatch_test(X.core.phi_bundles()):
                X.core.value(goal)
            else:
                X.core.add_features({'*'})
        else:
            log(f' did not find suitable goal.')
        return X

    def get_goal(X):
        return next((x for x in X.minimal_search_domain().minimal_search(intervention=lambda x: x.phase_head())
                     if x.goal_selection()), None)

    def goal_selection(X):
        return not X.copied and (X.H().core.referential() or X.phase_head())

    def EPP_violation(X):
        """
        Current implementation of the Agree/EPP system, tested as LF-legibility
        """
        if not X.check_some({'ASP', 'strong_pro'}):                         #   Amnesty for strong pro, theta heads and C/fin
            if not X.core.EF():                                       #   If X does not have EF,
                return X.local_edge() and not X.core.thematic_edge()             #   it cannot have nonthematic edge element
            if X.check({'-ΦPF'}) or not X.core.EPP():                 #   Amnesty for non-agreeing heads and heads without EPP
                return False
            if X.check({'weak_pro'}):                                       #   Secondary rule:
                return X.check({'ΦLF'}) and not X.local_edge()              #       If Agree(X, Y), SpecXP cannot be empty
            if X.check({'ΦLF'}) and X.check({'PER'}):                       #   Primary rule:
                return not X.primary_rule()                                 #       If Agree(X, Y), YP = SpecXP
            # If Agree(X, Y) does not occur, then violation can be avoided if X is specifically marked to not require Agree
            # or there is phi-consistent overt agreement suffices at X
            elif not X.check_some({'?ΦLF', '-ΦLF'}) and not (X.check({'ΦPF'}) and X.core.phi_consistent_head()):
                return True

    def primary_rule(X):
        return X.local_edge() and X.indexed_argument() and X.local_edge().H().core.get_id() == X.indexed_argument().H().core.get_id()

    def indexed_argument(X):
        idx = X.core.phi_index()
        if idx and X.sister():
            return next((x.max() for x in X.sister().minimal_search() if idx in x.H().core.features()), None)

    def feature_inheritance(X):
        if X.highest_finite_head():
            X.core.add_features({'!PER'})
        if X.check({'EF?'}):
            X.core.remove_features({'EF?'})
            X.core.add_features({'EF*'})
            if X.selected_by_SEM_internal_predicate():
                X.core.add_features({'-ΦLF'})
        return X

    def check(X, fset):
        return fset <= X.H().core.features()

    def check_some(X, fset):
        return fset & X.H().core.features()

    def get_tail_sets(X):
        return {frozenset(f[5:].split(',')) for f in X.H().core.features() if f[:4] == 'TAIL'}

    def spec_selection(X, W):
        return X.complex() and X.check_some(W.core.specifiers_licensed())

    def comp_selection(X, W):
        return X.zero_level() and W.check_some(X.core.complements_licensed())

    def feature_conflict(X):
        def remove_exclamation(g):
            if g[0] == '!':
                return g[1:]
            else:
                return g
        for f1 in X.core.features():
            if f1 == '*':
                return True
            if f1.startswith('-'):
                for f2 in X.core.features():
                    if f1[1:] == remove_exclamation(f2):
                        log(f'\n\t\tFeature conflict +/{f1}')
                        return True

    def operator_in_scope_position(X):
        """
        An operator in scope position is one which requires Ā-reconstructions
        (1) it must be an operator
        (2) it mut not be copied
        (3) it must not be a scope-marker
        (4) either it is contained in SpecCP or it is a operator predicate
        """
        return 'OP:' in X and not X.copied and 'OP' not in X.core.features() and ((X.container() and X.container().check({'Fin'})) or (X.check({'-insitu'}) and X.check_some({'T/fin', 'C/fin'})))

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
            if antecedent.H().core.referential():
                for P in X.core.valued_phi_at_probe():
                    for A in antecedent.H().core.valued_phi_at_antecedent():
                        if P[1] == A[1] and P[2] != A[2]:
                            return False
                return True

    def control(X):
        unvalued_phi = X.core.get_unvalued_minimal_phi()
        if unvalued_phi & {'PHI:NUM:_', 'PHI:PER:_'} and not X.core.get_valued_phi_types() & {'PHI:NUM', 'PHI:PER'} and not X.check({'PHI:NUM:SG,PER:3'}):
            return X.standard_control()
        elif unvalued_phi & {'PHI:DET:_'}:
            return X.finite_control()

    def standard_control(X):
        search_path = [x for x in takewhile(lambda x: not x.check({'SEM:external'}), X.path())]
        antecedent = next((x for x in search_path if X.is_possible_antecedent(x)), None)
        if not antecedent:
            return PhraseStructure(features={"PF:generic 'one'", 'LF:generic', 'φ', 'D'})
        return antecedent

    def finite_control(X):
        antecedent = X.next(X.path, lambda x: x.complex() and X.is_possible_antecedent(x))
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

    def size(X):
        s = 0
        if not X.copied:
            s = 1
            for x in X.const:
                if x:
                    s += x.size()
        return s

    def attach(X, W):
        X.speaker_model.results.consume_resources('Merge', X, W)
        if X.w_internal() and (PhraseStructure.speaker_model.settings.retrieve('UG_parameter_middle_field_HM', True) or X.check({'C'}) or X.bottom_affix().core.EHM()):
            return X ** W   #   EHM
        return X * W        #   Phrasal Merge (asymmetric)

    def detach(X):
        m = X.M()
        X.mother_ = None
        return X, m

    def copy(X):
        Y = PhraseStructure()
        Y.active_in_syntactic_working_memory = X.active_in_syntactic_working_memory
        Y.adjunct = X.adjunct
        Y.internal = X.internal
        Y.clitic = X.clitic
        Y.identity = X.identity
        Y.copied = X.copied
        Y.phrasal_zero = X.phrasal_zero
        Y.create_constituents([x.copy() for x in X.const])
        Y.core = X.core.copy()
        return Y

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

    def target_left_branch(X, N):
        return X.top().copy()[X.top().get_index(N)]

    # Support ----------------------------------------------------------------------
    def find_constituent_with_index(X, idx, Y):
        if X.core.index() == idx and X != Y:
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
            return self.first_dominating_complex_node().find_constituent_with_index(self.core.index(), self)

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
            lfs = [f[3:] for f in head.core.features() if f and f[:2] == 'LF']
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
        for f in X.core.features():
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
            if cat in head.core.features() and cat:
                return cat + suffix
        return '?' + suffix

    def chaincopy(X, **kwargs):
        def silence_phonologically(h):
            if h.L():
                silence_phonologically(h.L())
            if h.R():
                silence_phonologically(h.R())

        # Externalization may be added to copying
        if kwargs.get('externalize', False):
            X.transfer()
            X.adjunct = True
        X.identity = X.baptize_chain()
        X.create_feature_chain()
        Xc = X.copy()
        X.copied = Xc
        Xc.identity = X.identity
        silence_phonologically(Xc)
        if X.H().core.referential():
            Xc.adjunct = False
        return Xc

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
        if X.core.features() and 'null' in X.core.features() and X.complex():
            if X.adjunct:
                return '<__>' + chain_index_str
            else:
                return '__' + chain_index_str

        # Primitive heads
        if X.zero_level():
            if not X.get_phonological_string():
                return '?'
            elif X.copied:
                return f'(0)'
            return X.get_phonological_string()
        else:
            if X.adjunct:
                return f'<{X.L()} {X.R()}>' + chain_index_str
            else:
                return f'[{X.L()} {X.R()}]' + chain_index_str

    def get_phonological_string(X):
        if len(X.affixes()) == 1 or (X.affix() and X.affix().copied):
            return X.exponent()
        return f'{X.label()}({",".join([x.exponent() for x in X.affixes()[1:]])})'

    def exponent(X):
        stri = ''
        for fset in X.core.feature_bundles():
            stri += "".join([f[3:] for f in fset if f.startswith("PF:")])
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

    def contains_finiteness(X):
        return X.contains_features({'Fin'})

    def predicate(X):
        return X.zero_level() and 'Φ' in X.core

    def semantic_complement(X):
        return X.complement() and not X.core.semantic_match(X.complement().H())

    def selected_by_SEM_internal_predicate(X):
        return X.selector() and X.selector().SEM_internal_predicate()

    def selected_by_SEM_external_predicate(X):
        return X.selector() and X.selector().SEM_external_predicate()

    def isolated_preposition(X):
        return X.core.preposition() and X.sister() and X.sister().zero_level()

    def adjoinable(X):
        return X.complex() and not X.copied and X.H().get_tail_sets() and 'adjoinable' in X.H().core and 'nonadjoinable' not in X.H().core

    def license_scrambling(X):
        return X.adjoinable() and 'nonfloat' not in X.core

    def interpretable_adjunct(X):
        return X.core.referential() and X.max() and X.max().adjunct and X.max().is_R() and X.max().mother_ and X.max().mother_.referential()

    def w_internal(X):
        return X.bottom().bottom_affix().internal

    def phase_head(X):
        return X.zero_level() and X.check_some(PhraseStructure.phase_heads) and not X.check_some(PhraseStructure.phase_heads_exclude)

    def highest_finite_head(X):
        return X.core.finite() and not ['C', 'FORCE'] in X.core and \
               not (X.selector() and ['T', 'COPULA', 'Fin'] not in X.selector().core)

    def theta_marks(X, target):
        if X.sister() == target:
            return X.core.theta_predicate()
        if X.local_edge() == target:
            return X.plus_SPEC({'D', 'φ'})

    def operator_features(X):
        return 'OP:' in X

    def find_node_with_identity(X, identity, start):
        Y = None
        if X != start:
            if X.identity == identity:
                return X
            if X.complex():
                for x in X.const:
                    Y = x.find_node_with_identity(identity, start)
                    if Y:
                        break
        return Y

    def construct_semantic_working_memory(X, intervention_feature, assignment):
        sWM = set()
        for const in (x for x in X.path() if x.H().core.has_idx() and x.H().core.get_idx_tuple('QND') and x.H() != X and not x.copied):
            sWM.add(assignment[const.H().core.get_referential_index('QND')])
            if intervention_feature and not const.copied and {intervention_feature}.issubset(const.H().features):
                break
        return sWM

