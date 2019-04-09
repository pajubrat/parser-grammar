from support import set_logging, log, get_number_of_operations, reset_number_of_operations, log_result, illu
from LexicalInterface import LexicalInterface
from LF import LF
from operator import itemgetter

# Brattico-Chesi Parser
# 2019
# V. 0.9

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
            ps_ = self.drop(ps)
            log('\t\t\t= ' + ps_.illustrate())
            log(f'\t\tChecking LF-interface conditions.')

            # Test if the final configuration is grammatical
            # The three tests below check for LF-interface conditions
            if self.LF_legibility_test(ps_).all_pass():
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

                    # Merge the new word (disambiguateted lexical item) to the existing phrase structure
                    else:
                        log('\n\t\tConsume \"' + lex_decomposed.get_pf() + '\"\n')
                        log('\t\t' + ps.illustrate() + ' + ' + lex_decomposed.get_pf())

                        # --------- This is the core parsing functionality -----------

                        # Get the adjunction sites
                        adjunction_sites = self.ranking(self.filter(ps, lex_decomposed), lex_decomposed)

                        # Test each licit adjunction site in the order of ranking
                        for i, site in enumerate(adjunction_sites, start=1):
                            ps_ = ps.get_top().copy()
                            log(f'\t\tExploring solution number ({i}) =' + f'[{site} {lex_decomposed.get_pf()}]')
                            site_ = self.drop(ps_[ps.index(site)])
                            self.__first_pass_parse(site_.merge(lex_decomposed, 'right'), lst_branched, index + 1)
                            if self.exit:
                                break

                        # -------------------------------------------------------------

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
        for site in ps:
            if site.is_primitive() and site.internal:
                log(f'\t\t\tForce {w.get_pf()} COMP to {site.get_pf()}'
                    ' because morphology tells they were inside the same phonological word.')
                return [site]

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
                dropped = self.drop(site.copy())

                lf_test = self.LF_legibility_test(dropped)
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
                dropped = self.drop(site.copy())
                set_logging(True)

                if self.LF_legibility_test(dropped).fail():
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
                        if self.LF_legibility_test(self.drop(site_.copy())).all_pass():
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

    # This is reductive definition for EPP under current feature system
    def EPP(self, ps):
        """
        A reductive definition for the generalized EPP feature.

        This provides a reductive definition for Chomsky's (2000) generalized EPP as it is realized in the
        present theory: it is a combination of three things:

        i) SPEC:* feature,
        ii) !SPEC:* feature,
        iii) +PHI marking.

        The relevance of (iii) is currently open.
        """

        for f in ps.features:
            if f == 'SPEC:*' or f == '!SPEC:*' or f == '+PHI':
                return True
        return False

    # Returns True if a spec-feature of H matches with the category of the head of G
    def spec_match(self, H, G):

        if 'SPEC:*' in H.features or '!SPEC:*' in H.features:
            return True

        for f_ in H.for_parsing(H.get_specs()):
            for g_ in G.get_labels():
                if f_ == g_:
                    return True
        return False

    def LF_legibility_test(self, ps):
        """
        Checks if the phrase structure, as a detached item, is interpretable at the LF-level

        The construction is send off to LF interface (a separate class/object) for checking. The function that
        performs checking is lf.test(), lf being an object of the class LF().
        """
        def detached(ps):
            ps.mother = None
            return ps

        lf = LF()
        lf.test(detached(ps.copy()))
        return lf

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
        (w1, w2, a#b#c, w3) = (v1, v2, v3, c, b, a, v3), and puts the index to point 'a'.

        """

        # Morphological symbols
        # '#*   internal morpheme boundaries from the lexicon, will be removed
        # '$'   internal morpheme boundary, as marked by the morphological parser
        #       In syntax, $ corresponds to 'needs a host word, grab local head.'

        # Create a list of morphemes
        word = lexical_constituent.morphology

        #  All word-internal morphemes will begin with symbol $ (= phonological spellout feature)
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

    # ---- Movement related functions -------------------------------------------------

    # This locates node XP in [T/fin XP] or return the highest node if not found
    # It is required because many operations are restricted by a minimal tense condition
    # e.g. argument/adjunct float
    # todo the implementation is ugly and descriptive this must be re-thought
    # todo we have the same condition in other places but written differently
    def locate_minimal_tense_edge(self, ps):

        ps_iterator_ = ps
        node = ps

        # If we do not detect T/fin... go upwards
        while ps_iterator_ and \
                ps_iterator_.geometrical_sister() and \
                not ps_iterator_.is_finite() and \
                not ps_iterator_.geometrical_sister().is_finite():
            node = ps_iterator_
            ps_iterator_ = ps_iterator_.walk_upstream()

        if not ps_iterator_:
            ps_iterator_ = node

        # If we are inside T/fin..., we need to climb down to XP, [T/Fin XP]
        while ps_iterator_ and ps_iterator_.is_finite():
            node = ps_iterator_
            ps_iterator_ = ps_iterator_.walk_downstream()

        if not ps_iterator_:
            ps_iterator_ = node

        return ps_iterator_

    # Reverses all movement
    def drop(self, ps):
        """
        Performs phrasal dropping for a phrase structure.

        The phrase structure is first detached from its context (mother). (i) Floater dropping is applied first,
        followed by (ii) A/A-bar dropping (Chesi memory buffer). A/A-bar dropping are not distinguished in this version,
        but will be distinguished later.

        (i) The right edge of the phrase structure is explored to locate constituents (at left) with tail-head features
        at their heads that are not satisfied. Once found, the constituent is dropped. Dropping is implemented by
        going back to the highest node, walking downwards and looking for the first position that would satisfy the
        tail-features.

        (ii) Walk downwards on the right edge, while locating left heads with the EPP feature. If found, put the
        phrase from SPEC into M-buffer. Conversely, if we encounter a head that has a SPEC or COMP feature
        matching with something in M-buffer but missing in the phrase structure, elements are transferred from
        M-buffer into these positions. The result is that phrases are dropped from SPEC/EPP positions into
        positions in which they are lexically selected (either SPEC or COMP).
        """

        if ps.is_primitive():
            return ps

        # Checks intervention
        def memory_intervention(criterial_features):
            for constituent in memory_buffer:
                if constituent.get_criterial_features().intersection(criterial_features):
                    return True
            return False

            # Drops all floaters in a structure
        def drop_floaters(ps):

            # Drops one phrase that has been detected as a floater
            def drop_floater(floater, ps):

                def adjoin_floater(floater, site, direction):
                    site.merge(floater, direction)

                # ---drop floater beings here---
                Tfin = None
                T_fin_intervention = False

                # We need to locate the approriate starting point, the node XP in [T/fin XP]
                ps_iterator_ = self.locate_minimal_tense_edge(floater.mother)
                floater_copy = floater.copy()

                while not T_fin_intervention and ps_iterator_ and not ps_iterator_ == floater and not ps_iterator_.find_me_elsewhere:

                    # Determine if the conditions for T/fin intervention are satisfied
                    if ps_iterator_.sister() and 'T/fin' in ps_iterator_.sister().get_labels():
                        if Tfin == None:
                            Tfin = ps_iterator_.sister().get_head()
                        else:
                            if not ps_iterator_.sister().get_head() == Tfin:
                                T_fin_intervention = True

                    # Create hypothetical structure for testing
                    if 'ADV' in floater_copy.get_labels():
                        ps_iterator_.merge(floater_copy, 'right')
                    else:
                        ps_iterator_.merge(floater_copy, 'left')

                    # If a suitable position is found, dropping will be executed
                    if floater_copy.get_head().external_tail_head_test():
                        self.create_adjunct(floater)
                        dropped_floater = floater.transfer(self.babtize())
                        if 'ADV' in floater_copy.get_labels() or 'P' in floater_copy.get_labels():
                            adjoin_floater(dropped_floater, ps_iterator_, 'right')
                        else:
                            adjoin_floater(dropped_floater, ps_iterator_, 'left')
                        floater_copy.remove()
                        floater.find_me_elsewhere = True
                        log(f'\t\t\t\tFloater ' + dropped_floater.illustrate() + ' dropped.')
                        return
                    else:
                        floater_copy.remove()

                    ps_iterator_ = ps_iterator_.walk_downstream()

            # --- drops all floaters --- #

            _ps_iterator = ps.get_top()  # Begin from the top and move downstream
            log(f'\t\t\t!Operation: Dropping floaters...')
            while _ps_iterator:

                floater = None

                # Check if a phrase at the left has unsatisfied tail features
                if not _ps_iterator.is_primitive() and \
                        not _ps_iterator.left_const.is_primitive() and \
                        not _ps_iterator.left_const.find_me_elsewhere and \
                        _ps_iterator.left_const.get_head().get_tail_sets():
                    floater = _ps_iterator.left_const

                    # Check if its tail features fail to find a head
                    if not floater.get_head().external_tail_head_test():
                        log('\t\t\t\t' + floater.illustrate() + ' failed to tail ' + illu(
                            floater.get_head().get_tail_sets()))
                        drop_floater(floater, ps)

                    # Or if it (constituent with tail features) sits in an EPP SPEC position of a finite clause edge
                    elif floater.mother and self.EPP(floater.mother.get_head()) and floater.mother.is_finite():
                        log('\t\t\t\t' + floater.illustrate() + ' is in an EPP SPEC position.')
                        drop_floater(floater, ps)

                # Check if the right edge itself has tail features (e.g. DP at the bottom, floaters/adjuncts)
                if not _ps_iterator.is_primitive() and \
                        _ps_iterator.right_const.get_head().get_tail_sets():
                    floater = _ps_iterator.right_const.get_head()

                    # If tail features fail to find a head, the constituent must be dropped
                    if not floater.external_tail_head_test():
                        log('\t\t\t\t' + floater.illustrate() + ' failed to tail.')

                        # This is empirically very contentious matter:
                        # A right DP inside a finite clause with failed tail-test must be an adjunct(?)
                        if 'D' in floater.get_labels() and floater.get_top().contains_feature('CAT:T/fin'):
                            self.create_adjunct(floater)
                        drop_floater(floater.mother, ps)
                    else:
                        if 'ADV' in floater.get_labels() and not _ps_iterator.right_const.adjunct:
                            self.create_adjunct(floater)

                # Travels on the right edge
                _ps_iterator = _ps_iterator.walk_downstream()

            log(f'\t\t\t\t= ' + ps.illustrate())

            # --- drop floaters ends here --- #

        # This algorithm will try to apply extraposition to the phrase structure
        # Last resort function
        # The true nature of this rule, or if it indeed exists, is very unclear to me
        # todo, does not process correctly layered adjunctions (e.g. "of the visit of John")
        def try_extraposition(ps):
            # Returns the bottom node on the right edge (not geometrical)
            def get_bottom(ps):
                iterator_ = ps
                while iterator_:
                    if iterator_.is_primitive():
                        return iterator_
                    else:
                        iterator_ = iterator_.walk_downstream()

                return

            # Presupposition 1
            # LF - legibility fails(last resort)
            if self.LF_legibility_test(ps.get_top()).all_pass():
                return

            # Presupposition 2
            # Do this only for referential structures (T/fin, D)
            if not(ps.get_top().contains_feature('CAT:T/fin') or 'D' in ps.get_top().get_labels()):
                return

            log(f'\t\t\t\tExtraposition will be tried on {ps.get_top()}.')
            self.operator_counter_ += 1
            ps_ = get_bottom(ps).mother

            # Find first [H XP] where H is adjoinable and
            # we have either [XP][HP] or [X HP] with X not selecting for H
            while ps_:
                if ps_.left_const.is_primitive() and ps_.left_const.is_adjoinable() and ps_.sister():

                    # If its phrase, then we can select HP
                    if not ps_.sister().is_primitive():
                        break

                    # If it is head, then we select HP if the head rejects HP as complement
                    elif set(ps_.left_const.get_labels()) & set(ps_.sister().get_not_comps()):
                        break

                ps_ = ps_.walk_upstream()

            if ps_:

                # It only applies this rule if there is a verb (V) or D
                # This is LF-requirement: the adjunct must get semantic interpretation
                for head in ps_.left_const.get_feature_vector():
                    if 'T/fin' in head.get_labels() or 'D' in head.get_labels():
                        ps_.adjunct = True
                        log(f'\t\t\t\t{ps_} was made adjunct by an extraposition rule.')
                        if not self.LF_legibility_test(ps_.get_top()).all_pass():
                            # If phi set is available...
                            if self.promote_phi_set(ps_.left_const):
                                log(f'\t\t\t\tThe structure is still illicit. Try phi-tailing as a last resort.')
                                drop_floaters(ps_.get_top())
                                log(f'\t\t\t\t={ps_.get_top()}')
                        return True

            return False
            # ---end of try extraposition---#

        # Reverse-engineers A-movement and A-bar movement and uses Chesi memory buffer
        def drop_movement(ps):
            # Creates an adjunct of the constituent ('ps')

            memory_buffer = []
            _ps_iterator = ps
            _ps_last_site = _ps_iterator

            log(f'\t\t\t!Operation: Dropping A-/A-bar movement with Chesi memory buffer.')
            while _ps_iterator:

                # Target primitive heads on our way downstream
                if _ps_iterator.is_primitive():
                    h = _ps_iterator
                elif _ps_iterator.left_const.is_primitive():
                    h = _ps_iterator.left_const
                else:
                    h = None

                # If a primitive head was detected
                if h:
                    h_labels = sorted(h.get_labels())

                    # Case 1a. Missing Spec is filled.
                    # The head has no phrase in its Spec, but the memory buffer holds a suitable constituent
                    if _ps_iterator.sister() and _ps_iterator.sister().is_primitive():
                        target_const = None

                        # Select the first possible Spec constituent
                        for const in memory_buffer:
                            if self.spec_match(h, const) and not target_const:
                                target_const = const

                        # Transfer it from memory buffer into the phrase structure
                        if target_const:

                            # Try to merge it to Spec
                            _ps_iterator.merge(target_const.transfer(self.babtize()), 'left')

                            # Check that this does not cause tail-head violations
                            if _ps_iterator.geometrical_sister().get_head().external_tail_head_test():
                                log(f'\t\t\t\tDropping constituent {target_const} from memory buffer into Spec of ' +
                                    f'{h_labels}')
                                memory_buffer.remove(target_const)
                                self.operator_counter_ += 1
                            else:
                                # If there was a tail-head violation, dropping is cancelled
                                _ps_iterator.geometrical_sister().remove()

                    # Case 1b. EPP head hosts Specs.
                    # The head has the EPP and a phrase (or several) is sitting at its Specs (left)
                    if self.EPP(h):

                        # spec-iterator iterated over multiple Specs (if possible) into upward direction
                        _ps_spec_iterator = _ps_iterator
                        list_ = []
                        spec_found = False
                        while _ps_spec_iterator:

                            # If a phrase is found from left...

                            if _ps_spec_iterator.sister() and \
                                    not _ps_spec_iterator.sister().is_primitive() and \
                                    _ps_spec_iterator.sister().is_left():

                                # we gather criterial features from the Spec (WH, FOC, REL, TOP)
                                criterial_features = _ps_spec_iterator.sister().get_criterial_features()
                                # Reset memory if there is intervention
                                if memory_intervention(criterial_features):
                                    memory_buffer = []

                                # ...and it has not been moved already...
                                if not _ps_spec_iterator.sister().find_me_elsewhere:
                                    # ...we put a pointer to the specifier into memory buffer.
                                    list_.append(_ps_spec_iterator.sister())
                                    log(f'\t\t\t\tMoving \"' + _ps_spec_iterator.sister().spellout() + f'\" into memory buffer from SPEC of {h}.')

                                # If we already have processed one Spec, then we are gonna need to spawn phantom heads
                                if spec_found:

                                    if not criterial_features:
                                        log(f'\t\t\t\tNew head was spawned due to multiple specifiers at {h}'
                                            ' but its category is unknown!')
                                    else:
                                        log(f'\t\t\t\tNew {criterial_features} head was spawned due to '
                                            f'the occurrence of multiple specifiers at {h.get_pf()}')

                                    # Create and merge the new head, then move the pointer over it so we don't repeat
                                    new_h = self.engineer_head_from_specifier(criterial_features)
                                    _ps_spec_iterator.merge(new_h, 'left')

                                    # Move to the new constituent (otherwise we will loop this)
                                    _ps_spec_iterator = _ps_spec_iterator.walk_upstream()
                                    if new_h.get_tail_sets():
                                        log('\t\t\t\tThe new head has tail features, must be an adjunct floater.')
                                        self.create_adjunct(new_h)

                                        # Drop inside the right-adjunct
                                        if _ps_spec_iterator.mother:
                                            _ps_spec_iterator = _ps_spec_iterator.mother  # Move one step up
                                else:
                                    # If its just one Spec, copy criterial features
                                    spec_found = True  # We register that one head has been found
                                    if criterial_features:
                                        log(f'\t\t\t\tCriterial features {criterial_features} copied to {h_labels}')
                                        for f in criterial_features:
                                            # Create formal copies of features
                                            h.features.add('CAT:u' + f)
                                            # Add scope marker if needed, todo this looks stipulative in the present form
                                            if 'C/fin' in h.get_labels() or 'T/fin' in h.get_labels() or 'FORCE' in h.get_labels():
                                                h.features.add('CAT:i' + f)
                                            h.features = self.lexical_access.apply_parameters(
                                                self.lexical_access.apply_redundancy_rules(h.features))
                                        if h.get_tail_sets():
                                            log(f'\t\t\t\tTail features ' + illu(h.get_tail_sets()) + f' were detected at {h}, this must head an adjunct floater.')
                                            self.create_adjunct(h)
                                            if _ps_spec_iterator.mother:
                                                _ps_spec_iterator = _ps_spec_iterator.mother

                                # Move to next specifier
                                _ps_spec_iterator = _ps_spec_iterator.walk_upstream()

                            # If there is primitive c-commanding head on the left, we must stop searching
                            else:
                                _ps_spec_iterator = None

                        # Add everything into memory buffer
                        memory_buffer = list_ + memory_buffer

                        if len(list_) > 0:
                            log(f'\t\t\t\tMemory buffer: {memory_buffer}')

                    # Case 1c. Missing Comp.
                    # The head lacks complement but could take one, and a matching entity is found from memory buffer
                    if h.is_primitive() and not h.complement():
                        # If H has comp features
                        if h.get_comps():
                            target_const = None
                            for const in memory_buffer:
                                for c in h.get_comps():
                                    # If suitable candidate exists in the memory buffer
                                    if c in const.get_labels() and target_const == None:
                                        target_const = const

                            if target_const:
                                h.merge(target_const.transfer(self.babtize()), 'right')
                                log(f'\t\t\t\tDropping {repr(target_const)}(=' + target_const.spellout()
                                    + f') from memory buffer into Comp of {h_labels}.')
                                log(f'\t\t\t\tResult {h.get_top()}')
                                memory_buffer.remove(target_const)
                                log(f'\t\t\t\tRemaining items in memory buffer: {memory_buffer}')

                    # Case 1d. Mismatching Comp.
                    # The head has a non-matching complement and matching item is found from memory
                    if h.is_left() and h.complement():
                        match_found = False
                        target_const = None
                        for label in h.complement().get_labels():
                            for comp in h.get_comps():
                                if label == comp:
                                    match_found = True  # matching H-comp feature was found => don't bring anything from memory
                        # look if there is something in MB
                        if not match_found:
                            for const in memory_buffer:
                                for comp in h.get_comps():
                                    if comp in const.get_labels() and target_const == None:
                                        target_const = const

                        if not match_found and target_const:
                            log(f'\t\t\t\tDropping {repr(target_const)}(=' + target_const.spellout()
                                + f') from memory buffer into Comp of {h_labels} '
                                  f'due to the presence of mismatching complement {h.complement()}.')
                            h.complement().merge(target_const.transfer(self.babtize()), 'left')
                            # The mismatching complement will be demoted to floater status
                            if h.complement().right_const.is_adjoinable():
                                log('\t\t\t\tThe mismatching complement will be trasformed into floater adjunct.')
                                self.create_adjunct(h.complement().right_const)
                            memory_buffer.remove(target_const)
                            log(f'\t\t\t\tRemaining memory buffer: {memory_buffer}')

                # Walk downwards on the right edge
                _ps_last_site = _ps_iterator
                _ps_iterator = _ps_iterator.walk_downstream()

            try_extraposition(_ps_last_site)


        #---Dropping algorithm main body---#

        # Detach the structure
        original_mother = ps.detach()
        memory_buffer = []
        self.operator_counter_ = 0
        drop_floaters(ps)
        drop_movement(ps)

        # Restore the links
        if original_mother:
            ps.get_top().mother = original_mother

        # Return the new structure
        return ps

    # Creates an adjunct of a constituent
    def create_adjunct(self, ps):
        """
        Creates an adjunct out of a constituent.

        Adjuncts are marked as such by a specific feature of the constituent. Right adjuncts are processes in a
        separate syntactic working space. This function sets that feature to true.

        If the sister is already an adjunct, the operation is cancelled. In other words, [<XP>, <YP>] is not possible.
        This constituent is anomalous in the current system.

        If the constituent is a phrase, it is marked as adjunct and no further steps are taken. If the constituent
        is a head, then we have to consider how much of the surrounding structure will be eaten into the adjunct. If
        the head is marked for EPP, we eat the SPEC (if any). If not, we can eat only the complement. The procedure here
        is complex and must be verified by empirical tests.
        """

        def make_adjunct(ps):
            if ps.geometrical_sister() and ps.geometrical_sister().adjunct:
                log(f'\t\t\t\t{ps} cannot be made an adjunct because its sister is an adjunct.')
                return False
            ps.adjunct = True
            log(f'\t\t\t\t{ps} was made an adjunct.')
            return True

        # --- Main function begins here --- #

        head = ps.get_head()

        # If the head is primitive, we must decide how much of the surrounding structure we will eat
        if ps.is_primitive():
            # If the adjunct has found an acceptable position, we use !SPEC:* feature
            if head.external_tail_head_test():
                if '!SPEC:*' in head.features and head.mother.mother:
                    make_adjunct(head.mother.mother)
                    return ps.mother.mother
                else:
                    make_adjunct(head.mother)
                    return ps.mother
            # If the adjunct is still in wrong position, we eat the specifier if accepted
            else:
                # If potential Spec exists and the head accepts specifiers...
                if head.specifier() and not '-SPEC:*' in head.features and \
                        not set(head.get_not_specs()).intersection(set(head.specifier().get_labels())):
                    if head.mother.mother:
                        make_adjunct(head.mother.mother)
                    return ps.mother.mother
                else:
                    make_adjunct(head.mother)
                    return ps.mother
        else:
            make_adjunct(ps)

    # This will create a head from a specifier that lacks a head
    def engineer_head_from_specifier(self, features):
        """
        This operation spawns a head H from a detected specifier XP that lacks a head.

        The category of the new head will be constructed from the criterial features F... scanned from XP,
        by creating uninterpretable (uF) and interpretable (iF) copies of the original features (F).

        The uninterpretable feature uF is the probe feature that agrees with F, but does not have
        semantic effects. The interpretable feature iF represents the scope-marker or the criterial head.
        Accordingly, a head that is spawned is always a criterial head. Then, other required features
        are added to the head on the basis of lexical rules (or the language).
        """

        new_h = self.lexical_access.PhraseStructure()

        # The category of the new head is going to be a copy of criterial feature of Spec
        # We also create artificial phonological matrix for illustration
        for f in features:
            new_h.features.add('CAT:u' + f)
            new_h.features.add('PF:u' + f)
            new_h.features.add('CAT:i' + f)

        # We add EPP required features
        new_h.features = self.lexical_access.apply_parameters(
            self.lexical_access.apply_redundancy_rules(new_h.features))
        return new_h

    # This will provide unique names when chains are formed
    # It is used only for output purposes
    def babtize(self):
        self.name_provider_index += 1
        return str(self.name_provider_index)
