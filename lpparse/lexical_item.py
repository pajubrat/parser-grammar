from collections import namedtuple

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
