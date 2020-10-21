from support import set_logging, log, show_primitive_constituents, report_tail_head_problem
from lexical_interface import LexicalInterface
from LF import LF
from morphology import Morphology
from transfer import Transfer
from surface_conditions import SurfaceConditions
from adjunct_constructor import AdjunctConstructor
from log_functions import log_results
from time import process_time
from plausibility_metrics import PlausibilityMetrics

class LinearPhaseParser:
    def __init__(self, local_file_system, language=''):
        self.sentence = ''
        self.external_sources = local_file_system.external_sources
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
        self.plausibility_metrics = PlausibilityMetrics(self)
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

    def parse(self, count, lst):
        self.sentence = lst
        self.start_time = process_time()
        self.initialize()
        set_logging(True)
        log('\n-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------')
        log(f'\n{count}. {self.sentence}')
        log(f'\n\n\t 1. {self.sentence}\n')
        self.parse_new_item(None, lst, 0)

    def parse_new_item(self, ps, lst, index):
        set_logging(True)
        # Force the parser to exit by setting this flag in the code
        if self.exit:
            return

        if index < len(lst):
            log(f'\n\t\tNext item: "{lst[index]}". ')

        if index == len(lst):               # No more words in the input
            self.complete_processing(ps)    # Finalizes the output
            return                          # Completes the parsing branch

        log('Morphological processing...')

        # Try all lexical elements (if ambiguous)
        for lexical_constituent in self.lexicon.lexical_retrieval(lst[index]):
            terminal_lexical_item, lst_branched, inflection = self.morphology.morphological_parse(lexical_constituent, lst.copy(), index)
            terminal_lexical_item = self.process_inflection(inflection, terminal_lexical_item)
            log('Done.')
            if inflection:
                if ps:
                    self.parse_new_item(ps.copy(), lst_branched, index + 1)
                else:
                    self.parse_new_item(None, lst_branched, index + 1)
            else:
                self.consume_resources("Items from input")
                log('\n')
                if not ps:
                    self.parse_new_item(terminal_lexical_item.copy(), lst_branched, index + 1)
                else:
                    log(f'\n\t{self.resources["Items from input"]}. Consume \"' + terminal_lexical_item.get_phonological_string() + '\": ')
                    log(ps.illustrate() + ' + ' + terminal_lexical_item.get_phonological_string())
                    # -------------------------- consider merge solutions ------------------------------------- #
                    merge_sites = self.plausibility_metrics.rank_solutions(ps, terminal_lexical_item)
                    for site in merge_sites:
                        self.consume_resources("Merge")
                        ps_ = ps.top().copy()
                        left_branch_site_ = ps_.identify_equivalent_node(site)
                        if left_branch_site_.bottom_affix().internal:
                            new_ps = left_branch_site_.sink(terminal_lexical_item)
                        else:
                            log(f'\t\t\tNow exploring solution [{left_branch_site_} {terminal_lexical_item.get_phonological_string()}]...')
                            log('Transferring left branch...')
                            set_logging(False)
                            new_ps = self.transfer_to_LF(left_branch_site_) + terminal_lexical_item
                            set_logging(True)
                            log(f'Result: {new_ps}...Done.\n')
                        self.parse_new_item(new_ps, lst_branched, index + 1)
                        if self.exit:
                            break
                    # ---------------------------------------------------------------------------------------- #
        # If all solutions in the list have been explored,  backtrack
        if not self.exit:
            log('\n\tBacktracking to previous branching point...')

    def process_inflection(self, inflection, lexical_item):
        if inflection:
            self.memory_buffer_inflectional_affixes = self.memory_buffer_inflectional_affixes.union(inflection)
            self.consume_resources("Inflection")
            log(f'Added feature {inflection} into temporary feature working memory...')
        else:
            if self.memory_buffer_inflectional_affixes:
                log(f'{lexical_item.get_phonological_string()} is coming next...')
                log(f'Adding inflectional features {sorted(self.memory_buffer_inflectional_affixes)} to ' + lexical_item.get_phonological_string() + '...')
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
            log('Failure.\n')
            return
        log('\t\tTransferring to LF...')
        ps_ = self.transfer_to_LF(ps)
        log('\t\tDone.\n')
        log('\t\tLF-legibility check...')
        if self.LF_condition_violation(ps_) or self.interpret_semantically(ps_):
            self.add_garden_path()
            log('\t\tLF-legibility test failed.\n')
            log('\t\tMemory dump:\n')
            log(show_primitive_constituents(ps))
            log('\n')
            return
        log('Done.\n')
        log('\t\tSolution was accepted!\n')
        self.first_solution_found = True
        self.execution_time_results.append(int((process_time() - self.start_time) * 1000))
        self.report_solution(ps_, spellout_structure)

    def add_garden_path(self):
        if not self.first_solution_found:
            self.consume_resources("Garden Paths")

    def preparations(self, ps):
        log('\t------------------------------------------------------------------------------------------------------------------------------------------------\n')
        log(f'\tTrying spellout structure  ' + ps.illustrate() + '\n')

    def report_solution(self, ps, spellout_structure):
        self.result_list.append([ps, self.semantic_interpretation])
        self.spellout_result_list.append(spellout_structure)
        log(f'\t\tSemantic interpretation: {self.semantic_interpretation}')
        log_results(ps, self.sentence)
        self.first_solution_found = True

    def surface_condition_violation(self, ps):
        log('\t\tChecking surface conditions...')
        S = self.surface_conditions_module
        if not S.reconstruct(ps):
            log(f'Surface condition failure...Done')
            return True
        log('Done.\n')

    def LF_condition_violation(self, ps):
        self.LF.reset_flags()
        log(f'Checking LF-interface conditions...')
        lf = self.LF.test(ps)
        if not lf.final_tail_check(ps):
            report_tail_head_problem(ps)
            return True
        if not lf.all_pass():
            lf.report_lf_status()
            return True

    def interpret_semantically(self, ps):
        def detached(ps):
            ps.mother = None
            return ps
        self.semantic_interpretation = self.LF.transfer_to_CI(detached(ps.copy()))
        if not self.semantic_interpretation:
            log('\t\t\tThe sentence cannot be interpreted at LF.')
            return True

    def transfer_to_LF(self, ps, log_embedding=3):
        original_mother = ps.mother
        ps.detach()
        if self.check_transfer_presuppositions(ps):
            ps = self.transfer.transfer(ps, log_embedding)
        else:
            log(f'Transfer of {ps} terminated due to input condition violation...')
        if original_mother:
            ps.mother = original_mother
        return ps

    def check_transfer_presuppositions(self, ps):
        if 'FIN' in ps.head().features or 'INF' in ps.head().features:
            if not self.surface_conditions_module.reconstruct(ps):
                return False
        return True

    def consume_resources(self, key):
        if key in self.resources and not self.first_solution_found:
            self.resources[key] += 1

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