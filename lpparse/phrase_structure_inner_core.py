import itertools
from support import log
import re

abstraction_funct = {'EHM': lambda X: 'ε' in X,
                     'EF': lambda X: ['EF', 'EF*'] in X,
                     'EPP': lambda X: 'EF*' in X,
                     'event': lambda X: 'π' in X,
                     'predicate': lambda X: 'Φ' in X,
                     'finite': lambda X: ['Fin', 'T/fin', 'C/fin'] in X,
                     'force': lambda X: 'FORCE' in X,
                     'referential': lambda X: ['φ', 'D'] in X,
                     'adverbial': lambda X: 'Adv' in X,
                     'nominal': lambda X: 'N' in X,
                     'verbal': lambda X: 'ASP' in X,
                     'theta_predicate': lambda X: X.property('thetaSPEC') or X.property('thetaCOMP'),
                     'thetaSPEC': lambda X: 'θSPEC' in X,
                     'thetaCOMP': lambda X: 'θCOMP' in X,
                     'nonthematic_verb': lambda X: X.property('verbal') and not X.property('theta_predicate'),
                     'thematic_edge': lambda X: X.get_selection_features('+SPEC') & {'D', 'φ'},
                     'light_verb': lambda X: ['v', 'v*', 'impass', 'cau'] in X,
                     'finite_left_periphery': lambda X: X.property('finite') and ['T', 'C'] in X,
                     'finite_tense': lambda X: 'T/fin' in X or (X.property('finite') and 'T' in X),
                     'preposition': lambda X: 'P' in X,
                     'expresses_concept': lambda X: ['N', 'Neg', 'P', 'D', 'φ', 'A', 'V', 'Adv', 'Q', 'Num', '0'] in X and ['T/prt', 'COPULA'] not in X,
                     'SEM_internal_predicate': lambda X: 'SEM:internal' in X,
                     'SEM_external_predicate': lambda X: 'SEM:external' in X,
                     'scope_marker': lambda X: ['C', 'C/fin', 'OP'] in X,
                     'overt_phi': lambda X: 'ΦPF' in X,
                     'AgreeLF_occurred': lambda X: 'ΦLF' in X
                     }

feature_abstraction = {'phi': lambda f: 'PHI:' in f,
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
        if isinstance(kwargs.get('features'), set):
            self._features = [kwargs.get('features', set())]
        elif isinstance(kwargs.get('features'), list):
            self._features = kwargs.get('features', [])
        else:
            self._features = [set()]

    def __contains__(self, f=None):
        if isinstance(f, str):
            return f in self.features()
        if isinstance(f, set):
            return f <= self.features()
        if isinstance(f, list):
            return set(f) & self.features()

    def features(self, **kwargs):
        fset = set().union(*[fset for fset in self._features])

        if kwargs.get('match'):
            fset2 = set()
            for f in fset:
                for pattern in kwargs.get('match'):
                    if pattern.startswith('$'):
                        if f.startswith(pattern[1:]):
                            fset2.add(f)
                    elif pattern in f and not (pattern.startswith('^') and pattern[1:] in f):
                        fset2.add(f)
            fset = fset2

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

    def property(self, P):
        if abstraction_funct.get(P):
            return abstraction_funct[P](self)

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
        for i, fset in enumerate(self._features):
            if i > 0 and self.m_selection_violation(i, fset):     # ith morpheme
                return True

    def m_selection_violation(self, i, current_morph_fset):
        def get_negative_m_selection_features(fset):
            return set().union(*[set(f.split('=')[1].split(',')) for f in fset if f.startswith('-mCOMP=')])
        def get_positive_m_selection_features(fset):
            s = set().union(*[set(f.split('=')[1].split(',')) for f in fset if f.startswith('+mCOMP=')])
            return {f for f in s if not f.endswith('/else')}
        def get_positive_root_selection_features(fset):
            s = set().union(*[set(f.split('=')[1].split(',')) for f in fset if f.startswith('+mCOMP=')])
            return {f.split('/')[0] for f in s if f.endswith('/else')}

        fset_prev_morph = self._features[i-1]
        fset_else = self.features()
        if fset_prev_morph:
            neg_mset = get_negative_m_selection_features(current_morph_fset)
            pos_mset = get_positive_m_selection_features(current_morph_fset)
            pos_else_set = get_positive_root_selection_features(current_morph_fset)
            if neg_mset and (fset_prev_morph & neg_mset):
                return True
            if pos_mset and not (fset_prev_morph & pos_mset or fset_else & pos_else_set):
                return True

    # Phi-features ----------------------------------------------------------------------------

    def value(self, Y_goal):
        log(' values ')
        fset = self.features_to_value_from_goal(Y_goal)
        for phi in fset:
            self.value_phi_feature(phi)
            log(f'[{phi[5:]}]')
        log(f' from goal {Y_goal.max()}.')
        if len(fset) > 1:   # Partial agreement does not create ΦLF
            self.add_features({'ΦLF'})
        self.add_features({f'PHI:IDX:{Y_goal.H().core.get_id()}'})

    def value_phi_feature(self, f):
        self.remove_features({f'PHI:{f.split(":")[1]}:_'})
        self.add_features({f'{f[1:]}'})

    def features_to_value_from_goal(self, goal):
        def unvalued_counterparty(goal_feature, X):
            return f'PHI:{goal_feature.split(":")[1]}:_' in X.features()

        def feature_gate(goal_feature, P):
            """
            Feature A can be valued for B at probe head X iff
            (1) B is an unvalued feature of the same type as A
            (2) probe X contains overtly valued phi-bundle with the same type as A (gate condition)
            """
            for p in P:
                if goal_feature.split(":")[1] == p.split(':')[0]:  # Condition (2)
                    return True

        P = set().union(*self.phi_bundles())
        return [f for f in goal.H().core.features(type=['phi', 'interpretable']) if unvalued_counterparty(f, self) and (not P or feature_gate(f, P))]

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
        return X.property('overt_phi') and X.phi_consistent() and X.minimal_phi_for_reference()

    def phi_consistent(self):
        return next((False for fpair in itertools.permutations(self.complete_valued_phi_set(), 2) if value_mismatch(*fpair)), True)

    def minimal_phi_for_reference(self):
        return {'NUM', 'PER', 'DET'} <= {phi[:3] for phi in self.complete_valued_phi_set()}

    def complete_valued_phi_set(self):
        return set().union(*[frozenset(phi[4:].split(',')) for phi in self.features(type=['phi', 'valued'])])

    # Selection, thematic roles
    def get_selection_features(self, key):
        feats = [set(f.split(':')[1].split(',')) for f in self.features() if f.startswith(key)]
        return set().union(*feats)

    def selection_keys(self):
        return [f.split(':')[0] for f in self.features(match=['COMP', 'SPEC', 'SELF'])]

    def semantic_match(self, Y):
        pos_sem_a = self.features(match=['$+SEM'], format='reduced')
        neg_sem_a = self.features(match=['$-SEM'], format='reduced')
        pos_sem_b = Y.core.features(match=['$+SEM'], format='reduced')
        neg_sem_b = Y.core.features(match=['$-SEM'], format='reduced')
        return not ((pos_sem_a & neg_sem_b) or (pos_sem_b & neg_sem_a))

    # Get properties
    def get_id(self):
        if len(self.features(match=['$§'])) > 0:
            return ''.join(list(self.features(match=['$§'])))
        return '?'

    def get_lf(self):
        return [f[3:] for f in self.features(match=['$LF:'])]

    def index(self):
        return next(list(self.features(match=['$§'])), None)

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
            sorted_lst = [[], [], [], [], [], []]
            residuum = list(fset.copy())
            for f in fset:
                if f in sorting_order.keys():
                    sorted_lst[sorting_order[f]].append(f)
                    if f in residuum:
                        residuum.remove(f)
                else:
                    for k in sorting_order.keys():
                        if k.startswith('$') and k.endswith('$') and k[1:-1] in f:
                            sorted_lst[sorting_order[k]].append(f)
                            if f in residuum:
                                residuum.remove(f)
            result = []
            for lst in sorted_lst:
                result += lst
            return result + sorted(residuum)

        stri = ''
        for fset in self.feature_bundles():
            stri += '{'
            line = ''
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