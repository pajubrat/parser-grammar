from support import set_logging, log, show_primitive_constituents
from lexical_interface import LexicalInterface
from LF import LF
from morphology import Morphology
from transfer import Transfer
from surface_conditions import SurfaceConditions
from adjunct_constructor import AdjunctConstructor
from log_functions import log_results
from time import process_time
from plausibility_metrics import PlausibilityMetrics
from phrase_structure import PhraseStructure

class LinearPhaseParser:
    def __init__(self, local_file_system, language=''):
        self.sentence = ''
        self.local_file_system = local_file_system              # Access to file system (e.g., lexicon, settings)
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
        self.local_file_system = local_file_system              # Access to local file system
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
        self.time_from_stimulus_onset = 0
        self.total_time_per_sentence = 0
        self.time_from_stimulus_onset_for_word = []
        self.only_first_solution = False

    # Definition for parser initialization
    def initialize(self):
        if 'only_first_solution' in self.local_file_system.settings:
            if self.local_file_system.settings['only_first_solution']:
                self.only_first_solution = True
        self.name_provider_index = 0
        self.number_of_items_consumed = 0
        self.result_list = []                                   # Results (final analyses)
        self.spellout_result_list = []                          # Results (spellout structures)
        self.semantic_interpretation = set()                    # Semantic interpretation
        self.number_of_ambiguities = 0                          # Number of lexical ambiguities detected
        self.result_matrix = [[] for i in range(50)]            # Result matrix
        self.execution_time_results = []                        # Execution time
        self.memory_buffer_inflectional_affixes = set()         # Local memory buffer for inflectional affixes
        self.syntactic_working_memory = []                      # Syntactic working memory
        self.first_solution_found = False                       # Registers when the first solution if found
        self.exit = False                                       # Forced exit tag
        self.name_provider_index = 0                            # Index for name provider, for chain identification
        self.surface_conditions_pass = True                     # Surface conditions
        self.score = 0                                          # Discourse score
        self.resources = dict                                   # Resources consumed
        self.start_time = process_time()                        # Calculates execution time
        self.grammaticality_judgement = ['', '?', '?', '??', '??', '?*', '?*', '##']
        self.time_from_stimulus_onset = 0                       # Counts predicted cognitive time
        self.total_time_per_sentence = 0                        # Counts predicted cognitive time
        self.time_from_stimulus_onset_for_word = []             # Count predicted cognitive time
        # Reset operation counters in the PhraseStructure class
        for key in PhraseStructure.resources:
            PhraseStructure.resources[key] = {"ms": 1, "n": 0}
        self.resources = {"Total Time": {'ms': 0, 'n': 0},     # Count predicted cognitive time
                          "Garden Paths": {'ms': 1, 'n': 0},
                          "Memory Reactivation": {'ms': 500, 'n' : 0},
                          "Steps": {'ms': 0, 'n': 0},
                          "Merge": {'ms': 5, 'n': 0},
                          "Move Head": {'ms': 5, 'n': 0},
                          "Move Phrase": {'ms': 0, 'n': 0},
                          "A-Move Phrase": {'ms': 5, 'n': 0},
                          "A-bar Move Phrase": {'ms': 5, 'n': 0},
                          "Move Adjunct": {'ms': 15, 'n': 0},
                          "Agree": {'ms': 5, 'n': 0},
                          "Phi": {'ms': 5, 'n': 0},
                          "Transfer": {'ms': 5, 'n': 0},
                          "Item streamed into syntax": {'ms': 5, 'n': 0},
                          "Feature Processing": {'ms': 5, 'n': 0},
                          "Extraposition": {'ms': 15, 'n': 0},
                          "Inflection": {'ms': 5, 'n': 0},
                          "Failed Transfer": {'ms': 15, 'n': 0},
                          "LF recovery": {'ms': 15, 'n': 0},
                          "LF test": {'ms': 15, 'n': 0},
                          "Filter solution": {'ms': 5, 'n': 0},
                          "Rank solution": {'ms': 5, 'n': 0},
                          "Lexical retrieval": {'ms': 5, 'n': 0},
                          "Morphological decomposition": {'ms': 5, 'n': 0},
                          "Mean time per word": {'ms': 0, 'n': 0}
                          }

    def parse(self, count, lst):
        self.sentence = lst
        self.start_time = process_time()
        self.initialize()
        self.plausibility_metrics.initialize()  # Here we can parametrize plausibility metrics if needed
        set_logging(True)
        log('\n-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------')
        log(f'\n#{count}. {self.sentence}')
        log(f'\n\n\t 1. {self.sentence}\n')
        self.local_file_system.simple_log_file.write(f'\n\n#{count}. {self.sentence}\n')
        self.local_file_system.resource_sequence_file.write(f'\n{count}, {self.local_file_system.generate_input_sentence_string(lst)},  ')
        if not self.local_file_system.instruction_to_ignore_from_test_corpus:
            self.parse_new_item(None, lst, 0)
        else:
            print('\n(Ignored by user.)')
            log('\n(Ignored by user.)')

    def parse_new_item(self, ps, lst, index):
        set_logging(True)
        if self.exit:                                                                                               # Force the parser to exit by setting this flag in the code
            return

        if index < len(lst):
            log(f'\n\t\tNext item: "{lst[index]}". ')

        if index == len(lst):                                                                                        # No more words in the input
            self.complete_processing(ps)                                                                             # Finalizes the output
            return                                                                                                   # Completes the parsing branch

        self.time_from_stimulus_onset = int(len(lst[index]) * 25)                                                    # baseline/mean duration for each item
        if not self.first_solution_found:
            self.resources['Total Time']['n'] += self.time_from_stimulus_onset

        # Try all lexical elements (if ambiguous)
        for lexical_constituent in self.lexicon.lexical_retrieval(lst[index]):
            log('Lexical retrieval...')
            self.consume_resources('Lexical retrieval', lst[index])
            terminal_lexical_item, lst_branched, inflection = self.morphology.morphological_parse(self, lexical_constituent, lst.copy(), index)
            terminal_lexical_item = self.process_inflection(inflection, terminal_lexical_item)
            log('Done.')
            if inflection:
                if ps:
                    self.parse_new_item(ps.copy(), lst_branched, index + 1)
                else:
                    self.parse_new_item(None, lst_branched, index + 1)
            else:
                self.consume_resources("Item streamed into syntax", f'{terminal_lexical_item}')
                log(f'\n\t\tItem enters active working memory.')
                terminal_lexical_item.active_in_syntactic_working_memory = True  # The element enters active working memory
                log('\n')

                if not ps:
                    self.parse_new_item(terminal_lexical_item.copy(), lst_branched, index + 1)
                else:
                    log(f'\n\t{self.resources["Item streamed into syntax"]["n"]}. Consume \"' + terminal_lexical_item.get_phonological_string() + f'\": ')
                    log(f'{ps}' + ' + ' + terminal_lexical_item.get_phonological_string())
                    self.resources['Steps']['n'] += 1
                    self.local_file_system.simple_log_file.write(f'\n{self.resources["Steps"]["n"]}.\t{ps}\n\t{ps} + {terminal_lexical_item.get_phonological_string()}')
                    # -------------------------- consider merge solutions ------------------------------------- #
                    merge_sites = self.plausibility_metrics.filter_and_rank(ps, terminal_lexical_item)
                    for site in merge_sites:
                        ps_ = ps.top().copy()
                        left_branch = ps_.identify_equivalent_node(site)
                        if 'working_memory' in self.local_file_system.settings:
                            if self.local_file_system.settings['working_memory']:
                                if not site.active_in_syntactic_working_memory:
                                    self.consume_resources("Memory Reactivation", {site})
                                    log(f'\n\t\tA dormant constituent had to be woken back into syntactic working memory.')
                                    site.active_in_syntactic_working_memory = True
                        if left_branch.bottom_affix().internal and site.is_primitive():
                            log(f'\n\t\tSinking {terminal_lexical_item} into {left_branch.bottom_affix()} = ')
                            new_constituent = left_branch.bottom_affix().sink(terminal_lexical_item)
                            log(f'{new_constituent.top()}')
                            self.consume_resources("Merge", f'{terminal_lexical_item}')
                        else:
                            log(f'\n\t\tNow exploring solution [{left_branch} + {terminal_lexical_item.get_phonological_string()}]...')
                            log(f'Transferring left branch {left_branch}...')
                            self.consume_resources("Merge", f'{terminal_lexical_item}')
                            set_logging(False)
                            #
                            #
                            # Merge (attachment of new element to existing structure)
                            new_constituent = self.transfer_to_LF(left_branch) + terminal_lexical_item
                            #
                            #
                            #
                            set_logging(True)
                            log(f'Result: {new_constituent}...Done.\n')
                        if not self.first_solution_found:
                            self.time_from_stimulus_onset_for_word.append((terminal_lexical_item, self.time_from_stimulus_onset))
                        self.put_out_of_working_memory(merge_sites)
                        self.parse_new_item(new_constituent, lst_branched, index + 1)
                        if self.exit:
                            break
                    # ---------------------------------------------------------------------------------------- #
                    print('.', end='', flush=True)

        # If all solutions in the list have been explored,  backtrack
        if not self.exit:
            log(f'\n\t\tExplored {ps}, backtracking to previous branching point...')

    def put_out_of_working_memory(self, merge_sites):
        for site in merge_sites:
            site.active_in_syntactic_working_memory = False

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
            log('\n\t\tLF-legibility test failed.\n')
            log('\t\tMemory dump:\n')
            log(show_primitive_constituents(ps))
            return
        log('Done.\n')
        print('X', end='', flush=True)
        self.consume_resources('Steps')
        self.local_file_system.simple_log_file.write(f'\n{self.resources["Steps"]["n"]}\t{ps_}')
        self.local_file_system.simple_log_file.write(f'\n\t-------------------------------')
        if not self.first_solution_found:
            log(f'\t\tSolution was accepted at {self.resources["Total Time"]["n"]}ms stimulus onset.\n')
            self.first_solution_found = True
            self.resources['Mean time per word']['n'] = int(self.resources['Total Time']['n'] / self.count_words(self.sentence))
            self.resources.update(PhraseStructure.resources) # Add phrase resource consumption from class phrase structure
        if self.only_first_solution:
            self.exit = True
        self.execution_time_results.append(int((process_time() - self.start_time) * 1000))
        self.report_solution(ps_, spellout_structure)

    # This is needed because we want to count clitics as words
    def count_words(self, sentence):
        sentence_ = []
        for word in sentence:
            word_ = word.split('=')
            sentence_ = sentence_ + word_
        return len(sentence_)

    def add_garden_path(self):
        if not self.first_solution_found:
            self.consume_resources("Garden Paths")

    def preparations(self, ps):
        log('\n\t------------------------------------------------------------------------------------------------------------------------------------------------\n')
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
        self.remove_from_syntactic_working_memory(ps)
        return ps

    def remove_from_syntactic_working_memory(self, ps):
        ps.active_in_syntactic_working_memory = False
        if ps.mother and (ps.contains_feature('T/fin') or ps.contains_feature('OP:REL')): # Remove also container if transferred phrase is finite
            node = ps
            while node.mother:
                node = node.mother
                node.active_in_syntactic_working_memory = False

    def check_transfer_presuppositions(self, ps):
        if 'FIN' in ps.head().features or 'INF' in ps.head().features:
            if not self.surface_conditions_module.reconstruct(ps):
                return False
        return True

    def consume_resources(self, key, info=''):
        if key in self.resources and not self.first_solution_found:
            self.time_from_stimulus_onset += self.resources[key]['ms']
            if 'Total Time' in self.resources:
                self.resources['Total Time']['n'] += self.resources[key]['ms']
            self.resources[key]['n'] += 1
            log(f'({self.time_from_stimulus_onset}ms) ')
            if self.local_file_system.settings['datatake_resource_sequence']:
                self.local_file_system.resource_sequence_file.write(f'{key}({info}),{self.time_from_stimulus_onset},  ')

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