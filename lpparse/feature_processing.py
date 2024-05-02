def clean_string(str):
    str.strip()
    str = str.replace('\t', '')
    str = str.replace(' ', '')
    return str

def mandatory(f):
    return f.startswith('!')

def illicit(f):
    return f.startswith('-')

def convert_features_for_parsing(features):
    return {f[1:] if f.startswith('!') else f for f in features}

def negative_features(features_to_check):
    return {feature[1:] for feature in features_to_check if feature[0] == '*'}

def positive_features(features_to_check):
    return {feature for feature in features_to_check if feature[0] != '*' and feature[0] != '$'}

def well_formed_phi_level_feature(f):
    return f.startswith('Φ/') and f[2].isdigit()


