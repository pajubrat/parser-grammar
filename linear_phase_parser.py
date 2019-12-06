from support import set_logging, log, show_results, report_LF_problem, report_tail_head_problem, reset_number_of_operations, log_result, illu
from LexicalInterface import LexicalInterface
from LF import LF
from operator import itemgetter
from reconstruction import Reconstruction
from morphology import Morphology
from agreement_reconstruction import AgreementReconstruction
from transfer import Transfer
from surface_conditions import SurfaceConditions

# Defines the Linear Phase (LP) parser

class LinearPhaseParser():
    def __init__(self, context):

        # Contextual variables (language etc.)
        self.context = context

        # All results (analyses)
        self.result_list = []

        # Semantic interpretation
        self.semantic_interpretation = set()

        # Number of lexical ambiguities detected
        self.number_of_ambiguities = 0

        # Support function
        self.result_matrix = [[] for i in range(50)]

        # Local memory buffer for inflectional affixes
        self.memory_buffer_inflectional_affixes = set()

        # This counts the number of computational operations (not fully functional in this version)
        self.number_of_Merges = 1
        self.number_of_Moves = 1
        self.number_of_solutions_tried = 0
        self.discourse_plausibility = 0
        self.score = 0

        # Stops parsing when the first solution is available
        self.exit = False

        # Index for name provider, for chain identification
        self.name_provider_index = 0

        # Access to the lexicon
        self.lexicon = LexicalInterface(self.context.redundancy_rules_file)
        self.lexicon.load_lexicon(self.context.lexicon_file, context.language)
        self.lexicon.load_lexicon(self.context.ug_morphemes_file, context.language, combine=True)

        # Access to morphology
        self.morphology = Morphology(self.context)

        # Access to transfer (to LF)
        # This provides transfer to LF functionality
        self.transfer = Transfer(self.context)

        # Surface conditions
        self.surface_conditions_module = SurfaceConditions()
        self.surface_conditions_pass = True

    # This function activates the parser
    # Input is list of words ('lst')
    def parse(self, lst):

        # Reset parser state before beginning a new sentences
        self.result_list = []
        self.memory_buffer_inflectional_affixes = set()
        self.number_of_Merges = 0
        self.number_of_ambiguities = 0
        reset_number_of_operations()
        self.name_provider_index = 0

        set_logging(True)
        self.exit = False

        # ps = current phrase structure
        ps = None

        # Set flags
        self.surface_conditions_pass = True

        # Start parsing
        self._first_pass_parse(ps, lst, 0)

    # Recursive parsing algorithm
    def _first_pass_parse(self, ps, lst, index):

        if self.exit:
            return

        set_logging(True)
        self.number_of_Merges = self.number_of_Merges + 1

        # Print the current state to the log file
        if not self.memory_buffer_inflectional_affixes:
            log(f'\t\t\t={ps}')
            log('\n' + str(self.number_of_Merges) + '.')

        # Test if we have reached at the end of the input list
        if index == len(lst):
            self.number_of_solutions_tried = self.number_of_solutions_tried + 1

            # The whole sentence has been processed, we test if the result is legitimate
            log('\t>>>\t' + f'Trying candidate parse ' + ps.illustrate() + ' ('+str(self.number_of_solutions_tried)+'.)')

            # Check surface conditions and interpretations
            log('\t\tChecking surface conditions...')
            S = self.surface_conditions_module
            S.all_pass = True
            self.surface_conditions_pass = S.reconstruct(ps)

            if self.surface_conditions_pass:

                # We try to transfer it to LF
                log('\t\tReconstructing...')
                ps_ = self.transfer_to_lf(ps)
                log('\t\t\t= ' + ps_.illustrate())
                log(f'\t\tChecking LF-interface conditions.')
                lf = ps_.LF_legibility_test()

                # If the result passes at LF
                if lf.all_pass():
                    self.semantic_interpretation = self.transfer_to_CI(ps_)
                    if lf.final_tail_check(ps_):
                        if self.semantic_interpretation:
                            self.discourse_plausibility = lf.discourse_test_result
                            self.score = 1 - self.number_of_solutions_tried - self.discourse_plausibility

                            # Add the output (phrase structure) to result list
                            self.result_list.append(ps_)
                            log(f'\t\t\t\tSemantic interpretation/predicates and arguments: {self.semantic_interpretation}')
                            show_results(ps_, self.result_list, self.number_of_Merges, self.number_of_Moves, self.number_of_solutions_tried, self.semantic_interpretation)

                            self.exit = True    # Knock this out if you want to see all solutions
                        else:
                            log('\t\t\tThe sentence cannot be interpreted at LF')
                    else:
                        report_tail_head_problem(ps_)
                else:
                    report_LF_problem(ps_)
            else:
                log('\t\t\tSurface condition failure.\n\n')

            return  # This return will send the parser to an unexplored path in the recursive parse tree

        # Process next word
        else:
            # Initialize morphology
            m = self.morphology

            # Lexical ambiguity
            # If the item was not recognized, an ad hoc constituent is returned that has unknown label CAT:X
            disambiguated_word_list = self.lexicon.access_lexicon(lst[index])
            if len(disambiguated_word_list) > 1:
                log(f'\t\tAmbiguous lexical item \"{lst[index]}\" detected.')

            # Explore all possible lexical items
            for lexical_constituent in disambiguated_word_list:
                lst_branched = lst.copy()

                lexical_item = lexical_constituent
                # Morphological decomposition
                # Condition 1. The lexical item is polymorphemic
                # Result: insert the morphemes to the input list, return the first lexical item to be processed
                # Repeat the procedure until the lexical item to be processed does not decompose further
                while m.is_polymorphemic(lexical_item):
                    lexical_item, lst_branched = m.morphological_parse(lexical_constituent,
                                                                       lst_branched,
                                                                       index)

                # Read inflectional features (if any) and store them into memory buffer, then consume next word
                inflection = m.get_inflection(lexical_item)
                if inflection:

                    # Add inflectional features and prosodic features into memory
                    self.memory_buffer_inflectional_affixes = self.memory_buffer_inflectional_affixes.union(inflection)
                    log('\t\tConsume \"' + lst_branched[index + 1] + '\"')
                    if ps:
                        self._first_pass_parse(ps.copy(), lst_branched, index + 1)
                    else:
                        self._first_pass_parse(None, lst_branched, index + 1)

                # If the item was not inflection, it is a morpheme that must be merged
                else:

                    # Unload inflectional suffixes from the memory into the morpheme as features
                    lexical_item = m.set_inflection(lexical_item, self.memory_buffer_inflectional_affixes)
                    self.memory_buffer_inflectional_affixes = set()

                    # If there is no prior phrase structure, we create it by using the first word
                    if not ps:
                        self._first_pass_parse(lexical_item.copy(), lst_branched, index + 1)

                    # ------------------------------------------------------------------------------------
                    # MAIN PARSER LOOP
                    # ------------------------------------------------------------------------------------

                    # Merge the new word (disambiguated lexical item) to the existing phrase structure
                    else:
                        log('\t\tConsume \"' + lexical_item.get_pf() + '\"\n')
                        log('\t\t' + ps.illustrate() + ' + ' + lexical_item.get_pf())

                        # Get the merge sites
                        # Impossible merge sites are first filtered out
                        # Possible merge sites are then ranked
                        adjunction_sites = self.ranking(self.filter(ps, lexical_item), lexical_item)

                        # Test the adjunction sites in the order of ranking
                        for i, site in enumerate(adjunction_sites, start=1):
                            ps_ = ps.get_top().copy()

                            # If the next morpheme was inside the same word as previous, it will be
                            # eaten inside the constituent (will be reconstructed later)
                            if site.get_bottom_affix().internal:
                                log(f'\t\tExploring solution number ({i}) =' + f'[{site}*{lexical_item.get_pf()}]')
                                site_ = ps_[ps.index(site)]
                                new_ps = site_ * lexical_item

                            # If the next morpheme was not inside the same word as previous, it will be merged
                            else:
                                log(f'\t\tExploring solution number ({i}) =' + f'[{site} {lexical_item.get_pf()}]')
                                site_ = self.transfer_to_lf(ps_[ps.index(site)])
                                new_ps = site_ + lexical_item
                            self._first_pass_parse(new_ps, lst_branched, index + 1)
                            if self.exit:
                                break

                    # ------------------------------------------------------------------------------------
                    #
                    # ------------------------------------------------------------------------------------

            # If all solutions in the list have been explored, we backtrack
            if not self.exit:
                # All branches for the incoming surface word have been explored
                log(f'\t\tI have now explored all solutions for \"' + lst[index] + '\".')
                log('\t\tGoing one step backwards and taking another solution from previous ranking list........'
                    '\n\t\t.\n\t\t.\n\t\t.')
            return

    # Filter impossible sites
    def filter(self, ps, w):
        log('\t\t\tFiltering out impossible merge sites...')

        # Filter condition A.
        # Check if the new word must be inside the last word. If yes, we H-Comp solution will be used
        bottom_element = ps.get_bottom().get_bottom_affix()
        if bottom_element.internal:
            log(f'\t\t\tSink \"{w.get_pf()}\" into {bottom_element.get_pf()}'
                ' because they are inside the same phonological word.')
            return [ps.get_bottom()]  # We return the only possible solution

        # Prepare the list of adjunction sites
        adjunction_sites = []

        # Gather all merge nodes at the right edge of the phrase structure ('ps')
        for i, site in enumerate(ps, start=1):

            # Filter condition B.
            # If a primitive site does not accept complementizer, it cannot be a target for Merge
            if site.is_primitive():
                if '-COMP:*' in site.features:
                    log(f'\t\t\t\tReject [{site} {w}] because {site} does not accept complementizers.')
                    continue  # Do not add this site to the list

            # Filter condition C.
            # Check the left branch 'site' in Merge(site, W) for LF-legibility
            if not site.is_primitive():

                #
                # Presupposition. Drop all constituents before check
                #
                set_logging(False)
                dropped = self.transfer_to_lf(site.copy())

                # Test LF-legibility, only inspect tests which cannot be repaired later
                # Take the test
                lf_test = dropped.LF_legibility_test()
                # Condition for filtering
                # Condition 1. The LF-legibility test fails
                # Condition 2. W is not adjoinable
                # Condition 3. probe-goal test, head-integrity test and criterial feature test all failed.
                if lf_test.fail() and not (
                        w.is_adjoinable() and  # This condition because Merge(site, W) may be cancelled if W = adjunct
                        lf_test.probe_goal_test_result and
                        lf_test.head_integrity_test_result and
                        lf_test.criterial_feature_test_result):
                    set_logging(True)
                    log(f'\t\t\t\tReject [{dropped.illustrate()} {w}] due to bad left branch.')
                    continue  # Do not add this site to the list

            set_logging(True)

            # Filter condition D. Word-breaking violations
            # Remove all solutions which would cause phonological words to break apart
            if not site.is_primitive() and self.is_word_internal(site):
                if not w.is_adjoinable(): # Adjoinable phrases cannot be tested because they might become adjuncts later
                    log(f'\t\t\t\tReject [{repr(site)} {w}] as Spec because it breaks words.')
                    continue  # reject this site and start next site

            # Add the site to the list if it was not filtered out by previous conditions A-D.
            adjunction_sites.append(site)

        # Return the list of possible adjunction sites
        return adjunction_sites

    # This function order the adjunction sites in terms of the plausibility and grammatical possibility
    # It only affects efficiency, not grammaticality
    def ranking(self, site_list, w):

        # Gives the size of a phrase structure
        def get_size(ps):
            size_ = 1
            if ps.left_const:
                size_ = size_ + get_size(ps.left_const)
            if ps.right_const:
                size_ = size_ + get_size(ps.right_const)
            return size_

        # --- main function begins here --- #

        # If there is only one possible site, no ranking is required
        if len(site_list) == 1:
            return site_list

        log('\t\t\tRanking remaining sites...')

        # This are elements that are required several times and created only once
        word_specs = w.for_parsing(w.get_specs())
        word_rare_specs = w.for_parsing(w.get_rare_specs())
        word_not_specs = w.for_parsing(w.get_not_specs())
        word_cats = w.get_cats()
        word_tail_set = w.get_tail_sets()
        word_pf = w.get_pf()
        word_labels = w.get_labels()

        adjunction_sites = []
        avoid_set = set()

        # Loop through the possible merge sites
        for i, site in enumerate(site_list, start=1):

            # This determines how to order constituents with the same ranking
            # This method prioritizes lower sites (e.g., top node scores 0 bonus)
            priority_base = i

            priority = 0 + priority_base
            site_cats = site.get_head().get_cats()

            #
            # Case 2a. positive SPEC solutions
            #
            # Check if there are SPEC-w solutions
            # Get all positive SPEC solutions from w
            if word_specs & site_cats:
                # The higher the number the higher the relative ranking will be
                # This is in part arbitrary and should be considered carefully when aiming for realism
                priority = priority + priority_base + 100 * len(word_specs & site_cats)
                log(f'\t\t\t\tPrioritize {site.get_cats_string()} as SPEC,{word_pf}.')
                avoid_set.clear()

            #
            # Case 2b. Negative Spec solutions
            #
            # Check if there are negative SPEC conditions and avoid them
            # Get negative -SPEC features from w
            if not site.is_primitive() and (word_not_specs & site_cats):
                # The higher the number the higher the relative ranking will be
                # This is in part arbitrary and should be considered carefully when aiming for realism
                priority = priority + priority_base - 100 * len(word_not_specs & site_cats)
                log(f'\t\t\t\tAvoid {site.get_head().get_cats_string()}P as SPEC, {word_pf}.')
                avoid_set.add(site)

            #
            # Avoid all SPEC solutions if there is [-SPEC:*]
            #
            if '*' in word_not_specs:
                # The higher the number the higher the relative ranking will be
                # This is in part arbitrary and should be considered carefully when aiming for realism
                priority = priority + priority_base - 100
                log(f'\t\t\t\tAvoid {site.get_head().get_cats_string()}P as SPEC for {word_pf} due to unselective SPEC feature.')
                avoid_set.add(site)

            #
            # Avoid rare SPEC solutions
            #
            if word_rare_specs & site_cats:
                # The higher the number the higher the relative ranking will be
                # This is in part arbitrary and should be considered carefully when aiming for realism
                priority = priority + priority_base - 1000
                log(f'\t\t\t\tAvoid {site.get_head().get_cats_string()}P as SPEC for {word_pf} due to rare SPEC feature.')
                avoid_set.add(site)

            #
            # Case 2c. Check if existing H-Comp-relations would be broken, if yes, avoid them
            #
            # The rule captures that fact that 'H X' often means [H XP]
            # Improves performance 75%
            # Antecedent condition: site is c-commanded locally (possible selected) by a head H
            if not site.is_primitive() and site.mother and \
                    site.mother.left_const and site.mother.left_const.is_primitive():
                # and if H selects for site
                if site.mother.left_const.get_comps() & site.get_labels():
                    if 'ADV' not in w.get_labels(): # Adverbs will not break selection because they will be adjuncts
                        # The higher the number the higher the relative ranking will be
                        # This is in part arbitrary and should be considered carefully when aiming for realism
                        priority = priority + priority_base - 100 * len(site.mother.left_const.get_comps() & site.get_labels())
                        log(f'\t\t\t\tAvoid [{site}, {w}] because the operation breaks up an existing selectional dependency.')
                        avoid_set.add(site)

            #
            # Case 4. Prioritize/avoid Comp solutions
            #
            # Check if site is primitive (takes a complement)
            if site.is_primitive():
                # Check if the solution violates tailing agreement and if yes, avoid
                # Check that the new constituent has tailing features
                if word_tail_set:
                    test_word = w.copy()
                    site.merge(test_word, 'right') # We must merge the constituent in order to see possible violations
                    if not test_word.internal_tail_head_test():
                        priority = priority + priority_base - 50
                        log(f'\t\t\t\tAvoid [{site.get_pf()} {word_pf}] due to local agreement failure.')
                        avoid_set.add(site)
                    test_word.remove()

                # Evaluate Comp selection for all morphemes inside the site
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

            #
            # Case 5. LF-legibility violations
            #
            if not site.is_primitive():

                # Transfer before checking
                set_logging(False)  # "Hypothetical reconstruction" is confusing in the logs
                dropped = self.transfer_to_lf(site.copy())
                set_logging(True)

                # If Transfer results in failures, avoid the solution
                if dropped.LF_legibility_test().fail():
                    priority = priority + priority_base - 100
                    log(f'\t\t\t\tAvoid {dropped.illustrate()} as left branch because it constitutes illicit structure.')
                    avoid_set.add(site)

            #
            # Case 6. Word-breaking violations
            #
            # Remove all solutions which would cause phonological words to break apart
            if site.is_primitive() and self.is_word_internal(site):
                if 'ADV' not in w.get_labels():
                    priority = priority + priority_base - 100
                    log(f'\t\t\t\tAvoid {site} because it could break words.')
                    avoid_set.add(site)

            #
            # Case 7. Adverbials select legitimate tail-head configurations
            #
            if 'ADV' in word_labels and word_tail_set:
                # Make copies to test merge
                w_copy = w.copy()
                site.merge(w_copy, 'right')

                # Adverbial attachment is only tested inside finite tense
                if 'T/fin' in str(w_copy.get_feature_vector()):
                    if not w_copy.external_tail_head_test():
                        priority = priority + priority_base - 100
                        log(f'\t\t\t\tAvoid {site} due to tail-head failure.')
                        avoid_set.add(site)
                    else:
                        priority = priority + priority_base + 200
                        log(f'\t\t\t\tConsidering {site} due to legitimate tail-head configuration.')
                        avoid_set.clear()
                w_copy.remove()

            #
            # Case 8. Surface conditions
            #

            adjunction_sites.append((priority, site))

        #
        # Case 8. Phillips anomaly = no positive solution found based on local information available
        #
        if len(avoid_set) == len(adjunction_sites):

            # Search the largest adjoinable and LF-legible attachment site not containing T/fin
            size = 0
            max_site = None
            for priority, site_ in adjunction_sites:
                if site_.is_adjoinable():
                    size_ = get_size(site_)
                    if size_ > size and not site_.contains_feature('CAT:T/fin'):
                        set_logging(False)
                        if self.transfer_to_lf(site_.copy()).LF_legibility_test().all_pass():
                            max_site = site_
                            max_priority = priority
                            size = size_
                        set_logging(True)

            if max_site:
                log(f'\t\t\t\tPrioritize {max_site} because all solutions were negative.')
                adjunction_sites.remove((max_priority, max_site))
                adjunction_sites.append((max_priority + 200, max_site))

        # Print rankings into the log
        for priority, site in adjunction_sites:
            log(f'\t\t\t\t{site} + {word_pf} = {priority}]')

        # Sort based on priority (highest is prioritized)
        adjunction_sites = sorted(adjunction_sites, key=itemgetter(0))
        adjunction_sites = [site for priority, site in adjunction_sites]

        adjunction_sites.reverse()  # Reverse so that highest will be first

        # Print the completed ranking to the logs
        log(f'\t\tRanking completed:')
        for i, site in enumerate(adjunction_sites, start=1):
            log(f'\t\t\t{i}. [{site}; {word_pf}]')

        # Return the finished list of ranked adjunction sites
        return adjunction_sites

    def transfer_to_CI(self, ps):
        def detached(ps):
            ps.mother = None
            return ps
        lf = LF()
        return(lf.transfer_to_CI(detached(ps.copy())))

    # Checks if phrase structure XP cannot be broken off from H-XP because
    # H and X were part of the same word. It is used to prevent right merge to XP
    def is_word_internal(self, XP):
        if XP.mother and XP.sister() and XP.sister().is_primitive() and XP.sister().is_word_internal():
            return True
        else:
            return False

    # Reverses all movement inside left branches and values phi-features (when unvalued)
    def transfer_to_lf(self, ps):
        original_mother = ps.mother
        ps.detach()
        context = self.context

        T = self.transfer
        ps = T.transfer(ps, context)

        if original_mother:
            ps.mother = original_mother

        return ps
