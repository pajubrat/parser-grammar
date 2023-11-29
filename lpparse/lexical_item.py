

class LexicalItem:
    def __init__(self, name='?', feature_set=set()):
        self.name = name
        self.morphological_chunk = ''
        self.features = set()
        self.language = ''
        self.inflectional = False
        self.concatenation = ''
        self.allomorphs = {}
        self.create_lexical_item(feature_set)
        self.set_language()

    def copy(self):
        lex_ = LexicalItem(self.name, self.features)
        lex_.morphological_chunk = self.morphological_chunk
        lex_.language = self.language
        lex_.inflectional = self.inflectional
        lex_.concatenation = self.concatenation
        lex_.allomorphs = self.allomorphs
        return lex_

    def set_concat(self, str):
        self.concatenation = str
        return self

    def create_lexical_item(self, feature_set):
        self.features = feature_set
        for f in self.features:
            if '#' in f:
                self.morphological_chunk = f
            if f.startswith('ALLOMORPHS'):
                self.allomorphs = set(f.split(':')[1].split(','))
            if f == 'inflectional':
                self.inflectional = True

    def set_language(self):
        for feature in self.features:
            if feature.startswith('LANG:'):
                self.language = feature

    def __str__(self):
        return self.name
