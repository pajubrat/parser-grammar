from LexicalInterface import LexicalInterface

class Context():
    def __init__(self):
        self.lexicon_file = 'test_set1_word_order_lexicon.txt'
        self.ug_morphemes_file = 'ug_morphemes.txt'
        self.redundancy_rules_file = 'redundancy_rules.txt'
        self.language = 'LANG:FI'