import itertools

def phi_feature(f):
    return 'PHI:' in f

def interpretable_phi_feature(f):
    return f.startswith('iPHI')

def unvalued_phi_feature(f):
    return phi_feature(f) and f[-1] == '_'

def valued_phi_feature(f):
    return phi_feature(f) and f[-1] != '_'

def interpretable_phi_features(probe):
    return {phi for phi in probe.head().features if interpretable_phi_feature(phi)}

def feature_mismatch_test(G, PP):
    """
    G = interpretable phi-features at the goal
    PP = phi-bundles at the probe
    This function examines if there are unlicensed phi-features at the goal (G) that mismatch with
    phi-features at the probe. Unlicensed phi-features at the goal are those features which are not
    matched with phi-bundles at the probe.
    Note 1: The feature format is T:V with (i)PHI removed.
    """
    return not mismatch(unlicensed_phi_features_at_goal(G, PP), set().union(*PP))

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

