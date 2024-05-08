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
        self.speaker_lexicon = defaultdict(list)
        self.redundancy_rules = self.load_redundancy_rules()
        self.language = self.speaker_model.language

    def lexical_retrieval(self, phon):
        log(f'\n\tNext morpheme /{phon}/ retrieves ')
        phon, onset, offset = self.phonological_context(phon)
        if phon in self.speaker_lexicon:
            lexical_items_lst = [lex.copy().set_phonological_context(onset, offset) for lex in self.speaker_lexicon[phon] if
                                 self.language_match(lex) and self.phonological_context_match(lex, onset, offset)]
        else:
            lexical_items_lst = [self.unknown_word(phon)]
        self.log_lexical_items(phon, lexical_items_lst)
        self.speaker_model.results.consume_resources('Lexical Retrieval', phon)
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
        log(f' ')
        for i, lex in enumerate(lst):
            if lex:
                if lex.morphological_chunk:
                    log(f'({i+1}) morphological chunk [{lex.morphological_chunk}] ')
                else:
                    log(f'({i+1}) {lex} ')

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
            log(f' = UNRECOGNIZED WORD (processing will terminate) @@')
            self.speaker_model.exit = True
        return lex

    def language_match(self, lex):
        return (self.language in lex.language) or (lex.language == 'LANG:X')

    def apply_redundancy_rules(self, features):
        def feature_conflict(new_f, features_from_lexicon):
            for f in features_from_lexicon:
                if new_f.startswith('+COMP') and f.startswith('+COMP'):
                    return True
                if new_f.startswith('-COMP') and f.startswith('-COMP'):
                    return True
                if new_f.startswith('+SPEC') and f.startswith('+SPEC'):
                    return True
                if new_f.startswith('-SPEC') and f.startswith('-SPEC'):
                    return True
                if new_f.endswith(f) and new_f[0] != f[0]:
                    return True

        feature_set = set(features)
        new_features_to_add = set()

        # Apply the redundancy rules to the feature set
        for i in range(2):                                                  #   Apply twice (so as to allow added features to trigger further rules)
            for f in self.redundancy_rules:
                antecedent_trigger_set = set(f.split())
                matched_features = 0
                for feat in antecedent_trigger_set:
                    if feat.endswith('..'):
                        for g in feature_set:
                            if g.startswith(feat[:-2]):
                                matched_features += 1
                    else:
                        if feat in feature_set:
                            matched_features += 1
                if len(antecedent_trigger_set) <= matched_features:
                    new_features_to_add |= set(self.redundancy_rules[f])    #   we add the redundancy features

            # Resolve conflicts in favor of language specific lexical features
            features_not_blocked_by_language_specific_lexicon = set()
            for new_feature in new_features_to_add:
                if not feature_conflict(new_feature, feature_set):
                    features_not_blocked_by_language_specific_lexicon.add(new_feature)
            feature_set |= features_not_blocked_by_language_specific_lexicon
        return feature_set

    def load_redundancy_rules(self):
        redundancy_rules_dict = {}
        for line in open(self.speaker_model.settings.external_sources["redundancy_rules"], encoding='utf8'):    #todo remove SM from settings access
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

    def load_lexicons(self, settings):
        self.speaker_lexicon = {}
        for lexicon_file in [file.strip() for file in settings.retrieve('file_lexicons', '').split(';')]:
            self.load_and_create_lexicon(settings.folders['lexicon'] / lexicon_file)

    def load_and_create_lexicon(self, lexicon_file):
        lexical_entries = []
        if lexicon_file:
            lexical_entries = open(lexicon_file, encoding='utf8').readlines()

        for line in lexical_entries:
            if not line or '::' not in line or line.startswith('#'):            #   Ignore comments and empty lines
                continue
            line = line.strip()                                                 #   Remove extra spaces
            phonological_entries, lexical_features = line.split('::')           #   Separate key and value, by symbol '::'
            phonological_entries = phonological_entries.strip().split(',')      #   Remove extra spaces, create set of allomorphs
            lexical_features = [f.strip() for f in lexical_features.split()]    #   Create the feature list
            if not {f for f in lexical_features if f[:4] == 'LANG'}:            #   If no language is specified for the lexical entry, add it
                lexical_features.append(self.language)
            for p in phonological_entries:
                lex = LexicalItem(p, self.apply_redundancy_rules(lexical_features))
                if p not in self.speaker_lexicon.keys():
                    self.speaker_lexicon[p] = []
                self.speaker_lexicon[p].append(lex)
