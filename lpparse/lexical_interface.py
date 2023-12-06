import phrase_structure
from collections import defaultdict
from operator import itemgetter
from lexical_item import LexicalItem
from support import log

MBOUNDARY = ('#', '_')

# Definition for lexical interface
class LexicalInterface:
    def __init__(self, speaker_model):
        self.speaker_model = speaker_model
        self.PhraseStructure = phrase_structure.PhraseStructure
        self.surface_lexicon = defaultdict(list)
        self.redundancy_rules = self.load_redundancy_rules(self.speaker_model)
        self.language = self.speaker_model.language

    def lexical_retrieval(self, phon):
        log(f'\n\tNext word /{phon}/')
        phon, onset, offset = self.phonological_context(phon)
        if phon in self.surface_lexicon:
            lexical_items_lst = [lex.copy().set_phonological_context(onset, offset) for lex in self.surface_lexicon[phon] if
                                 self.language_match(lex) and self.phonological_context_match(lex, onset, offset)]
        else:
            lexical_items_lst = [self.unknown_word(phon)]
        self.log_lexical_items(phon, lexical_items_lst)
        return lexical_items_lst

    def log_lexical_items(self, phon, lst):
        log(f' => ')
        for i, lex in enumerate(lst):
            if lex:
                if lex.morphological_chunk:
                    log(f'{lex.morphological_chunk}')
                else:
                    log(f'({i+1}) {lex}° ')

    def phonological_context_match(self, lex, onset, offset):
        for pfc in [f[3:] for f in lex.features if f.startswith('PC')]:
            if (pfc[0] != 'X' and pfc[0] != onset) or (pfc[-1] != 'X' and pfc[-1] != offset):
                return False
        return True

    def phonological_context(self, phon):
        onset = ''
        offset = ''
        if phon.startswith(MBOUNDARY):
            onset = phon[0]
        if phon.endswith(MBOUNDARY):
            offset = phon[-1]
        return phon[len(onset):len(phon)-len(offset)], onset, offset

    def unknown_word(self, phonological_entry):
        lex = LexicalItem()
        lex.features = {f'PF:{phonological_entry}', '?'}
        lex.name = '?'
        if '#' in phonological_entry:
            lex.morphological_chunk = phonological_entry
            lex.internal = True
        else:
            log(f' = UNRECOGNIZED WORD (processing will terminate)')
            self.speaker_model.exit = True
        return lex

    def language_match(self, lex):
        return self.language in lex.language

    def apply_redundancy_rules(self, features):
        def feature_conflict(new_candidate_feature_to_add, features_from_lexicon):
            return (new_candidate_feature_to_add.startswith('-') and new_candidate_feature_to_add[1:] in features_from_lexicon) or \
                   (not new_candidate_feature_to_add.startswith('-') and '-' + new_candidate_feature_to_add in features_from_lexicon)

        feature_set = set(features)
        new_features_to_add = set()

        # Apply the redundancy rules to the feature set
        for i in range(2):                                                  #   Apply twice (so as to allow added features to trigger further rules)
            for f in self.redundancy_rules:
                antecedent_trigger_set = set(f.split())
                if antecedent_trigger_set <= feature_set:                   #   If the antecedent features all match,
                    new_features_to_add |= set(self.redundancy_rules[f])    #   we add the redundancy features

            # Resolve conflicts in favor of language specific lexical features
            features_not_blocked_by_language_specific_lexicon = set()
            for new_feature in new_features_to_add:
                if not feature_conflict(new_feature, feature_set):
                    features_not_blocked_by_language_specific_lexicon.add(new_feature)
            feature_set |= features_not_blocked_by_language_specific_lexicon
        return feature_set

    def load_redundancy_rules(self, speaker_model):
        redundancy_rules_dict = {}
        for line in open(speaker_model.local_file_system.external_sources["redundancy_rules"], encoding='utf8'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            antecedent_trigger, feature_list = line.split('::', 1)
            antecedent_trigger = antecedent_trigger.strip()
            feature_list = [f.strip() for f in feature_list.split()]
            if antecedent_trigger in redundancy_rules_dict.keys():
                redundancy_rules_dict[antecedent_trigger] = redundancy_rules_dict[antecedent_trigger] + feature_list
            else:
                redundancy_rules_dict[antecedent_trigger] = feature_list
        return redundancy_rules_dict

    def load_lexicon(self, local_file_system):
        # Load language-specific lexical entries
        self.load_lexicon_(local_file_system.external_sources["lexicon_file_name"])
        # Load universal morphemes
        self.load_lexicon_(local_file_system.external_sources["ug_morphemes"], True)

    def load_lexicon_(self, lexicon_file, combine=False):

        # Determines if we create the dictionary anew (combine = False) or
        # add to an existing one by reading additional files (Combine = True)
        if not combine:
            self.surface_lexicon = defaultdict(list)
            self.surface_lexicon = defaultdict(list)

        # Read the entries from the lexicon file (each line = one lexical entry)
        lexical_entries = []
        if lexicon_file:
            lexical_entries = open(lexicon_file, encoding='utf8').readlines()

        # Process the file line-by-line (entry-by-entry)
        for line in lexical_entries:
            line = line.strip()                                                 #   remove extra spaces
            if not line or line.startswith('#'):                                #   Ignore comments and empty lines
                continue
            phonological_entry, lexical_features = line.split('::', 1)          #   Separate key and value, by symbol '::'
            phonological_entry = phonological_entry.strip()                     #   Remove extra spaces
            lexical_features = [f.strip() for f in lexical_features.split()]    #   Create the feature list
            if not {f for f in lexical_features if f[:4] == 'LANG'}:            #   If no language is specified for the lexical entry, add it
                lexical_features.append(self.language)
            lex = LexicalItem(phonological_entry, self.apply_redundancy_rules(lexical_features))
            self.surface_lexicon[phonological_entry].append(lex)
