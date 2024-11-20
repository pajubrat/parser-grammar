
import itertools
import types
from feature_processing import *
from support import log
from phrase_structure_inner_core import PhraseStructureCore, mismatch


def some(A):
    return list(A)

class PhraseStructure:
    speaker_model = None
    major_cats = ['@', '√', 'n', 'N', 'Neg', 'Neg/fin', 'P', 'D', 'Qn', 'Num', 'φ', 'Top', 'C', 'C/fin', 'a', 'A', 'v', 'V', 'Pass',
                  'VA/inf', 'T', 'Fin', 'Agr', 'A/inf', 'MA/inf', 'ESSA/inf', 'E/inf', 'TUA/inf', 'KSE/inf', 'Inf', 'FORCE', 'EXPL', 'Adv',
                  '0', 'a', 'b', 'c', 'd', 'x', 'y', 'z', 'X', 'Y', 'Z']
    access_experimental_functions = None
    spellout_heads = False      # This parameter, if set true, spells out PF-content of heads in all printouts; otherwise only labels are shown
    phase_heads = {'ph', 'φ'}   # Phase heads set for all calculations
    phase_heads_exclude = set()
    resources = {"Merge-1": {"ms": 0, "n": 0}}
    chain_index = 0
    identity = 0
    cyclic = True
    operations = {'Noncyclic Ā-chain':
                    {'TRIGGER': lambda x: x.operator_in_scope_position() and not PhraseStructure.cyclic,
                     'TARGET': lambda x: x,
                     'TRANSFORM': lambda x, t: x.reconstruct_operator(t)},
                  'Feature inheritance':
                    {'TRIGGER': lambda x: x.zero_level() and x(['φ', 'EF?', 'Fin']),
                     'TARGET': lambda x: x,
                     'TRANSFORM': lambda x, t: x.feature_inheritance()},
                  'A-chain':
                    {'TRIGGER': lambda x: x.core('EPP') and x.is_R() and x.sister().complex() and x.sister()('referential') and 'OP:' not in x.sister() and x.tail_test(
                     tail_sets=x.sister().get_tail_sets(), direction='right', weak_test=True),
                     'TARGET': lambda x: x.sister(),
                     'TRANSFORM': lambda x, t: x * t.chaincopy()},
                  'IHM':
                    {'TRIGGER': lambda x: x.complex_head() and not x.core('EHM'),
                     'TARGET': lambda x: x.affix(),
                     'TRANSFORM': lambda x, t: x.head_reconstruction(t)},
                  'Scrambling':
                      {'TRIGGER': lambda x: x.max().license_scrambling() and (x.container() and x.container().core('EF') and
                                                                              (not x.container().core('theta_predicate') or x.container().core('preposition')) or not x.head().tail_test()) and
                                            x.scrambling_target() and x.scrambling_target() != x.top() and not x.operator_in_scope_position() and PhraseStructure.speaker_model.LF.pass_LF_legibility(x.scrambling_target().copy().transfer(), logging=False) and not PhraseStructure.cyclic,
                       'TARGET': lambda x: x.scrambling_target(),
                       'TRANSFORM': lambda x, t: x.scrambling_reconstruct(t)},
                   'Agree':
                      {'TRIGGER': lambda x: x.is_L() and x.core.features(type=['phi', 'unvalued']),
                       'TARGET': lambda x: x,
                       'TRANSFORM': lambda x, t: x.AgreeLF()}
                       }

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
        self.elliptic = False

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

    def head(X):
        return next((x for x in [X] + X.const if x.zero_level()), X.complex() and X.right_nonadjunct().head())

    def right_nonadjunct(X):
        if X.R().adjunct:
            return X.L()
        return X.R()

    def inside(X, head):
        return X.head() == head

    def container(X):
        if X.M() and X.head() != X.M().head():
            return X.M().head()

    def max(X):
        x = X
        while x.M() and x.M().head() == X.head():
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
        elif X.nn.head() == X.nn.R().head() or X.nn.head().proper_complement():
            X.nn = X.nn.R()
        else:
            X.nn = X.nn.L()
        return current.L()

    def minimal_search(X, **kwargs):
        return itertools.takewhile(lambda x: not kwargs.get('intervention', lambda x: False)(x), (x for x in X))

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
        return list(itertools.takewhile(lambda x: x.M() and x.M().inside(X), X.path()))

    def local_edge(X):
        return next(iter(X.edge()), None)

    def pro_edge(X):
        if X.generate_pro():
            return X.edge() + [X.generate_pro()]
        return X.edge()

    def identify_argument(X):
        arguments = [acquire(X) for acquire in [lambda x: x.generate_pro(),
                                                lambda x: x.complement_argument(),
                                                lambda x: x.indexed_argument(),
                                                lambda x: x.local_edge(),
                                                lambda x: x.control()]]
        return next((x for x in arguments if x), None)

    def complement_argument(X):
        if X.complement() and X.complement()('referential'):
            return X.complement()

    def contains_features(X, fset):
        if X.complex():
            for x in X.const:
                if x.contains_features(fset):
                    return True
        else:
            return X(fset)

    def geometrical_minimal_search(x):
        search_list = [x]
        while x.complex() and x.R():
            search_list.append(x.R())
            x = x.R()
        return search_list

    def predicate_composition(X):
        if X.complement():
            lst = [x for x in X.complement().minimal_search(intervention=lambda x: x.zero_level() and x(['π', 'D', 'φ'])) if x.zero_level()]
            if lst:
                lst = [X] + lst[:-1] + lst[-1].affixes()
            return lst

    def new_focus(X):
        return next((x for x in X.const[::-1] if X.complex() and x.zero_level()), X)

    def reconstruct(X, **kwargs):
        """
        Reconstruction cycle for element X (head or phrase).
        """

        # Get the operations from an input parameter or assume they apply all

        OPs = kwargs.get('operations', PhraseStructure.operations)

        # Apply each operation to X

        for type, calculate in OPs.items():
            if not X.copied and calculate['TRIGGER'](X):
                T = calculate['TARGET'](X)
                if T and not T.copied:
                    log(f'\n\t{type}({T.illustrate()})')
                    X = calculate['TRANSFORM'](X, T).new_focus()
                    log(f'\n\t = {X.top()}')

        return X.top()

    def transfer(X):
        Y, m = X.detach()

        # Reconstruction applies noncyclically during transfer such that
        # each operations applies to the whole structure,
        # and it applies successive-cyclically until no further structure is created (stability)

        for type, calculation in PhraseStructure.operations.items():
            size = 0
            while Y.top().size() != size:   # Apply each operation until there is no size change (stable outcome)
                size = Y.top().size()       # Store size before operations are applied
                for x in Y.bottom().self_path():
                    x.reconstruct(operations={type: calculation})

        return Y.reattach(m)

    # Virtual pronouns --------------------------------------------------------------------------------

    def generate_pro(X):
        if X.predicate() and X.core.overt_phi_sustains_reference():
            return PhraseStructure(features=X.core.features(type=['phi', 'valued']) | {'φ', 'PF:pro'})

    # Selection ---------------------------------------------------------------------------------------

    # -SPEC:L,K

    def minus_SPEC(X, fset):
        return not X.local_edge() or \
               X.local_edge().adjunct or \
               not X.local_edge()(some(fset))

    # +SPEC:L,K

    def plus_SPEC(X, fset):
        return (not X.local_edge() and 'ø' in fset) or \
               (X.local_edge() and X.local_edge()(some(fset)))

    # +COMP:L,K

    def plus_COMP(X, fset):
        return (not X.proper_complement() and 'ø' in fset) or \
               (X.proper_complement() and X.proper_complement()(some(fset)))

    # -COMP:L,K

    def minus_COMP(X, fset):
        return not X.proper_complement() or \
               not X.proper_complement()(some(fset))

    # -SELF

    def minus_SELF(X, fset):
        return not X(some(fset))

    # +SELF

    def plus_SELF(X, fset):
        return X(some(fset))

    # =SELF

    def conjunctive_minus_SELF(X, fset):
        return not X(fset)

    def w_selection(X):
        for f in X.core.features():
            if f.startswith('!wCOMP:') and not X.affix()(set(f.split(':')[1].split(','))):
                return True
            elif f.startswith('-wCOMP:') and X.affix()(f.split(':')[1].split(',')):
                return True

    def spec_selection(X, W):
        return X.complex() and X(some(W.core.features(type=['+SPEC'], format='licensed')))

    def comp_selection(X, W):
        return X.zero_level() and W(some(X.core.features(type=['+COMP'], format='licensed')))

    def complex_head_integrity(X):
        """Tests whether a complex head satisfies conditions of the UG"""

        if X.affix():
            x = X
            while x.affix():
                if x.w_selection() and PhraseStructure.speaker_model.settings.retrieve('w_selection', True):
                    return True
                if PhraseStructure.speaker_model.settings.retrieve('epsilon', True):
                    if x.affix().copied:
                        return x('EHM')      # [ε] blocks IHM
                    else:
                        if not x('EHM'):     # [ε] licenses EHM
                            return True
                x = x.affix()

    def probe_goal_test(X):
        if X.sister():
            for ff in [(f, X.probe(f[7:])) for f in X.core.features(match=['PROBE:'])]:
                if (ff[0].startswith('!') and not ff[1]) or (ff[0].startswith('-') and ff[1]):
                    return True

    def probe(X, G):
        return next((x for x in X.sister() if x({G})), None)

    def core_integrity(X):
        return X.core.integrity()

    # Projection principle ---------------------------------------------------------------------

    def projection_principle_failure(X):
        """Tests if there are referential arguments that do not receive theta roles"""

        if X.max() != X.top() and X.projection_principle_applies():
            return not X.max().gets_theta_role_from(X.max().container()) or X.pro_projection_principle_violation()

    def projection_principle_applies(X):
        return X.core('referential') and X.max().M() and not X.max().contains_features({'SEM:nonreferential'})

    def pro_projection_principle_violation(X):
        if X.zero_level() and X.core.overt_phi_sustains_reference() and X.right_sister():
            for x in X.right_sister().minimal_search(intervention=lambda y: y.core('theta_predicate') and y.core('verbal')):
                if x.zero_level():
                    if x.core.overt_phi_sustains_reference():
                        return True
                    if x.core('nonthematic_verb'):
                        if X.core('AgreeLF_occurred') or 'nonreferential_pro' not in X.core:
                            return True

    def gets_theta_role_from(Xmax, C):

        # C assigns theta-role to SPEC

        if Xmax == C.local_edge() and C.core('thetaSPEC'):
            return True

        # C assigns theta-role to COMP

        if Xmax == C.complement() and C.core('thetaCOMP'):
            return True

        # If neither above is true, C can assign theta-role to left sister iff it is not EF-head

        if Xmax == C.sister() and C.core('thetaCOMP') and not C.core('EF'):
            return True

    def unrecognized_label(X):
        return X.core('unrecognized_label')

    def scan_feature(X, feature):
        if X.copied:
            return X.copied.scan_feature(feature)
        elif X.zero_level():
            if X.core.features(match=['$'+feature]):
                return True
        else:
            for x in X.const:
                if x.scan_feature(feature):
                    return True

    @staticmethod
    def baptize_chain():
        PhraseStructure.chain_index += 1
        return str(PhraseStructure.chain_index)

    def create_feature_chain(X):
        if X.scan_strong_features():
            X.local_container().core.add_features(PhraseStructure.speaker_model.lexicon.lexical_redundancy(X.scan_strong_features()))

    def local_container(X):

        # Local container of zero-level X is:

        if X.zero_level():
            if X.M().zero_level():      # (1) Y if Y(X...)
                return X.M()
            M = X.M()                   # otherwise (2) create Y such that Y(X...)
            return M.create_constituents([PhraseStructure(features={'C', 'C/fin', 'Fin', 'PF:C', 'LF:C', 'OP'}) ** X, M.R()]).L()

        else:

            # Local container of XP is:

            if X.container() and X.container().local_edge() == X:
                return X.container()    # (1) Y if [XP [Y..]]
            # otherwise (2) create Y such that [XP [Y...]]
            return (PhraseStructure(features={'C', 'C/fin', 'PF:C', 'LF:C', 'Fin', 'EF'}) * X.sister()).L()

    def scan_strong_features(X):
        fset = X.core.features(type=['strong'])
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
            if T.zero_level() and T.core('finite') and not (T.selector() and T.selector().core('finite_C')):

                #   Sentence operator, null head, V2

                T = X.chaincopy()
                if x.complex():
                    return T * x.sister()       # [T [XP [T' YP]]], XP = x
                return T * x                    # [T [T' [K YP]]], K = x

            # Found a position where tail tests succeed

            if x.tail_test(tails_sets=T.get_tail_sets()):

                if T.complex():

                    # New SPEC

                    if not x.local_edge() and T(some(x.core.get_selection_features('+SPEC'))):
                        if x.is_R():
                            return T.chaincopy() * x
                        return T.chaincopy() * x.M()

                    # New COMP

                    if T(some(x.core.get_selection_features('+COMP'))):     # (2.1) No complement = [T....[x T']]
                        if not x.complement():
                            return x * T.chaincopy()

                elif T.zero_level():

                    # LHM

                    if T(some(x.core.get_selection_features('+COMP'))):
                        return T.chaincopy() * x.sister()
        return X

    def head_reconstruction(X, T):
        if PhraseStructure.cyclic:
            if not X.is_L():    # X is right or isolated = cyclic IHM
                if not ('OP:' in X and '-insitu' in X and 'TAM' in X):   #   Block cyclic IHM for fronted verbs with operator, must be reconstructed later
                    return X * T.chaincopy()
                return X
            else:   # X is left, special case of A-chain + IHM
                return X.sister() * T.chaincopy()
        else:
            return T.chaincopy() * X.sister()

    # Scrambling ==========================================================================

    def tail_fit(X, Y, direction='left'):
        return X.tail_test(tail_sets=Y.head().get_tail_sets(),
                           weak_test=Y.head().core('referential') or Y('preposition'),
                           direction=direction)

    def scrambling_reconstruct(XP, YP):
        """
        Reconstructs scrambled phrases.
        XP = the original phrase which was marked for scrambling.
        YP = target (may contain additional material such as Specs)
        """

        YP.transfer()
        YP.adjunct = True

        # In situ scrambling: if the externalized XP is in correct position, leave it there

        if XP('adverbial') or XP('preposition'):
            weak_test = False
        else:
            weak_test = True
        if XP.tail_test(weak_test=weak_test) and not (XP.container() and XP.container().core('EF')):
            return XP.top()

        O = YP
        Spec = O in O.container().edge()
        YP = YP.chaincopy()

        # Search for a new position

        for x in XP.local_tense_edge().minimal_search(intervention=lambda x: 'φ' in x.core or x == XP.head()):

            # Specifier positions

            if x.tail_fit(YP) and YP.spec_selection(x):
                if O.max().container() == x and Spec:
                    continue
                if x.is_L():
                    return YP * x.M()    #   [a X(P)] = [YP [a X(P)]]
                return YP * x            #   [X(P) a] = [X(P) [YP a]]

            # Complement positions

            if x.zero_level() and not x.proper_complement() and x.tail_fit(YP, 'right') and x.comp_selection(YP):
                return x * YP            #   [X(P) a] = [X(P) [a YP]] or [a <XP>] = [[a YP] <XP>]

        O.copied = False
        O.identity = 0
        return XP.top()     # If nothing is found, do nothing

    def local_tense_edge(X):
        return next((X.M() for X in X.path() if X.core('finite') or X.core('force')), X.top())

    def scrambling_target(X):
        """
        Returns the phrase to be scrambled. Heads H which must or may have
        specifiers will return [SPEC + HP] if SPEC is present (Condition 1); otherwise HP (Condition 2)
        """

        if X('EF') and X.head().local_edge() and not X.head().local_edge()(['T', 'V']):
            return X.head().local_edge().M()   # Condition 1
        return X.head().M()                    # Condition 2

    # Agreement ---------------------------------------------------------------------------------------------

    def AgreeLF(X):
        return X.Agree(X.get_goal())

    def Agree(X, goal):
        if len(X.core.features(type=['phi', 'unvalued'])) > 0 and goal:
            if not goal.head().core.feature_mismatch_test(X.core.phi_bundles()):
                X.core.value(goal)
            else:
                log(f' FEATURE MISMATCH {goal.head().core.feature_mismatch_test(X.core.phi_bundles())}')
                X.core.add_features({'*'})
        else:
            log(f' did not find suitable goal.')
        return X

    def get_goal(X):
        return next((x for x in X.minimal_search_domain().minimal_search(intervention=lambda x: x.phase_head()) if x.goal_selection()), None)

    def goal_selection(X):
        return not X.copied and (X('referential') or X.phase_head())

    def EPP_violation(X):
        """
        Current implementation of the Agree/EPP system, tested as LF-legibility
        """

        # Rule out stacking of non-adjunct constituents into the edge
        # e.g.,  base-generated '[_TP towards Paris [_TP Seine [T flows]]]'
        # Questionable whether this filter exists, requires careful consideration
        # Adjuncts can be stacked

        if len([x for x in X.edge() if not x.adjunct]) > 1:
            return True

        if not X(['ASP', 'strong_pro']):                                     #   Amnesty for strong pro, theta heads and C/fin
            if not X.core('EF'):                                            #   If X does not have EF,
                return X.local_edge() and not X.core('thematic_edge')             #   it cannot have nonthematic edge element
            if X({'-ΦPF'}) or not X.core('EPP'):                              #   Amnesty for non-agreeing heads and heads without EPP
                return False
            if X({'weak_pro'}):                                           #   Secondary rule:
                return X({'ΦLF'}) and not X.local_edge()                   #       If Agree(X, Y), SpecXP cannot be empty
            if X({'ΦLF'}):                                                #   Primary rule:
                return not X.primary_rule()                                 #       If Agree(X, Y), YP = SpecXP
            # If Agree(X, Y) does not occur, then violation can be avoided if X is specifically marked to not require Agree
            # or there is phi-consistent overt agreement suffices at X
            elif not X(['?ΦLF', '-ΦLF']) and not (X({'ΦPF'}) and X.core.phi_consistent()):
                return True

    def primary_rule(X):
        return X.local_edge() and X.indexed_argument() and X.local_edge().head().core.get_id() == X.indexed_argument().head().core.get_id()

    def indexed_argument(X):
        idx = next(iter(X.core.features(type=['phi_index'], format='only_value')), None)
        if idx and X.sister():
            return next((x.max() for x in X.sister().minimal_search() if x({idx})), None)

    def feature_inheritance(X):
        if X.highest_finite_head() and not X({'!PER'}):
            X.core.add_features({'!PER'})
        if X({'EF?'}):
            X.core.remove_features({'EF?'})
            X.core.add_features({'EF*'})
            if X.selected_by_SEM_internal_predicate():
                X.core.add_features({'-ΦLF'})
        if X({'φ'}) and X.complement():
            X.core.add_features(X.complement().head().core.features(type=['phi', 'interpretable']))
            X.core.add_features(X.complement().head().core.get_R_features())
        return X

    def get_tail_sets(X):
        return {frozenset(f[5:].split(',')) for f in X.head().core.features() if f.startswith('TAIL:')}

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
        (2) it must not be a scope-marker
        (3) either it is contained in SpecCP or it is a operator predicate
        """
        return 'OP:' in X and 'OP' not in X.core.features() and '-insitu' in X and \
               ((X.container() and X.container()({'Fin'})) or (X({'-insitu'}) and X(['TAM', 'C/fin', 'Neg/fin'])))

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
            for x in context:
                if x(some(tail_set)):
                    return x(tail_set)
        else:
            return X.check_container(tail_set) or X.check_aunt(tail_set)

    def check_container(X, tset):
        return X.max().container() and X.max().container()(tset)

    def check_aunt(X, tset):
        return X.max().M() and \
               X.max().M().sister() and \
               X.max().M().sister()(tset)

    # Control ---------------------------------------------------------------------------------------------------

    def control(X):
        last_resort = None
        if not X.core('overt_phi'):
            last_resort = PhraseStructure(features={"PF:one", 'LF:generic', 'φ', 'D'})
        return next((y for y in X.path() if y('referential') and not mismatch(X.phi_set(), y.head().phi_set())), last_resort)

    def phi_set(X):
        return X.core.features(type=['phi', 'valued'], format='reduced', match={'NUM:', 'PER:', '^,'})

    # Structure building --------------------------------------------------------------------------

    def __add__(X, Y):

        # Standard bare Merge

        return PhraseStructure(X, Y)

    def __mul__(X, Y):

        # Insert Merge (i.e. Merge-1)

        X.consume_resources('Merge-1', X)
        if X.M():
            return X.insert(Y, 'right')
        elif Y.M():
            return Y.insert(X, 'left')
        return X + Y

    def insert(Xa, Y, dir=''):
        if Xa.is_L():
            return Xa.M().insert_left(Xa.Merge(Y, dir))
        elif Xa.is_R():
            return Xa.M().insert_right(Xa.Merge(Y, dir))
        return Xa.Merge(Y, dir)

    def Merge(X, Y, dir):
        if dir == 'left':
            return Y + X
        return X + Y

    def insert_left(X, Y):
        return X.create_constituents([Y, X.R()]).L()

    def insert_right(X, Y):
        return X.create_constituents([X.L(), Y]).R()

    def __pow__(X, Y):

        # Head merge (HM)

        return X.affixes()[-1].create_constituents([Y])

    def __contains__(X, f):
        return X.scan_feature(f)

    def __call__(X, t, **kwargs):
        # todo this function should be generalized so that it also performs minimal and path searches through the sWM

        if isinstance(t, str) and X.head().core(t):
            return X.head()
        if (isinstance(t, set) or isinstance(t, frozenset)) and t <= X.head().core.features():
            return X.head()
        if isinstance(t, list) and set(t) & X.head().core.features():
            return X.head()
        if isinstance(t, types.FunctionType) and t(X.head()):
            return X.head()

    def size(X):
        s = 1
        for x in X.const:
            if x:
                s += x.size()
        return s

    def attach(X, W):
        X.speaker_model.results.consume_resources('Merge', X, W)
        if X.w_internal() or X({'C'}) or X.bottom_affix()('EHM'):
            return X ** W   #   EHM
        return X * W        #   Phrasal Merge (asymmetric)

    def detach(X):
        m = X.M()
        X.mother_ = None
        return X, m

    def copy_(X):
        Y = PhraseStructure()
        Y.core = X.core.copy()
        Y.active_in_syntactic_working_memory = X.active_in_syntactic_working_memory
        Y.adjunct = X.adjunct
        Y.internal = X.internal
        Y.clitic = X.clitic
        Y.identity = X.identity
        Y.copied = X.copied
        Y.elliptic = X.elliptic
        Y.phrasal_zero = X.phrasal_zero
        Y.create_constituents([x.copy_() for x in X.const])
        return Y

    def copy(X):
        return X.copy_().update_copied_chains()

    def update_copied_chains(X):
        if X.copied:
            X.copied = X.top().find_constituent_with_identity(X, X.identity)
        if X.complex:
            for x in X.const:
                x.update_copied_chains()
        return X

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

    def target_left_branch_and_copy(X, N):
        return X.top().copy()[X.top().get_index(N)]

    # Support ----------------------------------------------------------------------

    def first_dominating_complex_node(X):
        while X.M():
            if not X.M().zero_level() and not X.M().phrasal_zero and X.is_L():
                return X.sister()
            X = X.M()

    def find_constituent_with_identity(X, Y, identity):
        if X.identity == identity and X != Y:
            return X
        if X.complex():
            for x in X.const:
                const = x.find_constituent_with_identity(Y, identity)
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
        head = X.head()
        if X.complex():
            suffix = 'P'
        else:
            suffix = ''
        for cat in PhraseStructure.major_cats:
            if cat in head.core.features() and cat:
                return cat + suffix
        return '?' + suffix

    def chaincopy(X):
        X.identity = X.baptize_chain()
        X.create_feature_chain()
        Xc = X.copy()
        X.copied = Xc
        Xc.identity = X.identity
        Xc.elliptic = True
        if X.head().core('referential'):
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

        if X.elliptic and X.complex():
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

    def predicate(X):
        return X.zero_level() and X('predicate')

    def semantic_complement(X):
        return X.complement() and not X.core.semantic_match(X.complement().head())

    def selected_by_SEM_internal_predicate(X):
        return X.selector() and X.selector()('SEM_internal_predicate')

    def selected_by_SEM_external_predicate(X):
        return X.selector() and X.selector()('SEM_external_predicate')

    def adjoinable(X):
        return X.complex() and X.head().get_tail_sets() and X('adjoinable') and not X('nonadjoinable')

    def license_scrambling(X):
        return X.adjoinable() and not X('nonfloat')

    def interpretable_adjunct(X):
        return X.core('referential') and X.max() and X.max().adjunct and X.max().is_R() and X.max().mother_ and X.max().mother_.core('referential')

    def w_internal(X):
        return X.bottom().bottom_affix().internal

    def phase_head(X):
        return X.zero_level() and X(some(PhraseStructure.phase_heads)) and not X(some(PhraseStructure.phase_heads_exclude))

    def highest_finite_head(X):
        return X.core('finite') and not ['C', 'FORCE', 'T/prt'] in X.core and \
               not (X.selector() and ['T', 'COPULA', 'Fin'] not in X.selector().core)

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
        for const in (x for x in X.path() if x.head().core.has_idx() and x.head().core.get_idx_tuple('QND') and x.head() != X and not x.copied):
            sWM.add(assignment[const.head().core.get_referential_index('QND')])
            if intervention_feature and not const.copied and {intervention_feature}.issubset(const.head().core.features()):
                break
        return sWM
