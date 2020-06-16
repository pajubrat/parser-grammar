import phrase_structure
import logging
from collections import defaultdict
from support import set_logging, log, get_number_of_operations, reset_number_of_operations, log_result, illu
log = logging.getLogger(__name__)


# Definition for lexical interface
class LexicalInterface:

    # The interface contains a dictionary (surface vocabulary) which holds lexical items
    # The lexicon is a combination of
    #   1. language-invariant morphemes (UG_morphemes)
    #   2. language-specific morphemes and
    #   3. Lexical redundancy rules
    #
    # The dictionary (surface vocabulary) pairs phonological strings (keys) with primitive constituents (values)
    def __init__(self, controlling_parser_process):

        # Definitions for global, contextual variables
        self.controlling_parser_process = controlling_parser_process

        # Phrase structure objects that will hold lexical items
        self.PhraseStructure = phrase_structure.PhraseStructure

        # Lexicon as dictionary
        self.surface_vocabulary = defaultdict(list)

        # Redundancy rules
        self.redundancy_rules = self.load_redundancy_rules(self.controlling_parser_process)

        # Language
        self.language = self.controlling_parser_process.sentence_context.language

    # Definition for the process that reads the redundancy rules from a file
    # Redundancy rules are provided by means of a dictionary such that
    # KEY = antecedent condition (feature)
    # VALUE = list of features that are associated with KEY
    def load_redundancy_rules(self, controlling_parser_process):

        # Dictionary that will host the redundancy rules and will be returned
        d = {}

        # Read the lexical redundancy rules from a file, line by line
        for line in open(controlling_parser_process.sentence_context.redundancy_rules_file):

            # Removes leading and trailing whitespace characters
            line = line.strip()

            # Ignores comment lines
            if not line or line.startswith('#'):
                continue

            # Break the line into keys (antecedents) and features
            key, feature_list = line.split('::', 1)
            key = key.strip()
            # The list of features is the list of strings, separated by space, inside
            feature_list = [f.strip() for f in feature_list.split()]

            # Add the rule into dictionary
            d[key] = feature_list

        return d

    # Definition for process that loads the lexicon into memory
    def load_lexicon(self, controlling_parser_process):

        # Load the language specific lexicon
        self.load_lexicon_(controlling_parser_process.sentence_context.lexicon_file)

        # Load universal morphemes
        # These are combined with the language-specific lexicon, hence combine=True
        self.load_lexicon_(controlling_parser_process.sentence_context.ug_morphemes_file, True)

        return self.surface_vocabulary

    # Definition for the process that loads the language specific lexicon
    def load_lexicon_(self, lexicon_file, combine=False, lines=None):

        if not combine:
            # defaultdict is a dict where new entries are automatically empty objects of given type.
            # so in this case when adding new entries we don't have to start a new list of entries
            # but we can immediately append to it, as it is an empty list: self.d[key].append(const)
            self.surface_vocabulary = defaultdict(list)

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

            # Case 1.
            # The first feature contains morphemic decomposition, we create a special lexical entry
            if '#' in constituent_features[0]:

                # This is morphologically complex word, e.g. 'wonder-#T/fin'
                # lexicon stores an otherwise empty constituent with morphology to show how it decomposes
                const = self.PhraseStructure()
                const.morphology = constituent_features[0]
                const.features = constituent_features[1:]
                self.surface_vocabulary[key].append(const)

            # Case 2.
            # If we are adding lexical items to existing lexicon, and find the same item, we accumulate features
            elif combine and key in self.surface_vocabulary:
                for const in self.surface_vocabulary[key]:
                    const.features = set(const.features) | set(constituent_features)

            # Case 3.
            # Otherwise we add a new entry which has three properties
            # Property 1. The lexical item is a constituent (phrase structure object)
            # Property 2. Feature - means that the item is an inflectional feature
            # Property 3. Redundancy rules and possible lexical parameters are applied
            else:

                # property 1. The lexical item is a constituent (phrase structure object)
                const = self.PhraseStructure()

                # Property 2. Feature - means that the item is an inflectional feature
                if '-' in constituent_features:
                    const.morphology = ''
                else:
                    const.morphology = key

                # Property 3. Redundancy rules and possible lexical parameters are applied
                const.features = self.apply_parameters(self.apply_redundancy_rules(constituent_features))
                self.surface_vocabulary[key].append(const)

        # Return the dictionary
        return self.surface_vocabulary

    # Defines lexical retrieval
    # A constituent X is retrieved on the basis of key K if and only if
    # K matches with value X in the lexicon (dictionary)
    #
    # Note 1: retrieves several lexical constituent is K is ambiguous
    # Note 2: PHON/morphology features internal/incorporated are transformed into syntactic features
    def lexical_retrieval(self, key):

        # Assume that the morpheme is neither internal nor incorporated
        # Internal and incorporated are features provided by PHON/morphology
        internal = False
        incorporated = False

        # A morpheme symbol that ends with $ is an internal item
        if key.endswith('$'):
            key = key[:-1]
            internal = True

        # A morpheme string that ends with = is an incorporated item
        if key.endswith('='):
            key = key[:-1]
            incorporated = True

        # If the key K is found from the dictionary, it will return a constituent value
        if key in self.surface_vocabulary:

            # Copy lexical items matching with the key from the lexicon
            word_list = [const.copy() for const in self.surface_vocabulary[key]]

            # If the morpheme was internal, we mark the constituent(s) as internal for syntax
            if internal:
                for const in word_list:

                    # Mark this constituent (if not inflectional) as word-internal,
                    # so that it's merge solution is always COMP
                    if const.morphology:
                        const.internal = True

            # If the morpheme was incorporated, we mark the constituent(s) as incorporated for syntax
            if incorporated:
                for const in word_list:
                    const.incorporated = True

        # If the morpheme was not found, we create a placeholder item
        else:
            const = self.PhraseStructure()
            const.features = {'PF:?', 'CAT:?'}  # If the word is not found, we will still create it
            const.morphology = key
            const.internal = internal
            word_list = [const]

        return word_list

    # Definition for the application of the redundancy rules
    # Maps the old feature set (input) into new feature set (output)
    def apply_redundancy_rules(self, features):

        # Internal definition for the notion of negative feature
        def negative_feature(f):
            if f.startswith('-'):
                return True
            return False

        # Internal definition for feature conflict
        #
        # Note: Prevents new features from redundancy rules to get added if they conflict with a lexical rule
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

        features = set(features)
        new_features_to_add = set()

        # Include features of a lexical redundancy rule when the antecedent features are matched
        for f in self.redundancy_rules:
            trigger_set = set(f.split())
            if features & trigger_set == trigger_set:
                new_features_to_add |= set(self.redundancy_rules[f])

        # Resolve conflicts in favor of lexical features
        # new_feats contains new features from lexical redundancy rule to be added
        #
        # Note: language-specific features outperform redundancy rules
        for new_feature in new_features_to_add:
            if not feature_conflict(new_feature, features):
                features.add(new_feature)
        return features

    # Binary UG parameters
    # There are certain binary UG parameters that are "mirrored" in the lexicon in the sense that
    # lexical features occur in clusters, but this whole notion is controversial and possibly
    # inexistent
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

        return self.create_combined_lexical_categories(remove_redundancies(features))

    def create_combined_lexical_categories(self, features):

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

    def save_surface_vocabulary(self, file_name):
        results_file = open(file_name, "w", -1, "utf-8")

        for key in self.surface_vocabulary:
            for lexical_item in self.surface_vocabulary[key]:
                value =str(lexical_item.features)
                string = f'{key:<15} {value:<10}' + '\n'
                results_file.write(string)
