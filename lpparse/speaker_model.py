from support import set_logging, log, log_new_sentence, secure_copy, log_instance
from lexical_interface import LexicalInterface
from LF import LF
from SEM_narrow_semantics import NarrowSemantics
from lexical_stream import LexicalStream
from support import illu
import time
from plausibility_metrics import PlausibilityMetrics
from phrase_structure import PhraseStructure
from Experimental_functions import ExperimentalFunctions
from results import Results

class SpeakerModel:
    syntactic_working_memory = []                               # Syntactic working memory, allows the engine to focus to several items

    def __init__(self, settings, language='XX'):
        self.settings = settings
        self.language = language

        # Contains the following submodules

        self.narrow_semantics = NarrowSemantics(self)           # Narrow sentence-level semantics
        self.lexicon = LexicalInterface(self)                   # Access to the lexicon
        self.lexicon.load_lexicons(settings)                    # Load the language/dialect specific lexicon
        self.LF = LF(self)                                      # Access to LF
        self.lexical_stream = LexicalStream(self)               # Access to lexical stream
        self.plausibility_metrics = PlausibilityMetrics(self)
        self.Experimental_functions = ExperimentalFunctions(self)

        self.sentence = []
        self.results = Results(self)
        self.memory_buffer_inflectional_affixes = set()         # Local memory buffer for inflectional affixes
        self.exit = False                                       # Forced exit tag
        self.name_provider_index = 0                            # Index for name provider, for chain identification
        self.embedding = 0
        self.data_item = None
        self.ongoing_conversation = False

    def initialize(self):
        self.memory_buffer_inflectional_affixes = set()         # Local memory buffer for inflectional affixes
        self.exit = False                                       # Forced exit tag
        self.name_provider_index = 0                            # Index for name provider, for chain identification
        PhraseStructure.speaker_model = self                    # Provides phrase structure operations access to the current speaker model
        PhraseStructure.chain_index = 0
        self.lexical_stream.id = 0
        if Results.global_start_time == 0:
            Results.global_start_time = time.time()

    def parse_sentence(self, data_item):
        """Prepares the derivational search operation and
        calls the recursive derivational search function parse_new_item()"""

        # Bookkeeping and logging

        self.data_item = data_item
        if data_item.get("part_of_conversation", False):
            self.ongoing_conversation = True

        self.sentence = data_item["word_list"]
        log_new_sentence(self, data_item["index"], data_item["word_list"])
        PhraseStructure.chain_index = 0
        PhraseStructure.node_identity = 0

        # Initialize the components (mostly bookkeeping and logging)

        self.initialize()
        self.results.initialize(data_item["word_list"])
        self.plausibility_metrics.initialize()
        self.narrow_semantics.initialize()

        # Record lower level sensory processing (reading, hearing) for each word

        for word in self.sentence:
            self.results.consume_resources('Sensory Processing', word)

        # Call the derivational search function

        self.derivational_search_function(word_list=data_item["word_list"].copy())

    # Recursive derivational search function (parser)

    def derivational_search_function(self, **kwargs):
        X = kwargs.get('phrase_structure', None)
        lst = kwargs.get('word_list', [])
        index = kwargs.get('index', 0)
        infl_buffer = kwargs.get('infl_buffer', [set()])
        prosody = kwargs.get('prosody', set())

        Results.accumulate_global_steps()   #   Internal bookkeeping
        log_instance.indent_level = self.embedding

        # Stop processing if there are no more words to consume

        if not self.circuit_breaker(X, lst, index):

            # Retrieve lexical items on the basis of phonological input

            retrieved_lexical_items = self.lexicon.lexical_retrieval(lst[index])
            log_instance.indent_level = self.embedding

            # Examine all retrieved lexical items (ambiguity resolution)

            for lex in retrieved_lexical_items:
                # Recursive branching: 1) morphological parsing, 2) inflection, 3) stream into syntax
                # 1) Morphological parsing, if applicable

                if lex.morphological_chunk:
                    self.embedding += 1
                    self.derivational_search_function(phrase_structure=secure_copy(X),
                                                      word_list=lex.morphological_parse(X, lst.copy(), index),
                                                      index=index,
                                                      infl_buffer=infl_buffer,
                                                      prosody=prosody)

                # 2. Process inflectional feature (withhold streaming to syntax)
                # NOTE: processing goes from right to left (reverse order)

                if not lex.morphological_chunk and lex.inflectional and lex.type != 'prosodic':

                    # Portmanteau morphemes are added to the last feature bundle

                    if lex.type == 'portmanteau':
                        infl_buffer[-1].update(lex.features - {'inflectional'})

                    # Other morphemes boundaries create a new feature bundle

                    else:
                        infl_buffer[-1].update(lex.features - {'inflectional'})
                        infl_buffer.append(set())
                    log(f'= {illu(lex.features)}')
                    self.derivational_search_function(phrase_structure=secure_copy(X),
                                                      word_list=lst,
                                                      index=index + 1,
                                                      infl_buffer=infl_buffer,
                                                      prosody=prosody)

                # 3. Process prosodic features

                if not lex.morphological_chunk and not lex.inflectional and lex.type == 'prosodic':
                    prosody = lex.features
                    log(f'= prosodic feature {illu(lex.features)}')
                    self.derivational_search_function(phrase_structure=secure_copy(X),
                                                      word_list=lst,
                                                      index=index + 1,
                                                      infl_buffer=infl_buffer,
                                                      prosody=prosody)

                # 4. Extract features from primitive lex and wrap them into primitive constituent and stream into syntax

                if not lex.morphological_chunk and not lex.inflectional and not lex.type == 'prosodic':
                    self.syntactic_branching(X, self.lexical_stream.wrap(lex, infl_buffer[::-1], prosody), lst, index)

                infl_buffer = [set()]
                prosody = set()

        log(f'\n\t\tBacktracking...')

    def syntactic_branching(self, X, W, lst, index):
        if not X:
            self.derivational_search_function(phrase_structure=W.copy(), word_list=lst, index=index + 1)
        else:
            self.results.record_derivational_step(X, 'Phrase structure in syntactic working memory')

            # Acquire a list of right edge nodes which can be targeted by Merge-1

            for N in self.plausibility_metrics.filter_and_rank(X, W):

                # Create candidate solution [[X...] W]

                Y = X.target_left_branch_and_copy(N).transfer().attach(W.copy())
                log(f'\n\t= {Y.top()}\n')
                PhraseStructure.cyclic = True
                log(f'\n\tCyclic reconstruction:\n')

                # Cyclic reconstruction

                Y = Y.bottom().reconstruct()

                # Consume next item (recursion)

                self.derivational_search_function(phrase_structure=secure_copy(Y), word_list=lst, index=index + 1)

                # If set True, recursion will exit by force

                if self.exit:
                    break

        self.narrow_semantics.pragmatic_pathway.forget_object(W)

    def circuit_breaker(self, X, lst, index):
        set_logging(True)
        if self.exit:
            return True

        # If there are no more words in the input pipeline, the result will be evaluated

        if index == len(lst):
            self.evaluate_complete_solution(X)
            return True

    # Evaluates a complete solution at the LF-interface and semantic interpretation

    def evaluate_complete_solution(self, X):
        self.results.record_derivational_step(X, 'PF-interface')
        PhraseStructure.cyclic = False
        log('\n\n----Noncyclic derivation------------------------------------------------------------------------------\n')
        log(f'\n\t{X.top()}\n')

        # Noncyclic transfer

        X.transfer()
        X = X.top()
        log('\n\n------------------------------------------------------------------------------------------------------\n')
        log(f'\n\t= LF-interface {X}\n\n')
        self.results.record_derivational_step(X, 'LF-interface')

        # Postsyntactic tests (LF-interface legibility and semantic interpretation)

        self.LF.active_test_battery = self.LF.LF_legibility_tests
        if self.LF.pass_LF_legibility(X) and self.LF.final_tail_check(X) and self.narrow_semantics.postsyntactic_semantic_interpretation(X):

            # Report and record accepted solution

            self.results.update_resources(PhraseStructure.resources, self.sentence)
            self.results.store_solution(X, self.data_item)
            self.results.log_success(X)
            self.results.record_derivational_step(X, 'Accepted LF-interface')
            if self.settings.retrieve('general_parameter_only_first_solution', True):
                self.exit = True
        else:

            # Report failure

            self.results.report_failure(X)
            self.results.reset_output_fields()
            self.narrow_semantics.reset_for_new_interpretation()

        # Register one garden path if we evaluated complete solution but
        # there has not been any accepted solutions

        if not self.results.first_solution_found:
            self.results.consume_resources("Garden Paths", X)
        PhraseStructure.cyclic = True

    @classmethod
    def clean_syntactic_working_memory(cls):
        cls.syntactic_working_memory = []

    @classmethod
    def add_item_to_syntactic_working_memory(cls, X):
        cls.syntactic_working_memory.append(X)

    @classmethod
    def read_syntactic_working_memory(cls):
        return cls.syntactic_working_memory

