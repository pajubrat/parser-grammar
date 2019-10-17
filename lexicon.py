import phrase_structure
import json
import sys
import logging
log = logging.getLogger(__name__)

#==============================================================================================================
# THE LEXICON
#==============================================================================================================
#
# The lexicon is a (key, value) dictionary of the following format:
# key =     the possibly ambiguous surface string, i.e. /bank/
# value =   list of possible lexical items associated with the key (i.e. bank1, bank2...)
#           In the JSON file the lexical item is a list of the form [string, [F1, F2...]]
#           which will be converted into lex, such that string = lex.morphology and [F1...] = lex.features


# Lexical items are objects in a class 'lexical_item'.
class lex:

    def __init__(self, morphology, input_features):
        self.features = input_features
        self.morphology = morphology

# This class provides the interface between the lexicon (and the lexical files) and the rest of the program
# ======================================================================================
# Universal language-invariant morphemes are collected here
#=======================================================================================
#
# This collection will be combined with language-specific lexical information downloaded
# from the file during parsing. The features from the two sets are combined together by set union
#
# Important: the keys must refer to UG morphemes, not language specific keys


# Lexical redundancy rules
# Key = antecedent condition
# Value = automatically added features (if not already existing)
# Symbols:  -COMP:X, don't expect X as a complement
#           -SPEC:X, don't expect (and don't accept inside a left branch phase) X as a specifier
#           !COMP:X, X is a mandatory complement inside a left branch phase
#           -SPEC:*, nothing can be at Spec (mirror of EPP)

# ###### DEPRECATED #######
# Use redundancy_rules.txt instead!
Lexical_redundancy_rules = {
    'CAT:D':        {'COMP:N', '-SPEC:*', '-COMP:T/fin'},
    'CAT:N':        {'SPEC:A', '-COMP:V', '-COMP:v', '-SPEC:P', '-COMP:D', '-COMP:T/fin',
                     '-SPEC:N', '-SPEC:C/fin', 'COMP:uR', 'COMP:R', '-SPEC:ADV', '-COMP:WH'},
    'CAT:P':        {'COMP:D', '-COMP:ADV', '!COMP:D', '-SPEC:ADV', '-SPEC:T/fin'},
    'CAT:C/fin':    {'PROBE:T/fin', '-SPEC:T/fin', '-SPEC:C/fin'},
    'CAT:T/fin':    {'COMP:v', 'COMP:V', 'SPEC:D', 'PROBE:V', '-SPEC:N', '-SPEC:T/fin', '-SPEC:FORCE', '-SPEC:V'},
    'CAT:v':        {'PROBE:V', 'SPEC:D', '-SPEC:N'},
    'CAT:V':        {'-COMP:Adv', 'COMP:P', 'SPEC:D', 'SPEC:P', '-SPEC:T/fin', '-COMP:uR', '-COMP:WH',
                     'SPEC:FORCE'},
    'CAT:WH':       {'-COMP:D', '-COMP:C/fin', 'ABAR:WH', '-COMP:ADV'},
    'CAT:R':        {'-COMP:D', '-COMP:T/fin', '-COMP:C/fin', 'ABAR:R'},
    'CAT:uR':       {'PROBE:R', 'PROBE:T/fin'},
    'CAT:FORCE':    {'PROBE:T/fin', '-SPEC:D'}
}

# ###### DEPRECATED #######
# See LexicalInterface.py
class interface:

    # The interface contains a dictionary which holds the lexical items
    # The lexicon is a combination of language-invariant morphemes (UG_morphemes) and language-specific morphemes
    # loaded from a file (in JSON format)
    def __init__(self):
        self.Dictionary = {}

    # This function loads the lexicon from the file 'file' and then combines it with the language-invariant UG morphemes
    def load_lexicon(self, file):
        # ###### DEPRECATED #######
        # See ug_morphemes.txt
        UG_morphemes = {
            "T/fin": [lex("T/fin", {"CAT:T/fin", "EPP", "PF:T/fin"})],
            "v": [lex("v", {"CAT:v", "SPEC:D", "COMP:V", "PF:v"})],
            "C/fin": [lex("C/fin", {"CAT:C/fin", "EPP", "PF:C", "COMP:T/fin"})],
            "D": [lex("D", {"PF:D", "CAT:D"})],
            "P": [lex("P", {"PF:P", "CAT:P"})],

            "acc": [lex("", {"PF:ACC", "CASE:ACC"})],
            "nom": [lex("", {"PF:NOM", "CASE:NOM"})],
            "par": [lex("", {"PF:PAR", "CASE:PAR"})],
            "gen": [lex("", {"PF:GET", "CASE:GEN"})],
            "uWH": [lex("", {"PF:uWH", 'CAT:uWH'})],
            "WH":  [lex("", {"PF:WH", 'CAT:WH'})],
            "3sg": [lex("", {"PF:3sg", "NUM:SG", "PER:3"})],
            "top": [lex("", {"PF:TOP", "ABAR:TOP"})],
            "foc": [lex("", {"PF:FOC", "ABAR:FOC"})],
            "rel": [lex("", {"PF:RELPRO", "CAT:R", "ABAR:R"})]
        }

        # This loads the lexicon from the file 'file'
        self.Dictionary = {}
        self.Dictionary.clear()

        with open(file, 'r') as f:
            try:
                temp_dic = json.load(f)
            except json.decoder.JSONDecodeError:
                print("Please check the formatting in the lexicon.")
                sys.exit(1)

            # Because JSON does not support sets, we convert the list of features from the file into the feature set
            # required by lex
            for key, value in temp_dic.items():
                value_modified = []
                for w in value:
                    value_modified.append(lex(w[0], set(w[1])))
                    self.Dictionary.update({key: value_modified})

        # Combines the language-specific lexicon with the invariant UG morphemes
        for key, value in UG_morphemes.items():

            # If the UG morpheme does not exist in the language-specific dict, simply add it
            if not self.Dictionary.get(key):
                self.Dictionary.update({key: value})
            # if already exists, we add the features
            else:
                self.Dictionary[key][0].features = self.Dictionary[key][0].features.union(UG_morphemes[key][0].features)

    def show_lexicon(self):
        for key, value in self.Dictionary.items():
            self.show_lexical_entry(key)

    def show_ug_morphemes(self):
        for key, value in UG_morphemes.items():
            print(key + ':' + value[0].morphology + ',' + str(value[0].features))

    def show_lexical_entry(self, key):
        if self.Dictionary.get(key):
            for w in self.Dictionary.get(key):
                print(key + '\t\t', end='')
                print(w.morphology, end='\t')
                print(w.features, end='\n')

    # This function will take a literal string as input, finds all lexical items that match it, loads them
    # into an empty constituent shell, and returns a list of those shells. If the input is not recognized, an ad hoc
    # lexical item is created
    def access_lexicon(self, id):
        def is_inflectional(ps):
            if ps.morphology == '':
                return True
            else:
                return False

        # This list will contain all possible words for the key
        word_list = []
        # This flag will tell if the lexical element was originally found inside a phonological word
        no_word_boundary_before = False

        # Word-internal pronouncing is marked by $ by morphological decomposing
        # We transform it into a tag 'no_word_boundary_before' that will be later used to make it a feature
        if id[:1] == '$':
            no_word_boundary_before = True
            id = id[1:]

        if id in self.Dictionary.keys():
            for word in self.Dictionary.get(id):
                ps = phrase_structure.PhraseStructure()
                ps.features = word.features
                ps.morphology = word.morphology

                # Mark this constituent (if not inflectional) as word-internal,
                # so that it's adjunction option is always COMP
                if no_word_boundary_before and not is_inflectional(ps):
                    ps.features.add('$')

                word_list.append(ps)
        else:
            ps = phrase_structure.PhraseStructure()
            ps.features = {'PF:?', 'CAT:?'}  # If the word is not found, we will still create it
            ps.morphology = id
            word_list = [ps]

        for word in word_list:
            self.apply_redundancy_rules(word)

        return word_list

    # This function applies the lexical redundancy rules to a lexical item ps
    # Args: ps = the phrase structure containing the lexical item
    #
    # If applies all features from the redundancy rule set if and only if
    # 1. the triggering feature (key) is found
    # 2. the features do not already exist
    # 3. if there is a conflict, general lexical rule is not applied (specificity principle)
    def apply_redundancy_rules(self, ps):

        new_features = set()
        # Search through the features of the lexical item
        for f in ps.features:
            # If antecedent feature of some rule is found
            if f in Lexical_redundancy_rules.keys():
                # and if there is no conflict between the features (-S, S)
                for g in Lexical_redundancy_rules.get(f):
                    if self.check_feature_conflict(g, ps.features):
                        # Add the feature from the lexical redundancy rules into to lexical item
                        new_features.add(g)
        ps.features = ps.features.union(new_features)

    # This function returns 'False' if there is a feature conflict between g and any feature in the set
    def check_feature_conflict(self, g, feature_set):

        # If g is a negative feature...
        if g[0] == '-':
            # ...we search for the positive version
            feature_to_search = g[1:]
        else:
            # ...otherwise we search for negative version
            feature_to_search = '-'+g

        for j in feature_set:
            if j == feature_to_search:
                return False

        return True

    # Returns the categories of word with key 'id' from the dictionary
    def get_category(self, id):
        if id in self.Dictionary.keys():
            for x in self.Dictionary.get(id)[0].features:
                if x[:3] == 'CAT':
                    return x[:4]

    def is_inflectional(self, id):
        if self.Dictionary.get(id) and self.Dictionary.get(id).morphology == '':
            return True
        else:
            return False