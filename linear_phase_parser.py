from support import set_logging, log, show_primitive_constituents, report_tail_head_problem, show_all_vectors
from lexical_interface import LexicalInterface
from LF import LF
from operator import itemgetter
from morphology import Morphology
from transfer import Transfer
from surface_conditions import SurfaceConditions
from adjunct_constructor import AdjunctConstructor
from log_functions import log_results
from time import process_time

class LinearPhaseParser:
    def __init__(self, external_source, language=''):
        self.sentence = ''
        self.external_source = external_source
        self.language = language                                # Contextual variables (language etc.)
        self.result_list = []                                   # Results (final analyses)
        self.spellout_result_list = []                          # Results (spellout structures)
        self.semantic_interpretation = set()                    # Semantic interpretation
        self.number_of_ambiguities = 0                          # Number of lexical ambiguities detected
        self.result_matrix = [[] for i in range(50)]            # Result matrix
        self.execution_time_results = []                        # Execution time
        self.memory_buffer_inflectional_affixes = set()         # Local memory buffer for inflectional affixes
        self.syntactic_working_memory = []                      # Syntactic working memory
        self.name_provider_index = 0                            # Used to name chains for output purposes
        self.first_solution_found = False                       # Registers when the first solution if found
        self.exit = False                                       # Forced exit tag
        self.name_provider_index = 0                            # Index for name provider, for chain identification
        self.lexicon = LexicalInterface(self)                   # Access to the lexicon
        self.lexicon.load_lexicon(self)                         # Load the language/dialect specific lexicon
        self.morphology = Morphology(self)                      # Access to morphology
        self.transfer = Transfer(self)                          # Access to transfer
        self.LF = LF(self)                                      # Access to LF
        self.surface_conditions_module = SurfaceConditions()    # Surface conditions
        self.surface_conditions_pass = True                     # Surface conditions
        self.adjunct_constructor = AdjunctConstructor(self)     # Adjunct constructor
        self.score = 0                                          # Discourse score
        self.resources = dict                                   # Resources consumed
        self.start_time = 0                                     # Calculates execution time
        self.end_time = 0                                       # Calculates execution time
        self.number_of_items_consumed = 0
        self.grammaticality_judgement = []

    # Definition for parser initialization
    def initialize(self):
        self.name_provider_index = 0
        self.number_of_items_consumed = 0
        self.result_list = []  # Results (final analyses)
        self.spellout_result_list = []  # Results (spellout structures)
        self.semantic_interpretation = set()  # Semantic interpretation
        self.number_of_ambiguities = 0  # Number of lexical ambiguities detected
        self.result_matrix = [[] for i in range(50)]  # Result matrix
        self.execution_time_results = []  # Execution time
        self.memory_buffer_inflectional_affixes = set()  # Local memory buffer for inflectional affixes
        self.syntactic_working_memory = []  # Syntactic working memory
        self.first_solution_found = False  # Registers when the first solution if found
        self.exit = False  # Forced exit tag
        self.name_provider_index = 0  # Index for name provider, for chain identification
        self.surface_conditions_pass = True  # Surface conditions
        self.score = 0  # Discourse score
        self.resources = dict  # Resources consumed
        self.start_time = process_time()  # Calculates execution time
        self.grammaticality_judgement = ['', '?', '?', '??', '??', '?*', '?*', '##']
        self.resources = {"Garden Paths": 0,
                          "Merge": 0,
                          "Move Head": 0,
                          "Move Phrase": 0,
                          "A-Move Phrase": 0,
                          "A-bar Move Phrase": 0,
                          "Move Adjunct": 0,
                          "Agree": 0,
                          "Transfer": 0,
                          "Items from input": 0,
                          "Feature Processing": 0,
                          "Extraposition": 0,
                          "Inflection": 0,
                          "Failed Transfer": 0,
                          "LF recovery": 0,
                          "LF test": 0}

    def parse(self, lst):
        self.sentence = lst
        self.start_time = process_time()
        set_logging(True)
        self.initialize()
        self._first_pass_parse(None, lst, 0)

    def _first_pass_parse(self, ps, lst, index):
        set_logging(True)

        # Force the parser to exit by setting this flag in the code
        if self.exit:
            return

        if not self.memory_buffer_inflectional_affixes:
            log(f'\t\t\t={ps}')

        if index == len(lst):               # No more words in the input
            self.complete_processing(ps)    # Finalizes the output
            return                          # Completes the parsing branch

        # Test each lexical item in the case of lexical ambiguity
        for lexical_constituent in self.lexicon.lexical_retrieval(lst[index]):
            m = self.morphology
            lexical_item, lst_branched, inflection = m.morphological_parse(lexical_constituent, lst.copy(), index)
            lexical_item = self.process_inflection(inflection, lexical_item, ps, lst_branched, index)
            self.consume_resources("Items from input")
            if inflection:
                self._first_pass_parse(self.copy(ps), lst_branched, index + 1)
            else:
                if not ps:
                    self._first_pass_parse(lexical_item.copy(), lst_branched, index + 1)
                else:
                    log(f'\n\t{self.resources["Items from input"]}. Consume \"' + lexical_item.get_phonological_string() + '\"\n')
                    log('\t\t' + ps.illustrate() + ' + ' + lexical_item.get_phonological_string())

                    # -------------------------- consider merge solutions ------------------------------------- #
                    adjunction_sites = self.ranking(self.filter(ps, lexical_item), lexical_item)
                    for site in adjunction_sites:
                        self.consume_resources("Merge")
                        ps_ = ps.top().copy()
                        site_ = self.node_at(ps_, self.get_position_on_geometric_right_edge(site))
                        if site_.bottom_affix().internal:
                            new_ps = site_.sink(lexical_item)
                        else:
                            log(f'\t\t\tExploring solution [{site_} {lexical_item.get_phonological_string()}]')
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

    def process_inflection(self, inflection, lexical_item, ps, lst_branched, index):
        if inflection:
            self.memory_buffer_inflectional_affixes = self.memory_buffer_inflectional_affixes.union(inflection)
            self.consume_resources("Inflection")
            log(f'\n\t{self.resources["Items from input"]}. Consume \"' + lst_branched[index + 1] + '\"')
        else:
            if self.memory_buffer_inflectional_affixes:
                log(f'\t\tAdding inflectional features {sorted(self.memory_buffer_inflectional_affixes)} to ' + lexical_item.get_phonological_string())
                lexical_item.features = lexical_item.features | set(self.memory_buffer_inflectional_affixes)
                self.memory_buffer_inflectional_affixes = set()
        return lexical_item

    # Internal function
    def babtize(self):
        self.name_provider_index += 1
        return str(self.name_provider_index)

    def complete_processing(self, ps):
        spellout_structure = ps.copy()
        self.preparations(ps)
        if self.surface_condition_violation(ps):
            self.add_garden_path()
            return
        ps_ = self.transfer_to_lf(ps)
        if self.LF_condition_violation(ps_) or self.transfer_to_CI(ps_):
            self.add_garden_path()
            log('\n' + show_primitive_constituents(ps))
            return
        self.first_solution_found = True
        self.execution_time_results.append(int((process_time() - self.start_time) * 1000))
        self.report_solution(ps_, spellout_structure)

    def add_garden_path(self):
        if not self.first_solution_found:
            self.consume_resources("Garden Paths")

    def preparations(self, ps):
        log('------------------------------------------------------------------------------------------------------------------------------------------------')
        log('\n\t>>>\t' + f'Trying spellout structure  ' + ps.illustrate())

    def report_solution(self, ps, spellout_structure):
        self.result_list.append([ps, self.semantic_interpretation])
        self.spellout_result_list.append(spellout_structure)
        log(f'\t\t\t\tSemantic interpretation/predicates and arguments: {self.semantic_interpretation}')
        log_results(ps, self.sentence)
        self.first_solution_found = True
        # self.exit = True    # Knock this out if you want to see all solutions

    def surface_condition_violation(self, ps):
        log('\t\tChecking surface conditions...')
        S = self.surface_conditions_module
        if not S.reconstruct(ps):
            log(f'\t\t\tSurface condition failure.\n\n')
            return True

    def LF_condition_violation(self, ps):
        self.LF.reset_flags()
        log('\t\tReconstructing...')
        log('\t\t\t= ' + ps.illustrate())
        log(f'\t\tChecking LF-interface conditions...')
        lf = self.LF.test(ps)
        if not lf.final_tail_check(ps):
            report_tail_head_problem(ps)
            return True
        if not lf.all_pass():
            lf.report_lf_status()
            return True

    def filter(self, ps, w):
        log('\t\t\tFiltering out impossible merge sites...')
        adjunction_sites = []
        if ps.bottom().bottom_affix().internal:
            log(f'\t\t\tSink \"{w.get_phonological_string()}\" because it belongs to the same word.')
            return [ps.bottom()]

        #--------------------geometrical minimal search------------------------------
        for N in ps.geometrical_minimal_search():
            if self.does_not_accept_any_complementizers(N):
                log(f'\t\t\t\tReject {N} + {w} because {N} does not accept complementizers.')
                continue
            if N.is_complex() and self.bad_left_branch_test(N, w):
                log(f'\t\t\t\tReject {N} + {w} due to bad left branch.')
                continue
            if self.breaks_words(N, w):
                log(f'\t\t\t\tReject {N} + {w} because it breaks words.')
                continue
            adjunction_sites.append(N)
        #-------------------------------------------------------------------------------
        return adjunction_sites

    def bad_left_branch_test(self, N, w):
        set_logging(False)
        dropped = self.transfer_to_lf(N.copy())
        lf = self.LF.test(dropped)
        set_logging(True)
        if self.left_branch_rejection(lf):
            return True

    def left_branch_rejection(self, lf_test):
        return not (lf_test.probe_goal_test_result and
                lf_test.head_integrity_test_result and
                lf_test.selection_test_result and
                lf_test.wrong_complement_test_result)

    def does_not_accept_any_complementizers(self, N):
        if N.is_primitive() and '-COMP:*' in N.features:
            return True

    def breaks_words(self, N, w):
        if self.is_word_internal(N):
            if not w.is_adjoinable():  # Adjoinable phrases cannot be tested because they might become adjuncts later
                set_logging(True)

    # Definition for the ranking function
    # This function will be implemented differently
    def ranking(self, site_list, w):
        if len(site_list) <= 1:
            return site_list
        log('\t\t\tRanking remaining sites...')
        word_specs = w.convert_features_for_parsing(w.licensed_specifiers())
        word_rare_specs = w.convert_features_for_parsing(w.rare_specs())
        word_not_specs = w.convert_features_for_parsing(w.specifiers_not_licensed())
        word_tail_set = w.get_tail_sets()
        word_pf = w.get_phonological_string()
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

            # Case 2a. positive SPEC solutions
            # Check if there are SPEC-w solutions
            if word_specs & site_features:
                # The higher the number the higher the relative ranking will be
                # This is in part arbitrary and should be considered carefully when aiming for realism
                priority = priority + priority_base + 100 * len(word_specs & site_features)
                log(f'\t\t\t\tPrioritize {site.get_cats_string()} as SPEC,{word_pf}.')
                avoid_set.clear()

            # Case 2b. Negative Spec solutions
            # Check if there are negative SPEC conditions and avoid them
            if not site.is_primitive() and (word_not_specs & site_features):
                # The higher the number the higher the relative ranking will be
                # This is in part arbitrary and should be considered carefully when aiming for realism
                priority = priority + priority_base - 100 * len(word_not_specs & site_features)
                log(f'\t\t\t\tAvoid {site.head().get_cats_string()}P as SPEC, {word_pf}.')
                avoid_set.add(site)
            # Avoid all SPEC solutions if there is [-SPEC:*]
            if '*' in word_not_specs:
                # The higher the number the higher the relative ranking will be
                # This is in part arbitrary and should be considered carefully when aiming for realism
                priority = priority + priority_base - 100
                log(f'\t\t\t\tAvoid {site.head().get_cats_string()}P as SPEC for {word_pf} due to unselective SPEC feature.')
                avoid_set.add(site)
            # Avoid rare SPEC solutions
            if word_rare_specs & site_features:
                # The higher the number the higher the relative ranking will be
                # This is in part arbitrary and should be considered carefully when aiming for realism
                priority = priority + priority_base - 1000
                log(f'\t\t\t\tAvoid {site.head().get_cats_string()}P as SPEC for {word_pf} due to rare SPEC feature.')
                avoid_set.add(site)

            # Case 2c. Check if existing H-Comp-relations would be broken, if yes, avoid them
            # Antecedent condition: site is c-commanded locally (possible selected) by a head H
            if not site.is_primitive() and site.mother and \
                    site.mother.left_const and site.mother.left_const.is_primitive():
                # and if H selects for site
                if site.mother.left_const.licensed_complements() & site.features:
                    if 'ADV' not in w.features: # Adverbs will not break selection because they will be adjuncts
                        # The higher the number the higher the relative ranking will be
                        # This is in part arbitrary and should be considered carefully when aiming for realism
                        priority = priority + priority_base - 100 * len(site.mother.left_const.licensed_complements() & site.features)
                        log(f'\t\t\t\tAvoid [{site}, {w}] because the operation breaks up an existing selectional dependency.')
                        avoid_set.add(site)

            # Case 4. Prioritize/avoid Comp solutions
            # Check if site is primitive (takes a complement)
            if site.is_primitive():
                # Check if the solution violates tailing agreement and if yes, avoid
                # Check that the new constituent has tailing features
                if word_tail_set:
                    test_word = w.copy()
                    site.merge_1(test_word, 'right') # We must merge the constituent in order to see possible violations
                    if not test_word.internal_tail_head_test():
                        priority = priority + priority_base - 50
                        log(f'\t\t\t\tAvoid [{site.get_phonological_string()} {word_pf}] due to local agreement failure.')
                        avoid_set.add(site)
                    test_word.remove()
                # Evaluate Comp selection for all morphemes inside the site
                for m in site.get_affix_list():
                    # Check if H selects w and if yes, prioritize this solution
                    if w.features & m.convert_features_for_parsing(m.licensed_complements()):
                        priority = priority + priority_base + 100
                        log(f'\t\t\t\tPrioritize [{m.get_phonological_string()} {word_pf}] due to complement selection.')
                        avoid_set.clear()
                    # ... if f cannot be merged to the complement, avoid this solution
                    if w.features & m.convert_features_for_parsing(m.complements_not_licensed()):
                        priority = priority + priority_base - 100 * len(w.features & m.convert_features_for_parsing(m.complements_not_licensed()))
                        log(f'\t\t\t\tAvoid [{m.get_phonological_string()} {word_pf}] due to complement selection.')
                        avoid_set.add(site)
                    if not LF.semantic_match(m, w):
                        priority = priority + priority_base - 100
                        log(f'\t\t\t\tAvoid [{site},{w}] solution due to semantic mismatch.')
                        avoid_set.add(site)

            # Case 5. LF-legibility violations
            if not site.is_primitive():
                # Transfer before checking
                set_logging(False)  # "Hypothetical reconstruction" is confusing in the logs
                dropped = self.transfer_to_lf(site.copy())
                set_logging(True)
                # If Transfer results in failures, avoid the solution
                if self.LF_legibility_test(dropped):
                    priority = priority + priority_base - 100
                    log(f'\t\t\t\tAvoid {dropped.illustrate()} as left branch because it constitutes illicit structure.')
                    avoid_set.add(site)

            # Case 6. Word-breaking violations
            # Remove all solutions which would cause phonological words to break apart
            if site.is_primitive() and self.is_word_internal(site):
                if 'ADV' not in w.features:
                    priority = priority + priority_base - 100
                    log(f'\t\t\t\tAvoid {site} because it could break words.')
                    avoid_set.add(site)

            # Case 7. Adverbials select legitimate tail-head configurations
            if 'ADV' in word_labels and word_tail_set:
                # Make copies to test merge
                w_copy = w.copy()
                site.merge_1(w_copy, 'right')

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

            # Case 8. Surface conditions
            adjunction_sites.append((priority, site))

        # Case 8. Phillips anomaly = no positive solution found based on local information available
        if len(avoid_set) == len(adjunction_sites):
            # Search the largest adjoinable and LF-legible attachment site not containing T/fin
            size = 0
            max_site = None
            for priority, site_ in adjunction_sites:
                if site_.is_adjoinable():
                    size_ = site_.size()
                    if size_ > size and not site_.contains_feature('T/fin'):
                        set_logging(False)
                        if self.LF_legibility_test(self.transfer_to_lf(site_.copy())):
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
        self.semantic_interpretation = self.LF.transfer_to_CI(detached(ps.copy()))
        if not self.semantic_interpretation:
            log('\t\t\tThe sentence cannot be interpreted at LF.')
            return True

    # Checks if phrase structure XP cannot be broken off from H-XP because
    # H and X were part of the same word. It is used to prevent right merge to XP
    def is_word_internal(self, XP):
        if XP.mother and XP.sister() and XP.sister().is_primitive() and XP.sister().internal:
            return True
        else:
            return False

    def transfer_to_lf(self, ps, log_embedding=3):
        original_mother = ps.mother
        ps.detach()
        if self.check_transfer_presuppositions(ps):
            ps = self.transfer.transfer(ps, log_embedding)
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

    @staticmethod
    def node_at(h, position):
        ps_ = h.top()
        for pos in range(0, position):
                ps_ = ps_.right_const
        return ps_

    @staticmethod
    def get_position_on_geometric_right_edge(h):
        ps_ = h.top()
        position = 0
        while ps_:
            if ps_ == h:
                return position
            if ps_.right_const:
                position = position + 1
                ps_ = ps_.right_const
            else:
                return None

    def consume_resources(self, key):
        if key in self.resources and not self.first_solution_found:
            self.resources[key] += 1

    # Definition for LF-legibility
    def LF_legibility_test(self, ps):
        def detached(ps):
            ps.mother = None
            return ps
        return self.LF.test(detached(ps.copy())).all_pass()

    def grammaticality_judgment(self):
        if 0 >= self.score >= -6:
            return self.grammaticality_judgement[int(round(abs(self.score), 0))]
        else:
            return '##'
