import phrase_structure
import logging
from collections import defaultdict
log = logging.getLogger(__name__)


# Lexicon
class LexicalInterface:

    # The interface contains a dictionary which holds the lexical items
    # The lexicon is a combination of language-invariant morphemes (UG_morphemes) and language-specific morphemes
    def __init__(self, redundancy_rules_file='redundancy_rules.txt'):
        self.PhraseStructure = phrase_structure.PhraseStructure
        self.d = defaultdict(list)
        self.redundancy_rules = self.load_redundancy_rules(redundancy_rules_file)
        self.language = ''

    def load_redundancy_rules(self, file):
        d = {}
        for line in open(file):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            key, feats = line.split('::', 1)
            key = key.strip()
            feats = [f.strip() for f in feats.split()]
            d[key] = feats
        return d

    def load_lexicon(self, file='', language='LANG:EN', combine=False, lines=None):

        self.language = language

        if not combine:
            # defaultdict is a dict where new entries are automatically empty objects of given type.
            # so in this case when adding new entries we don't have to start a new list of entries
            # but we can immediately append to it, as it is an empty list: self.d[key].append(const)
            self.d = defaultdict(list)

        lines = lines or []
        if file:
            lines = open(file).readlines()

        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            key, feats = line.split('::', 1)
            key = key.strip()
            feats = [f.strip() for f in feats.split()]
            if '#' in feats[0]:
                # This is morphologically complex word, e.g. 'wonder-#T/fin'
                # lexicon stores an otherwise empty constituent with morphology to show how it decomposes
                const = self.PhraseStructure()
                const.morphology = feats[0]
                const.features = feats[1:]
                self.d[key].append(const)
            elif combine and key in self.d:
                # When combining lexicons (e.g. adding universal morphemes), instead of creating new word entries,
                # features from new lexicon are added to words found from old lexicon.
                for const in self.d[key]:
                    const.features = set(const.features) | set(feats)
            else:
                # Creating new word entry
                const = self.PhraseStructure()
                # constituents that should have no morphology have feature '-'
                const.morphology = key if '-' not in feats else ''
                const.features = self.apply_parameters(self.apply_redundancy_rules(feats))
                self.d[key].append(const)

        # Show the lexicon
        # for key, value in self.d.items():
        #   print(key, str(value[0].features))
        return self.d

    def access_lexicon(self, key):
        """ This function will take a literal string as input, finds all lexical items that match it and returns
        copies of them. If the input is not recognized, an ad hoc lexical item is created.
        """
        internal = False
        # Word-internal pronouncing is marked by $ by morphological decomposing
        if key.startswith('$'):
            key = key[1:]
            internal = True
        if key in self.d:
            word_list = [const.copy() for const in self.d[key]]
            if internal:
                for const in word_list:
                    # Mark this constituent (if not inflectional) as word-internal,
                    # so that it's adjunction option is always COMP
                    if const.morphology:
                        const.internal = True
        else:
            const = self.PhraseStructure()
            const.features = {'PF:?', 'CAT:X'}  # If the word is not found, we will still create it
            const.morphology = key
            const.internal = internal
            word_list = [const]

        return word_list

    def apply_redundancy_rules(self, feats):

        def negative_feature(f):
            if f.startswith('-'):
                return True
            return False

        # Prevents new features from redundancy rules to get added if they conflict with a lexical rule
        # todo suboptimal because F and +F both mean the same must be fixed
        def feature_conflict(new_candidate_feature_to_add, features_from_lexicon):

            # If we try to add a negative feature -F, we reject if there is a positive feature
            # either +F or F.
            if negative_feature(new_candidate_feature_to_add):
                if new_candidate_feature_to_add[1:] in features_from_lexicon:
                    return True
            # If we try to add a positive feature, we reject if there is a negative feature
            if not negative_feature(new_candidate_feature_to_add):
                if '-' + new_candidate_feature_to_add[1:] in features_from_lexicon:
                    return True
            return False

        feats = set(feats)
        new_feats = set()
        for feat in feats:
            # If a feature is found in the redundancy rules
            if feat in self.redundancy_rules:
                # the rule set from redundancy rules will be transferred
                new_feats |= set(self.redundancy_rules[feat])
        # order of features added by redundancy rules affects whether they conflict or not. Sorting them here causes
        # that features starting with '-' are added first and possible positive features are then in conflict and get
        # not added.
        for new_feat in sorted(new_feats):
            if not feature_conflict(new_feat, feats):
                feats.add(new_feat)
        return feats

    # Binary UG parameters
    # There are certain binary UG parameters that are "mirrored" in the lexicon in the sense that
    # lexical features occur in clusters,
    #
    # todo, this is not the right way, but it works for now
    def apply_parameters(self, features):
        def remove_redundancies(features):
            new_set = set()
            # -SPEC:* eliminates all specific Spec features
            if '-SPEC:*' in features:
                for f in features:
                    if not f[:6] == '-SPEC:':
                        new_set.add(f)
                new_set.add('-SPEC:*')
            else:
                return features
            return new_set

        features = set(features)

        # Check if the word is language-specific
        language_specific = False
        for f in features:
            if f[:4] == 'LANG':
                language_specific = True

        if not language_specific:
            features.add(self.language)

        # Parameter 1. Rich finite agreement
        if 'LANG:EN' in features:
            rich_finite_agreement = False
        else:  # default
            rich_finite_agreement = True

        # Parameter 2. Non-finite agreement (probably not needed anymore)
        if 'LANG:FI' in features:
            non_finite_agreement = True
        else:  # default
            non_finite_agreement = False

        # Parameter 3, Grammaticalized gender (probably will be just a list of grammaticalized phi-features)
        if 'LANG:IT' or 'LANG:EN' in features:
            gender = True
        else:
            gender = False

        if 'LANG:FI' in features:
            gender = False

        # ----- Effects of parameters ----- #

        # This will add unvalued (uD, up) for each +ARGG head and promotes ARG also into the status of a label
        if 'ARG' in features:
            features.add('CAT:ARG')
            features.add('PHI:PER:_')
            features.add('PHI:NUM:_')
            features.add('PHI:DET:_')
            if gender:
                features.add('PHI:GEN:_')
            if 'VAL' in features:
                features.add('SPEC:*')
                features.add('!SPEC:*')

        if '-ARG' in features:
            features.add('CAT:-ARG')

        if non_finite_agreement:  # Finnish operator snowballing
            if 'CAT:uWH' in features and not 'CAT:FORCE' in features:
                features.add('!SPEC:uWH')

        return self.create_combined_categories(remove_redundancies(features))

    def create_combined_categories(self, features):

        cat_string = ''
        # Create a list of categorical features
        cc_ = [f[4:] for f in features if f[:4] == 'CAT:']
        cc_.sort()
        if cc_:
            for f in cc_:
                if len(cat_string) == 0:
                    cat_string = cat_string + f
                else:
                    cat_string = cat_string + '/' + f

            features.add('CAT:' + cat_string)

        return features