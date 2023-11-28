from support import set_logging, log, report_failure, report_success, log_new_sentence
from lexical_interface import LexicalInterface
from LF import LF
from morphology import Morphology
from SEM_narrow_semantics import NarrowSemantics
from lexical_stream import LexicalStream
from time import process_time
from plausibility_metrics import PlausibilityMetrics
from phrase_structure import PhraseStructure
from Experimental_functions import ExperimentalFunctions

class SpeakerModel:
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
        self.LF = LF(self)                                      # Access to LF
        self.lexical_stream = LexicalStream(self)               # Access to lexical stream
        self.plausibility_metrics = PlausibilityMetrics(self)
        self.resources = dict                                   # Resources consumed
        self.start_time = 0                                     # Calculates execution time
        self.end_time = 0                                       # Calculates execution time
        self.number_of_items_consumed = 0
        self.time_from_stimulus_onset = 0
        self.total_time_per_sentence = 0
        self.time_from_stimulus_onset_for_word = []
        self.only_first_solution = False
        self.Experimental_functions = ExperimentalFunctions(self)

    def initialize(self):
        if 'only_first_solution' in self.local_file_system.settings:
            if self.local_file_system.settings['only_first_solution']:
                self.only_first_solution = True
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
                          "Feature Inheritance": {'ms': 5, 'n': 0},
                          "Agree": {'ms': 5, 'n': 0},
                          "Feature": {'ms': 5, 'n': 0},
                          "Left Scrambling": {'ms': 5, 'n': 0},
                          "Right Scrambling": {'ms': 5, 'n': 0},
                          "Extraposition": {'ms': 6, 'n': 0},
                          "Last Resort Extraposition": {'ms': 5, 'n': 0},
                          "Mean time per word": {'ms': 0, 'n': 0}
                          }

    # Prepares the derivational search operation and then calls the recursive
    # derivational search function parse_new_item()
    def parse_sentence(self, count, lst):

        # Bookkeeping and logging
        self.sentence = lst
        self.start_time = process_time()
        log_new_sentence(self, count, lst)
        PhraseStructure.chain_index = 0

        # Initialize the components (mostly bookkeeping and logging)
        self.initialize()
        self.plausibility_metrics.initialize()
        self.narrow_semantics.initialize()

        # Provides phrase structure operations access to the current speaker model
        PhraseStructure.speaker_model = self

        # Call the derivational search function
        self.parse_new_item(None, lst, 0)

    # Recursive derivational search function (parser)
    def parse_new_item(self, ps, lst, index, inflection_buffer=None):
        if self.circuit_breaker(ps, lst, index):
            return

        # Match the phonological input word/symbol with lexical entries and
        # return the corresponding lexical items (constituents)
        retrieved_lexical_items = self.lexicon.lexical_retrieval(lst[index])
        for lexical_constituent in retrieved_lexical_items:

            # Process polymorphemic words (convert them into input list) and
            # call parse_new_item() recursively with the result if applicable
            self.morphology.morphological_parse(ps, lexical_constituent, lst.copy(), index, inflection_buffer)

            # Primitive lexical item enters the syntactic component, which
            # handles inflectional features if any (plus recursive call) and other operations
            self.lexical_stream.stream_into_syntax(lexical_constituent, lst, ps, index, inflection_buffer)

            # Filter and rank all possible attachment sites, then call the function recursively
            # to create the derivational search space
            for N, transfer, address_label in self.plausibility_metrics.filter_and_rank(ps, lexical_constituent):
                new_constituent = ps.target_left_branch(N).attach(N, lexical_constituent, transfer, address_label)
                self.parse_new_item(new_constituent.top(), lst, index + 1)
                if self.exit:
                    break

            # Pragmatic processing that has to do with psychological allocation and
            # information structure
            self.narrow_semantics.pragmatic_pathway.forget_object(lexical_constituent)

        # Backtrack
        log(f'\n\t\tBacktracking...')

    def circuit_breaker(self, ps, lst, index):
        set_logging(True)
        if self.exit:
            return True

        # If there are no more words, the solution is evaluated
        # at LF-interface and postsyntactically
        if index == len(lst):
            self.evaluate_complete_solution(ps)
            return True
        self.time_from_stimulus_onset = int(len(lst[index]) * 10)
        if not self.first_solution_found:
            self.resources['Total Time']['n'] += self.time_from_stimulus_onset

    # Evaluates a complete solution at the LF-interface and semantic interpretation
    def evaluate_complete_solution(self, ps):
        log(f'\n\n\tPF/LF-interface mapping: ----------------------------------------------------------------------------\n ')
        log(f'\n\t\tPF-interface {ps}\n')
        ps.transfer_to_LF()
        log(f'\n\n\t\tLF-interface {ps.top()}\n')

        # Postsyntactic tests (LF-interface legibility and semantic interpretation)
        if self.postsyntactic_tests(ps):
            self.resources.update(PhraseStructure.resources)
            report_success(self, ps)
        else:
            self.narrow_semantics.reset_for_new_interpretation()
            report_failure(ps)

        # Register one garden path if we evaluated complete solution but
        # there has not been any accepted solutions
        if not self.first_solution_found:
            self.consume_resources("Garden Paths", ps)

    def postsyntactic_tests(self, ps):
        log(f'\n\t\tLF-interface and postsyntactic legibility tests:')
        return self.LF.pass_LF_legibility(ps) and self.LF.final_tail_check(ps) and self.narrow_semantics.postsyntactic_semantic_interpretation(ps)

    def consume_resources(self, key, target):
        if not self.first_solution_found:
            self.time_from_stimulus_onset += self.resources[key]['ms']
            if 'Total Time' in self.resources:
                self.resources['Total Time']['n'] += self.resources[key]['ms']
            self.resources[key]['n'] += 1
            if key != 'Agree' and key != 'Last Resort Extraposition':
                log(f'\n\t\t{key}({target.illustrate()}) => {target.top()}.')
