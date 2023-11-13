def unvalued(f):
    return f[:4] == 'PHI:' and f[-1] == '_'

def valued(f):
    return not unvalued(f)

def phi_feature(f):
    return 'PHI:' in f

def interpretable_phi_feature(f):
    return f.startswith('iPHI')

def interpretable_phi_features(probe):
    return {phi for phi in probe.head().features if interpretable_phi_feature(phi)}

def type_value_mismatch(p, g):
    return p.split(':')[0] == g.split(':')[0] and p.split(':')[1] != g.split(':')[1]

def feature_licensing(G, PP):
    if not PP:
        return True
    for P in PP:
        if P <= G:                                  # Verify that there is P such that P subset of G (licensing).
            for g in G - P:                         # Verify that unlicensed (G - PP) are not contradicted
                for p in set().union(*PP):          # Examine each individual phi-feature at the probe
                    if type_value_mismatch(p, g):
                        return False
            return True


def unvalued_phi_feature(f):
    return phi_feature(f) and f[-1] == '_'

def valued_phi_feature(f):
    return phi_feature(f) and f[-1] != '_'

def i(phi):
    if interpretable_phi_feature(phi):
        return phi[5:]
    return phi

def exactly_one_PHI():
    return 'DPF*'

def at_least_one_PHI():
    return 'DPF'

def convert_features_for_parsing(features):
    return {f[1:] if f.startswith('!') else f for f in features}


def feature_check(antecedent_feature, probe_feature):
    return antecedent_feature == probe_feature or (probe_feature[-1] == '_' and antecedent_feature[:len(probe_feature[:-1])] == probe_feature[:-1])


def negative_features(features_to_check):
    return {feature[1:] for feature in features_to_check if feature[0] == '*'}


def positive_features(features_to_check):
    return {feature for feature in features_to_check if feature[0] != '*' and feature[0] != '$'}



