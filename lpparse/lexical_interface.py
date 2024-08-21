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
        """Applies features by lexical redundancy rules (LRRs) until the set of lexical features stabilizes (no longer changes)
        This version allows execution of LRRs in a sequence
        Structure of the algorithm: WHILE (LRRs would add new features F) ADD F
        Return the new feature set after combining and pruning
        """
        while not set().union(*{frozenset(self.redundancy_rules[f]) for f in self.redundancy_rules.keys() if set(f.split()) <= features}) <= features:
            features = features | set().union(*{frozenset(self.redundancy_rules[f]) for f in self.redundancy_rules.keys() if set(f.split()) <= features})
        return self.combine_features(features)

    def combine_features(self, features):
        """Maps [X:Y] + [X:Z] into [X:Y,Z]"""
        feature_dict = {}
        unmodified_features = features.copy()
        for feature in features:
            if len(feature.split(':')) == 2:
                key, value = feature.split(':')
                if key in feature_dict.keys():
                    feature_dict[key] |= set(value.split(','))
                else:
                    feature_dict[key] = set(value.split(','))
                unmodified_features.discard(feature)
        new_aggregrated_features = {f'{key}:{",".join(feature_dict[key])}' for key in feature_dict.keys()}
        return unmodified_features | new_aggregrated_features

    def load_redundancy_rules(self):
        redundancy_rules_dict = {}
        for line in open(self.speaker_model.settings.external_sources["redundancy_rules"], encoding='utf8'):    #todo remove SM from settings access
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            antecedent, features = line.split('::', 1)
            antecedent = antecedent.strip()
            feature_set = {f.strip() for f in features.split()}
            if antecedent in redundancy_rules_dict.keys():
                redundancy_rules_dict[antecedent] = redundancy_rules_dict[antecedent] | feature_set
            else:
                redundancy_rules_dict[antecedent] = feature_set
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
            lexical_features = {f.strip() for f in lexical_features.split()}    #   Create the feature set
            if not {f for f in lexical_features if f[:4] == 'LANG'}:            #   If no language is specified for the lexical entry, add it
                lexical_features.add(self.language)
            for p in phonological_entries:
                lex = LexicalItem(p, self.apply_redundancy_rules(lexical_features))
                if p not in self.speaker_lexicon.keys():
                    self.speaker_lexicon[p] = []
                self.speaker_lexicon[p].append(lex)
