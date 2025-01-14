import sys
from feature_processing import *
from support import log, set_logging
from phrase_structure_inner_core import PhraseStructureCore, mismatch


def some(A):
    return list(A)

class PhraseStructure:
    speaker_model = None
    major_cats = ['@', '√', 'n', 'N', 'Neg', 'Neg/fin', 'P', 'D', 'Qn', 'Num', 'φ', 'Top', 'C', 'C/fin', 'a', 'A', 'v', 'V', 'Pass',
                  'VA/inf', 'T', 'Fin', 'Agr', 'A/inf', 'MA/inf', 'ESSA/inf', 'E/inf', 'TUA/inf', 'KSE/inf', 'Inf', 'FORCE', 'EXPL', 'Adv',
                  '0', 'a', 'b', 'c', 'd', 'x', 'y', 'z', 'X', 'Y', 'Z']
    access_experimental_functions = None
    phase_heads = {'ph', 'φ'}   # Phase heads set for all calculations
    phase_heads_exclude = set()
    resources = {"Merge-1": {"ms": 0, "n": 0}}
    chain_index = 0             # Provides chain indexes in increasing order when creating chains
    identity = 0                # Each constituent has an identity, but copies share the identity
    cyclic = True               # When true, the engine is in cyclic calculations mode (i.e. still consuming input words)

    # Reconstruction operations are defined in this table
    # TRIGGER = what triggers the operation
    # TARGET = the target of the operation (e.g., Spec for some triggering EPP head)
    # TRANSFORM = the operation itself
    # todo these should be simplified and ultimately synthesized into just one function

    operations = {'Noncyclic Ā-chain':
                    {'TRIGGER': lambda x: x.operator_in_scope_position() and
                                          not PhraseStructure.cyclic,
                     'TARGET': lambda x: x,
                     'TRANSFORM': lambda x, t: x.reconstruct_operator(t)},
                  'Feature inheritance':
                    {'TRIGGER': lambda x: x.zero_level() and x.INT(['φ', 'EF?', 'Fin']),
                     'TARGET': lambda x: x,
                     'TRANSFORM': lambda x, t: x.feature_inheritance()},
                  'A-chain':
                    {'TRIGGER': lambda x: x.core('EPP') and
                                          x.is_R() and x.sister() and x.sister().complex() and
                                          x.sister().INT('referential') and not x.sister().INT('operator', scan=True) and
                                          x.tail_test(tail_sets=x.sister().get_tail_sets(), direction='right', weak_test=True),
                     'TARGET': lambda x: x.sister().chaincopy(),
                     'TRANSFORM': lambda x, t: x * t},
                  'IHM':
                    {'TRIGGER': lambda x: x.complex_head() and not x.core('EHM'),
                     'TARGET': lambda x: x.affix(),
                     'TRANSFORM': lambda x, t: x.head_reconstruction(t)},
                  'Scrambling':
                      {'TRIGGER': lambda x: x.max().license_scrambling() and
                                            (x.container() and x.container().core('EF') and
                                             (not x.container().core('theta_predicate') or x.container().core('preposition')) or
                                             not x.head().tail_test()) and x.scrambling_target() and
                                            x.scrambling_target() != x.top() and not x.operator_in_scope_position() and
                                            PhraseStructure.speaker_model.LF.pass_LF_legibility(x.scrambling_target().copy().transfer(), logging=False) and
                                            not PhraseStructure.cyclic,
                       'TARGET': lambda x: x.scrambling_target(),
                       'TRANSFORM': lambda x, t: x.scrambling_reconstruct(t)},
                  'Agree':
                      {'TRIGGER': lambda x: x.sister() and x.is_L() and x.core.features(type=['phi', 'unvalued']),
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

        self.adjunct = False
        self.copied = None
        self.identity = 0
        self.internal = False
        self.clitic = False
        self.elliptic = False
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
        X.const = [x.set_mother(X) for x in lst]
        return X

    def set_mother(X, mother):
        X.mother_ = mother
        return X

    def terminal(X):
        return not X.const

    def complex(X):
        return len(X.const) > 1

    def zero_level(X):
        return len(X.const) < 2

    def is_L(X):
        return X.M() and X.M().L() == X

    def is_R(X):
        return X.M() and X.M().R() == X

    def head(X):
        return X.INT()

    def complex_head(X):
        return len(X.affixes()) > 1

    def bottom(X):
        return X.top().collect_sWM()[-1]

    def max(X):
        return X.EXT(domain='max', self=True, acquire='maximal')

    def top(X):
        return X.EXT(self=True, acquire='maximal')

    def get_right_edge_index(X, target):
        for i, node in enumerate(X.collect_sWM(geometrical=True, self=True)):
            if target == node:
                return i

    def inside(X, head):
        return X.head() == head

    def geometrical_sister(X):
        return X.EXT()

    def sister(X):
        return X.EXT(criteria=lambda x: not x.adjunct)

    def complement(X):
        return X.EXT(domain='max')

    def proper_complement(X):
        return X.EXT(domain='max', criteria=lambda x: x.is_R())

    def specifier(X):
        return X.EXT(domain='max', criteria=lambda x: x.is_L())

    def extract_affix(X):
        affix = X.affix()
        X.const = []
        return affix

    def affix(X):
        if X.L() == X.R():
            return X.L()

    def affixes(X):
        return X.collect_sWM(affixes=True)

    def bottom_affix(X):
        return X.collect_sWM(affixes=True, intervention=lambda x: x.copied)[-1]

    # Paths -----------------------------------------------------------------------------

    def EXT(X, **kwargs):
        return X.external_search_path(**kwargs)

    def external_search_path(X, **kwargs):

        # Default values and preparations

        x = X
        y = None
        collection = []
        intervention = kwargs.get('intervention', lambda x: False)  # default value for domain is "top"
        if kwargs.get('domain') == 'max':
            intervention = lambda x: x.M().head() != x.head()
        criteria = kwargs.get('criteria', lambda x: True)           # default value for criteria is "everything"
        if kwargs.get('self', False):
            collection.append(X)

        # Upward path

        while x.M() and not intervention(x):
            y = x
            x = x.M()
            for z in x.const:
                if z != y and criteria(z) and not (z.is_R() and z.adjunct):
                    collection.append(z)

        # Return

        if kwargs.get('acquire', 'minimal') == 'minimal':
            return next(iter(collection), None)
        if kwargs.get('acquire') == 'maximal':
            return x
        return collection

    def INT(X, target_seed=None, **kwargs):

        # If there are no arguments, use defaults

        if len(kwargs) == 0:
            kwargs['criteria'] = lambda x: x.zero_level()
            if isinstance(target_seed, str):
                kwargs['intervention'] = lambda x: x.zero_level()

        return X.internal_search_path(NodePicture(target_seed,
                                                  criteria=kwargs.get('criteria', lambda x: True)),
                                      **kwargs)

    def internal_search_path(X, NodePic=None, **kwargs):

        # Collect

        if kwargs.get('collect', False):
            if kwargs.get('geometrical', False):
                PhraseStructure.speaker_model.syntactic_working_memory.append(X)
            else:
                if X.complex():
                    PhraseStructure.speaker_model.syntactic_working_memory.append(X.L())
                else:
                    PhraseStructure.speaker_model.syntactic_working_memory.append(X)

        # Match

        if X.match(NodePic):
            return X

        if X.complex() and X.L().match(NodePic):
            return X.L()

        # Continue search (either X is complex OR we search inside complex heads)

        if X.complex() or (X.affix() and kwargs.get('affixes', False)):

            # Intervention

            if kwargs.get('intervention', lambda x: False)(X.L()) or \
                    kwargs.get('intervention', lambda x: False)(X):
                return

            # Scan

            if kwargs.get('scan'):

                if kwargs.get('scan', False):
                    Y = X.L().internal_search_path(NodePic, **kwargs)
                    if Y:
                        return Y
                    return X.R().internal_search_path(NodePic, **kwargs)

            # Minimal search

            else:

                # Geometrical search

                if kwargs.get('geometrical', False):
                    return X.R().internal_search_path(NodePic, **kwargs)

                # Non-geometrical search

                if not X.R().adjunct:
                    return X.R().internal_search_path(NodePic, **kwargs)
                else:
                    return X.L().internal_search_path(NodePic, **kwargs)

    def container(X):
        if X.M() and X.head() != X.M().head():
            return X.M().head()

    # Argument identification --------------------------------------------------------------------------------

    def identify_argument(X):
        arguments = [acquire(X) for acquire in [lambda x: x.generate_pro(),
                                                lambda x: x.complement() and x.complement().INT('referential'),
                                                lambda x: x.indexed_argument(),
                                                lambda x: x.specifier(),
                                                lambda x: x.control()]]
        return next((x for x in arguments if x), None)

    def generate_pro(X):
        if X.core('predicate') and X.core.overt_phi_sustains_reference():
            return PhraseStructure(features=X.core.features(type=['phi', 'valued']) | {'φ', 'PF:pro'})

    def predicate_composition(X):
        if X.complement():
            lst = X.complement().collect_sWM(criteria=lambda x: x.zero_level(), intervention=lambda x: x.zero_level() and x(['π', 'D', 'φ']))
            if lst:
                lst = [X] + lst[:-1] + lst[-1].affixes()
            return lst

    # Discontinuous constituents -----------------------------------------------------------------------------------------

    def match(X, NodePic):
        return NodePic.criteria(X) and X.core(NodePic.feature_abstraction) and NodePic.conj <= X.core.features() and (len(NodePic.disj) == 0 or NodePic.disj & X.core.features())

    def collect_sWM(X, T=None, **kwargs):
        PhraseStructure.speaker_model.clean_syntactic_working_memory()
        if kwargs.get('self', False):
            PhraseStructure.speaker_model.add_item_to_syntactic_working_memory(X)
        kwargs['criteria'] = kwargs.get('criteria', lambda x: False)            # Default value
        kwargs['intervention'] = kwargs.get('intervention', lambda x: False)    # Default value
        X.INT(T, collect=True, **kwargs)
        return PhraseStructure.speaker_model.read_syntactic_working_memory()

    # Reconstruct -------------------------------------------------------------------------------------------

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
            while Y.top().size() != size:           # Apply each operation until there is no size change (stable outcome)
                size = Y.top().size()               # Store size before operations are applied
                for x in Y.bottom().EXT(acquire='all', self=True):
                    x.reconstruct(operations={type: calculation})
        return Y.reattach(m)

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

            if X.container() and X.container().specifier() == X:
                return X.container()    # (1) Y if [XP [Y..]]
            # otherwise (2) create Y such that [XP [Y...]]
            return (PhraseStructure(features={'C', 'C/fin', 'PF:C', 'LF:C', 'Fin', 'EF'}) * X.sister()).L()

    def scan_strong_features(X):
        T = X.INT('strong_features', scan=True)
        if T:
            return {x[2:] for x in T.core('strong_features')}

    def chaincopy(X):
        if X.identity == 0:
            X.identity = X.baptize_chain()
        X.create_feature_chain()
        Xc = X.copy()
        X.copied = Xc
        Xc.identity = X.identity
        Xc.elliptic = True
        if X.head().core('referential'):
            Xc.adjunct = False
        return Xc

    def update_copied_chains(X):
        if X.copied:
            X.copied = X.top().find_constituent_with_identity(X, X.identity)
        if X.complex:
            for x in X.const:
                x.update_copied_chains()
        return X

    # Selection ---------------------------------------------------------------------------------------

    def spec_selection(X, W):
        return X.complex() and X.INT(some(W.core.features(type=['+SPEC'], format='licensed')))

    def comp_selection(X, W):
        return X.zero_level() and W.INT(some(X.core.features(type=['+COMP'], format='licensed')))

    def minus_SPEC(X, fset):
        Y = X.specifier()
        return not Y or not Y.head().INT(some(fset))

    def plus_SPEC(X, fset):
        Y = X.specifier()
        return (not Y and 'ø' in fset) or (Y and Y.head().INT(some(fset)))

    def plus_COMP(X, fset):
        Y = X.proper_complement()
        return (not Y and 'ø' in fset) or (Y and Y.head().INT(some(fset)))

    def minus_COMP(X, fset):
        Y = X.proper_complement()
        return not Y or not Y.head().INT(some(fset))

    def minus_SELF(X, fset):
        return not X.INT(some(fset))

    def plus_SELF(X, fset):
        return X.INT(some(fset))

    def conjunctive_minus_SELF(X, fset):
        return not X.INT(fset)

    def semantic_selection(X):
        return X.complement() and not X.core.semantic_match(X.complement().head())

    def probe_goal_test(X):
        if X.sister():
            for ff in [(f, X.probe(f[7:])) for f in X.core.features(match=['PROBE:'])]:
                if (ff[0].startswith('+') and not ff[1]) or (ff[0].startswith('-') and ff[1]):
                    return True

    def probe(X, G):
        return X.sister().INT(criteria=lambda x: x.zero_level() and x.INT({G}),
                              intervention=lambda x: x.INT('finite_C'))

    # Word-internal selection properties

    def w_selection(X):
        for f in X.core.features():
            if f.startswith('+wCOMP:') and not X.affix()(set(f.split(':')[1].split(','))):
                return True
            elif f.startswith('-wCOMP:') and X.affix()(f.split(':')[1].split(',')):
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
                        return x.INT('EHM')      # [ε] blocks IHM
                    else:
                        if not x.INT('EHM'):     # [ε] licenses EHM
                            return True
                x = x.affix()

    def core_integrity(X):
        return X.core.integrity()

    def unrecognized_label(X):
        return X.INT('unrecognized_label')

    # Projection principle ---------------------------------------------------------------------

    def projection_principle_failure(X):
        """Tests if there are referential arguments that do not receive theta roles"""

        if X.max() != X.top() and X.projection_principle_applies():
            return not X.max().gets_theta_role_from(X.max().container()) or X.pro_projection_principle_violation()

    def projection_principle_applies(X):
        return X.core('referential') and X.max() and not X.max().INT('nonreferential', scan=True)

    def pro_projection_principle_violation(X):
        if X.zero_level() and X.core.overt_phi_sustains_reference() and X.complement():
            return X.complement()(criteria=lambda y: y.zero_level() and
                                                     y.core.overt_phi_sustains_reference(), intervention=lambda y: y('theta_predicate') and
                                                                                                                   y('verbal'))

    def gets_theta_role_from(Xmax, Y):

        # Y assigns theta-role to SPEC

        if Xmax == Y.specifier() and Y.INT('thetaSPEC'):
            return True

        # Y assigns theta-role to COMP

        if Xmax == Y.proper_complement() and Y.INT('thetaCOMP'):
            return True

        # If neither above is true, Y can assign theta-role to left sister iff it is not EF-head

        if Xmax == Y.sister() and Y.INT('thetaCOMP') and not Y.INT('EF'):
            return True

    # Ā-Chain creation =====================================================================

    def reconstruct_operator(X, T):
        for x in X.sister().collect_sWM(intervention=lambda x: x.zero_level() and x.INT('referential')):
            if T.zero_level() and \
                    T.INT('finite') and \
                    not T.EXT(criteria=lambda x: x.zero_level() and x.INT('finite_C')):

                #   Sentence operator, null head, V2

                T = X.chaincopy()
                if x.complex():
                    return T * x.sister()       # [T [XP [T' YP]]], XP = x
                return T * x                    # [T [T' [K YP]]], K = x

            # Found a position where tail tests succeed

            if x.tail_test(tails_sets=T.get_tail_sets()) and x.zero_level():

                if T.complex():

                    # New SPEC

                    if not x.specifier() and T.INT(some(x.core.get_selection_features('+SPEC'))):
                        if x.is_R():
                            return T.chaincopy() * x
                        return T.chaincopy() * x.M()

                    # New COMP

                    if T.INT(some(x.core.get_selection_features('+COMP'))):     # (2.1) No complement = [T....[x T']]
                        if not x.complement():
                            return x * T.chaincopy()

                elif T.zero_level():

                    # LHM

                    if T.INT(some(x.core.get_selection_features('+COMP'))):
                        return T.chaincopy() * x.sister()
        return X

    def head_reconstruction(X, T):
        if PhraseStructure.cyclic:
            if not X.is_L():    # X is right or isolated = cyclic IHM
                if not (X.INT('operator', criteria=lambda x: True, intervention=lambda x: False, scan=True) and
                        X.INT('-insitu', criteria=lambda x: True, intervention=lambda x: False, scan=True) and
                        X.INT('TAM', criteria=lambda x: True, intervention=lambda x: False, scan=True)):   #   Block cyclic IHM for fronted verbs with operator, must be reconstructed later
                    return X * T.chaincopy()
                return X
            else:   # X is left, special case of A-chain + IHM')
                return X.sister() * T.chaincopy()
        else:
            return T.chaincopy() * X.sister()

    # Scrambling ==========================================================================

    def tail_fit(X, Y, direction='left'):
        return X.tail_test(tail_sets=Y.head().get_tail_sets(), weak_test=Y.head().core('referential') or Y.INT('preposition'), direction=direction)

    def scrambling_reconstruct(XP, YP):
        """
        Reconstructs scrambled phrases.
        XP = the original phrase which was marked for scrambling.
        YP = target (may contain additional material such as Specs)
        """
        set_logging(False)
        YP.transfer()
        set_logging(True)
        YP.adjunct = True

        # In situ scrambling: if the externalized XP is in correct position, leave it there

        if XP.INT('adverbial') or XP.INT('preposition'):
            weak_test = False
        else:
            weak_test = True
        if XP.tail_test(weak_test=weak_test) and not (XP.container() and XP.container().INT('EF')):
            return XP.head().top()

        O = YP
        if O.container():
            Spec = O in O.container().EXT(acquire='all', domain='max')
        else:
            Spec = None
        YP = YP.chaincopy()

        # Search for a new position

        for x in XP.local_tense_edge().collect_sWM(intervention=lambda x: 'φ' in x.core or x == XP.head()):

            # Specifier positions

            if x.zero_level() and x.tail_fit(YP) and YP.spec_selection(x):
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
        return XP.head().top()     # If nothing is found, do nothing

    def local_tense_edge(X):
        if X.EXT(criteria=lambda x: x.M() and x.core('finite')):
            return X.EXT(criteria=lambda x: x.M() and x.core('finite')).M()
        return X.top()

    def scrambling_target(X):
        """
        Returns the phrase to be scrambled. Heads H which must or may have
        specifiers will return [SPEC + HP] if SPEC is present (Condition 1); otherwise HP (Condition 2)
        """

        if X.INT('EF') and X.head().specifier() and not X.head().specifier().INT(['T', 'V']):
            return X.head().specifier().M()   # Condition 1
        return X.head().M()                    # Condition 2

    def license_scrambling(X):
        return X.complex() and X.head().get_tail_sets() and X.INT('adjoinable') and not X.INT('nonadjoinable') and not X.INT('nonfloat')

    def AgreeLF(X):
        return X.Agree(X.get_goal())

    def Agree(X, goal):

        # Agreement is executed if the probe has unvalued phi-features and there is a goal

        if len(X.core.features(type=['phi', 'unvalued'])) > 0 and goal:

            # Valuation is possible if there are no phi-feature mismatches between the probe and goal
            # This handles standard agreement errors

            if not goal.head().core.feature_mismatch_test(X.core.phi_bundles()):
                X.core.value(goal)
            else:
                log(f' FEATURE MISMATCH {goal.head().core.feature_mismatch_test(X.core.phi_bundles())}')
                X.core.add_features({'*'})
        else:
            log(f' did not find suitable goal.')
        return X

    def get_goal(X):
        return X.sister().INT(criteria=lambda x: not x.copied and x.head().core('referential'),
                              intervention=lambda x: x.phase_head())

    def phase_head(X):
        return X.zero_level() and X.INT(some(PhraseStructure.phase_heads)) and \
               not X.INT(some(PhraseStructure.phase_heads_exclude))

    def EPP_violation(X):
        """
        Current implementation of the Agree/EPP system, tested as LF-legibility
        todo There must be a deeper/simpler function but currently it is unknown
        """

        # Rule out stacking of non-adjunct constituents into the edge
        # e.g.,  base-generated '[_TP towards Paris [_TP Seine [T flows]]]'
        # Questionable whether this filter exists, requires careful consideration
        # Adjuncts can be stacked

        if len(X.EXT(domain='max', criteria=lambda x: x.is_L(), acquire='all')) > 2:
            return True

        # Main rules

        if not X.INT(['ASP', 'strong_pro']):                                    #   Amnesty for strong pro, theta heads and C/fin
            if not X.core('EF'):                                            #   If X does not have EF,
                return X.specifier() and not X.core('thematic_edge')       #   it cannot have nonthematic edge element
            if X.INT({'-ΦPF'}) or not X.core('EPP'):                            #   Amnesty for non-agreeing heads and heads without EPP
                return False
            if X.INT({'weak_pro'}):                                             #   Secondary rule:
                return X.INT({'ΦLF'}) and not X.specifier()                  #   if Agree(X, Y), SpecXP cannot be empty
            if X.INT({'ΦLF'}):                                                  #   Primary rule:
                return not X.primary_rule()                                 #   if Agree(X, Y), YP = SpecXP

            # If Agree(X, Y) does not occur, then violation can be avoided if X is specifically marked to not require Agree
            # or there is phi-consistent overt agreement suffices at X

            elif not X.INT(['?ΦLF', '-ΦLF']) and not (X.INT({'ΦPF'}) and X.core.phi_consistent()):
                return True

    def primary_rule(X):
        """
        Primary rule forces Agree(X, Y) => Move(YP). This function checks that this rule holds.
        """

        return X.specifier() and \
               X.indexed_argument() and \
               X.specifier().head().core.get_id() == X.indexed_argument().head().core.get_id()

    def indexed_argument(X):
        idx = next(iter(X.core.features(type=['phi_index'], format='only_value')), None)
        if idx and X.sister():
            return X.sister().INT(criteria=lambda x: x.head().INT({idx}), intervention=lambda x: x.INT('finite_C'))

    def feature_inheritance(X):

        # C-T feature inheritance

        if X.core('finite') and \
                not X.EXT(criteria=lambda x: x.zero_level() and x.core('finite')) and not X.INT({'!PER'}):
            X.core.add_features({'!PER'})

        # Obligatory control

        if X.INT({'EF?'}):
            X.core.remove_features({'EF?'})
            X.core.add_features({'EF*'})
            if X.EXT(criteria=lambda x: x.zero_level() and x.INT('SEM_internal_predicate')):
                X.core.add_features({'-ΦLF'})

        # DP-internal concord (rudimentary, not studied in detail)

        if X.INT({'φ'}) and X.complement():
            X.core.add_features(X.complement().head().core.features(type=['phi', 'interpretable']))
            X.core.add_features(X.complement().head().core.get_R_features())
        return X

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
        return X.INT('operator', scan=True) and \
               not X.core.features(match=['$OP$']) and \
               X.INT('-insitu', scan=True) and \
               ((X.container() and X.container().INT({'Fin'})) or
                (X.INT({'-insitu'}) and X.INT(['TAM', 'C/fin', 'Neg/fin'])))

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
            for x in X.EXT(acquire='all', criteria=lambda x: x.zero_level() and
                                                             x.is_L(), self=(direction == 'right')):
                if x.INT(some(tail_set)):
                    return x.INT(tail_set)
        else:
            return X.max().container() and X.max().container().INT(tail_set)

    def get_tail_sets(X):
        return {frozenset(f[5:].split(',')) for f in X.head().core.features() if f.startswith('TAIL:')}

    # Control ---------------------------------------------------------------------------------------------------

    def control(X):

        # If there is a suitable antecedent, return it

        if X.EXT(criteria=lambda y: y.INT('referential') and not mismatch(X.phi_set(), y.head().phi_set())):
            return X.EXT(criteria=lambda y: y.INT('referential') and not mismatch(X.phi_set(), y.head().phi_set()))

        # Otherwise, if X does not have overt phi, return generic 'one'

        if not X.INT('overt_phi'):
            return PhraseStructure(features={"PF:one", 'LF:generic', 'φ', 'D'})

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

    def size(X):
        s = 1
        for x in X.const:
            if x:
                s += x.size()
        return s

    def attach(X, W):
        X.speaker_model.results.consume_resources('Merge', X, W)
        if X.w_internal() or X.INT({'C'}) or X.bottom_affix().INT('EHM'):
            return X ** W   #   EHM
        return X * W        #   Phrasal Merge (asymmetric)

    def detach(X):
        m = X.M()
        X.mother_ = None
        return X, m

    def copy_(X):
        Y = PhraseStructure()
        Y.core = X.core.copy()
        Y.adjunct = X.adjunct
        Y.internal = X.internal
        Y.clitic = X.clitic
        Y.identity = X.identity
        Y.copied = X.copied
        Y.elliptic = X.elliptic
        Y.create_constituents([x.copy_() for x in X.const])
        return Y

    def copy(X):
        return X.copy_().update_copied_chains()

    def reattach(X, m):
        X.mother_ = m
        return X

    def target_left_branch_and_copy(X, N):
        return X.top().copy().collect_sWM(geometrical=True, self=True)[X.top().get_right_edge_index(N)]

    # Support ----------------------------------------------------------------------

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

        # Add chain identity marker

        if X.identity != 0:
            chain_index_str = f':{X.identity}'
        else:
            chain_index_str = ''

        # Add copy marker (if needed)

        if X.copied:
            copy_str = ''
        else:
            copy_str = ''

        # Phonologically null complex constituents

        if X.elliptic and X.complex():
            if X.adjunct:
                return '<__>' + chain_index_str + copy_str
            else:
                return '__' + chain_index_str + copy_str

        # Primitive heads

        if X.zero_level():
            if not X.get_phonological_string():
                return '?'
            elif X.copied:
                return f'(0)'
            return X.get_phonological_string()

        # Complex phrasal constituents

        else:
            if X.adjunct:
                return f'<{X.L()} {X.R()}>' + chain_index_str + copy_str
            else:
                return f'[{X.L()} {X.R()}]' + chain_index_str + copy_str

    def get_phonological_string(X):
        if len(X.affixes()) == 1 or (X.affix() and X.affix().copied):
            return X.exponent()
        return f'{X.label()}({",".join([x.exponent() for x in X.affixes()[1:]])})'

    def exponent(X):
        stri = ''
        for fset in X.core.feature_bundles():
            stri += "".join([f[3:] for f in fset if f.startswith("PF:")])
        return stri

    def consume_resources(X, resource_key, target):
        PhraseStructure.resources[resource_key]['n'] += 1

    def w_internal(X):
        return X.bottom().bottom_affix().internal

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
        for const in (x for x in X.EXT(acquire='all') if x.head().core.has_idx() and x.head().core.get_idx_tuple('QND') and x.head() != X and not x.copied):
            sWM.add(assignment[const.head().core.get_referential_index('QND')])
            if intervention_feature and not const.copied and {intervention_feature}.issubset(const.head().core.features()):
                break
        return sWM

class NodePicture:
    def __init__(self, t=None, **kwargs):

        # Convert the input parameter into a node picture object

        if isinstance(t, str):
            self.feature_abstraction = t
        else:
            self.feature_abstraction = ''

        if isinstance(t, set) or isinstance(t, frozenset):
            self.conj = t
        else:
            self.conj = set()

        if isinstance(t, list):
            self.disj = set(t)
        else:
            self.disj = set()

        self.criteria = kwargs.get('criteria')

    def __str__(self):
        stri = ''
        stri += f's: {self.feature_abstraction}, A: {self.conj}, V: {self.disj}'
        return stri
