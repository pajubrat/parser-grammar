from support import log
from lexical_interface import LexicalInterface


def verbal_head():
    return {'V', 'FIN', 'T', 'v', 'INF'}

class Morphology:
    def __init__(self, controlling_parser_process):
        self.brain_model = controlling_parser_process
        self.lexicon = LexicalInterface(self.brain_model)
        self.lexicon.load_lexicon(self.brain_model)

    # Definition for morphological parsing for lexical item (set of features)
    def morphological_parse(self, controlling_parsing_process, lexical_item, input_word_list, index):
        current_lexical_item = lexical_item
        while self.is_polymorphemic(current_lexical_item):
            # Iterative loop which makes sure that the first item in the decomposition is primitive and can be
            # send to syntax for Merge-1
            log(f'{current_lexical_item.morphology}: ')

            # Solves an ambiguity in C_features, i.e. whether they are criterial or head features
            current_lexical_item = self.Aux_inversion(current_lexical_item)

            # Morphological decomposition based on the lexical entry
            # Returns a list of morphemes
            morpheme_list = self.decompose(current_lexical_item.morphology)

            # Transfer knowledge of incorporation
            morpheme_list = self.handle_incorporation(current_lexical_item, morpheme_list)

            # Apply the morphological mirror principle (should follow automatically from something)
            self.apply_mirror_principle(input_word_list, morpheme_list, index)

            controlling_parsing_process.consume_resources('Morphological decomposition')

            # Retrieve the first item in the list from the lexicon
            # Exit the process only if this is primitive (i.e. while-loop)
            current_lexical_item = self.lexicon.lexical_retrieval(input_word_list[index])[0]

        # Extract infection features if the current element is inflectional feature and not a lexical item
        inflection_features = self.get_inflection_features(current_lexical_item, input_word_list[index])

        return current_lexical_item, input_word_list, inflection_features

    def handle_incorporation(self, current_lexical_item, morpheme_list_):
        if current_lexical_item.incorporated:
            morpheme_list_.append('inc$')
        return morpheme_list_

    def apply_mirror_principle(self, input_word_list, morpheme_list_, index):
        """
        Applies morphological mirror principle (Baker, Julien)
        """
        del input_word_list[index]
        for w_ in morpheme_list_:
            input_word_list.insert(index, w_)           # Mirror principle

    def is_polymorphemic(self, lexical_item):
        return '#' in lexical_item.morphology or '=' in lexical_item.morphology

    def get_inflection_features(self, lexical_item, morpheme_string):
        if 'inflectional' in lexical_item.features:
            log(f'Inflectional feature {morpheme_string}...')
            inflection_features = lexical_item.features
            if inflection_features and not morpheme_string.endswith('$'):
                log(f'Is stranded... ')
                lexical_item.features.add('PF:' + morpheme_string)
                lexical_item.features.add('CAT:?')
                inflection_features = set()
            return inflection_features
        else:
            return set()

    def set_inflection(self, lexical_item, inflectional_affixes):
        if inflectional_affixes:
            log(f'Adding {inflectional_affixes} to ' + lexical_item.get_phonological_string() + '...')
            lexical_item.features = lexical_item.features | set(inflectional_affixes)
        return lexical_item

    def Aux_inversion(self, lexical_item):
        """
        In some cases we must generate extra C/fin head (aux-inversion). This function handles it. Currently only handles
        Finnish head + operator feature combinations. This is implemented by some more general operation which
        is unknown at present.
        """
        decomposition = self.extract_morphemes(lexical_item.morphology)
        m = self.lexicon.lexical_retrieval(decomposition[0])[0]
        if m.verbal() and 'LANG:FI' in m.features:
            self.insert_C_head(lexical_item)
        return lexical_item

    def insert_C_head(self, lexical_item):
        """
        This function generates a null C head as a response to criterial C-features (currently only in Finnish).
        The operator is assigned feature [V1] = [-EDGE:*] which prevents it from hosting anything at its edge,
        including adjuncts. It corresponds in some way (that is not currently clear) to the V2 signatures
        """
        m_lst = lexical_item.morphology.split('#')                      # Create morpheme list
        for i in range(0, len(m_lst)):                                  # Examine x#y pairs
            if self.recognize_operator_string(m_lst[i]):                # Detect operator boundary x#op, x not operator morpheme
                new_m_lst = m_lst + ['C/fin', 'V1'] + m_lst[i:]         # add C/fin
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
        """
        Extracts morphemes from [word]. Nontrivial part is recursion: any morpheme may refer to further
        complex entry. This function decomposes enough so that the first morpheme is primitive, the
        rest will be decomposed later when processing reaches them.
        """
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
        """
        Morphological decomposition is performed at # and = and the parts are converted into a list
        """
        word = word.replace("#", "#$")
        word = word.replace("=", '#=')
        word_ = self.flip_boundary(word.split("#"))
        log(f'{word_}...')
        return word_