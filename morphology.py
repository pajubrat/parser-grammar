from support import set_logging, log, get_number_of_operations, reset_number_of_operations, log_result, illu
from LexicalInterface import LexicalInterface


class Morphology:
    def __init__(self, controlling_parser_process):
        self.controlling_parser_process = controlling_parser_process
        self.lexicon = LexicalInterface(self.controlling_parser_process)
        self.lexicon.load_lexicon(self.controlling_parser_process)

    # Definition for morphological parsing for lexical item
    # Condition 1.  If LI is monomorphemic(w), return the same item and input list (i.e. do nothing)
    # Condition 2.  If LI is polymorphemic(W), use morphology field to decompose it
    #               Step 1. Break the morphemes into a list (W = w1#w2#w3 => w1, w2$, w3$)
    #               Step 2. Follow mirror principle and reverse (w1, $w2, $w3 => w3$, w2$, w1)
    #               Step 3. Substitute this list with the original word in the input list
    #               Step 4. Return the list
    # Condition 3.  From these assumptions it follows that it is possible to receive $W.
    #               In such case, $ will be inherited to the first morpheme ($W = $w1, $w2...)
    #               Furthermore, W will be marked as an incorporated element
    def morphological_parse(self, lexical_item, lst_branched, index):

        next_lexical_item = lexical_item

        # Conditions 1-2
        while self.is_polymorphemic(next_lexical_item):

            # Disambiguates Finnish #FOC feature
            lexical_item.morphology = self.handle_Cop_feature(lexical_item.morphology)

            # Condition 2. Step 1.
            # Create a list of morphemes
            # Operation 1. Create a list of morphemes from the multimorphemic phonological input string
            # This operation should deal with surface complexities (fusion, and such)
            word = next_lexical_item.morphology
            lst_ = self.morphophonological_processing(word)

            # If the element was incorporated (not affixed), this information will be passed on as a feature
            if next_lexical_item.incorporated:
                lst_.append('inc$')

            # Condition 2, Step 3.
            # The list will substitute the original multimorphemic word
            log(f'\n\t\tNext word contains multiple morphemes ' + str(lst_[::-1]))
            del lst_branched[index]

            # Add the decomposed morphemes to the input list (in reverse order; Mirror Principle)
            for w_ in lst_:
                lst_branched.insert(index, w_)

            # Condition 2, Step 4.
            # Take the first morpheme discovered
            next_lexical_item = self.lexicon.lexical_retrieval(lst_branched[index])[0]

        return next_lexical_item, lst_branched

    def is_polymorphemic(self, lexical_item):
        if '#' not in lexical_item.morphology and '=' not in lexical_item.morphology:
            return False
        else:
            return True

    def get_inflection(self, lexical_item):
        if lexical_item.morphology == '':
            log(f'\t\tStoring inflectional feature {sorted(lexical_item.features)} into working memory.')
            return lexical_item.features
        else:
            return set()

    def set_inflection(self, lexical_item, inflectional_affixes):
        if inflectional_affixes:
            log(f'\t\tAdding inflectional features {inflectional_affixes} to ' + lexical_item.get_pf())
            lexical_item.features = lexical_item.features | set(inflectional_affixes)
        return lexical_item

    # Definition for generative morphology that only handles FOC disambiguation at present
    def handle_Cop_feature(self, word):

        # Extract morphemes
        list_ = self.extract_morphemes(word)

        # Recognize the presence of the foc  on a head
        if len(list_) > 1:
            if 'foc' in list_ or 'C/op' in list_:

                # We select the critical morpheme
                if len(list_) < 3:
                    critical_morpheme = self.lexicon.lexical_retrieval(list_[0])[0]
                else:
                    critical_morpheme = self.lexicon.lexical_retrieval(list_[-3])[0]
                labels = critical_morpheme.features

                if 'V' in labels or 'FIN' in labels or 'T' in labels or 'v' in labels or 'INF' in labels:
                    log('\t\t\t\tFeature interpreted as a C morpheme with C-feature C/op')
                    word = word.replace('#C/op', '#C/fin#C/op')
                    word = word.replace('#foc', '#C/fin#C/op')


        return word

    # Definition for morpheme decomposition
    # Input is a string, returns a string in which any morpheme is replaced with
    def extract_morphemes(self, word):
        # First item in the list is the word itself
        list_ = [word]

        # If the word has several morphemes
        while '#' in list_[0]:
            # Split the first item and insert them into the beginning of the list
            list_ = list_[0].split('#') + list_[1:]
            # Substitute the first item with the morphemic decomposition
            # (and continue decomposition if that is complex as well)
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

    # Definition for morphophonological processing (fusion etc.)
    def morphophonological_processing(self, word):

        word = word.replace("#", "#$")
        word = word.replace("=", '#=')
        return self.flip_boundary(word.split("#"))
