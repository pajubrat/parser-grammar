from support import set_logging, log, get_number_of_operations, reset_number_of_operations, log_result, illu
from LexicalInterface import LexicalInterface
from context import Context

class Morphology():
    def __init__(self, context):
        self.context = context
        self.lexicon = LexicalInterface(self.context.redundancy_rules_file)
        self.lexicon.load_lexicon(self.context.lexicon_file, context.language)
        self.lexicon.load_lexicon(self.context.ug_morphemes_file, context.language, combine=True)

    def morphological_parse(self, lexical_constituent, lst_branched, index, prosodic_features):
        """
        Operation performs morphological parsing for word w.

        Morpheme boundaries must be marked by # in the input. The function separates the morphemes into a list L and
        substitutes the original multi-morphemic word w with the inverse of the resulting list L in the input string,
        (w1, w2, a#b#c, w3) = (v1, v2, v3, c, b, a, v3), and puts the index to point 'c'.

        """

        # Morphological symbols
        # '#*   internal morpheme boundaries from the lexicon, will be removed
        # '$'   internal morpheme boundary, as marked by the morphological parser
        #       In syntax, $ corresponds to 'needs a host word, grab local head.'

        # Create a list of morphemes
        word = lexical_constituent.morphology

        # Prosodic emphasis on finite element expressed C/fin/foc
        if '#T/fin' in word and 'FOC' in prosodic_features:
            word = word + '#C/fin'
            log('\t\tProsodic focus detected at finite element, converted into C/fin.')

        #  All word-internal morphemes will begin with symbol $ (= phonological spell-out feature)
        word = word.replace("#", "#$")
        lst_ = word.split("#")

        # If we had more than one morpheme, the list will substitute the original multimorphemic word
        if len(lst_) > 1:
            log('\n' + f'\t\tNext word contains multiple morphemes ' + str(lst_[::-1]))
            del lst_branched[index]
            for w_ in lst_:
                lst_branched.insert(index, w_)

        # Take the first morpheme discovered, add prosodic features
        lexical_item = self.lexicon.access_lexicon(lst_branched[index])[0]
        lexical_item.features = lexical_item.features | prosodic_features
        return lexical_item, lst_branched

    def get_inflection(self, lexical_item):
        if lexical_item.morphology == '':
            s = set()
            log(f'\t\tStoring inflectional feature {sorted(lexical_item.features)} into working memory.')
            for feature in lexical_item.features:
                s.add(feature)
                return s
        else:
            return set()

    def set_inflection(self, lexical_item, inflectional_affixes):
        if inflectional_affixes:
            log('\n\t\tAdding inflectional features to ' + lexical_item.get_pf())
            lexical_item.features = \
                lexical_item.features = lexical_item.features.union(set(inflectional_affixes))
            lexical_item.features = self.lexicon.create_combined_categories(lexical_item.features)
            log(f'\t\t= {sorted(lexical_item.features)}')
        return lexical_item

    def extract_prosody(self, word):
        decomposition = word.split('=')
        if len(decomposition) == 1:
            return word, set()
        else:
            log('\t\tProsodic features detected.')
            return decomposition[0], set(decomposition[1:])
