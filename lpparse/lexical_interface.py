import phrase_structure
from collections import defaultdict
from lexical_item import LexicalItem
from support import log, log_instance

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

    def phonological_context(self, phon):
        onset = ''
        offset = ''
        if not phon.startswith(MBOUNDARY):
            if self.speaker_model.embedding > 0:
                self.speaker_model.embedding -= 1
        if not phon.startswith(MBOUNDARY) and not phon.endswith(MBOUNDARY):
            return phon, '_', '_'
        if phon.startswith(MBOUNDARY):
            onset = phon[0]
        if phon.endswith(MBOUNDARY):
            offset = phon[-1]
        return phon[len(onset):len(phon)-len(offset)], onset, offset

    def log_lexical_items(self, phon, lst):
        log(f' => ')
        for i, lex in enumerate(lst):
            if lex:
                if lex.morphological_chunk:
                    log(f'morphological chunk [{lex.morphological_chunk}] => ')
                else:
                    log(f'({i+1}) {lex}° ')

    def phonological_context_match(self, lex, onset, offset):
        for pfc in [f[3:] for f in lex.features if f.startswith('PC')]:
            if (pfc[0] != 'X' and pfc[0] != onset) or (pfc[-1] != 'X' and pfc[-1] != offset):
                return False
        return True

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
        return (self.language in lex.language) or (lex.language == 'LANG:X')

    def apply_redundancy_rules(self, features):
        def feature_conflict(new_feature, features_from_lexicon):
            return (new_feature.startswith('-') and (new_feature[1:] in features_from_lexicon or '!' + new_feature[1:] in features_from_lexicon)) or \
                   (not new_feature.startswith('-') and '-' + new_feature in features_from_lexicon)

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

    def load_lexicons(self, local_file_system):
        self.surface_lexicon = defaultdict(list)
        for lexicon_file in list(local_file_system.settings['lexicons']):
            self.load_lexicon(local_file_system.folder['lexicon'] / lexicon_file)

    def load_lexicon(self, lexicon_file):

        # Read the entries from the lexicon file (each line = one lexical entry)
        lexical_entries = []
        if lexicon_file:
            lexical_entries = open(lexicon_file, encoding='utf8').readlines()

        # Process the file line-by-line (entry-by-entry)
        for line in lexical_entries:
            line = line.strip()                                                 #   remove extra spaces
            if not line or line.startswith('#'):                                #   Ignore comments and empty lines
                continue
            phonological_entries, lexical_features = line.split('::', 1)        #   Separate key and value, by symbol '::'
            phonological_entries = phonological_entries.strip().split(',')      #   Remove extra spaces, create set of allomorphs
            lexical_features = [f.strip() for f in lexical_features.split()]    #   Create the feature list
            if not {f for f in lexical_features if f[:4] == 'LANG'}:            #   If no language is specified for the lexical entry, add it
                lexical_features.append(self.language)
            for p in phonological_entries:
                lex = LexicalItem(p, self.apply_redundancy_rules(lexical_features))
                self.surface_lexicon[p].append(lex)
