import itertools

phi_map_dict = {'1': 'first person',
                '2': 'second person',
                '3': 'third person',
                'PL': 'plural',
                'SG': 'singular',
                'HUM': 'human',
                'NONHUM': 'non-human',
                'M': 'masculine',
                'F': 'feminine'}


def phi_map(phi_feature):
    return phi_map_dict.get(phi_feature, '')

def phi_feature(f):
    return 'PHI:' in f

def interpretable_phi_feature(f):
    return f.startswith('iPHI')

def unvalued_phi_feature(f):
    return phi_feature(f) and f[-1] == '_'

def unvalued_counterparty(goal_feature, X):
    return f'PHI:{goal_feature.split(":")[1]}:_' in X.features

def valued_phi_feature(f):
    return phi_feature(f) and f[-1] != '_' and len(f.split(':')) == 3

def interpretable_phi_features(probe):
    return {phi for phi in probe.head().features if interpretable_phi_feature(phi)}

def unlicensed_phi_features_at_goal(G, PP):
    return G - set().union(*{frozenset(phi) for phi in PP if phi <= G})

def mismatch(G, P):
    return {(p, g) for p, g in itertools.product(G, P) if type_value_mismatch(p, g)}

def type_value_mismatch(p, g):
    return p.split(':')[0] == g.split(':')[0] and p.split(':')[1] != g.split(':')[1]

def i(phi):
    if interpretable_phi_feature(phi):
        return phi[1:]
    return phi

