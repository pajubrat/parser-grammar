from support import log, set_logging
from lexical_interface import LexicalInterface


def verbal_head():
    return {'V', 'FIN', 'T', 'v', 'INF'}

class Morphology:
    def __init__(self, controlling_parser_process, language):
        self.language = language
        self.brain_model = controlling_parser_process
        self.lexicon = LexicalInterface(self.brain_model)
        self.lexicon.load_lexicon(self.brain_model)

    # Definition for morphological parsing for lexical item (set of features)
    def morphological_parse(self, ps, lexical_item, input_word_list, index, inflection_buffer):
        current_lexical_item = lexical_item
        if self.is_polymorphemic(current_lexical_item):
            log(f'\n\n\tMorphological decomposition of /{input_word_list[index]}/ ~ ')
            current_lexical_item = self.Aux_inversion(current_lexical_item)
            morpheme_list = self.decompose(current_lexical_item.morphology)
            morpheme_list = self.handle_incorporation(current_lexical_item, morpheme_list)
            log(f'{morpheme_list} ')
            self.apply_mirror_principle(input_word_list, morpheme_list, index)
            self.brain_model.parse_new_item(ps, input_word_list, index, inflection_buffer)

    def handle_incorporation(self, current_lexical_item, morpheme_list_):
        if current_lexical_item.incorporated:
            morpheme_list_.append('inc$')
        return morpheme_list_

    def apply_mirror_principle(self, input_word_list, morpheme_list_, index):
        del input_word_list[index]
        for w_ in morpheme_list_:
            input_word_list.insert(index, w_)           # Mirror principle

    def is_polymorphemic(self, lexical_item):
        return '#' in lexical_item.morphology or '=' in lexical_item.morphology

    def Aux_inversion(self, lexical_item):
        def verbal(head):
            return {'V', 'v', 'T', 'T/fin', 'NEG', 'FORCE'} & head.head().features
        set_logging(False)
        decomposition = self.extract_morphemes(lexical_item.morphology)
        m = self.lexicon.lexical_retrieval(decomposition[0])[0]
        if verbal(m) and 'LANG:FI' in m.features:
            self.insert_C_head(lexical_item)
        set_logging(True)
        return lexical_item

    def insert_C_head(self, lexical_item):
        """
        This function generates a null C head as a response to criterial C-features.
        To understand this we need to study other languages than Finnish
        """
        m_lst = lexical_item.morphology.split('#')                      # Create morpheme list
        for i in range(0, len(m_lst)):                                  # Examine x#y pairs
            if self.recognize_operator_string(m_lst[i]):                # Detect operator boundary x#op, x not operator morpheme
                new_m_lst = m_lst + ['C/fin'] + m_lst[i:]         # add C/fin
                log(f'C generated = ')
                lexical_item.morphology = ''                            # Recreate morphology
                for m in new_m_lst:                                     # ...
                    lexical_item.morphology += m + '#'                  # ...
                lexical_item.morphology = lexical_item.morphology[:-1]  # Remove last unnecessary '#'
                log(f'{lexical_item.morphology}...')
                break

    def recognize_operator_string(self, string):
        return {string} & {'[foc]', 'foc', '[hAn]', '[pA]', '[kO]', 'C/op', '[wh]', 'wh'}

    # Definition for morpheme decomposition
    def extract_morphemes(self, word):
        list_ = [word]
        while '#' in list_[0]:
            list_ = list_[0].split('#') + list_[1:]
            list_[0] = self.lexicon.lexical_retrieval(list_[0])[0].morphology
        return list_

    def flip_boundary(self, lst_):
        """
        Flips $ from the start to end, only because it is more easy to read in this way.
        Otherwise irrelevant.
        """
        lst2_ = []
        for w in lst_:
            if w.startswith('$'):
                lst2_.append(w[1:] + '$')
            elif w.startswith('='):
                lst2_.append(w[1:] + '=')
            else:
                lst2_.append(w)
        return lst2_

    # Definition for morphological decomposition
    def decompose(self, word):
        word = word.replace("#", "#$")
        word = word.replace("=", '#=')
        word_ = self.flip_boundary(word.split("#"))
        return word_
