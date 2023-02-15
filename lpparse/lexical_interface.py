import phrase_structure
from support import log
from collections import defaultdict
from operator import itemgetter

# Definition for lexical interface
class LexicalInterface:
    def __init__(self, controlling_parser_process):
        self.controlling_parser_process = controlling_parser_process
        self.PhraseStructure = phrase_structure.PhraseStructure
        self.surface_vocabulary = defaultdict(list)
        self.redundancy_rules = self.load_redundancy_rules(self.controlling_parser_process)
        self.language = self.controlling_parser_process.language

    def load_redundancy_rules(self, controlling_parser_process):
        redundancy_rules_dict = {}
        for line in open(controlling_parser_process.local_file_system.external_sources["redundancy_rules"], encoding='utf8'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            antecedent_trigger, feature_list = line.split('::', 1)
            antecedent_trigger = antecedent_trigger.strip()
            feature_list = [f.strip() for f in feature_list.split()]
            redundancy_rules_dict[antecedent_trigger] = feature_list
        return redundancy_rules_dict

    def load_lexicon(self, controlling_parser_process):
        self.load_lexicon_(controlling_parser_process.local_file_system.external_sources["lexicon_file_name"])
        self.load_lexicon_(controlling_parser_process.local_file_system.external_sources["ug_morphemes"], True)
        return self.surface_vocabulary

    def load_lexicon_(self, lexicon_file, combine=False, lines=None):

        # Determines if we create the dictionary anew or add to an existing one
        if not combine:
            self.surface_vocabulary = defaultdict(list)

        lines = lines or []
        if lexicon_file:
            lines = open(lexicon_file, encoding='utf8').readlines()

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

            lexical_features.append('PHON')

            # If the word is complex, we treat it differently
            if '#' in lexical_features[0]:
                const = self.PhraseStructure()
                const.morphology = lexical_features[0]
                const.features = set(lexical_features[1:])
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

        # A morpheme symbol that ends with $ is a word internal item
        if phonological_entry.endswith('$'):
            phonological_entry = phonological_entry[:-1]
            internal = True

        # A morpheme string that ends with = is an incorporated item
        if phonological_entry.endswith('='):
            phonological_entry = phonological_entry[:-1]
            incorporated = True

        # If a matching element is found from the dictionary, it will return a list of constituents
        # These constituents contain raw morphological strings
        morpheme_lst = []
        if phonological_entry in self.surface_vocabulary:
            morpheme_lst = [const.copy() for const in self.surface_vocabulary[phonological_entry] if self.language_match(const)]

            # Add internal/incorporation information to each
            if internal:
                for const in morpheme_lst:
                    if const.morphology:
                        const.internal = True
            if incorporated:
                for const in morpheme_lst:
                    const.incorporated = True

        if not morpheme_lst:
            const = self.PhraseStructure()
            const.features = {'PF:?', '?'}
            const.morphology = phonological_entry
            const.internal = internal
            morpheme_lst = [const]

        if len(morpheme_lst) > 1:
            morpheme_lst = self.rank_lexical_items(morpheme_lst)
            log(f'\n\tRetrieved:')
            for idx, word in enumerate(morpheme_lst, start=1):
                log(f'\n\t\t({idx}) {phonological_entry} {word.features}')
            log('\n\t\t')
        return morpheme_lst

    def language_match(self, const):
        return 'LANG:XX' in const.features or self.language in const.features

    def rank_lexical_items(self, word_list):
        def frequency(word):
            for f in word.features:
                if f[:5] == 'FREQ:':
                    return int(f[5:])
            return 0
        ranked_list = [(word, frequency(word)) for word in word_list]
        ranked_list.sort(key=itemgetter(1), reverse=True)
        return [word for (word, freq) in ranked_list]

    def apply_redundancy_rules(self, features):
        def negative_feature(f):
            if f.startswith('-'):
                return True

        def feature_conflict(new_candidate_feature_to_add, features_from_lexicon):
            if negative_feature(new_candidate_feature_to_add):
                if new_candidate_feature_to_add[1:] in features_from_lexicon:
                    return True
            if not negative_feature(new_candidate_feature_to_add):
                if '-' + new_candidate_feature_to_add in features_from_lexicon:
                    return True

        # ---- main function -----#
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

        # Add language if it is missing
        for f in features:
            if f[:4] == 'LANG':
                language_specific = True
        if not language_specific:
            features.add(self.language)

        # ARG and VAL feature distribution
        if 'ARG' in features:
            if 'NO_NUMBER' not in features:
                features.add('PHI:NUM:_')
            if 'NO_PERSON' not in features:
                features.add('PHI:PER:_')
            if 'NO_DET' not in features:
                features.add('PHI:DET:_')
            if {'LANG:IT', 'LANG:EN'} & features:
                features.add('PHI:GEN:_')

        return features