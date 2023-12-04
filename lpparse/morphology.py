from support import log, set_logging, secure_copy

def verbal_head():
    return {'V', 'FIN', 'T', 'v', 'INF'}

class Morphology:
    def __init__(self, speaker_model, language):
        self.language = language
        self.speaker_model = speaker_model

    # Definition for morphological parsing for lexical item (set of features)
    def morphological_parse(self, ps, lex, input_word_list, index, inflection_buffer):
        log(f'\n\n\tMorphological decomposition of /{input_word_list[index]}/ = ')
        return self.apply_mirror_principle(input_word_list, self.decompose(lex.morphological_chunk), index)

    def decompose(self, word):
        log(f'{word} ')
        word = word.replace("#", "#$#")
        word = word.replace("=", '=$=')
        word_list = word.split('$')
        log(f'= {word_list}')
        word_list[0] = '_' + word_list[0]
        word_list[-1] = word_list[-1] + '_'
        return word_list

    def apply_mirror_principle(self, input_word_list, morpheme_list_, index):
        del input_word_list[index]
        for w_ in morpheme_list_:
            input_word_list.insert(index, w_)
        return input_word_list
