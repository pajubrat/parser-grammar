from support import set_logging, log, get_number_of_operations, reset_number_of_operations, log_result, illu
from LexicalInterface import LexicalInterface
from context import Context

class Morphology():
    def __init__(self, context):
        self.context = context
        self.lexicon = LexicalInterface(self.context.redundancy_rules_file)
        self.lexicon.load_lexicon(self.context.lexicon_file, context.language)
        self.lexicon.load_lexicon(self.context.ug_morphemes_file, context.language, combine=True)

    def morphological_parse(self, lexical_constituent, lst_branched, index):
        """
        Operation performs morphological parsing for word w.
        """

        # Morphological symbols
        # '#*   internal morpheme boundaries from the lexicon, will be removed
        # '$'   internal morpheme boundary, as marked by the morphological parser
        #       In syntax, $ corresponds to 'needs a host word, grab local head.'

        phonological_input_word = lst_branched[index]
        # Create a list of morphemes
        # If the word has not been recognized, its morphology must be computed
        if 'CAT:X' in lexical_constituent.features:
            morphologically_decomposed_input = self.generative_morphology(phonological_input_word)
            lexical_constituent.morphology = morphologically_decomposed_input

        word = lexical_constituent.morphology
        word = word.replace("#", "#$")
        lst_ = word.split("#")

        # If we had more than one morpheme, the list will substitute the original multimorphemic word
        if len(lst_) > 1:
            log(f'\t\tNext word contains multiple morphemes ' + str(lst_[::-1]))
            del lst_branched[index]
            for w_ in lst_:
                lst_branched.insert(index, w_)

        # Take the first morpheme discovered, add prosodic features
        lexical_item = self.lexicon.access_lexicon(lst_branched[index])[0]
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
                    word = word.replace('#foc', '#C/fin') # This meanss that #foc is interpreted as a morpheme

        return word

    def extract_morphemes(self, word):
        list_ = [word]
        while '#' in list_[0]:
            list_ = list_[0].split('#') + list_[1:]
            list_[0] = self.lexicon.access_lexicon(list_[0])[0].morphology

        return list_
