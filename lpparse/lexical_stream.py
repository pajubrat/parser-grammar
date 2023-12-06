from support import log, secure_copy
from phrase_structure import PhraseStructure

class LexicalStream:
    def __init__(self, speaker_model):
        self.speaker_model = speaker_model
        self.lexicon = self.speaker_model.lexicon
        self.id = 0

    def wrap(self, lex, inflectional_buffer):
        log(f'\n\tNext morph {lex}°')
        const = PhraseStructure()
        const.features = lex.features
        const.features.add('§' + str(self.consume_id()))
        const.features = self.lexicon.apply_redundancy_rules(const.features | inflectional_buffer)
        self.speaker_model.narrow_semantics.pragmatic_pathway.allocate_attention(const)
        if lex.onset == '#':
            const.internal = True
        return const

    def consume_id(self):
        self.id += 1
        return self.id