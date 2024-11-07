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
    OPs = {'Noncyclic Ā-chain':
              {'TRIGGER': lambda x: x.operator_in_scope_position() and x.sister() and not PhraseStructure.cyclic,
               'TARGET': lambda x: x,
               'TRANSFORM': lambda x, t: x.reconstruct_operator(t)},
           'Feature inheritance':
              {'TRIGGER': lambda x: x.check({'EF?'}) or (x.highest_finite_head() and not x.check({'!PER'})),
               'TARGET': lambda x: x,
               'TRANSFORM': lambda x, t: x.feature_inheritance()},
            'A-chain':
              {'TRIGGER': lambda x: x.zero_level() and
                                    x.core.EPP() and
                                    x.is_R() and x.sister() and x.sister().complex() and not x.sister().copied and x.sister().H().core.referential() and
                                    not x.sister().operator_features() and x.tail_test(tail_sets=x.sister().get_tail_sets(), direction='right', weak_test=True),
               'TARGET': lambda x: x.sister().chaincopy(),
               'TRANSFORM': lambda x, t: x * t},
           'IHM':
               {'TRIGGER': lambda x: x.complex_head() and not x.core.EHM() and not x.affix().copied,
                'TARGET': lambda x: x.affix(),
                'TRANSFORM': lambda x, t: x.head_reconstruction(t)},
           'Scrambling': {'TRIGGER': lambda x: x.max().license_scrambling() and
                                               (x.container() and x.container().core.EF() or not x.H().tail_test()) and
                                               x.scrambling_target() and x.scrambling_target() != x.top() and
                                               not x.operator_in_scope_position() and PhraseStructure.speaker_model.LF.pass_LF_legibility(
              x.scrambling_target().copy().transfer(), logging=False) and
                                               not PhraseStructure.cyclic,
                         'TARGET': lambda x: x.scrambling_target().chaincopy(externalize=True),
                         'TRANSFORM': lambda x, t: x.scrambling_target().scrambling_reconstruct(t)},
           'Agree':
              {'TRIGGER': lambda x: x.zero_level() and x.is_L() and x.core.is_unvalued() and 'ΦLF' not in x.core,
               'TARGET': lambda x: x,
               'TRANSFORM': lambda x, t: x.AgreeLF()},
           'Cyclic Ā-chain':
              {'TRIGGER': lambda x: x.zero_level() and x.is_R() and x.core.thematic_head() and x.sister() and x.sister().zero_level() and PhraseStructure.cyclic,
               'TARGET': lambda Y: next((x.chaincopy() for x in Y.path() if
                                         x.complex() and x.operator_features() and x.H().check_some(
                                             Y.core.get_selection_features('+SPEC')) and Y.tail_test(
                                             tail_sets=x.get_tail_sets())), None),
               'TRANSFORM': lambda x, t: t * x}
           }

    def __init__(self, settings, language='XX'):
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
        infl_buffer = kwargs.get('infl_buffer', [])

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
                # 1. Morphological parsing if applicable
                if lex.morphological_chunk:
                    self.embedding += 1
                    self.derivational_search_function(phrase_structure=secure_copy(X),
                                                      word_list=lex.morphological_parse(X, lst.copy(), index),
                                                      index=index,
                                                      infl_buffer=infl_buffer)

                # 2. Process inflectional feature (withhold streaming to syntax)
                if not lex.morphological_chunk and lex.inflectional:
                    infl_buffer.append(lex.features - {'inflectional'})
                    log(f'= {illu(lex.features)}')
                    self.derivational_search_function(phrase_structure=secure_copy(X), word_list=lst, index=index + 1, infl_buffer=infl_buffer)

                # 3. Extract features from primitive lex and wrap them into primitive constituent and stream into syntax
                if not lex.morphological_chunk and not lex.inflectional:
                    self.syntactic_branching(X, self.lexical_stream.wrap(lex, infl_buffer), lst, index)

                infl_buffer = []

        log(f'\n\t\tBacktracking...')

    def syntactic_branching(self, X, W, lst, index):
        if not X:
            self.derivational_search_function(phrase_structure=W.copy(), word_list=lst, index=index + 1)
        else:
            self.results.record_derivational_step(X, 'Phrase structure in syntactic working memory')
            for N in self.plausibility_metrics.filter_and_rank(X, W):
                Y = X.target_left_branch(N).transfer().attach(W.copy())
                PhraseStructure.cyclic = True
                Y = Y.bottom().reconstruct(self.OPs)
                log(f'\n\t= {Y.top()}\n')
                self.derivational_search_function(phrase_structure=Y, word_list=lst, index=index + 1)
                if self.exit:
                    break
        self.narrow_semantics.pragmatic_pathway.forget_object(W)

    def circuit_breaker(self, X, lst, index):
        set_logging(True)
        if self.exit:
            return True
        if index == len(lst):
            self.evaluate_complete_solution(X)
            return True

    # Evaluates a complete solution at the LF-interface and semantic interpretation
    def evaluate_complete_solution(self, X):
        self.results.record_derivational_step(X, 'PF-interface')
        PhraseStructure.cyclic = False
        log('\n\n----Noncyclic derivation------------------------------------------------------------------------------\n')
        X.transfer()
        X = X.top()
        # X.tidy_names(1)
        log(f'\n\t= LF-interface {X}\n\n')
        self.results.record_derivational_step(X, 'LF-interface')

        # Postsyntactic tests (LF-interface legibility and semantic interpretation)
        self.LF.active_test_battery = self.LF.LF_legibility_tests
        if self.LF.pass_LF_legibility(X) and self.LF.final_tail_check(X) and self.narrow_semantics.postsyntactic_semantic_interpretation(X):
            self.results.update_resources(PhraseStructure.resources, self.sentence)
            self.results.store_solution(X, self.data_item)
            self.results.log_success(X)
            self.results.record_derivational_step(X, 'Accepted LF-interface')
            if self.settings.retrieve('general_parameter_only_first_solution', True):
                self.exit = True
        else:
            self.results.report_failure(X)
            self.results.reset_output_fields()
            self.narrow_semantics.reset_for_new_interpretation()

        # Register one garden path if we evaluated complete solution but
        # there has not been any accepted solutions
        if not self.results.first_solution_found:
            self.results.consume_resources("Garden Paths", X)

        PhraseStructure.cyclic = True
