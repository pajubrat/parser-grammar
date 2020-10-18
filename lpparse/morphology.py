from support import log
from lexical_interface import LexicalInterface


def verbal_head():
    return {'V', 'FIN', 'T', 'v', 'INF'}

class Morphology:
    def __init__(self, controlling_parser_process):
        self.controlling_parser_process = controlling_parser_process
        self.lexicon = LexicalInterface(self.controlling_parser_process)
        self.lexicon.load_lexicon(self.controlling_parser_process)

    # Definition for morphological parsing for lexical item (set of features)
    def morphological_parse(self, lexical_item, input_word_list, index):
        lexical_item_ = lexical_item
        while self.is_polymorphemic(lexical_item_):
            lexical_item_ = self.C_op_processing(lexical_item_)
            morpheme_list = self.decompose(lexical_item_.morphology)
            morpheme_list = self.handle_incorporation(lexical_item_, morpheme_list)
            log(f'\n\t\tNext word contains multiple morphemes ' + str(morpheme_list))
            self.refresh_input_list(input_word_list, morpheme_list, index)
            lexical_item_ = self.lexicon.lexical_retrieval(input_word_list[index])[0]
        return lexical_item_, input_word_list, self.get_inflection(lexical_item_)

    def handle_incorporation(self, lexical_item_, morpheme_list_):
        if lexical_item_.incorporated:
            morpheme_list_.append('inc$')
        return morpheme_list_

    def refresh_input_list(self, input_word_list, morpheme_list_, index):
        del input_word_list[index]
        for w_ in morpheme_list_:
            input_word_list.insert(index, w_)           # Mirror principle

    def is_polymorphemic(self, lexical_item):
        return '#' in lexical_item.morphology or '=' in lexical_item.morphology

    def get_inflection(self, lexical_item):
        if lexical_item.morphology == '':
            log(f'\t\tStoring inflectional feature {sorted(lexical_item.features)} into working memory.')
            return lexical_item.features
        else:
            return set()

    def set_inflection(self, lexical_item, inflectional_affixes):
        if inflectional_affixes:
            log(f'\t\tAdding inflectional features {inflectional_affixes} to ' + lexical_item.get_phonological_string())
            lexical_item.features = lexical_item.features | set(inflectional_affixes)
        return lexical_item

    # C/op processing
    # Determines whether C/op feature is at the head or not
    def C_op_processing(self, lexical_item):
        list_ = self.extract_morphemes(lexical_item.morphology)
        if len(list_) > 1 and 'foc' in list_ or 'C/op' in list_:
            critical_morpheme = self.determine_critical_morpheme(list_)
            if verbal_head() & critical_morpheme.features:
                log('\t\t\t\tFeature interpreted as a C morpheme with C-feature')
                lexical_item.morphology = lexical_item.morphology.replace('#C/op', '#C/fin#C/op')
                lexical_item.morphology = lexical_item.morphology.replace('#foc', '#C/fin#C/op')
        return lexical_item

    def determine_critical_morpheme(self, list_):
        if len(list_) < 3:
            return self.lexicon.lexical_retrieval(list_[0])[0]
        return self.lexicon.lexical_retrieval(list_[-3])[0]

    # Definition for morpheme decomposition
    def extract_morphemes(self, word):
        list_ = [word]
        while '#' in list_[0]:
            list_ = list_[0].split('#') + list_[1:]
            list_[0] = self.lexicon.lexical_retrieval(list_[0])[0].morphology
        return list_

    # Flips $ from the start to end, only because it is more easy to read in this way.
    def flip_boundary(self, lst_):
        lst2_ = []
        for w in lst_:
            if w.startswith('$'):
                lst2_.append(w[1:] + '$')
            elif w.startswith('='):
                lst2_.append(w[1:] + '=')
            else:
                lst2_.append(w)
        return lst2_

    # Definition for morphological decomposition (converts string pattern into a list)
    def decompose(self, word):
        word = word.replace("#", "#$")
        word = word.replace("=", '#=')
        return self.flip_boundary(word.split("#"))