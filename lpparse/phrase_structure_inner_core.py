import itertools
from support import log
import re

# These abbreviations define notions that are typically used in several places,
# so that all changes made here will generalize everywhere

abstraction_funct = {'EHM': lambda X: 'ε' in X,
                     'EF': lambda X: ['EF', 'EF*'] in X,
                     'EPP': lambda X: 'EF*' in X,
                     'TAM': lambda X: X.features(match=['TAM']),
                     'event': lambda X: 'π' in X,
                     'polarity': lambda X: X.features(match=['POL:']),
                     'strong_features': lambda X: X.features(match=['**...']),
                     'predicate': lambda X: 'Φ' in X,
                     'finite': lambda X: ['Fin', 'T/fin', 'C/fin'] in X,
                     'force': lambda X: 'FORCE' in X,
                     'finite_C': lambda X: 'C' in X,
                     'referential': lambda X: ['φ', 'D'] in X,
                     'nonreferential': lambda X: 'SEM:nonreferential' in X,
                     'adverbial': lambda X: 'Adv' in X,
                     'adjoinable': lambda X: 'adjoinable' in X,
                     'nonfloat': lambda X: 'nonfloat' in X,
                     'nominal': lambda X: 'N' in X,
                     'verbal': lambda X: 'ASP' in X,
                     'theta_predicate': lambda X: X('thetaSPEC') or X('thetaCOMP'),
                     'thetaSPEC': lambda X: 'θSPEC' in X,
                     'thetaCOMP': lambda X: 'θCOMP' in X,
                     'nonthematic_verb': lambda X: X('verbal') and not X('theta_predicate'),
                     'thematic_edge': lambda X: X.get_selection_features('+SPEC') & {'D', 'φ'},
                     'light_verb': lambda X: ['v', 'v*', 'impass', 'cau'] in X,
                     'finite_left_periphery': lambda X: X('finite') and ['T', 'C'] in X and 'T/prt' not in X,
                     'finite_tense': lambda X: 'T/fin' in X or (X('finite') and 'T' in X),
                     'preposition': lambda X: 'P' in X,
                     'expresses_concept': lambda X: ['N', 'Neg', 'P', 'D', 'φ', 'A', 'V', 'Adv', 'Q', 'Num', '0'] in X and ['T/prt', 'COPULA'] not in X,
                     'SEM_internal_predicate': lambda X: 'SEM:internal' in X,
                     'SEM_external_predicate': lambda X: 'SEM:external' in X,
                     'scope_marker': lambda X: ['C', 'C/fin', 'OP'] in X,
                     'operator': lambda X: X.features(match=['OP:...']),
                     '-insitu': lambda X: X.features(match=['-insitu']),
                     'overt_phi': lambda X: 'ΦPF' in X,
                     'unrecognized_label': lambda X: ['CAT:?', '?'] in X,
                     'AgreeLF_occurred': lambda X: 'ΦLF' in X
                     }

feature_abstraction = {'phi': lambda f: 'PHI:' in f and 'IDX' not in f,
                       'R': lambda f: f.startswith('R:'),
                       '+SPEC': lambda f: f.startswith('+SPEC:'),
                       '+COMP': lambda f: f.startswith('+COMP:'),
                       'index': lambda f: f.startswith('IDX:'),
                       'phi_index': lambda f: f.startswith('PHI:IDX:'),
                       'interpretable': lambda f: f.startswith('iPHI:'),
                       'uninterpretable': lambda f: f.startswith('PHI:'),
                       'unvalued': lambda f: f.endswith('_'),
                       'strong': lambda f: f.startswith('**'),
                       'valued': lambda f: not f.endswith('_')}

def value_mismatch(p, g):
    return p.split(':')[0] == g.split(':')[0] and p.split(':')[1] != g.split(':')[1]

def mismatch(G, P):
    for p, g in itertools.product(G, P):
        if value_mismatch(p, g):
            return p, g

class PhraseStructureCore:
    def __init__(self, **kwargs):

        # The core contains a list of feature sets (feature bundles)

        if isinstance(kwargs.get('features'), set):
            self._features = [kwargs.get('features', set())]
        elif isinstance(kwargs.get('features'), list):
            self._features = kwargs.get('features', [])
        else:
            self._features = [set()]

    def __contains__(self, f=None):

        # Strings are matches with features

        if isinstance(f, str):
            return f in self.features()

        # Sets match conjunctively

        if isinstance(f, set):
            return f <= self.features()

        # Lists match disjunctively

        if isinstance(f, list):
            return set(f) & self.features()

    def __call__(self, stri):

        # Safeguard

        if not stri:
            return True

        # If the string stri provides a valid key for the dictionary containing the definition,
        # test whether the definition applies

        if abstraction_funct.get(stri):
            return abstraction_funct[stri](self)

    def features(self, **kwargs):
        fset = set().union(*[fset for fset in self._features])

        # We can probe features which match with strings and substrings
        # todo This will be implemented by regex pattern matching

        if kwargs.get('match'):
            fset2 = set()
            for f in fset:
                for pattern in kwargs.get('match'):
                    if pattern.endswith('...'):
                        if f.startswith(pattern[0:-3]):
                            fset2.add(f)
                    elif pattern.startswith('$') and pattern.endswith('$'):
                        if pattern == f:
                            fset2.add(f)
                    elif pattern in f:
                        fset2.add(f)
            fset = fset2

        # We can also probe with features by referring to their type

        if kwargs.get('type'):
            for feature_type in kwargs.get('type', []):
                fset = {f for f in fset if feature_abstraction[feature_type](f)}
            if kwargs.get('format') == 'reduced':
                fset = {':'.join(f.split(':')[1:]) for f in fset}
            if kwargs.get('format') == 'no_value':
                fset = {':'.join(f.split(':')[0:-1]) for f in fset}
            if kwargs.get('format') == 'only_value':
                fset = {f.split(':')[-1] for f in fset}
            if kwargs.get('format') == 'licensed':
                fset = set().union(*{frozenset(f.split(':')[1].split(',')) for f in fset})

        return fset

    def feature_bundles(self):
        return self._features

    def bundle_features(self, f):
        for fset in self._features:
            if f in fset:
                return fset

    def set_features(self, fset):
        self._features = [fset]

    def remove_features(self, fset):
        for i, fset_ in enumerate(self._features):
            self._features[i] = fset_ - fset

    def add_features(self, fset):
        if self._features[0]:
            self._features[0].update(fset)
        else:
            self._features = [fset]

    def copy(self):
        c = PhraseStructureCore()
        c._features = self.copy_features()
        return c

    def copy_features(self):
        return [s.copy() for s in self._features]

    def integrity(self):

        # Examine each bundle and check m-selection

        for i in range(1, len(self._features)):
            if self.m_selection_violation(i):
                return True

    def m_selection_violation(self, i):

        # Return a set of m-features of type [type]
        # Feature format is TYPE=A,B,C...

        def m_selection(fset, type):
            return set().union(*[set(f.split('=')[1].split(',')) for f in fset if f.startswith(type)])

        # --------------- MAIN FUNCTION -----------------------------------------------------

        # Check that the previous bundle (i-1) does not have negative m-selected features

        if self._features[i-1] & m_selection(self._features[i], '-mCOMP='):
            return True

        # Check that the previous bundle (i-1) contains positive m-selected features

        pos_mset = {f for f in m_selection(self._features[i], '+mCOMP=') if not f.endswith('/root')}
        pos_root = {f[:-5] for f in m_selection(self._features[i], '+mCOMP=') if f.endswith('/root')}
        if pos_mset:
            if not self._features[i-1] & pos_mset and not self.features() & pos_root:
                return True

    # Phi-features ----------------------------------------------------------------------------

    def value(self, Y_goal):
        log(' values ')

        # get features from the goal

        fset = self.features_to_value_from_goal(Y_goal)
        if fset:

            # Value the acquired features

            for phi in fset:
                self.value_phi_feature(phi)
                log(f'[{phi[5:]}]')
        else:
            log(f'nothing')
        log(f' from goal {Y_goal.max()}.')

        # Partial agreement does not create ΦLF

        if len(fset) > 1:
            self.add_features({'ΦLF'})
            self.remove_features({'?ΦLF'})
        self.add_features({f'PHI:IDX:{Y_goal.head().core.get_id()}'})

    def value_phi_feature(self, f):

        # Remove the unvalued feature

        self.remove_features({f'PHI:{f.split(":")[1]}:_'})

        # Add the valued feature

        self.add_features({f'{f[1:]}'})

    def features_to_value_from_goal(self, goal):

        # Returns the unvalued counterparty T:V:_ for feature T:V:K

        def unvalued_counterparty(goal_feature, X):
            return f'PHI:{goal_feature.split(":")[1]}:_' in X.features()

        # Feature valuation presupposes that either the probe does not have gate features or
        # if it has them, the same type must exist
        # Note: mismatches have already been checked earlier

        def feature_gate(f, P):
            for p in P:
                if f.split(':')[1] == p.split(':')[0]:
                    return True

        # ---------------------- MAIN FUNCTION -----------------------------------------------

        # Set of phi-features that are licensed at the probe

        P = set().union(*self.phi_bundles())

        # Return the set of features that can be valued from the goal at the probe

        return [f for f in goal.head().core.features(type=['phi', 'interpretable']) if unvalued_counterparty(f, self) and (not P or feature_gate(f, P))]

    def phi_bundles(self):
        return [set(phi[4:].split(',')) for phi in self.features(type=['phi', 'valued', 'uninterpretable'])]

    def feature_mismatch_test(X, PP):
        """
        X = goal
        PP = phi-bundles at the probe
        This function examines if there are unlicensed phi-features at the goal (G) that mismatch with
        phi-features at the probe. Unlicensed phi-features at the goal are those features which are not
        matched with phi-bundles at the probe.
        Note 1: The feature format is TYPE:VALUE with (i)PHI removed.
        """

        def unlicensed_phi_features_at_goal(G, PP):
            return G - set().union(*{frozenset(phi) for phi in PP if phi <= G})

        return mismatch(unlicensed_phi_features_at_goal(X.features(type=['phi', 'interpretable'], format='reduced'), PP), set().union(*PP))

    # pro-calculations

    def overt_phi_sustains_reference(X):

        # Definition for "sustains reference" i.e. can establish referential denotation:
        # (1) must have overt phi-features,
        # (2) is phi-consistent,
        # (3) has minimal phi-features for reference.

        return X('overt_phi') and X.phi_consistent() and X.minimal_phi_for_reference()

    def phi_consistent(self):

        # Definition for phi-consistency, i.e. features of type T do not have different values

        return next((False for fpair in itertools.permutations(self.complete_valued_phi_set(), 2) if value_mismatch(*fpair)), True)

    def minimal_phi_for_reference(self):

        # The bundle must contain number, person and det features

        return {'NUM', 'PER', 'DET'} <= {phi[:3] for phi in self.complete_valued_phi_set()}

    def complete_valued_phi_set(self):
        return set().union(*[frozenset(phi[4:].split(',')) for phi in self.features(type=['phi', 'valued'])])

    # Selection, thematic roles

    def get_selection_features(self, key):
        feats = [set(f.split(':')[1].split(',')) for f in self.features() if f.startswith(key)]
        return set().union(*feats)

    def selection_keys(self):
        return sorted([f.split(':')[0] for f in self.features(match=['COMP', 'SPEC', 'SELF'])])

    def semantic_match(self, Y):
        pos_sem_a = self.features(match=['+SEM...'], format='reduced')
        neg_sem_a = self.features(match=['-SEM...'], format='reduced')
        pos_sem_b = Y.core.features(match=['+SEM...'], format='reduced')
        neg_sem_b = Y.core.features(match=['-SEM...'], format='reduced')
        return not ((pos_sem_a & neg_sem_b) or (pos_sem_b & neg_sem_a))

    # Get properties

    def get_id(self):
        if len(self.features(match=['§...'])) > 0:
            return ''.join(list(self.features(match=['§...'])))
        return '?'

    def get_lf(self):
        return [f[3:] for f in self.features(match=['LF:...'])]

    def index(self):
        return next(iter(f[1:] for f in self.features(match=['§...'])), None)

    def semantic_index(self, space):
        return next((f.split(':')[1].split(',')[0] for f in self.features(type=['index'], match=[space])), None)

    def has_idx(self, space=''):
        return next((idx for idx, space_ in [tuple(f[4:].split(',')) for f in self.features(type=['index'])] if space_ == space or space == ''), None)

    def get_idx_tuple(self, requested_space):
        return next(((idx, space) for idx, space in [tuple(f[4:].split(',')) for f in self.features(type=['index'])] if space == requested_space or requested_space == ''), None)

    def get_R_features(self):
        return {f for f in self.features(type=['R'])}

    def get_referential_index(self, space):
        def index_(f):
            return f.split(':')[1].split(',')[0]

        def space_(f):
            return f.split(':')[1].split(',')[1]

        return next((index_(f) for f in self.features(type=['index']) if space_(f) == space), None)

    def __str__(self):
        sorting_order = {'D': 0, 'φ': 0, 'N': 0, 'V': 0, 'A': 0, 'P': 0, 'Adv': 0, 'T': 0, 'C': 0, 'Fin': 0, 'Inf': 0,
                         'Φ': 1, 'EF': 1, 'EF*': 1, 'θ': 1, 'κ': 1, 'π': 1,
                         '$LF:$': 2, '$PF:$': 2,
                         '$PHI$': 3, '$ΦLF$': 3, '$ΦPF$': 3, '$pro$': 3, 'sg': 3, 'pl': 3, 'hum': 3, 'nonhum': 3, 'def': 3, 'indef': 3, 'udef': 3, '1p': 3, '2p': 3, '3p': 3,
                         '$SPEC$': 4, '$COMP$': 4, '$SELF$': 4, '$PROBE$': 4,
                         '$LANG:$': 5}

        def feature_sort(fset):

            # Each feature will be allocated to one of these lists = sorting

            sorted_lst = [[], [], [], [], [], []]

            # Holds all features at first then all the remaining features

            residuum = list(fset.copy())

            # Examine each feature

            for f in fset:

                # Checks the priority of the feature and inserts it into the sorted list,
                # then removes from residuum

                if f in sorting_order.keys():
                    sorted_lst[sorting_order[f]].append(f)
                    if f in residuum:
                        residuum.remove(f)

                # Special notation which matches only substring $F$ = matches F

                else:
                    for k in sorting_order.keys():
                        if k.startswith('$') and k.endswith('$') and k[1:-1] in f:
                            sorted_lst[sorting_order[k]].append(f)
                            if f in residuum:
                                residuum.remove(f)

            result = []

            # Examine each class of features and adds them into the result

            for lst in sorted_lst:
                result += lst
            return result + sorted(residuum)

        stri = ''

        # Examine each feature bundle

        for fset in self.feature_bundles():
            stri += '{'     # Start with this symbol
            line = ''

            # Produce formatted output

            for i, f in enumerate(feature_sort(fset)):
                if 0 < i < len(fset):
                    line += ' '
                line += f'{f}'
                if len(line) > 70:
                    stri += f'{line}\n\t\t{" ":<11}'
                    line = ''
            if line:
                stri += f'{line}}}\n\t\t{" ":<11}'
        return stri
