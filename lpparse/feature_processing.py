def unvalued(f):
    return f[:4] == 'PHI:' and f[-1] == '_'

def valued(f):
    return not unvalued(f)

def phi_feature(f):
    return 'PHI:' in f

def interpretable_phi_feature(f):
    return 'iPHI:' in f

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


def phi_consistency(phi_set):
    def is_valued_phi_feature(f):
        return f[:4] == 'PHI:' and f[-1] != '_'

    def phi_conflict(f, g):
        def deconstruct_phi_feature(f):
            return f.split(':')[1], f.split(':')[2]

        f_type, f_value = deconstruct_phi_feature(f)
        g_type, g_value = deconstruct_phi_feature(g)
        if f_type == g_type and f_value != g_value:
            return True

    for f in phi_set:
        if is_valued_phi_feature(f):
            for g in phi_set:
                if is_valued_phi_feature(g):
                    if phi_conflict(f, g):
                        return False
    return True
