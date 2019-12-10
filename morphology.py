from support import set_logging, log, get_number_of_operations, reset_number_of_operations, log_result, illu
from LexicalInterface import LexicalInterface

class Morphology():
    def __init__(self, context):
        self.context = context
        self.lexicon = LexicalInterface(self.context.redundancy_rules_file)
        self.lexicon.load_lexicon(self.context.lexicon_file, context.language)
        self.lexicon.load_lexicon(self.context.ug_morphemes_file, context.language, combine=True)

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

            log(f'\t\tDecomposing a polymorphemic word {next_lexical_item.morphology}.')
            # This disambiguates Finnish #FOC feature -- disabled
            # if 'CAT:X' in lexical_item.features:
            #    morphologically_decomposed_input = self.generative_morphology(lexical_item.morphology)
            #    lexical_item.morphology = morphologically_decomposed_input

            # Condition 2. Step 1.
            # Create a list of morphemes
            # Operation 1. Morphophonological operations (fusion ect.) create a list of morphemes from the multimorphemic input
            word = next_lexical_item.morphology
            lst_ = self.morphophonological_processing(word, lst_branched[index][0])

            # If the element was incorporated (not affixed), this information will be passed on as a feature
            if next_lexical_item.incorporated:
                lst_.append('inc$')

            # Condition 2, Step 3.
            # The list will substitute the original multimorphemic word
            log(f'\t\tNext word contains multiple morphemes ' + str(lst_[::-1]))
            del lst_branched[index]
            # Add the decomposed morphemes to the input list (in reverse order; Mirror Principle)
            for w_ in lst_:
                lst_branched.insert(index, w_)

            # Condition 2, Step 4.
            # Take the first morpheme discovered
            next_lexical_item = self.lexicon.access_lexicon(lst_branched[index])[0]

        return next_lexical_item, lst_branched

    def is_polymorphemic(self, lexical_item):
        if '#' not in lexical_item.morphology:
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
            log('\n\t\tAdding inflectional features to ' + lexical_item.get_pf())
            lexical_item.features = lexical_item.features.union(set(inflectional_affixes))
            lexical_item.features = self.lexicon.create_combined_categories(lexical_item.features)
        return lexical_item

    # Definition for generative morphology that only handles FOC disambiguation at present
    def generative_morphology(self, word):

        # Extract morphemes
        list_ = self.extract_morphemes(word)

        # Recognize the presence of the foc feature
        if len(list_) > 1:
            if 'foc' in list_:
                # We use the category of second last morpheme as a cue
                second_last_morpheme = self.lexicon.access_lexicon(list_[-2])[0]
                labels = second_last_morpheme.get_labels()
                if 'V' in labels or 'FIN' in labels or 'T' in labels or 'v' in labels or 'INF' in labels:
                    log('\t\t\t\tProsodic feature [foc] interpreted as a C morpheme')
                    word = word.replace('#foc', '#C/fin')  # This means that #foc is interpreted as a morpheme

        return word

    # Definition for morpheme decomposition
    # Input is a string, returns a string in which any morpheme is replaced with
    def extract_morphemes(self, word):
        list_ = [word]
        while '#' in list_[0]:
            list_ = list_[0].split('#') + list_[1:]
            list_[0] = self.lexicon.access_lexicon(list_[0])[0].morphology

        return list_

    # This function flips the $ sing from the start to end, only because it is more easy to read in this way.
    def flip_boundary(self, lst_):
        lst2_ = []
        for w in lst_:
            if w.startswith('$'):
                lst2_.append(w[1:] + '$')
            elif w.startswith('_'):
                lst2_.append(w[1:] + '_')
            else:
                lst2_.append(w)

        return lst2_

    # Definition for morphophonological processing (fusion etc.)
    def morphophonological_processing(self, word, phon):

        morpheme_list = word.split("#")
        s = ''
        # If either a or b in a#b is morphologically complex, then a#b is deemed a case of incorporation (a_b)
        for index in range(0, len(morpheme_list)-1):
            if self.is_polymorphemic(self.lexicon.access_lexicon(morpheme_list[index])[0]) or\
                    self.is_polymorphemic(self.lexicon.access_lexicon(morpheme_list[index+1])[0]):
                s = s + morpheme_list[index] + '_'
            else:
                s = s + morpheme_list[index] + '#'
        s = s + morpheme_list[-1]

        word = s.replace("#", "#$")
        word = word.replace("_", '#_')

        # Flip $ to the end (for easier readability) and create the new list
        lst_ = self.flip_boundary(word.split("#"))

        return lst_
