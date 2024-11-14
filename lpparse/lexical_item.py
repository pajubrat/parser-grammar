

class LexicalItem:
    MBOUNDARY = {'_': 'word', '#': 'affix', '=': 'clitic', '.': 'portmanteau', '|': 'prosodic'}
    def __init__(self, **kwargs):
        name = kwargs.get('name', '?')
        feature_set = kwargs.get('features', set())
        self.name = name
        self.morphological_chunk = ''
        self.features = set()
        self.language = ''
        self.inflectional = False
        self.type = ''
        self.onset = ''
        self.offset = ''
        self.create_lexical_item(feature_set)
        self.set_language()

    def copy(self):
        lex_ = LexicalItem(name=self.name, features=self.features)
        lex_.morphological_chunk = self.morphological_chunk
        lex_.language = self.language
        lex_.inflectional = self.inflectional
        lex_.type = self.type
        lex_.onset = self.onset
        lex_.offset = self.offset
        return lex_

    def set_phonological_context(self, onset, offset):
        self.onset = onset
        self.offset = offset
        if self.onset in LexicalItem.MBOUNDARY.keys():
            self.type = LexicalItem.MBOUNDARY[onset]
        return self

    def create_lexical_item(self, feature_set):
        """
        Create a lexical item on the basis of the features [feature_set]
        """
        self.features = set(feature_set)
        for f in self.features:
            if self.is_morphological_chunk(f):
                self.features.add(f[1:-1])
                self.morphological_chunk = f[1:-1]
                self.features.remove(f)
            if f == 'inflectional':
                self.inflectional = True
            if f == 'prosodic':
                self.type = 'prosodic'

    def is_morphological_chunk(self, f):
        return f.startswith('"') and f.endswith('"')

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

    def morphological_parse(self, ps, input_word_list, index):
        """
        Replaces the morphologically complex word with its constituents
        """
        word = self.morphological_chunk
        for b in LexicalItem.MBOUNDARY.keys():
            if b != '_':
                word = word.replace(b, f'{b}${b}')
        word_list = word.split('$')
        word_list[0] = self.onset + word_list[0]
        word_list[-1] = word_list[-1] + self.offset

        # Mirror principle
        del input_word_list[index]
        for w_ in word_list:
            input_word_list.insert(index, w_)
        return input_word_list
