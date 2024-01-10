from support import set_logging, log, log_new_sentence, secure_copy, log_instance
from lexical_interface import LexicalInterface
from LF import LF
from SEM_narrow_semantics import NarrowSemantics
from lexical_stream import LexicalStream

from plausibility_metrics import PlausibilityMetrics
from phrase_structure import PhraseStructure
from Experimental_functions import ExperimentalFunctions
from results import Results

class SpeakerModel:
    def __init__(self, settings, local_file_system, language='XX'):
        self.settings = settings
        self.sentence = []
        self.language = language                                # Contextual variables (language etc.)
        self.results = Results(self)
        self.memory_buffer_inflectional_affixes = set()         # Local memory buffer for inflectional affixes
        self.exit = False                                       # Forced exit tag
        self.name_provider_index = 0                            # Index for name provider, for chain identification
        self.narrow_semantics = NarrowSemantics(self)           # Narrow sentence-level semantics
        self.lexicon = LexicalInterface(self)                   # Access to the lexicon
        self.lexicon.load_lexicons(settings)                     # Load the language/dialect specific lexicon
        self.LF = LF(self)                                      # Access to LF
        self.lexical_stream = LexicalStream(self)               # Access to lexical stream
        self.plausibility_metrics = PlausibilityMetrics(self)
        self.Experimental_functions = ExperimentalFunctions(self)
        self.embedding = 0

    def initialize(self):
        self.memory_buffer_inflectional_affixes = set()         # Local memory buffer for inflectional affixes
        self.exit = False                                       # Forced exit tag
        self.name_provider_index = 0                            # Index for name provider, for chain identification
        PhraseStructure.speaker_model = self                    # Provides phrase structure operations access to the current speaker model
        PhraseStructure.chain_index = 0

    def parse_sentence(self, index, lst):
        """Prepares the derivational search operation and
        calls the recursive derivational search function parse_new_item()"""

        # Bookkeeping and logging
        self.sentence = lst
        log_new_sentence(self, index, lst)

        # Initialize the components (mostly bookkeeping and logging)
        self.initialize()
        self.results.initialize(lst)
        self.plausibility_metrics.initialize()
        self.narrow_semantics.initialize()

        # Record lower level sensory processing (reading, hearing) for each word
        for word in self.sentence:
            self.results.consume_resources('Sensory Processing', word)

        # Call the derivational search function
        self.parse_new_item(None, lst, 0)

    # Recursive derivational search function (parser)
    def parse_new_item(self, ps, lst, index, inflection_buffer=frozenset()):

        log_instance.indent_level = self.embedding

        # Stop processing if there are no more words to consume
        if not self.circuit_breaker(ps, lst, index):

            # Retrieve lexical items on the basis of phonological input
            retrieved_lexical_items = self.lexicon.lexical_retrieval(lst[index])

            log_instance.indent_level = self.embedding

            # Examine all retrieved lexical items (ambiguity resolution)
            for lex in retrieved_lexical_items:

                # Recursive branching: 1) morphological parsing, 2) inflection, 3) stream into syntax
                # 1. Morphological parsing if applicable
                if lex.morphological_chunk:
                    self.embedding += 1
                    self.parse_new_item(secure_copy(ps), lex.morphological_parse(ps, lst.copy(), index, inflection_buffer), index, inflection_buffer)

                # 2. Process inflectional feature (withhold streaming to syntax)
                if not lex.morphological_chunk and lex.inflectional:
                    inflection_buffer = inflection_buffer | lex.features - {'inflectional'}
                    self.parse_new_item(secure_copy(ps), lst, index + 1, inflection_buffer)

                # 3. Extract features from primitive lex and wrap them into primitive constituent and stream into syntax
                if not lex.morphological_chunk and not lex.inflectional:
                    self.explore_derivation_space(ps, self.lexical_stream.wrap(lex, inflection_buffer), lst, index)

                inflection_buffer = set()

        log(f'\n\t\tBacktracking...')

    def explore_derivation_space(self, ps, X, lst, index):
        if not ps:
            # If there is no phrase structure in syntactic working memory, create it from X
            log(f' => Insert into working memory.')
            self.parse_new_item(X.copy(), lst, index + 1)
        else:
            self.results.record_derivational_step(ps, 'Phrase structure in syntactic working memory')
            # Create derivational search space for existing phrase structure and new constituent X
            for N, transfer, address_label in self.plausibility_metrics.filter_and_rank(ps, X):
                new_constituent = ps.target_left_branch(N).attach(N, X, transfer, address_label)
                self.parse_new_item(new_constituent.top().copy(), lst, index + 1)
                if self.exit:
                    break
        self.narrow_semantics.pragmatic_pathway.forget_object(X)

    def circuit_breaker(self, ps, lst, index):
        set_logging(True)
        if self.exit:
            return True

        # If there are no more words, the solution is evaluated
        # at LF-interface and postsyntactically
        if index == len(lst):
            self.embedding = 0
            log_instance.indent_level = self.embedding
            self.evaluate_complete_solution(ps)
            return True

    # Evaluates a complete solution at the LF-interface and semantic interpretation
    def evaluate_complete_solution(self, ps):
        self.results.record_derivational_step(ps, 'PF-interface')
        log(f'\n\n\tPF/LF-interface mapping: ----------------------------------------------------------------------------\n ')
        log(f'\n\t\tPF-interface {ps}\n')
        ps.transfer_to_LF()
        ps = ps.top()
        log(f'\n\n\t\tLF-interface {ps}\n')
        self.results.record_derivational_step(ps, 'LF-interface')

        # Postsyntactic tests (LF-interface legibility and semantic interpretation)
        if self.postsyntactic_tests(ps):
            self.results.update_resources(PhraseStructure.resources, self.sentence)
            self.results.store_solution(ps)
            self.results.log_success(ps)
            self.results.record_derivational_step(ps, 'Accepted LF-interface')
            if self.settings.get()['only_first_solution']:
                self.exit = True
        else:
            self.narrow_semantics.reset_for_new_interpretation()
            self.results.report_failure(ps)

        # Register one garden path if we evaluated complete solution but
        # there has not been any accepted solutions
        if not self.results.first_solution_found:
            self.results.consume_resources("Garden Paths", ps)

    def postsyntactic_tests(self, ps):
        log(f'\n\t\tLF-interface and postsyntactic legibility tests:')
        return self.LF.pass_LF_legibility(ps) and self.LF.final_tail_check(ps) and self.narrow_semantics.postsyntactic_semantic_interpretation(ps)
