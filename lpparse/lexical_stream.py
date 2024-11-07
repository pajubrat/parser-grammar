from support import log, secure_copy
from phrase_structure import PhraseStructure

class LexicalStream:
    def __init__(self, speaker_model):
        self.speaker_model = speaker_model
        self.lexicon = self.speaker_model.lexicon
        self.id = 0

    def wrap(self, lex, infl_buffer):
        log(f'\n\n\tNext head {lex}°\n')
        X = PhraseStructure(features=self.lexicon.apply_redundancy_rules([lex.features.copy()] + infl_buffer[::-1]))
        X.core.add_features({f'§{str(self.consume_id())}'})
        self.speaker_model.narrow_semantics.pragmatic_pathway.allocate_attention(X)
        if lex.onset == '#':
            X.internal = True
        if lex.onset == '=':
            X.internal = True
            X.clitic = True
        return X

    def consume_id(self):
        self.id += 1
        return self.id