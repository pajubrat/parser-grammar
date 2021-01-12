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
    def morphological_parse(self, controlling_parsing_process, lexical_item, input_word_list, index):
        """
        Processes a polymorphemic word in the input.

        If the lexical item retrieved from the surface lexicon is polymorphemic, it must be decomposed
        before anything can be merged into the syntactic structure. This function performs the decomposition.
        It breaks down the polymorphemic unit and embeds it into the existing list of elements. The operation
        is performed until the element currently under processing is primitive lexical item that can be
        merged (other elements do not matter as they will be decomposed later when processing moves forward).

        This mechanisms implements several other purely morphological operations.

        """
        current_lexical_item = lexical_item
        while self.is_polymorphemic(current_lexical_item):
            log('Morphological decomposition...')
            controlling_parsing_process.consume_resources('Morphological decomposition')

            # Solves an ambiguity in C_features, i.e. whether they are criterial or head features
            current_lexical_item = self.C_op_processing(current_lexical_item)
            # Morphological decomposition based on the lexical entry
            morpheme_list = self.decompose(current_lexical_item.morphology)
            # Transfer knowledge of incorporation
            morpheme_list = self.handle_incorporation(current_lexical_item, morpheme_list)
            log(f'Word "{input_word_list[index]}" contains multiple morphemes ' + str(morpheme_list) +'...')
            self.refresh_input_list(input_word_list, morpheme_list, index)
            current_lexical_item = self.lexicon.lexical_retrieval(input_word_list[index])[0]
        return current_lexical_item, input_word_list, self.get_inflection(current_lexical_item)

    def handle_incorporation(self, current_lexical_item, morpheme_list_):
        if current_lexical_item.incorporated:
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
            return lexical_item.features
        else:
            return set()

    def set_inflection(self, lexical_item, inflectional_affixes):
        if inflectional_affixes:
            log(f'Adding inflectional features {inflectional_affixes} to ' + lexical_item.get_phonological_string() + '...')
            lexical_item.features = lexical_item.features | set(inflectional_affixes)
        return lexical_item

    # C/op processing
    # Determines whether C/op feature is at the head or not
    def C_op_processing(self, lexical_item):
        list_ = self.extract_morphemes(lexical_item.morphology)
        if len(list_) > 1 and 'foc' in list_ or 'C/op' in list_:
            critical_morpheme = self.determine_critical_morpheme(list_)
            if verbal_head() & critical_morpheme.features:
                log('Feature interpreted as a C morpheme with C-feature...')
                lexical_item.morphology = lexical_item.morphology.replace('#C/op', '#C/fin#C/op')
                lexical_item.morphology = lexical_item.morphology.replace('#foc', '#C/fin#C/op')
        return lexical_item

    def determine_critical_morpheme(self, list_):
        return self.lexicon.lexical_retrieval(list_[0])[0]

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

    # Definition for morphological decomposition
    def decompose(self, word):
        word = word.replace("#", "#$")
        word = word.replace("=", '#=')
        return self.flip_boundary(word.split("#"))