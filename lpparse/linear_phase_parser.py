from support import set_logging, log, show_primitive_constituents
from lexical_interface import LexicalInterface
from LF import LF
from morphology import Morphology
from transfer import Transfer
from narrow_semantics import NarrowSemantics
from surface_conditions import SurfaceConditions
from adjunct_constructor import AdjunctConstructor
from lexical_stream import LexicalStream
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
        self.narrow_semantics = NarrowSemantics(self)           # Narrow sentence-level semantics
        self.lexicon = LexicalInterface(self)                   # Access to the lexicon
        self.lexicon.load_lexicon(self)                         # Load the language/dialect specific lexicon
        self.morphology = Morphology(self)                      # Access to morphology
        self.transfer = Transfer(self)                          # Access to transfer
        self.local_file_system = local_file_system              # Access to local file system
        self.LF = LF(self)                                      # Access to LF
        self.lexical_stream = LexicalStream(self)               # Access to lexical stream
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
        self.operations = 0

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
        self.time_from_stimulus_onset_for_word = []             # Counts predicted cognitive time
        # Reset operation counters in the PhraseStructure class
        for key in PhraseStructure.resources:
            PhraseStructure.resources[key] = {"ms": 1, "n": 0}
        self.operations = 0
        self.resources = {"Total Time": {'ms': 0, 'n': 0},     # Count predicted cognitive time
                          "Garden Paths": {'ms': 0, 'n': 0},
                          "Memory Reactivation": {'ms': 500, 'n' : 0},
                          "Steps": {'ms': 0, 'n': 0},
                          "Merge": {'ms': 5, 'n': 0},
                          "Move Head": {'ms': 5, 'n': 0},
                          "Move Phrase": {'ms': 5, 'n': 0},
                          "A-Move Phrase": {'ms': 5, 'n': 0},
                          "A-bar Move Phrase": {'ms': 5, 'n': 0},
                          "Move Adjunct": {'ms': 5, 'n': 0},
                          "Agree": {'ms': 5, 'n': 0},
                          "Phi": {'ms': 0, 'n': 0},
                          "Transfer": {'ms': 5, 'n': 0},
                          "Item streamed into syntax": {'ms': 5, 'n': 0},
                          "Feature Processing": {'ms': 5, 'n': 0},
                          "Extraposition": {'ms': 5, 'n': 0},
                          "Inflection": {'ms': 5, 'n': 0},
                          "Failed Transfer": {'ms': 5, 'n': 0},
                          "LF recovery": {'ms': 5, 'n': 0},
                          "LF test": {'ms': 5, 'n': 0},
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
        self.plausibility_metrics.initialize()
        self.narrow_semantics.initialize()
        set_logging(True)
        log('\n-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------')
        log(f'\n#{count}. {self.local_file_system.generate_input_sentence_string(lst)}')
        log(f'\n{self.sentence}')
        log(f'\n\n\t 1. {self.sentence}\n')
        self.local_file_system.simple_log_file.write(f'\n\n#{count}. {self.local_file_system.generate_input_sentence_string(lst)} / {self.sentence}\n')
        if not self.local_file_system.instruction_to_ignore_from_test_corpus:
            self.parse_new_item(None, lst, 0)
        else:
            print('\n(Ignored by user.)')
            log('\n(Ignored by user.)')

    def parse_new_item(self, ps, lst, index):

        # CIRCUIT BREAKER
        if self.circuit_breaker(ps, lst, index):
            return

        # LEXICAL AMBIGUITY
        list_of_retrieved_lexical_items_matching_the_phonological_word = self.lexicon.lexical_retrieval(lst[index])
        for lexical_constituent in list_of_retrieved_lexical_items_matching_the_phonological_word:
            log('Lexical retrieval...')
            self.consume_resources('Lexical retrieval', lst[index])

            # MORPHOLOGY
            terminal_lexical_item, lst_branched, inflection = self.morphology.morphological_parse(self, lexical_constituent, lst.copy(), index)

            # LEXICAL ACCESS AND STREAM
            terminal_lexical_item = self.lexical_stream.stream_into_syntax(terminal_lexical_item, lst_branched, inflection, ps, index)

            # SYNTACTIC MODULE
            merge_sites = self.plausibility_metrics.filter_and_rank(ps, terminal_lexical_item)

            # ---------------------------------------------------------------------------------------------#
            # Examine each possible solution
            for site, transfer in merge_sites:
                left_branch = self.target_left_branch(ps, site)
                new_constituent = self.attach(left_branch, site, terminal_lexical_item, transfer)
                self.put_rest_out_of_working_memory(merge_sites)
                self.parse_new_item(new_constituent, lst_branched, index + 1)
                if self.stop_looking_for_further_solutions():
                    break
            # ---------------------------------------------------------------------------------------- #
            print('.', end='', flush=True)
            self.narrow_semantics.pragmatic_pathway.forget_object(terminal_lexical_item)

        if not self.exit:
            log(f'\n\t\tExplored {ps}, backtracking to previous branching point...')

    def stop_looking_for_further_solutions(self):
        if self.exit:
            return True

    def target_left_branch(self, ps, site):
        def identify_equivalent_node(ps, site):
            def node_at(ps, position):
                ps_ = ps.top()
                for pos in range(0, position):
                    ps_ = ps_.right_const
                return ps_
            def get_position_on_geometric_right_edge(node):
                ps_ = node.top()
                position = 0
                while ps_:
                    if ps_ == node:
                        return position
                    if ps_.right_const:
                        position = position + 1
                        ps_ = ps_.right_const
                    else:
                        return None
                return None

            return node_at(ps, get_position_on_geometric_right_edge(site))

        ps_ = ps.top().copy()
        return identify_equivalent_node(ps_, site)

    def attach(self, left_branch, site, terminal_lexical_item, transfer):
        self.maintain_working_memory(site)
        if self.belong_to_same_word(left_branch, site):
            new_constituent = self.sink_into_complex_head(left_branch, terminal_lexical_item)
        else:
            new_constituent = self.attach_into_phrase(left_branch, terminal_lexical_item, transfer)

        if not self.first_solution_found:
            self.time_from_stimulus_onset_for_word.append((terminal_lexical_item, self.time_from_stimulus_onset))

        return new_constituent

    def belong_to_same_word(self, left_branch, site):
        if left_branch.bottom_affix().internal and site.is_primitive():
            return True

    def attach_into_phrase(self, left_branch, terminal_lexical_item, transfer):
        log(f'\n\t\tConsidering [{left_branch} + {terminal_lexical_item.get_phonological_string()}]...')
        log(f'Transferring left branch {left_branch}...')
        self.consume_resources("Merge", f'{terminal_lexical_item}')
        set_logging(False)
        if transfer:
            new_left_branch, output_from_interfaces = self.transfer_to_LF(left_branch)
        else:
            new_left_branch = left_branch

        new_constituent = new_left_branch + terminal_lexical_item
        set_logging(True)
        self.remove_from_syntactic_working_memory(left_branch)
        log(f'Result: {new_constituent}...Done.\n')
        return new_constituent

    def sink_into_complex_head(self, left_branch, terminal_lexical_item):
        log(f'\n\t\tSinking {terminal_lexical_item} into {left_branch.bottom_affix()} = ')
        new_constituent = left_branch.bottom_affix().sink(terminal_lexical_item)
        log(f'{new_constituent.top()}')
        self.consume_resources("Merge", f'{terminal_lexical_item}')
        log('\n')
        return new_constituent

    def maintain_working_memory(self, site):
        # If site is not in active working memory, it must be activated
        if 'working_memory' in self.local_file_system.settings and self.local_file_system.settings['working_memory']:
            if not site.active_in_syntactic_working_memory:
                self.consume_resources("Memory Reactivation", {site})
                log(f'\n\t\tA dormant constituent had to be woken back into syntactic working memory.')
                site.active_in_syntactic_working_memory = True

    def circuit_breaker(self, ps, lst, index):

        set_logging(True)
        # We have decided not to explore any more solutions, exit the recursion
        if self.exit:
            return True

        if index < len(lst):
            log(f'\n\t\tNext item {lst[index]}. ')

        # If there are no more words, we attempt to complete processing
        if index == len(lst):
            self.complete_processing(ps)
            return True

        # Set the amount of cognitive resources (in ms) consumed based on word length
        self.time_from_stimulus_onset = int(len(lst[index]) * 10)

        # Add the time to total time if we haven't yet found any solutions
        if not self.first_solution_found:
            self.resources['Total Time']['n'] += self.time_from_stimulus_onset

        return False

    def put_rest_out_of_working_memory(self, merge_sites):
        for site, transfer in merge_sites:
            site.active_in_syntactic_working_memory = False

    def babtize(self):
        self.name_provider_index += 1
        return str(self.name_provider_index)

    def complete_processing(self, ps):
        spellout_structure = ps.copy()
        self.preparations(ps)  # Currently just for logging purposes
        if self.surface_condition_violation(ps):
            self.add_garden_path()
            log('Failure.\n')
            return
        log('\t\tTransferring to LF...')
        ps_, self.narrow_semantics.access_interface = self.transfer_to_LF(ps)
        log('\t\tDone.\n')
        log('\t\tLF-legibility check...')
        if self.LF_condition_violation(ps_) or self.narrow_semantics.postsyntactic_semantic_interpretation(ps_):
            self.add_garden_path()
            log('\n\t\tLF-legibility test failed.\n')
            log('\t\tMemory dump:\n')
            log(show_primitive_constituents(ps_))
            self.narrow_semantics.reset_for_new_interpretation()
            return
        self.consume_resources('Steps')
        log('Done.\n')
        print('X', end='', flush=True)
        self.local_file_system.simple_log_file.write(f'\n{self.resources["Steps"]["n"]}\t{ps_} <= accepted')
        if len(self.narrow_semantics.semantic_interpretation['Assignments']) == 0:
            log('\t\t!! Sentence was judged uninterpretable due to lack of legitimate assignments.\n')
        if not self.first_solution_found:
            log(f'\t\tSolution was accepted at {self.resources["Total Time"]["n"]}ms stimulus onset.\n')
            self.resources['Mean time per word']['n'] = int(self.resources['Total Time']['n'] / self.count_words(self.sentence))
            self.resources.update(PhraseStructure.resources) # Add phrase resource consumption from class phrase structure
        if self.only_first_solution:
            self.exit = True
        self.execution_time_results.append(int((process_time() - self.start_time) * 1000))
        self.store_solution(ps_, spellout_structure)
        self.first_solution_found = True

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

    def store_solution(self, ps, spellout_structure):
        self.result_list.append([ps, self.narrow_semantics.semantic_interpretation])
        self.spellout_result_list.append(spellout_structure)
        if not self.first_solution_found:
            log(f'\n\tSemantic interpretation:\n{self.local_file_system.formatted_semantics_output(self.narrow_semantics.semantic_interpretation, self)}')
        ps.tidy_names(1)
        log('\n\n')
        log('\t\tLexical features:\n')
        log(show_primitive_constituents(ps))
        if not self.first_solution_found:
            log('\n\t\tSemantic bookkeeping:')
            log(f'\t\t{self.local_file_system.format_semantic_interpretation(self)}\n')
            log('\t\t-------------------------------------------------------------------------------------------------------------------------------------------------------------------\n')
        log('\n\tChecking if the sentence is ambiguous...\n')
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
        lf = self.LF.LF_legibility_test(ps)
        if not lf.final_tail_check(ps):
            return True
        if not lf.all_pass():
            lf.report_lf_status()
            return True

    def transfer_to_LF(self, ps, log_embedding=3):
        original_mother = ps.mother
        ps.detach()
        output_from_interfaces = {}
        if self.check_transfer_presuppositions(ps):
            ps, output_from_interfaces = self.transfer.transfer(ps, log_embedding)
        else:
            log(f'Transfer of {ps} terminated due to input condition violation...')
        if original_mother:
            ps.mother = original_mother
        return ps, output_from_interfaces

    def remove_from_syntactic_working_memory(self, ps):
        ps.active_in_syntactic_working_memory = False
        if ps.mother and ps.contains_feature('T/fin') and ps.contains_feature('OP:REL'): # Remove also container if transferred phrase is finite
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
        self.operations += 1
        if key in self.resources and not self.first_solution_found:
            self.time_from_stimulus_onset += self.resources[key]['ms']
            if 'Total Time' in self.resources:
                self.resources['Total Time']['n'] += self.resources[key]['ms']
            self.resources[key]['n'] += 1
            if self.local_file_system.settings['datatake_resource_sequence']:
                self.local_file_system.resource_sequence_file.write(f'{key}({info}),{self.time_from_stimulus_onset},  ')

    def LF_legibility_test(self, ps):
        def detached(ps):
            ps.mother = None
            return ps
        return self.LF.LF_legibility_test(detached(ps.copy())).all_pass()