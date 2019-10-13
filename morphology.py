from support import set_logging, log, get_number_of_operations, reset_number_of_operations, log_result, illu
from LexicalInterface import LexicalInterface
from context import Context

class Morphology():
    def __init__(self, lexicon):
        self.lexicon = lexicon

    def morphological_parse(self, lexical_constituent, lst_branched, phonological_input_word):
        """
        Operation performs morphological parsing for word w.
        """

        # Morphological symbols
        # '#*   internal morpheme boundaries from the lexicon, will be removed
        # '$'   internal morpheme boundary, as marked by the morphological parser
        #       In syntax, $ corresponds to 'needs a host word, grab local head.'

        # Create a list of morphemes
        # If the word has not been recognized, its morphology must be computed
        if 'CAT:X' in lexical_constituent.features:
            morphologically_decomposed_input = self.generative_morphology(phonological_input_word)
            lexical_constituent.morphology = morphologically_decomposed_input

        word = lexical_constituent.morphology
        word = word.replace("#", "#$")
        morphemes = word.split("#")

        if len(morphemes) == 1:
            return lexical_constituent, lst_branched

        # If we had more than one morpheme, the list will substitute the original multimorphemic word
        log(f'\t\tNext word "{phonological_input_word}" contains multiple morphemes {morphemes[::-1]}')
        for morpheme in morphemes:
            lst_branched.insert(0, morpheme)

        # Take the first morpheme discovered, add prosodic features
        lexical_item = self.lexicon.access_lexicon(lst_branched.pop(0))[0]
        return lexical_item, lst_branched

    def get_inflection(self, lexical_item):
        if lexical_item.morphology == '':
            log(f'\t\tStoring inflectional feature {sorted(lexical_item.features)} into working memory.')
            return lexical_item.features
        else:
            return set()

    def set_inflection(self, lexical_item, inflectional_affixes):
        if inflectional_affixes:
            log('\n\t\tAdding inflectional features ' + str(inflectional_affixes) + ' to ' + lexical_item.get_pf())
            lexical_item.features = lexical_item.features.union(set(inflectional_affixes))
            lexical_item.features = self.lexicon.create_combined_categories(lexical_item.features)
            log(f'\t\t= {sorted(lexical_item.features)}')
        return lexical_item

    def generative_morphology(self, word):

        # This procedure will deal with the prosodic feature foc. The problem is that it can be either a feature or a morpheme,
        # This could be solved by relying on disambiguation, but that is not realistic. The whole problem is intriguing and
        # tricky.

        # First we extract morphemes
        list_ = self.extract_morphemes(word)
        # Recognize the presence of the foc feature
        if len(list_) > 1:
            if 'foc' in list_:
                # We use the category of second last morpheme as a cue
                second_last_morpheme = self.lexicon.access_lexicon(list_[-2])[0]
                labels = second_last_morpheme.get_labels()
                if 'V' in labels or 'FIN' in labels or 'T' in labels or 'v' in labels or 'INF' in labels:
                    log('\t\t\t\tProsodic feature [foc] interpreted as a C morpheme')
                    word = word.replace('#foc', '#C/fin') # This means that #foc is interpreted as a morpheme

        return word

    def extract_morphemes(self, word):
        morphemes = [word]
        while '#' in morphemes[0]:
            morphemes = morphemes[0].split('#') + morphemes[1:]
            morphemes[0] = self.lexicon.access_lexicon(morphemes[0])[0].morphology

        return morphemes
