def unvalued(f):
    return f[:4] == 'PHI:' and f[-1] == '_' and f[:7] != 'PHI:DET'

def convert_features_for_parsing(features):
    return {f[1:] if f.startswith('!') else f for f in features}

def feature_check(antecedent_feature, probe_feature):
    return antecedent_feature == probe_feature or (probe_feature[-1] == '_' and antecedent_feature[:len(probe_feature[:-1])] == probe_feature[:-1])

def negative_features(features_to_check):
    return {feature[1:] for feature in features_to_check if feature[0] == '*'}

def positive_features(features_to_check):
    return {feature for feature in features_to_check if feature[0] != '*' and feature[0] != '$'}
