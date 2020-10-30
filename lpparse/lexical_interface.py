import phrase_structure
from support import log
from collections import defaultdict

# Definition for lexical interface
class LexicalInterface:
    def __init__(self, controlling_parser_process):
        self.controlling_parser_process = controlling_parser_process
        self.PhraseStructure = phrase_structure.PhraseStructure
        self.surface_vocabulary = defaultdict(list)
        self.redundancy_rules = self.load_redundancy_rules(self.controlling_parser_process)
        self.language = self.controlling_parser_process.language

    # Definition for the process that reads the redundancy rules from a file
    def load_redundancy_rules(self, controlling_parser_process):
        redundancy_rules_dict = {}
        for line in open(controlling_parser_process.local_file_system.external_sources["redundancy_rules"]):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            antecedent_trigger, feature_list = line.split('::', 1)
            antecedent_trigger = antecedent_trigger.strip()
            feature_list = [f.strip() for f in feature_list.split()]
            redundancy_rules_dict[antecedent_trigger] = feature_list
        return redundancy_rules_dict

    # Definition for process that loads the lexicon into memory
    def load_lexicon(self, controlling_parser_process):
        self.load_lexicon_(controlling_parser_process.local_file_system.external_sources["lexicon_file_name"])
        self.load_lexicon_(controlling_parser_process.local_file_system.external_sources["ug_morphemes"], True)
        return self.surface_vocabulary

    # Definition for the process that loads the language specific lexicon
    def load_lexicon_(self, lexicon_file, combine=False, lines=None):

        # Determines if we create the dictionary anew or add to an existing one
        if not combine:
            self.surface_vocabulary = defaultdict(list)

        lines = lines or []
        if lexicon_file:
            lines = open(lexicon_file).readlines()

        # Read the lexical file line-by-line
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):    #  Ignore comments
                continue
            phonological_entry, lexical_features = line.split('::', 1)
            phonological_entry = phonological_entry.strip()
            lexical_features = [f.strip() for f in lexical_features.split()]
            if not {f for f in lexical_features if f[:4] == 'LANG'}:
                lexical_features.append(self.language)

            # If the word is complex, we treat it differently
            if '#' in lexical_features[0]:
                const = self.PhraseStructure()
                const.morphology = lexical_features[0]
                const.features = lexical_features[1:]
                self.surface_vocabulary[phonological_entry].append(const)

            # If we are adding to existing lexicon, and find the same item, we accumulate features
            elif combine and phonological_entry in self.surface_vocabulary:
                for const in self.surface_vocabulary[phonological_entry]:
                    const.features = set(const.features) | set(lexical_features)

            # Add a new entry
            else:
                new_const = self.PhraseStructure()
                if 'inflectional' in lexical_features or '-' in lexical_features:
                    new_const.morphology = ''
                else:
                    new_const.morphology = phonological_entry
                new_const.features = self.apply_parameters(self.apply_redundancy_rules(lexical_features))
                self.surface_vocabulary[phonological_entry].append(new_const)
        return self.surface_vocabulary

    # Defines lexical retrieval
    def lexical_retrieval(self, phonological_entry):
        internal = False
        incorporated = False

        # A morpheme symbol that ends with $ is an internal item
        if phonological_entry.endswith('$'):
            phonological_entry = phonological_entry[:-1]
            internal = True

        # A morpheme string that ends with = is an incorporated item
        if phonological_entry.endswith('='):
            phonological_entry = phonological_entry[:-1]
            incorporated = True

        # If the key K is found from the dictionary, it will return a constituent value
        if phonological_entry in self.surface_vocabulary:
            word_list = [const.copy() for const in self.surface_vocabulary[phonological_entry]]
            if internal:
                for const in word_list:
                    if const.morphology:
                        const.internal = True
            if incorporated:
                for const in word_list:
                    const.incorporated = True
        else:
            const = self.PhraseStructure()
            const.features = {'PF:?', '?'}
            const.morphology = phonological_entry
            const.internal = internal
            word_list = [const]

        if len(word_list) > 1:
            log(f'{phonological_entry} is {len(word_list)}-way ambiguous...')
        return word_list

    # Definition for the application of the redundancy rules
    def apply_redundancy_rules(self, features):

        # Internal definition for the notion of negative feature
        def negative_feature(f):
            if f.startswith('-'):
                return True

        # Internal definition for feature conflict
        def feature_conflict(new_candidate_feature_to_add, features_from_lexicon):
            if negative_feature(new_candidate_feature_to_add):
                if new_candidate_feature_to_add[1:] in features_from_lexicon:
                    return True
            if not negative_feature(new_candidate_feature_to_add):
                if '-' + new_candidate_feature_to_add in features_from_lexicon:
                    return True

        feature_set = set(features)
        new_features_to_add = set()

        # Include features of a lexical redundancy rule when the antecedent features are matched
        for f in self.redundancy_rules:
            antecedent_trigger_set = set(f.split())
            if feature_set & antecedent_trigger_set == antecedent_trigger_set:
                new_features_to_add |= set(self.redundancy_rules[f])

        # Resolve conflicts in favor of lexical features
        features_not_blocked_by_specific_lexicon = set()
        for new_feature in new_features_to_add:
            if not feature_conflict(new_feature, feature_set):
                features_not_blocked_by_specific_lexicon.add(new_feature)
        feature_set |= features_not_blocked_by_specific_lexicon
        return feature_set

    def apply_parameters(self, features):
        features = set(features)
        language_specific = False

        for f in features:
            if f[:4] == 'LANG':
                language_specific = True
        if not language_specific:
            features.add(self.language)

        if 'LANG:FI' in features:
            non_finite_agreement = True
        else:  # default
            non_finite_agreement = False

        if 'LANG:IT' or 'LANG:EN' in features:
            gender = True
        else:
            gender = False

        if 'LANG:FI' in features:
            gender = False

        # ----- Effects of parameters ----- #
        if 'ARG' in features:
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
                # features.add('!SPEC:*')

        # Finnish operator snowballing
        if non_finite_agreement:
            if 'OP:_' in features and 'FORCE' not in features:
                operator_features = {'OP:WH', 'OP:TOP', 'OP:FOC'}
                if not operator_features & features:
                    features.add('!SPEC:OP:_')

        return features