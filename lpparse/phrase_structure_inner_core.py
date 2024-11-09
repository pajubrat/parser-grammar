import itertools
from support import log


def feature_gate(goal_feature, P):
    """
    Feature A can be valued for B at probe head X iff
    (1) B is an unvalued feature of the same type as A
    (2) probe X contains overtly valued phi-bundle with the same type as A (gate condition)
    """
    for p in P:
        if goal_feature.split(":")[1] == p.split(':')[0]:  # Condition (2)
            return True

def phi_feature(f):
    return 'PHI:' in f

def interpretable_phi_feature(f):
    return f.startswith('iPHI')

def unvalued_phi_feature(f):
    return phi_feature(f) and f[-1] == '_'

def unvalued_counterparty(goal_feature, X):
    return f'PHI:{goal_feature.split(":")[1]}:_' in X.features()

def valued_phi_feature(f):
    return phi_feature(f) and f[-1] != '_'

def interpretable_phi_features(probe):
    return {phi for phi in probe.H().features if interpretable_phi_feature(phi)}

def unlicensed_phi_features_at_goal(G, PP):
    return G - set().union(*{frozenset(phi) for phi in PP if phi <= G})

def mismatch(G, P):
    return {(p, g) for p, g in itertools.product(G, P) if type_value_mismatch(p, g)}

def i(phi):
    if interpretable_phi_feature(phi):
        return phi[1:]
    return phi

def mandatory(f):
    return f.startswith('!')

def illicit(f):
    return f.startswith('-')

def type_value_mismatch(p, g):
    return p.split(':')[0] == g.split(':')[0] and p.split(':')[1] != g.split(':')[1]


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

    def features(self):
        return set().union(*[fset for fset in self._features])

    def bundle_features(self, f):
        for fset in self._features:
            if f in fset:
                return fset

    def feature_bundles(self):
        return self._features

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
        fset_prev_morph = self._features[i-1]
        fset_else = self.features()
        if fset_prev_morph:
            neg_mset = self.get_negative_m_selection_features(current_morph_fset)
            pos_mset = self.get_positive_m_selection_features(current_morph_fset)
            pos_else_set = self.get_positive_root_selection_features(current_morph_fset)
            if neg_mset and (fset_prev_morph & neg_mset):
                return True
            if pos_mset and not (fset_prev_morph & pos_mset or fset_else & pos_else_set):
                return True

    def get_negative_m_selection_features(self, fset):
        return set().union(*[set(f.split('=')[1].split(',')) for f in fset if f.startswith('-mCOMP=')])

    def get_positive_m_selection_features(self, fset):
        s = set().union(*[set(f.split('=')[1].split(',')) for f in fset if f.startswith('+mCOMP=')])
        return {f for f in s if not f.endswith('/else')}

    def get_positive_root_selection_features(self, fset):
        s = set().union(*[set(f.split('=')[1].split(',')) for f in fset if f.startswith('+mCOMP=')])
        return {f.split('/')[0] for f in s if f.endswith('/else')}

    # Phi-features ----------------------------------------------------------------------------

    def value(self, Y_goal):
        log(' values ')
        for phi in self.features_to_value_from_goal(Y_goal):
            self.value_phi_feature(phi)
            log(f'[{phi[5:]}]')
        log(f' from goal {Y_goal.max()}.')
        self.add_features({'ΦLF'})
        self.add_features({f'PHI:IDX:{Y_goal.H().core.get_id()}'})

    def formatted_phi(self):
        def remove_phi_prefix(feature):
            if feature.startswith('iPHI:'):
                return feature[5:]
            return feature[4:]
        return [remove_phi_prefix(f).split(',') for f in self.features() if valued_phi_feature(f)]

    def value_phi_feature(self, f):
        self.remove_features({f'PHI:{f.split(":")[1]}:_'})
        self.add_features({f'{f[1:]}'})

    def strong_features(self):
        return {f for f in self.features() if f.startswith('**')}

    def valued_phi_features(self):
        return {f for f in self.features() if 'PHI:' in f and f[-1] != '_'}

    def phi_features(self):
        return {f[4:] for f in self.features() if f.startswith('PHI:') and not f.endswith('_')}

    def complete_valued_phi_set(self):
        phi_sets = [phi[4:].split(',') for phi in self.features() if phi.startswith('PHI:') and not phi.endswith('_')]
        return {phi for phi_set in phi_sets for phi in phi_set}

    def phi_consistent_head(self):
        for fpair in itertools.permutations(self.complete_valued_phi_set(), 2):
            if type_value_mismatch(*fpair):
                return False
        return True

    def complete_agreement_suffixes(self):
        return self.phi_consistent_head() and self.has_minimal_phi_set_for_reference() and 'ΦPF' in self.features()

    def has_minimal_phi_set_for_reference(self):
        return {'NUM', 'PER', 'DET'} <= {phi[:3] for phi in self.complete_valued_phi_set()}

    def pro_features(X):
        return X.valued_phi_features() | {'φ', 'PF:pro', 'pro'}

    def independent_pro_from_overt_agreement(self):
        return ['weak_pro', 'strong_pro'] in self

    def nonreferential_pro(self):
        return 'nonreferential_pro' in self

    def interpretable_phi_features(self):
        return {f[5:] for f in self.features() if f.startswith('iPHI:')}

    def features_to_value_from_goal(self, goal):
        P = set().union(*self.phi_bundles())
        return [f for f in goal.H().core.features() if interpretable_phi_feature(f) and unvalued_counterparty(f, self) and (not P or feature_gate(f, P))]

    def AgreeLF_has_occurred(self):
        return 'ΦLF' in self

    def phi_bundles(self):
        return [set(phi[4:].split(',')) for phi in self.features() if valued_phi_feature(phi) and not phi.startswith('i') and 'IDX' not in phi]

    def phi_index(self):
        return next((f.split(':')[2] for f in self.features() if f.startswith('PHI:IDX:')), None)

    def feature_mismatch_test(self, PP):
        """
        X = goal
        PP = phi-bundles at the probe
        This function examines if there are unlicensed phi-features at the goal (G) that mismatch with
        phi-features at the probe. Unlicensed phi-features at the goal are those features which are not
        matched with phi-bundles at the probe.
        Note 1: The feature format is TYPE:VALUE with (i)PHI removed.
        """
        return mismatch(unlicensed_phi_features_at_goal(self.interpretable_phi_features(), PP), set().union(*PP))

    def is_unvalued(X):
        for f in X.features():
            if unvalued_phi_feature(f):
                return True

    def needs_valuation(self):
        if not self.complete_agreement_suffixes() and self.get_unvalued_minimal_phi():
            return self.get_unvalued_minimal_phi()

    def get_unvalued_minimal_phi(self):
        return {x for x in self.features() if x[-1] == '_' and x[:7] in {'PHI:NUM', 'PHI:PER', 'PHI:DET'}}

    def phi_is_unvalued(self):
        for f in self.features():
            if f[-1] == '_':
                return True

    def valued_phi_at_probe(self):
        return [phi.split(':') for phi in self.features() if (phi[:7] == 'PHI:NUM' or phi[:7] == 'PHI:PER') and not phi.endswith('_') and not ',' in phi]

    def valued_phi_at_antecedent(self):
        return [phi.split(':') for phi in self.features() if (phi[:7] == 'PHI:NUM' or phi[:7] == 'PHI:PER' or phi[:8] == 'iPHI:NUM' or phi[:8] == 'iPHI:PER') and not phi.endswith('_')]

    def get_valued_phi_types(self):
        return {f[:7] for f in self.features() if valued_phi_feature(f)}

    # Selection, thematic roles
    def get_selection_features(self, key):
        feats = [set(f.split(':')[1].split(',')) for f in self.features() if f.startswith(key)]
        return set().union(*feats)

    def specifiers_licensed(self):
        return set().union(*{frozenset(f[6:].split(',')) for f in self.features() if f.startswith('+SPEC:')})

    def complements_licensed(self):
        return set().union(*{frozenset(f[6:].split(',')) for f in self.features() if f.startswith('+COMP:')})

    def selection_keys(self):
        return [f.split(':')[0] for f in self.features() if 'COMP' in f or 'SPEC' in f or 'SELF' in f]

    def thematic_head(self):
        return 'θ' in self

    def semantic_match(self, Y):
        pos_sem_a = {f[5:] for f in self.features() if f.startswith('+SEM:')}
        neg_sem_a = {f[5:] for f in self.features() if f.startswith('-SEM:')}
        pos_sem_b = {f[5:] for f in Y.core.features() if f.startswith('+SEM:')}
        neg_sem_b = {f[5:] for f in Y.core.features() if f.startswith('-SEM:')}
        return not ((pos_sem_a & neg_sem_b) or (pos_sem_b & neg_sem_a))

    def probe_features(self):
        return [f for f in self.features() if 'PROBE:' in f]

    # Get properties
    def get_id(self):
        for f in self.features():
            if f.startswith('§'):
                return f
        return '?'

    def get_pf(X):
        return {f[3:] for f in X.features() if f[:3] == 'PF:'}

    def get_lf(X):
        return {f[3:] for f in X.features() if f.startswith('LF:')}

    def get_phi_set(X):
        return {f for f in X.features() if f[:4] == 'PHI:' and len(f.split(':')) == 3}

    def index(self):
        return next((f for f in self.features() if f.startswith('§')), None)

    def semantic_index(self, space):
        return next((f.split(':')[1].split(',')[0] for f in self.features() if f.startswith('IDX') and space in f), None)

    def has_idx(self, space=''):
        return next((idx for idx, space_ in [tuple(f[4:].split(',')) for f in self.features() if f.startswith('IDX:')] if space_ == space or space == ''), None)

    def get_idx_tuple(self, requested_space):
        return next(((idx, space) for idx, space in [tuple(f[4:].split(',')) for f in self.features() if f.startswith('IDX:')] if space == requested_space or requested_space == ''), None)

    def get_referential_index(self, space):
        def index_(f):
            return f.split(':')[1].split(',')[0]

        def space_(f):
            return f.split(':')[1].split(',')[1]

        return next((index_(f) for f in self.features() if f.startswith('IDX:') and space_(f) == space), None)



    # Abstractions
    def EHM(self):
        return 'ε' in self

    def EF(self):
        return ['EF', 'EF*'] in self

    def EPP(self):
        return 'EF*' in self

    def event(self):
        return 'π' in self

    def finite(self):
        return ['Fin', 'T/fin', 'C/fin'] in self

    def force(self):
        return 'FORCE' in self

    def referential(self):
        return ['φ', 'D'] in self

    def adverbial(self):
        return 'Adv' in self

    def nominal(self):
        return 'N' in self

    def verbal(self):
        return 'ASP' in self

    def theta_predicate(self):
        return 'θ' in self and '-θ' not in self

    def nonthematic_verb(self):
        return self.verbal() and not self.theta_predicate()

    def thematic_edge(self):
        return self.get_selection_features('+SPEC') & {'D', 'φ'}

    def light_verb(self):
        return ['v', 'v*', 'impass', 'cau'] in self

    def relative(self):
        return 'REF' in self

    def finite_left_periphery(self):
        return self.finite() and ['T', 'C'] in self

    def finite_tense(self):
        return 'T/fin' in self or (self.finite() and 'T' in self)

    def preposition(self):
        return 'P' in self

    def floatable(self):
        return 'nonfloat' not in self

    def expresses_concept(self):
        return ['N', 'Neg', 'P', 'D', 'φ', 'A', 'V', 'Adv', 'Q', 'Num', '0'] in self and ['T/prt', 'COPULA'] not in self

    def SEM_internal_predicate(self):
        return 'SEM:internal' in self

    def SEM_external_predicate(self):
        return 'SEM:external' in self

    def scope_marker(self):
        return ['C', 'C/fin', 'OP'] in self
