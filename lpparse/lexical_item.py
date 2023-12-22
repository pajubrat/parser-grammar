from support import log_instance


class LexicalItem:
    def __init__(self, name='?', feature_set=set()):
        self.name = name
        self.morphological_chunk = ''
        self.features = set()
        self.language = ''
        self.inflectional = False
        self.onset = ''
        self.offset = ''
        self.create_lexical_item(feature_set)
        self.set_language()

    def copy(self):
        lex_ = LexicalItem(self.name, self.features)
        lex_.morphological_chunk = self.morphological_chunk
        lex_.language = self.language
        lex_.inflectional = self.inflectional
        lex_.onset = self.onset
        lex_.offset = self.offset
        return lex_

    def set_phonological_context(self, onset, offset):
        self.onset = onset
        self.offset = offset
        return self

    def create_lexical_item(self, feature_set):
        self.features = feature_set
        for f in self.features:
            if '#' in f and not f.startswith('PC:'):
                self.morphological_chunk = f
            if f == 'inflectional':
                self.inflectional = True

    def set_language(self):
        for feature in self.features:
            if feature.startswith('LANG:'):
                self.language = feature

    def spellout(self):
        for f in self.features:
            if f.startswith('PF:'):
                return f.split(':')[1]

    def __str__(self):
        return self.name

    def morphological_parse(self, ps, input_word_list, index, inflection_buffer):
        word = self.morphological_chunk
        word = word.replace("#", "#$#")
        word = word.replace("=", '=$=')
        word_list = word.split('$')
        word_list[0] = self.onset + word_list[0]
        word_list[-1] = word_list[-1] + self.offset

        # Mirror principle
        del input_word_list[index]
        for w_ in word_list:
            input_word_list.insert(index, w_)

        return input_word_list
