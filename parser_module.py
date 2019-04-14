from support import set_logging, log, get_number_of_operations, reset_number_of_operations, log_result, illu
from LexicalInterface import LexicalInterface
from LF import LF
from operator import itemgetter
from reconstruction import Reconstruction

# Parser-Grammar
# 2019
# V. 1.02

class Pcb_parser():
    def __init__(self, lexicon_file, ug_morphemes_file='ug_morphemes.txt',
                 redundancy_rules_file='redundancy_rules.txt', language='LANG:EN'):

        # All results (analyses)
        self.result_list = []

        # Access to the lexicon
        self.lexical_access = LexicalInterface(redundancy_rules_file)

        # Number of lexical ambiguities detected (support function)
        self.number_of_ambiguities = 0

        # Support function
        self.result_matrix = [[] for i in range(50)]

        # Local memory buffer for inflectional affixes
        self.memory_buffer_inflectional_affixes = []

        # This counts the number of computational operations (support function)
        self.number_of_operations = 1
        self.number_of_solutions_tried = 0

        # Stops parsing when the first solution is available
        self.exit = False

        # index for name provider, for output reasons (chain identification)
        self.name_provider_index = 0

        self.lexical_access.load_lexicon(lexicon_file, language)
        self.lexical_access.load_lexicon(ug_morphemes_file, language, combine=True)

    # Preparatory steps.
    def parse(self, lst):
        """
        Parses a list of words.

        The operation prepares the parser and its parameters, and then initiates the recursive
        parsing operation.
        """
        # Reset parser state
        self.result_list = []
        self.memory_buffer_inflectional_affixes = []
        self.number_of_operations = 0
        self.number_of_ambiguities = 0
        reset_number_of_operations()
        self.name_provider_index = 0

        set_logging(True)
        self.exit = False
        ps = None
        self.__first_pass_parse(ps, lst, 0)     # Initiate the recursive parsing operation

    # Recursive parsing algorithm
    def __first_pass_parse(self, ps, lst, index):
        """
        Recursive parsing operation that works with current parse, list of words, and a position in the list of words

        The operation takes the current phrase structure PS and a word w, and ranks the possible adjunction sites
        of w into the right edge of PS. The ranked list is then used as a seed to call this same function recursively.

        The above description is simplification in the following sense:

        i) if w is ambiguous, then the function is called recursively by trying each possible lexical item,
        ii) if w is a multi-morphemic word, it is first decomposed into a sequence of morphemes
        (words w1, . . ., wn); the function is then called with a list that substitutes the original word with the
        decomposed list,
        iii) if an inflectional suffix is encountered, it is stored into memory and associated as a feature to a new
        non-inflectional item (head) retrieved from the lexicon,
        iv) if the list is exhausted, then the result is evaluated and, if accepted, delivered as an output. This
        terminates parsing if it is set to find only one solution; otherwise it will continue to discover alternative
        solutions recursively until the whole combinatorial space has been explored.
        """

        if self.exit:
            return

        set_logging(True)
        self.number_of_operations = self.number_of_operations + 1

        log(f'\t\t\t={ps}')

        log('\n'+str(self.number_of_operations)+ '.')

        # Test if we have reached at the end of the input list
        if index == len(lst):
            self.number_of_solutions_tried = self.number_of_solutions_tried + 1
            log('\t>>>\t' + f'Trying candidate parse ' + ps.illustrate() + ' ('+str(self.number_of_solutions_tried)+'.)')
            log('\t\tReversing movement.')
            ps_ = self.reconstruct(ps)
            log('\t\t\t= ' + ps_.illustrate())
            log(f'\t\tChecking LF-interface conditions.')

            # Test if the final configuration is grammatical
            # The three tests below check for LF-interface conditions
            if ps_.LF_legibility_test().all_pass():
                if LF.final_tail_check(ps_) and self.transfer_to_LF(ps_):
                    log(f'!--->\t\tTests passed (with {self.number_of_operations}/'
                        f'{get_number_of_operations()} operations) <------------------------------------')
                    self.result_list.append(ps_)
                    ps_.tidy_names(1)
                    print(chr(96 + len(self.result_list)) + '. ' + ps_.show())
                    print(ps_.spellout())
                    print(ps_.illustrate_spellout())
                    print(ps_.illustrate()+'\n')
                    log_result(ps_)
                    log(ps_.show_primitive_constituents())
                    log(ps_.show_all_vectors())
                    self.exit = True    # Knock this out if you want to see all solutions
                    log('\t\t\tChecking if the sentence is ambiguous...')
                else:
                    log('\t\t\tFinal tail-head check failed.')
                    log(ps_.show_primitive_constituents())
                    log(ps_.show_all_vectors())
                    log('\t\t\tLet\'s find another solution...\n.\n.\n.')
            else:
                log('\t\t\tLF-interface condition(s) violated')
                log(ps_.show_primitive_constituents())
                log(ps_.show_all_vectors())
                log('\n\t\tTrying to find other solutions...')
            # This return will send the parser to an unexplored path in the recursive parse tree
            return

        # Process next word if exists
        else:

            # Sort out lexical ambiguity
            disambiguated_word_list = self.lexical_access.access_lexicon(lst[index])
            if len(disambiguated_word_list) > 1:
                log('\t\tAmbiguous lexical item ' + str(disambiguated_word_list) + 'detected.')

            for lexical_constituent in disambiguated_word_list:

                # Morphological parser
                lst_branched = lst.copy()
                lex_decomposed = self.morphological_parse(lexical_constituent, lst_branched, index)

                # Inflectional suffixes are stored as features to be used in connection with the next word
                if lex_decomposed.morphology == '':
                    log(f'\t\tStoring inflectional feature {sorted(lex_decomposed.features)} into working memory.')
                    # Unload the features to memory
                    for feature in lex_decomposed.features:
                        self.memory_buffer_inflectional_affixes.append(feature)

                    log('\n\t\tConsume \"' + lst_branched[index + 1] + '\"\n')
                    if ps:
                        self.__first_pass_parse(ps.copy(), lst_branched, index + 1)
                    else:
                        self.__first_pass_parse(None, lst_branched, index + 1)

                # Process morpheme (inflectional features are processed above)
                else:

                    # Unload inflectional suffixes from the memory first
                    if self.memory_buffer_inflectional_affixes:
                        log('\n\t\tAdding inflectional features to ' + lex_decomposed.get_pf())
                        lex_decomposed.features = \
                            lex_decomposed.features = lex_decomposed.features.union(set(self.memory_buffer_inflectional_affixes))
                        lex_decomposed.features = self.lexical_access.create_combined_categories(lex_decomposed.features)
                        self.memory_buffer_inflectional_affixes = []
                        log(f'\t\t= {sorted(lex_decomposed.features)}')

                    # If there is no prior phrase structure, we create it by using the first word
                    if not ps:
                        self.__first_pass_parse(lex_decomposed.copy(), lst_branched, index + 1)

                    # Merge the new word (disambiguated lexical item) to the existing phrase structure
                    else:
                        log('\n\t\tConsume \"' + lex_decomposed.get_pf() + '\"\n')
                        log('\t\t' + ps.illustrate() + ' + ' + lex_decomposed.get_pf())

                        # --------- This is the core parsing functionality ----------------------------------------
                        # -----------------------------------------------------------------------------------------

                        # Get the merge sites
                        adjunction_sites = self.ranking(self.filter(ps, lex_decomposed), lex_decomposed)

                        # Test each licit adjunction site in the order of ranking
                        for i, site in enumerate(adjunction_sites, start=1):
                            ps_ = ps.get_top().copy()
                            if site.get_bottom_affix().internal:
                                log(f'\t\tExploring solution number ({i}) =' + f'[{site}*{lex_decomposed.get_pf()}]')
                                new_ps = site * lex_decomposed  # Sink
                            else:
                                site_ = self.reconstruct(ps_[ps.index(site)])
                                new_ps = site_ + lex_decomposed  # Merge
                                log(f'\t\tExploring solution number ({i}) =' + f'[{site} {lex_decomposed.get_pf()}]')
                            self.__first_pass_parse(new_ps, lst_branched, index + 1)
                            if self.exit:
                                break

                        # ------------------------------------------------------------------------------------------
                        # ------------------------------------------------------------------------------------------

            if not self.exit:
                # All branches for the incoming surface word have been explored
                log(f'\t\tI have now explored all solutions for \"' + lst[index] + '\".')
                log('\t\tGoing one step backwards and taking another solution from previous ranking list........'
                    '\n\t\t.\n\t\t.\n\t\t.')
            return

    # This function filters impossible sites
    # It returns the list of possible sites which are then ordered nondeterministically
    def filter(self, ps, w):
        """
        Filters out impossible merge sites, given some phrase structure PS and a new word w.

        The operation checks all nodes at the right edge of PS and examines if w cannot be merged to that node.
        The purpose is to prune impossible nodes out from the parsing search space. The following conditions are
        used:

        i) if the w and the lowest head H at the right edge of PS are part of the same word, then only the
        [H,w] solution is accepted, i.e. H is the only accetable merge site,
        ii) if the lowest head H does not accept complements of any kind, then [H,w] is ruled out,
        iii) if [XP,w] results in a left branch XP that is not interpretable at LF, this solution is filtered out.
        """

        log('\t\t\tFiltering out impossible merge sites...')

        # Check if the new word must be inside the last word. If yes, we must use H-Comp solution
        if ps.get_bottom().get_bottom_affix().internal:
            log(f'\t\t\tSink \"{w.get_pf()}\" into {ps.get_bottom().get_pf()}'
                ' because they are inside the same phonological word.')
            return [ps.get_bottom()]

        adjunction_sites = []

        for i, site in enumerate(ps, start=1):

            if site.is_primitive():
                # Check if the site does not accept complementizers of any kind
                if '-COMP:*' in site.features:
                    log(f'\t\t\t\tReject [{site} {w}] because {site} does not accept complementizers.')
                    continue

            # LF-legibility violations
            if not site.is_primitive():

                # We must drop all constituents before we check for conditions
                set_logging(False) # I silence this because "hypothetical droppings" are confusing in the logs
                dropped = self.reconstruct(site.copy())

                lf_test = dropped.LF_legibility_test()
                # Conditions for permanent rejection
                if lf_test.fail() and not (
                        w.is_adjoinable() and
                        lf_test.probe_goal_test_result and
                        lf_test.head_integrity_test_result and
                        lf_test.criterial_feature_test_result):
                    set_logging(True)
                    log(f'\t\t\t\tReject [{dropped.illustrate()} {w}] due to bad left branch.')
                    continue  # reject this site and start next site

            set_logging(True)

            # Word-breaking Violations
            # Remove all solutions which would cause phonological words to break apart
            if not site.is_primitive() and self.is_word_internal(site):
                # How to control for the fact that right adjuncts don't break words?
                # Solution: if w is not adjoinable at all, we can reject it...
                if not w.is_adjoinable():
                    log(f'\t\t\t\tReject [{repr(site)} {w}] as Spec because it breaks words.')
                    continue  # reject this site and start next site

            adjunction_sites.append(site)

        # Return the list of possible adjunction sites left
        return adjunction_sites

    # This function order the adjunction sites in terms of the plausibility and grammatical possibility
    def ranking(self, site_list, w):
        """
        Given a word w, this operation ranks a list of possible merge sites in the order of their plausibility.

        Because all merge sites appearing in the input list are possible in principle, this function determines
        the whole search space for parsing and thus its computational efficiency. Notice that impossible sites
        have been pruned by the function filter().

        There are several ways to organize ranking, and the amount of factors that can influence it is unbounded.
        Here we use the following factors to regulate the ranking:

        i) lexical features SPEC and COMP, both positive and negative,
        ii) previously satisfied H-COMP relations, specifically we check that they are not broken,
        iii) violations of topological semantic features between H and w,
        iv) violations of internal tail-head relations (morphosyntax) between H and w,
        v) bad properties of the resulting left branch XP, in [XP, w],
        vi) adverbials are emerged so that their tail-head requirements are met,
        vii) special set of rules when nothing applies.

        These conditions may be in conflict, in which case ranking is based on their combined input. The current
        algorithm weights each node on the basis of (i-vii) and then ranks them accordingly.

        """
        def get_size(ps):
            size_ = 1
            if ps.left_const:
                size_ = size_ + get_size(ps.left_const)
            if ps.right_const:
                size_ = size_ + get_size(ps.right_const)
            return size_

        # --- main function begins here --- #

        if len(site_list) == 1:
            return site_list

        log('\t\t\tRanking remaining sites...')

        word_specs = sorted(w.for_parsing(w.get_specs()))
        word_not_specs = sorted(w.for_parsing(w.get_not_specs()))
        word_cats = sorted(w.get_cats())
        word_tail_set = w.get_tail_sets()
        word_pf = w.get_pf()
        word_labels = w.get_labels()

        adjunction_sites = []
        avoid_set = set()

        for i, site in enumerate(site_list, start=1):

            priority_base = i
            priority = 0
            site_cats = sorted(site.get_head().get_cats())

            # Case 2a. Spec Solutions
            # Check if there are SPEC-w solutions

            # Get all positive SPEC solutions from w
            for spec_solution in word_specs:

                # Get the category label(s) from hP
                for label_in_existing_parse in site_cats:

                    # Check if there is a positive Spec-H match and if yes, rank it higher
                    if spec_solution == label_in_existing_parse:
                        priority = priority + priority_base + 100
                        log(f'\t\t\t\tPrioritize {site.get_cats_string()} as SPEC,{word_pf}')
                        avoid_set.clear()

            # Case 2b. Spec Mismatches
            # Check if there are negative SPEC conditions and avoid them

            # Get negative -SPEC features from w
            if not site.is_primitive():

                for non_spec_solution in word_not_specs:

                    # Get labels from the head of phrase h(P)
                    for label_in_existing_parse in site_cats:

                        # Check if the features match
                        if non_spec_solution == label_in_existing_parse:

                            # If they match, rank this spec solution lower
                            priority = priority + priority_base - 100
                            log(f'\t\t\t\tAvoid {site.get_head().get_cats_string()}P as SPEC, {word_pf}')
                            avoid_set.add(site)

                    # Avoid all SPEC solutions if there is [-SPEC:*]
                    if '*' == non_spec_solution:
                        priority = priority + priority_base - 100
                        log(f'\t\t\t\tAvoid {site.get_head().get_cats_string()}P as SPEC for {word_pf}')
                        avoid_set.add(site)

            # Case 2c. Check if existing H-Comp-relations would be broken
            # The rule captures that fact that 'H X' often means [H XP]
            # Improves performance 75%
            # Antecedent condition: site is c-commanded locally (possible selected) by a head H
            if not site.is_primitive() and site.mother and \
                    site.mother.left_const and site.mother.left_const.is_primitive():
                # and if H selects for site
                if set(site.mother.left_const.get_comps()) & set(site.get_labels()):
                    priority = priority + priority_base - 100
                    log(f'\t\t\t\tAvoid [{site}, {w}] because the operation breaks up an existing selectional dependency.')
                    avoid_set.add(site)

            # Case 4. Comp solutions and local morphosyntax
            # Check if h is primitive (takes a complement)
            if site.is_primitive():

                # . . . search through the categorical features of the new word
                for f in word_cats:

                    # Check if H selects w and if yes, prioritize this solution
                    if f in site.for_parsing(site.get_comps()):
                        priority = priority + priority_base + 100
                        log(f'\t\t\t\tPrioritize [{site.get_pf()} {word_pf}] due to complement selection for [' + f + ']')
                        avoid_set.clear()

                    # ... if f cannot be merged to the complement, avoid this solution
                    if f in site.for_parsing(site.get_not_comps()):
                        priority = priority + priority_base - 100
                        log(f'\t\t\t\tAvoid [{site.get_cats_string()} {word_pf}] due to complement selection against [' + f + ']')
                        avoid_set.add(site)

                if not LF.semantic_match(site, w):
                    priority = priority + priority_base - 100
                    log(f'\t\t\t\tAvoid [{site},{w}] solution due to semantic mismatch.')
                    avoid_set.add(site)

                # Check if the solution violates tailing agreement and if yes, avoid
                # Check that the new constituent has tailing features
                if word_tail_set:
                    test_word = w.copy()
                    site.merge(test_word, 'right')
                    if not test_word.internal_tail_head_test():
                        priority = priority + priority_base - 100
                        log(f'\t\t\t\tAvoid [{site.get_pf()} {word_pf}] due to local agreement failure.')
                        avoid_set.add(site)
                    test_word.remove()

            # Case 5. LF-legibility violations
            # We don't check primitive "left branch phases"
            if not site.is_primitive():

                # We must drop all constituents before we check for conditions
                set_logging(False) # I silence this because "hypothetical droppings" are confusing in the logs
                dropped = self.reconstruct(site.copy())
                set_logging(True)

                if dropped.LF_legibility_test().fail():
                    priority = priority + priority_base - 100
                    log(f'\t\t\t\tAvoid {dropped.illustrate()} as left branch because it constitutes illicit structure.')
                    avoid_set.add(site)

            # Case 6. Word-breaking violations
            # Remove all solutions which would cause phonological words to break apart
            if not site.is_primitive() and self.is_word_internal(site):
                priority = priority + priority_base - 100
                log(f'\t\t\t\tAvoid {site} because it could break words.')
                avoid_set.add(site)

            # Case 7. Adverbials select legitimate tail-head configurations
            if 'ADV' in word_labels and word_tail_set:
                # Make copies to test merge
                w_copy = w.copy()
                site.merge(w_copy, 'right')
                if 'T/fin' in str(w_copy.get_feature_vector()):
                    if not w_copy.external_tail_head_test():
                        priority = priority + priority_base - 100
                        log(f'\t\t\t\tAvoid {site} due to tail-head failure.')
                        avoid_set.add(site)
                    else:
                        priority = priority + priority_base + 100
                        log(f'\t\t\t\tConsidering {site} due to legitimate tail-head configuration.')
                        avoid_set.clear()
                w_copy.remove()

            adjunction_sites.append((priority, site))

        # Case 8. Phillips anomaly = no positive solution found based on local information available
        if len(avoid_set) == len(adjunction_sites):

            # Search the largest adjoinable and LF-legible attachment site not containing T/fin
            size = 0
            max_site = None
            for priority, site_ in adjunction_sites:
                if site_.is_adjoinable():
                    size_ = get_size(site_)
                    if size_ > size and not site_.contains_feature('CAT:T/fin'):
                        set_logging(False)
                        if self.reconstruct(site_.copy()).LF_legibility_test().all_pass():
                            max_site = site_
                            max_priority = priority
                            size = size_
                        set_logging(True)

            if max_site:
                log(f'\t\t\t\tPrioritize {max_site} because all solutions were negative.')
                adjunction_sites.remove((max_priority, max_site))
                adjunction_sites.append((max_priority + 200, max_site))

        # Sort based on priority (and only priority, not phrase structure)
        adjunction_sites = sorted(adjunction_sites, key=itemgetter(0))

        adjunction_sites = [site for priority, site in adjunction_sites]
        adjunction_sites.reverse()

        log(f'\t\tRanking completed:')
        for i, site in enumerate(adjunction_sites, start=1):
            log(f'\t\t\t{i}. [{site}; {word_pf}]')
        return adjunction_sites

    # This will promote a phi set (if any) into tail features
    def promote_phi_set(self, ps):
        """
        Promotes the phi-set into the status of a tail feature.

        An argument DP can be floated by allowing its phi-features to function as tail-features. When this happens,
        the DP will function like an adverb that tries to link with a functional element containing those phi-
        features. Intuitively, it links DPs with c-commanding heads that share their phi-features. This function
        must be scrutinized later when we add phi-feature mechanisms more generally.
        """

        if ps.get_phi_set():
            new_tail_feature_list = list(ps.get_phi_set())
            new_tail_feature = f'TAIL:{",".join([str(f) for f in sorted(new_tail_feature_list)])},!COMP:*'
            ps.features.add(new_tail_feature)
            return True
        else:
            return False

    def transfer_to_LF(self, ps):
        """
        Transfers the syntactic phrase structure into the conceptual-intentional system through the LF-interface.

        If transfer is successful, i.e. if the configuration is interpretable semantically, the function returns
        true (and the conceptual-intentional system takes over). If it is not successful, the operation returns
        false. This will generally imply that the solution was rejected and parsing must continue.
        """
        def detached(ps):
            ps.mother = None
            return ps

        lf = LF()
        return(lf.transfer_to_LF(detached(ps.copy())))

    def morphological_parse(self, lexical_constituent, lst_branched, index):
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

        #  All word-internal morphemes will begin with symbol $ (= phonological spell-out feature)
        word = word.replace("#", "#$")
        lst_ = word.split("#")

        # If we had more than one morpheme, the list will substitute the original multimorphemic word
        if len(lst_) > 1:
            log('\n' + f'\t\tNext word contains multiple morphemes ' + str(lst_[::-1]))

            del lst_branched[index]
            for w_ in lst_:
                lst_branched.insert(index, w_)

            # Take the first morpheme discovered and continues parsing from that
            return self.lexical_access.access_lexicon(lst_branched[index])[0]
        else:
            # If there was only one morpheme, we return that
            return lexical_constituent

    # This function checks if phrase structure XP cannot be broken off from its selector H (H-XP) because
    # H and X were part of the same word. It is used to prevent right adjunction to XP
    def is_word_internal(self, XP):
        if XP.mother and XP.sister() and XP.sister().is_primitive() and XP.sister().is_word_internal():
            return True
        else:
            return False

    # Reverses all movement
    def reconstruct(self, ps):
        original_mother = ps.mother
        ps.detach()
        R = Reconstruction()
        ps = R.reconstruct(ps)
        if original_mother:
            ps.mother = original_mother

        return ps