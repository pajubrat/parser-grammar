from support import log, set_logging, secure_copy

def verbal_head():
    return {'V', 'FIN', 'T', 'v', 'INF'}

class Morphology:
    def __init__(self, speaker_model, language):
        self.language = language
        self.speaker_model = speaker_model

    # Definition for morphological parsing for lexical item (set of features)
    # todo: this function is temporary placeholder
    def morphological_parse(self, ps, lex, input_word_list, index, inflection_buffer):
        log(f'\n\n\tMorphological decomposition of /{input_word_list[index]}/ ~ ')
        lex = self.Aux_inversion(lex)                                         #  todo: not yet correct formulation
        morpheme_list = self.decompose(lex.morphological_chunk)
        morpheme_list = self.handle_incorporation(lex, morpheme_list)                  #  todo: incorporation remains to be implemented
        log(f'{morpheme_list} ')
        self.apply_mirror_principle(input_word_list, morpheme_list, index)
        return input_word_list

    def handle_incorporation(self, current_lexical_item, morpheme_list_):
        if current_lexical_item.concatenation == '=':
            morpheme_list_.append('inc$')
        return morpheme_list_

    def apply_mirror_principle(self, input_word_list, morpheme_list_, index):
        del input_word_list[index]
        for w_ in morpheme_list_:
            input_word_list.insert(index, w_)

    # todo: the issue underlining this function must be rethought completely
    def Aux_inversion(self, lexical_item):
        def verbal(lexical_item):
            return {'V', 'v', 'T', 'T/fin', 'NEG', 'FORCE'} & lexical_item.features
        set_logging(False)
        decomposition = self.extract_morphemes(lexical_item.morphological_chunk)
        if self.speaker_model.lexicon.lexical_retrieval(decomposition[0]):
            m = self.speaker_model.lexicon.lexical_retrieval(decomposition[0])[0]
            if verbal(m) and 'LANG:FI' in m.features:
                self.insert_C_head(lexical_item)
        set_logging(True)
        return lexical_item

    def insert_C_head(self, lexical_item):
        """
        This function generates a null C head as a response to criterial C-features.
        To understand this we need to study other languages than Finnish
        """
        m_lst = lexical_item.morphological_chunk.split('#')                      # Create morpheme list
        for i in range(0, len(m_lst)):                                  # Examine x#y pairs
            if self.recognize_operator_string(m_lst[i]):                # Detect operator boundary x#op, x not operator morpheme
                new_m_lst = m_lst + ['C/fin'] + m_lst[i:]         # add C/fin
                log(f'C generated = ')
                lexical_item.morphological_chunk = ''                            # Recreate morphology
                for m in new_m_lst:                                # ...
                    lexical_item.morphological_chunk += m + '#'                  # ...
                lexical_item.morphological_chunk = lexical_item.morphological_chunk[:-1]     # Remove last unnecessary '#'
                log(f'{lexical_item.morphological_chunk}...')
                break

    def recognize_operator_string(self, string):
        return {string} & {'[foc]', 'foc', '[hAn]', '[pA]', '[kO]', 'C/op', '[wh]', 'wh'}

    # Definition for morpheme decomposition
    # Decomposes so that the first morpheme does not have morphological decomposition
    def extract_morphemes(self, morpheme_chunk):
        list_ = [morpheme_chunk]
        while '#' in list_[0] and not list_[0].startswith('#'):                     # TODO: fix this stipulation
            list_ = list_[0].split('#') + list_[1:]
            if self.speaker_model.lexicon.lexical_retrieval(list_[0])[0].morphological_chunk:
                list_[0] = self.speaker_model.lexicon.lexical_retrieval(list_[0])[0].morphological_chunk
        return list_

    # Definition for morphological decomposition
    def decompose(self, word):
        def flip_boundary(lst_):
            """
            Flips $ from the start to end, only because it is more easy to read in this way.
            Otherwise irrelevant.
            """
            lst2_ = []
            for w in lst_:
                if w.startswith('$'):
                    lst2_.append(w[1:] + '#')
                elif w.startswith('='):
                    lst2_.append(w[1:] + '=')
                else:
                    lst2_.append(w)
            return lst2_

        word = word.replace("#", "#$")
        word = word.replace("=", '#=')
        word_ = flip_boundary(word.split("#"))
        return word_
