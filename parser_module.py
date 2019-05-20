from support import set_logging, log, show_results, report_LF_problem, report_tail_head_problem, reset_number_of_operations, log_result, illu
from LexicalInterface import LexicalInterface
from LF import LF
from operator import itemgetter
from reconstruction import Reconstruction
from morphology import Morphology

# Parser-Grammar
# 2019
# V. 1.02

class Pcb_parser():
    def __init__(self, context):

        # Contextual variables (language etc.)
        self.context = context

        # All results (analyses)
        self.result_list = []

        # Number of lexical ambiguities detected (support function)
        self.number_of_ambiguities = 0

        # Support function
        self.result_matrix = [[] for i in range(50)]

        # Local memory buffer for inflectional affixes
        self.memory_buffer_inflectional_affixes = set()

        # This counts the number of computational operations (support function)
        self.number_of_Merges = 1
        self.number_of_Moves = 1
        self.number_of_solutions_tried = 0
        self.discourse_plausibility = 0
        self.score = 0

        # Stops parsing when the first solution is available
        self.exit = False

        # index for name provider, for output reasons (chain identification)
        self.name_provider_index = 0

        # Access to the lexicon
        self.lexicon = LexicalInterface(self.context.redundancy_rules_file)
        self.lexicon.load_lexicon(self.context.lexicon_file, context.language)
        self.lexicon.load_lexicon(self.context.ug_morphemes_file, context.language, combine=True)
        self.morphology = Morphology(self.context)
        self.reconstruction = Reconstruction(self.context)

    # Preparatory steps.
    def parse(self, lst):
        """
        Parses a list of words.

        The operation prepares the parser and its parameters, and then initiates the recursive
        parsing operation.
        """
        # Reset parser state
        self.result_list = []
        self.memory_buffer_inflectional_affixes = set()
        self.number_of_Merges = 0
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
        self.number_of_Merges = self.number_of_Merges + 1
        log(f'\t\t\t={ps}')
        log('\n' + str(self.number_of_Merges) + '.')

        # Test if we have reached at the end of the input list
        if index == len(lst):
            self.number_of_solutions_tried = self.number_of_solutions_tried + 1
            log('\t>>>\t' + f'Trying candidate parse ' + ps.illustrate() + ' ('+str(self.number_of_solutions_tried)+'.)')
            log('\t\tReconstructing...')
            ps_ = self.reconstruct(ps)
            log('\t\t\t= ' + ps_.illustrate())
            log(f'\t\tChecking LF-interface conditions.')
            lf = ps_.LF_legibility_test()
            if lf.all_pass():
                if lf.final_tail_check(ps_) and self.transfer_to_LF(ps_):
                    self.discourse_plausibility = lf.discourse_test_result
                    self.score = 1 - self.number_of_solutions_tried - self.discourse_plausibility
                    self.result_list.append(ps_)
                    # show_results(ps_, self.result_list, self.number_of_Merges, self.number_of_Moves, self.number_of_solutions_tried)
                    self.exit = True    # Knock this out if you want to see all solutions
                else:
                    report_tail_head_problem(ps_)
            else:
                report_LF_problem(ps_)
            return  # This return will send the parser to an unexplored path in the recursive parse tree
        # Process next word
        else:
            # Initialize morphology
            m = self.morphology

            # Lexical ambiguity
            # If the item was not recognized, an ad hoc constituent is returned that has CAT:X
            disambiguated_word_list = self.lexicon.access_lexicon(lst[index])
            if len(disambiguated_word_list) > 1:
                log('\t\tAmbiguous lexical item ' + str(disambiguated_word_list) + 'detected.')

            for lexical_constituent in disambiguated_word_list:
                lst_branched = lst.copy()

                # Morphological decomposition: increases the input list if there are several morphemes
                # If the word was not recognized (CAT:X), generative morphology will be tried
                lexical_item, lst_branched = m.morphological_parse(lexical_constituent,
                                                                   lst_branched,
                                                                   index)

                # Read inflectional features (if any) and store them into memory buffer, then consume next word
                inflection = m.get_inflection(lexical_item)
                if inflection:
                    # Add inflectional features and prosodic features into memory
                    self.memory_buffer_inflectional_affixes = self.memory_buffer_inflectional_affixes.union(inflection)
                    log('\n\t\tConsume \"' + lst_branched[index + 1] + '\"\n')
                    if ps:
                        self.__first_pass_parse(ps.copy(), lst_branched, index + 1)
                    else:
                        self.__first_pass_parse(None, lst_branched, index + 1)

                # If the item was not inflection, it is a morpheme that must be merged
                else:
                    # Unload inflectional suffixes from the memory into the morpheme as features
                    lexical_item = m.set_inflection(lexical_item, self.memory_buffer_inflectional_affixes)
                    self.memory_buffer_inflectional_affixes = set()

                    # If there is no prior phrase structure, we create it by using the first word
                    if not ps:
                        self.__first_pass_parse(lexical_item.copy(), lst_branched, index + 1)

                    # Merge the new word (disambiguated lexical item) to the existing phrase structure
                    else:
                        log('\n\t\tConsume \"' + lexical_item.get_pf() + '\"\n')
                        log('\t\t' + ps.illustrate() + ' + ' + lexical_item.get_pf())

                        # ------------------------------------------------------------------------------
                        # ------------------------------------------------------------------------------

                        # Get the merge sites
                        adjunction_sites = self.ranking(self.filter(ps, lexical_item), lexical_item)

                        # Test each licit adjunction site in the order of ranking
                        for i, site in enumerate(adjunction_sites, start=1):
                            ps_ = ps.get_top().copy()   # We copy the phrase structure first to create clean branch
                            if site.get_bottom_affix().internal:
                                log(f'\t\tExploring solution number ({i}) =' + f'[{site}*{lexical_item.get_pf()}]')
                                site_ = ps_[ps.index(site)]
                                new_ps = site_ * lexical_item
                            else:
                                log(f'\t\tExploring solution number ({i}) =' + f'[{site} {lexical_item.get_pf()}]')
                                site_ = self.reconstruct(ps_[ps.index(site)])
                                new_ps = site_ + lexical_item
                            self.__first_pass_parse(new_ps, lst_branched, index + 1)
                            if self.exit:
                                break

                        # ------------------------------------------------------------------------------
                        # ------------------------------------------------------------------------------

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

            # Word-breaking violations
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

        word_specs = w.for_parsing(w.get_specs())
        word_rare_specs = w.for_parsing(w.get_rare_specs())
        word_not_specs = w.for_parsing(w.get_not_specs())
        word_cats = w.get_cats()
        word_tail_set = w.get_tail_sets()
        word_pf = w.get_pf()
        word_labels = w.get_labels()

        adjunction_sites = []
        avoid_set = set()

        for i, site in enumerate(site_list, start=1):

            # This determines how to order constituents with the same ranking
            # This method takes the local phrase
            priority_base = i

            priority = 0 + priority_base
            site_cats = site.get_head().get_cats()

            # Case 2a. Spec Solutions
            # Check if there are SPEC-w solutions
            # Get all positive SPEC solutions from w
            if word_specs & site_cats:
                priority = priority + priority_base + 100 * len(word_specs & site_cats)
                log(f'\t\t\t\tPrioritize {site.get_cats_string()} as SPEC,{word_pf}.')
                avoid_set.clear()

            # Case 2b. Spec Mismatches
            # Check if there are negative SPEC conditions and avoid them
            # Get negative -SPEC features from w
            if not site.is_primitive() and (word_not_specs & site_cats):
                priority = priority + priority_base - 100 * len(word_not_specs & site_cats)
                log(f'\t\t\t\tAvoid {site.get_head().get_cats_string()}P as SPEC, {word_pf}.')
                avoid_set.add(site)

            # Avoid all SPEC solutions if there is [-SPEC:*]
            if '*' in word_not_specs:
                priority = priority + priority_base - 100
                log(f'\t\t\t\tAvoid {site.get_head().get_cats_string()}P as SPEC for {word_pf} due to unselective SPEC feature.')
                avoid_set.add(site)

            # Avoid rare SPEC solutions
            if word_rare_specs & site_cats:
                priority = priority + priority_base - 1000
                log(f'\t\t\t\tAvoid {site.get_head().get_cats_string()}P as SPEC for {word_pf} due to rare SPEC feature.')
                avoid_set.add(site)

            # Case 2c. Check if existing H-Comp-relations would be broken
            # The rule captures that fact that 'H X' often means [H XP]
            # Improves performance 75%
            # Antecedent condition: site is c-commanded locally (possible selected) by a head H
            if not site.is_primitive() and site.mother and \
                    site.mother.left_const and site.mother.left_const.is_primitive():
                # and if H selects for site
                if site.mother.left_const.get_comps() & site.get_labels():
                    if 'ADV' not in w.get_labels(): # Adverbs will not break selection because they will be adjuncts
                        priority = priority + priority_base - 100 * len(site.mother.left_const.get_comps() & site.get_labels())
                        log(f'\t\t\t\tAvoid [{site}, {w}] because the operation breaks up an existing selectional dependency.')
                        avoid_set.add(site)

            # Case 4. Comp solutions and local morphosyntax
            # Check if site is primitive (takes a complement)
            if site.is_primitive():
                # Check if the solution violates tailing agreement and if yes, avoid
                # Check that the new constituent has tailing features
                if word_tail_set:
                    test_word = w.copy()
                    site.merge(test_word, 'right')
                    if not test_word.internal_tail_head_test():
                        priority = priority + priority_base - 50
                        log(f'\t\t\t\tAvoid [{site.get_pf()} {word_pf}] due to local agreement failure.')
                        avoid_set.add(site)
                    test_word.remove()

                # Evaluation Comp selection for all morphemes inside the site
                # This can also be implemented by using get_affix_comps() function
                for m in site.get_affix_list():
                    # Check if H selects w and if yes, prioritize this solution
                    if word_cats & m.for_parsing(m.get_comps()):
                        priority = priority + priority_base + 100
                        log(f'\t\t\t\tPrioritize [{m.get_pf()} {word_pf}] due to complement selection.')
                        avoid_set.clear()

                    # ... if f cannot be merged to the complement, avoid this solution
                    if word_cats & m.for_parsing(m.get_not_comps()):
                        # This condition has the effect that D{N} will be favored as SPEC
                        # (i.e. neither D nor N will take w as COMP and so negative comp solutions are not examined)
                        if 'CAT:N' not in m.features and 'CAT:D' not in m.features:
                            priority = priority + priority_base - 100 * len(word_cats & m.for_parsing(m.get_not_comps()))
                            log(f'\t\t\t\tAvoid [{m.get_pf()} {word_pf}] due to complement selection.')
                            avoid_set.add(site)

                    if not LF.semantic_match(m, w):
                        priority = priority + priority_base - 100
                        log(f'\t\t\t\tAvoid [{site},{w}] solution due to semantic mismatch.')
                        avoid_set.add(site)

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
            if site.is_primitive() and self.is_word_internal(site):
                if 'ADV' not in w.get_labels():
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

        # Provide rankings
        for priority, site in adjunction_sites:
            log(f'\t\t\t\t{site} + {word_pf} = {priority}]')

        # Sort based on priority (and only priority, not phrase structure)
        adjunction_sites = sorted(adjunction_sites, key=itemgetter(0))
        adjunction_sites = [site for priority, site in adjunction_sites]

        adjunction_sites.reverse()

        log(f'\t\tRanking completed:')
        for i, site in enumerate(adjunction_sites, start=1):
            log(f'\t\t\t{i}. [{site}; {word_pf}]')
        return adjunction_sites

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

    # This function checks if phrase structure XP cannot be broken off from its selector H (H-XP) because
    # H and X were part of the same word. It is used to prevent right adjunction to XP
    def is_word_internal(self, XP):
        if XP.mother and XP.sister() and XP.sister().is_primitive() and XP.sister().is_word_internal():
            return True
        else:
            return False

    # Reverses all movement inside left branches
    def reconstruct(self, ps):
        original_mother = ps.mother
        ps.detach()
        R = self.reconstruction
        ps, ops = R.reconstruct(ps)
        self.number_of_Moves += ops
        if original_mother:
            ps.mother = original_mother

        return ps
