from support import set_logging, log, show_results, report_LF_problem, report_tail_head_problem, reset_number_of_operations, log_result, illu
from LexicalInterface import LexicalInterface
from LF import LF
from operator import itemgetter
from morphology import Morphology
from agreement_reconstruction import AgreementReconstruction
from transfer import Transfer
from surface_conditions import SurfaceConditions
from adjunct_constructor import AdjunctConstructor

class LinearPhaseParser:
    def __init__(self, sentence_context):

        # Contextual variables (language etc.)
        self.sentence_context = sentence_context

        # All results (final analyses)
        self.result_list = []

        # All results (spellout structures)
        self.spellout_result_list = []

        # Semantic interpretation
        self.semantic_interpretation = set()

        # Number of lexical ambiguities detected
        self.number_of_ambiguities = 0

        # Support function
        self.result_matrix = [[] for i in range(50)]

        # Local memory buffer for inflectional affixes
        self.memory_buffer_inflectional_affixes = set()

        # Syntactic working memory
        self.syntactic_working_memory = []

        # Used to name chains for output purposes
        self.name_provider_index = 0

        # Number of computational operations
        self.number_of_Merge = 0
        self.number_of_head_Move = 0
        self.number_of_phrasal_Move = 0
        self.number_of_floating_Move = 0
        self.number_of_Transfer = 0
        self.number_of_solutions_tried = 0
        self.number_of_inflectional_features_processed = 0
        self.number_of_items_consumed = 0
        self.discourse_plausibility = 0
        self.score = 0

        # Registers when the first solution if found
        # The first solution is the one corresponding to what a hearer would select under canonical circumstances
        self.first_solution_found = False

        # Stops parsing when the first solution is available
        self.exit = False

        # Index for name provider, for chain identification
        self.name_provider_index = 0

        # Access to the lexicon
        self.lexicon = LexicalInterface(self)

        # Load the language/dialect specific lexicon
        self.lexicon.load_lexicon(self)

        # Access to morphology
        self.morphology = Morphology(self)

        # Access to transfer (to LF)
        # This provides transfer to LF functionality
        self.transfer = Transfer(self)

        # Surface conditions
        self.surface_conditions_module = SurfaceConditions()
        self.surface_conditions_pass = True

        self.adjunct_constructor = AdjunctConstructor(self)

    def parse(self, lst):
        set_logging(True)
        self.result_list = []
        self.spellout_result_list = []
        self.semantic_interpretation = set()
        self.number_of_ambiguities = 0
        self.result_matrix = [[] for i in range(50)]
        self.memory_buffer_inflectional_affixes = set()
        self.number_of_Merge = 0
        self.number_of_head_Move = 0
        self.number_of_phrasal_Move = 0
        self.number_of_floating_Move = 0
        self.number_of_Transfer = 0
        self.number_of_solutions_tried = 0
        self.number_of_inflectional_features_processed = 0
        self.number_of_items_consumed = 0
        self.discourse_plausibility = 0
        self.score = 0
        self.first_solution_found = False
        self.exit = False
        self.name_provider_index = 0
        self.surface_conditions_pass = True

        self._first_pass_parse(None, lst, 0)

    def _first_pass_parse(self, ps, lst, index):
        if self.exit:
            return
        set_logging(True)
        if not self.memory_buffer_inflectional_affixes:
            log(f'\t\t\t={ps}')

        if index == len(lst):               # No more words in the input
            self.complete_processing(ps)    # Finalizes the output, LF-legibility
            return                          # Complete this parsing branch
        else:
            for lexical_constituent in self.lexicon.lexical_retrieval(lst[index]):  # Branch for lexical ambiguity
                m = self.morphology
                lexical_item, lst_branched, inflection = m.decompose(lexical_constituent, lst.copy(), index)    # Morphological decomposition
                lexical_item = self.process_inflection(inflection, lexical_item, ps, lst_branched, index)       # Process inflection (if any)
                self.number_of_items_consumed += 1
                if inflection:
                    self._first_pass_parse(self.copy(ps), lst_branched, index + 1)
                else:
                    if not ps:
                        self._first_pass_parse(lexical_item.copy(), lst_branched, index + 1)
                    else:
                        log(f'\n\t{self.number_of_items_consumed}. Consume \"' + lexical_item.get_pf() + '\"\n')
                        log('\t\t' + ps.illustrate() + ' + ' + lexical_item.get_pf())

                        # ----------------------- consider merge solutions --------------------------------------- #
                        adjunction_sites = self.ranking(self.filter(ps, lexical_item), lexical_item)
                        for site in adjunction_sites:
                            self.number_of_Merge = self.number_of_Merge + 1
                            ps_ = ps.top().copy()
                            site_ = ps_.node_at(site.get_position_on_geometric_right_edge())

                            if site_.get_bottom_affix().internal:
                                new_ps = site_.sink(lexical_item)
                            else:
                                log(f'\t\t\tExploring solution [{site_} {lexical_item.get_pf()}]')
                                new_ps = self.transfer_to_lf(site_) + lexical_item
                            self._first_pass_parse(new_ps, lst_branched, index + 1)
                            if self.exit:
                                break
                        # ---------------------------------------------------------------------------------------- #

            # If all solutions in the list have been explored,  backtrack
            if not self.exit:
                log('\t\nBacktracking...\n')
            return

    def copy(self, ps):
        if ps:
            return ps.copy()
        else:
            return None

    def process_inflection(self, inflection, lexical_item, ps, lst_branched, index):
        if inflection:
            self.memory_buffer_inflectional_affixes = self.memory_buffer_inflectional_affixes.union(inflection)
            self.number_of_inflectional_features_processed = self.number_of_inflectional_features_processed + 1
            log(f'\n\t{self.number_of_items_consumed}. Consume \"' + lst_branched[index + 1] + '\"')
        else:
            if self.memory_buffer_inflectional_affixes:
                log(f'\t\tAdding inflectional features {self.memory_buffer_inflectional_affixes} to ' + lexical_item.get_pf())
                lexical_item.features = lexical_item.features | set(self.memory_buffer_inflectional_affixes)
                self.memory_buffer_inflectional_affixes = set()

        return lexical_item

    # Internal function
    def babtize(self):
        self.name_provider_index += 1
        return str(self.name_provider_index)

    def complete_processing(self, ps):
        spellout_structure = ps.copy()
        if not self.first_solution_found:
            self.number_of_solutions_tried = self.number_of_solutions_tried + 1
        log('\n\t>>>\t' + f'Trying spellout structure ' + ps.illustrate())
        log('\t\tChecking surface conditions...')

        # SURFACE CONDITIONS
        S = self.surface_conditions_module
        if not S.reconstruct(ps):
            log(f'\t\t\tSurface condition failure.\n\n')
        else:

            # FINAL TRANSFER
            log('\t\tReconstructing...')
            ps_ = self.transfer_to_lf(ps)
            log('\t\t\t= ' + ps_.illustrate())

            # LF-LEGIBILITY
            log(f'\t\tChecking LF-interface conditions...')
            lf = ps_.LF_legibility_test()
            if not lf.all_pass():
                report_LF_problem(ps_)
            else:
                self.semantic_interpretation = self.transfer_to_CI(ps_)

                # FINAL TAIL-HEAD CHECK
                if not lf.final_tail_check(ps_):
                    report_tail_head_problem(ps_)
                else:
                    if not self.semantic_interpretation:
                        log('\t\t\tThe sentence cannot be interpreted at LF.')
                    else:
                        self.result_list.append([ps_, self.semantic_interpretation])
                        self.spellout_result_list.append(spellout_structure)
                        log(f'\t\t\t\tSemantic interpretation/predicates and arguments: {self.semantic_interpretation}')
                        show_results(ps_, self.result_list, self.semantic_interpretation)
                        self.first_solution_found = True
                        # self.exit = True    # Knock this out if you want to see all solutions

    def filter(self, ps, w):
        log('\t\t\tFiltering out impossible merge sites...')
        adjunction_sites = []
        N = ps

        if ps.bottom().get_bottom_affix().internal:
            log(f'\t\t\tSink \"{w.get_pf()}\" because it belongs to the same word.')
            return [ps.bottom()]

        while N:
            reject = False
            if self.does_not_accept_any_complementizers(N):
                log(f'\t\t\t\tReject {N} + {w} because {N} does not accept complementizers.')
                reject = True
            elif N.is_complex() and self.bad_left_branch(N, w):
                log(f'\t\t\t\tReject {N} + {w} due to bad left branch.')
                reject = True
            elif self.breaks_words(N, w):
                log(f'\t\t\t\tReject {N} + {w} because it breaks words.')
                reject = True
            if not reject:
                adjunction_sites.append(N)
            N = N.walk_downstream_geometrically()
        return adjunction_sites

    def bad_left_branch(self, N, w):
        # set_logging(False)
        dropped = self.transfer_to_lf(N.copy())
        lf_test = dropped.LF_legibility_test()
        set_logging(True)
        if lf_test.fail() and not (
                w.is_adjoinable() and
                lf_test.probe_goal_test_result and
                lf_test.head_integrity_test_result and
                lf_test.criterial_feature_test_result):
            return True

    def does_not_accept_any_complementizers(self, N):
        if N.is_primitive() and '-COMP:*' in N.features:
            return True

    def breaks_words(self, N, w):
        if self.is_word_internal(N):
            if not w.is_adjoinable():  # Adjoinable phrases cannot be tested because they might become adjuncts later
                set_logging(True)

    # Definition for the ranking function
    def ranking(self, site_list, w):
        # If there is only one possible site, no ranking is required
        if len(site_list) == 1:
            return site_list

        log('\t\t\tRanking remaining sites...')

        # This are elements that are required several times and created only once
        word_specs = w.for_parsing(w.specs())
        word_rare_specs = w.for_parsing(w.get_rare_specs())
        word_not_specs = w.for_parsing(w.get_not_specs())
        word_tail_set = w.get_tail_sets()
        word_pf = w.get_pf()
        word_labels = w.features

        adjunction_sites = []
        avoid_set = set()

        # Loop through the possible merge sites
        for i, site in enumerate(site_list, start=1):

            # This determines how to order constituents with the same ranking
            # This method prioritizes lower sites (e.g., top node scores 0 bonus)
            priority_base = i
            priority = priority_base

            site_features = site.head().features

            #
            # Case 2a. positive SPEC solutions
            #
            # Check if there are SPEC-w solutions
            # Get all positive SPEC solutions from w
            if word_specs & site_features:
                # The higher the number the higher the relative ranking will be
                # This is in part arbitrary and should be considered carefully when aiming for realism
                priority = priority + priority_base + 100 * len(word_specs & site_features)
                log(f'\t\t\t\tPrioritize {site.get_cats_string()} as SPEC,{word_pf}.')
                avoid_set.clear()

            #
            # Case 2b. Negative Spec solutions
            #
            # Check if there are negative SPEC conditions and avoid them
            # Get negative -SPEC features from w
            if not site.is_primitive() and (word_not_specs & site_features):
                # The higher the number the higher the relative ranking will be
                # This is in part arbitrary and should be considered carefully when aiming for realism
                priority = priority + priority_base - 100 * len(word_not_specs & site_features)
                log(f'\t\t\t\tAvoid {site.head().get_cats_string()}P as SPEC, {word_pf}.')
                avoid_set.add(site)

            #
            # Avoid all SPEC solutions if there is [-SPEC:*]
            #
            if '*' in word_not_specs:
                # The higher the number the higher the relative ranking will be
                # This is in part arbitrary and should be considered carefully when aiming for realism
                priority = priority + priority_base - 100
                log(f'\t\t\t\tAvoid {site.head().get_cats_string()}P as SPEC for {word_pf} due to unselective SPEC feature.')
                avoid_set.add(site)

            #
            # Avoid rare SPEC solutions
            #
            if word_rare_specs & site_features:
                # The higher the number the higher the relative ranking will be
                # This is in part arbitrary and should be considered carefully when aiming for realism
                priority = priority + priority_base - 1000
                log(f'\t\t\t\tAvoid {site.head().get_cats_string()}P as SPEC for {word_pf} due to rare SPEC feature.')
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
                if site.mother.left_const.get_comps() & site.features:
                    if 'ADV' not in w.features: # Adverbs will not break selection because they will be adjuncts
                        # The higher the number the higher the relative ranking will be
                        # This is in part arbitrary and should be considered carefully when aiming for realism
                        priority = priority + priority_base - 100 * len(site.mother.left_const.get_comps() & site.features)
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
                    if w.features & m.for_parsing(m.get_comps()):
                        priority = priority + priority_base + 100
                        log(f'\t\t\t\tPrioritize [{m.get_pf()} {word_pf}] due to complement selection.')
                        avoid_set.clear()

                    # ... if f cannot be merged to the complement, avoid this solution
                    if w.features & m.for_parsing(m.get_not_comps()):
                        priority = priority + priority_base - 100 * len(w.features & m.for_parsing(m.get_not_comps()))
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
                if 'ADV' not in w.features:
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
                if 'T/fin' in str(w_copy.feature_vector()):
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
                    size_ = site_.size()
                    if size_ > size and not site_.contains_feature('T/fin'):
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
        return lf.transfer_to_CI(detached(ps.copy()))

    # Checks if phrase structure XP cannot be broken off from H-XP because
    # H and X were part of the same word. It is used to prevent right merge to XP
    def is_word_internal(self, XP):
        if XP.mother and XP.sister() and XP.sister().is_primitive() and XP.sister().is_word_internal():
            return True
        else:
            return False

    # Error correction procedure
    def transfer_to_lf(self, ps, log_embedding=3):

        # Detach the constituent for transfer
        original_mother = ps.mother
        ps.detach()

        # Check preconditions (surface conditions in the current version) and then initiate transfer
        if self.check_transfer_presuppositions(ps):

            # Keep record of the number of Transfer operations
            self.number_of_Transfer = self.number_of_Transfer + 1

            # Perform transfer
            T = self.transfer
            ps = T.transfer(ps, log_embedding)
        else:
            log(f'\t\t\t\tTransfer of {ps} terminated due to input condition violation.')

        if original_mother:
            ps.mother = original_mother

        return ps

    def check_transfer_presuppositions(self, ps):
        if 'FIN' in ps.head().features or 'INF' in ps.head().features:
            if not self.surface_conditions_module.reconstruct(ps):
                return False

        return True
