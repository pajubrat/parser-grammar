from support import set_logging, log, report_failure, report_success, log_new_sentence
from lexical_interface import LexicalInterface
from LF import LF
from morphology import Morphology
from transfer import Transfer
from SEM_narrow_semantics import NarrowSemantics
from adjunct_constructor import AdjunctConstructor
from lexical_stream import LexicalStream
from time import process_time
from plausibility_metrics import PlausibilityMetrics
from phrase_structure import PhraseStructure
from working_memory import SyntacticWorkingMemory


class LinearPhaseParser:
    def __init__(self, local_file_system, language='XX'):
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
        self.first_solution_found = False                       # Registers when the first solution if found
        self.exit = False                                       # Forced exit tag
        self.name_provider_index = 0                            # Index for name provider, for chain identification
        self.narrow_semantics = NarrowSemantics(self)           # Narrow sentence-level semantics
        self.lexicon = LexicalInterface(self)                   # Access to the lexicon
        self.lexicon.load_lexicon(self)                         # Load the language/dialect specific lexicon
        self.morphology = Morphology(self, language)            # Access to morphology
        self.working_memory = SyntacticWorkingMemory(self)      # Access to working memory
        self.transfer = Transfer(self)                          # Access to transfer
        self.LF = LF(self)                                      # Access to LF
        self.lexical_stream = LexicalStream(self)               # Access to lexical stream
        self.adjunct_constructor = AdjunctConstructor(self)     # Adjunct constructor
        self.plausibility_metrics = PlausibilityMetrics(self)
        self.resources = dict                                   # Resources consumed
        self.start_time = 0                                     # Calculates execution time
        self.end_time = 0                                       # Calculates execution time
        self.number_of_items_consumed = 0
        self.time_from_stimulus_onset = 0
        self.total_time_per_sentence = 0
        self.time_from_stimulus_onset_for_word = []
        self.only_first_solution = False

    def initialize(self):
        if 'only_first_solution' in self.local_file_system.settings:
            if self.local_file_system.settings['only_first_solution']:
                self.only_first_solution = True
        self.working_memory.initialize()
        self.number_of_items_consumed = 0
        self.result_list = []                                   # Results (final analyses)
        self.semantic_interpretation = set()                    # Semantic interpretation
        self.number_of_ambiguities = 0                          # Number of lexical ambiguities detected
        self.result_matrix = [[] for i in range(50)]            # Result matrix
        self.execution_time_results = []                        # Execution time
        self.memory_buffer_inflectional_affixes = set()         # Local memory buffer for inflectional affixes
        self.first_solution_found = False                       # Registers when the first solution if found
        self.exit = False                                       # Forced exit tag
        self.name_provider_index = 0                            # Index for name provider, for chain identification
        self.resources = dict                                   # Resources consumed
        self.start_time = process_time()                        # Calculates execution time
        self.time_from_stimulus_onset = 0                       # Counts predicted cognitive time
        self.total_time_per_sentence = 0                        # Counts predicted cognitive time
        self.time_from_stimulus_onset_for_word = []             # Counts predicted cognitive time
        for key in PhraseStructure.resources:
            PhraseStructure.resources[key] = {"ms": 1, "n": 0}
        self.resources = {"Total Time": {'ms': 0, 'n': 0},     # Count predicted cognitive time
                          "Garden Paths": {'ms': 0, 'n': 0},
                          "Merge": {'ms': 5, 'n': 0},
                          "Head Chain": {'ms': 5, 'n': 0},
                          "Phrasal Chain": {'ms': 5, 'n': 0},
                          "Feature Chain": {'ms': 5, 'n': 0},
                          "Agree": {'ms': 5, 'n': 0},
                          "Feature": {'ms': 5, 'n': 0},
                          "Adjunct Chain": {'ms': 5, 'n': 0},
                          "Extraposition": {'ms': 6, 'n': 0},
                          "Last Resort Extraposition": {'ms': 5, 'n': 0},
                          "Mean time per word": {'ms': 0, 'n': 0}
                          }

    def parse_sentence(self, count, lst):
        self.sentence = lst
        self.start_time = process_time()
        self.initialize()
        self.plausibility_metrics.initialize()
        self.narrow_semantics.initialize()
        log_new_sentence(self, count, lst)
        self.parse_new_item(None, lst, 0)

    def parse_new_item(self, ps, lst, index, inflection_buffer=None):
        if self.circuit_breaker(ps, lst, index):
            return
        retrieved_lexical_items = self.lexicon.lexical_retrieval(lst[index])
        for lexical_constituent in retrieved_lexical_items:
            lexical_item, lst_branched, inflection = self.morphology.morphological_parse(lexical_constituent, lst.copy(), index)
            lexical_item = self.lexical_stream.stream_into_syntax(lexical_item, lst_branched, inflection, ps, index, inflection_buffer)
            merge_sites = self.plausibility_metrics.filter_and_rank(ps, lexical_item)
            for site, transfer, address_label in merge_sites:
                log(f'\n\t\t{address_label}')
                new_constituent = self.attach(ps.target_left_branch(site), site, lexical_item, transfer)
                self.working_memory.remove_items(merge_sites)
                self.parse_new_item(new_constituent.top(), lst_branched, index + 1)
                if self.exit:
                    break
            print('.', end='', flush=True)
            self.narrow_semantics.pragmatic_pathway.forget_object(lexical_item)
        if not self.exit:
            log(f'\n\t\tBacktracking to {lst[index]}')

    def attach(self, left_branch, site, terminal_lexical_item, transfer):
        self.working_memory.maintain(site)
        if left_branch.belong_to_same_word(site):
            new_constituent = left_branch.sink_into_complex_head(terminal_lexical_item)
        else:
            new_constituent = self.attach_into_phrase(left_branch, terminal_lexical_item, transfer)
        self.consume_resources("Merge", terminal_lexical_item)
        log('\n')
        return new_constituent

    def attach_into_phrase(self, left_branch, terminal_lexical_item, transfer):
        new_left_branch = left_branch
        if transfer:
            set_logging(False)
            new_left_branch = self.transfer.transfer_to_LF(left_branch)
            set_logging(True)
        new_constituent = new_left_branch.Merge(terminal_lexical_item)
        self.working_memory.remove_item(left_branch)
        return new_constituent

    def circuit_breaker(self, ps, lst, index):
        set_logging(True)
        if self.exit:
            return True
        if index == len(lst):
            self.complete_processing(ps)
            return True
        self.time_from_stimulus_onset = int(len(lst[index]) * 10)
        if not self.first_solution_found:
            self.resources['Total Time']['n'] += self.time_from_stimulus_onset

    def complete_processing(self, ps):
        self.transfer.transfer_to_LF(ps)
        if self.postsyntactic_tests(ps):
            self.resources.update(PhraseStructure.resources)
            report_success(self, ps)
        else:
            self.narrow_semantics.reset_for_new_interpretation()
            report_failure(ps)
        if not self.first_solution_found:
            self.consume_resources("Garden Paths", ps)

    def postsyntactic_tests(self, ps):
        log(f'\n\t\tLF-interface and postsyntactic legibility tests:')
        return self.LF.LF_legibility_test(ps) and \
               self.LF.final_tail_check(ps) and \
               self.narrow_semantics.postsyntactic_semantic_interpretation(ps)

    def consume_resources(self, key, target):
        if not self.first_solution_found:
            self.time_from_stimulus_onset += self.resources[key]['ms']
            if 'Total Time' in self.resources:
                self.resources['Total Time']['n'] += self.resources[key]['ms']
            self.resources[key]['n'] += 1
            log(f'\n\t\t{key}({target.illustrate()}) => {target.top()}')
