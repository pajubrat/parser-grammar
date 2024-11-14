from support import log, secure_copy
from phrase_structure import PhraseStructure

class LexicalStream:
    def __init__(self, speaker_model):
        self.speaker_model = speaker_model
        self.lexicon = self.speaker_model.lexicon
        self.id = 0

    def wrap(self, lex, infl_buffer, prosody):
        """
        Create lexical constituent from lexical item + inflectional buffer contents
        """
        log(f'\n\n\tNext head {lex}°\n')
        inner_core_feature_bundle_lst = [lex.features.copy() | prosody | infl_buffer[0]]
        if len(infl_buffer) > 1:
            inner_core_feature_bundle_lst += infl_buffer[1:]
        X = PhraseStructure(features=self.lexicon.apply_redundancy_rules(inner_core_feature_bundle_lst))
        X.core.add_features({f'§{str(self.consume_id())}'})
        self.speaker_model.narrow_semantics.pragmatic_pathway.allocate_attention(X)
        if lex.onset == '#' or lex.onset == '.' or lex.onset == '=':
            X.internal = True
        if lex.onset == '=':
            X.clitic = True
        return X

    def consume_id(self):
        self.id += 1
        return self.id