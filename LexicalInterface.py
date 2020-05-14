import phrase_structure
import logging
from collections import defaultdict
from support import set_logging, log, get_number_of_operations, reset_number_of_operations, log_result, illu
log = logging.getLogger(__name__)


# Lexicon
class LexicalInterface:

    # The interface contains a dictionary which holds the lexical items
    # The lexicon is a combination of language-invariant morphemes (UG_morphemes) and language-specific morphemes
    def __init__(self, controlling_parser_process):
        self.controlling_parser_process = controlling_parser_process
        self.PhraseStructure = phrase_structure.PhraseStructure
        self.lexicon_dictionary = defaultdict(list)
        self.redundancy_rules = self.load_redundancy_rules(self.controlling_parser_process)
        self.language = self.controlling_parser_process.sentence_context.language

    def load_redundancy_rules(self, controlling_parser_process):
        d = {}
        for line in open(controlling_parser_process.sentence_context.redundancy_rules_file):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            key, feats = line.split('::', 1)
            key = key.strip()
            feats = [f.strip() for f in feats.split()]
            d[key] = feats
        return d

    def load_lexicon(self, controlling_parser_process):
        self.load_lexicon_(controlling_parser_process.sentence_context.lexicon_file)
        self.load_lexicon_(controlling_parser_process.sentence_context.ug_morphemes_file, True)
        return self.lexicon_dictionary

    def load_lexicon_(self, lexicon_file, combine=False, lines=None):

        if not combine:
            # defaultdict is a dict where new entries are automatically empty objects of given type.
            # so in this case when adding new entries we don't have to start a new list of entries
            # but we can immediately append to it, as it is an empty list: self.d[key].append(const)
            self.lexicon_dictionary = defaultdict(list)

        lines = lines or []

        # Read the lexicon from the file
        if lexicon_file:
            lines = open(lexicon_file).readlines()

        # Go through the lexicon file line by line
        for line in lines:
            line = line.strip()

            # Ignore comments
            if not line or line.startswith('#'):
                continue

            # Split into keys and lexical information
            key, constituent_features = line.split('::', 1)
            key = key.strip()

            # Use space to extract features
            constituent_features = [f.strip() for f in constituent_features.split()]

            # If the first feature contains morpheme information, we create a special higher level entry
            if '#' in constituent_features[0]:
                # This is morphologically complex word, e.g. 'wonder-#T/fin'
                # lexicon stores an otherwise empty constituent with morphology to show how it decomposes
                const = self.PhraseStructure()
                const.morphology = constituent_features[0]
                const.features = constituent_features[1:]
                self.lexicon_dictionary[key].append(const)

            # If we are adding lexical items to existing lexicon, we accumulate features if key exists already
            elif combine and key in self.lexicon_dictionary:
                for const in self.lexicon_dictionary[key]:
                    const.features = set(const.features) | set(constituent_features)
            # Otherwise we add a new entry
            else:
                # Creating new word entry
                const = self.PhraseStructure()

                # Constituents that have feature '-' are inflectional and have no morphological decomposition
                if '-' in constituent_features:
                    const.morphology = ''
                else:
                    const.morphology = key

                # Every new lexical item must be applied (i) redundancy rules and (ii) parameters
                const.features = self.apply_parameters(self.apply_redundancy_rules(constituent_features))
                self.lexicon_dictionary[key].append(const)

        # Show the lexicon
        # for key, value in self.d.items():
        #     print(key, str(value[0].features))
        return self.lexicon_dictionary

    # Accesses the lexicon (lexicon_dictionary) based on a key
    def access_lexicon(self, key):
        internal = False
        # Word-internal pronouncing is marked by $ by morphological decomposing
        # Here it is removed and converted into a feature
        internal = False
        incorporated = False
        if key.endswith('$'):
            key = key[:-1]
            internal = True
        if key.endswith('='):
            key = key[:-1]
            incorporated = True
        if key in self.lexicon_dictionary:
            # Copy lexical items from the lexicon
            word_list = [const.copy() for const in self.lexicon_dictionary[key]]
            if internal:
                for const in word_list:
                    # Mark this constituent (if not inflectional) as word-internal,
                    # so that it's merge solution is always COMP
                    if const.morphology:
                        const.internal = True
            if incorporated:
                for const in word_list:
                    const.incorporated = True
        else:
            # Create placeholder if the item was not recognized
            const = self.PhraseStructure()
            const.features = {'PF:?', 'CAT:?'}  # If the word is not found, we will still create it
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
        def feature_conflict(new_candidate_feature_to_add, features_from_lexicon):

            # If we try to add a negative feature -F, we reject if there is a positive feature
            # either +F or F.
            if negative_feature(new_candidate_feature_to_add):
                if new_candidate_feature_to_add[1:] in features_from_lexicon:
                    return True
            # If we try to add a positive feature, we reject if there is a negative feature
            if not negative_feature(new_candidate_feature_to_add):
                if '-' + new_candidate_feature_to_add in features_from_lexicon:
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

        # This will add unvalued (D_, PHI_) for each +ARG head and promotes ARG also into the status of a label
        # ARG:  uninterpretable phi-set, unsaturated predicate
        # VAL:  whether agreement reconstruction can value D_, PHI_
        if 'ARG' in features:
            features.add('CAT:ARG')
            if 'NO_NUMBER' not in features:
                features.add('PHI:NUM:_')
            if 'NO_PERSON' not in features:
                features.add('PHI:PER:_')
            if 'NO_DET' not in features:
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
