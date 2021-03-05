from support import log
from SEM_operators_variables import OperatorVariableModule
from SEM_discourse import Discourse
from SEM_LF_recovery import LF_Recovery

class NarrowSemantics:
    """
    Narrow semantics is responsible for creating semantic interpretation for isolated sentences. The result of
    narrow semantic interpretation will be combined with broad semantic interpretation that takes context
    into account. This class will eventually replace semantics.py module
    """
    def __init__(self, controlling_parsing_process):
        self.operator_variable_module = OperatorVariableModule(self)
        self.LF_recovery_module = LF_Recovery(controlling_parsing_process)
        self.discourse_module = Discourse(self)
        self.semantic_bookkeeping = {}
        self.semantic_interpretation = {}
        self.semantic_interpretation_failed = False
        self.index_counter = None
        self.controlling_parsing_process = controlling_parsing_process
        self.phi_interpretation_failed = False
        self.semantic_type = {'T/fin':'Proposition',
                              'D': '§Thing',
                              'Q': '§Quantifier',
                              'NUM': '§Quantity',
                              'NEG': '§Polarity',
                              'C/fin': '§Proposition',
                              'C': '§Proposition',
                              'N': '§Predicate',
                              'V': '§Predicate',
                              'A': '§Predicate',
                              'a': '§Predicate',
                              'ADV': '§Predicate',
                              '0': '§Predicate',
                              'P': '§Topology',
                              'v': '§Valency',
                              'T': '§Tense',
                              'ASP': '§Eventive',
                              'ARG': '§Unsaturated',
                              'SEM:internal': '§Internal',
                              'SEM:external': '§External',
                              'FORCE': '§Proposition'
                              }

    def initialize(self):
        self.index_counter = 1
        self.semantic_bookkeeping = {}
        self.semantic_interpretation_failed = False
        self.semantic_interpretation = {'Recovery': [],
                                        'Aspect': [],
                                        'D-features': [],
                                        'Operator bindings': [],
                                        'Speaker attitude': [],
                                        'Information structure': {'Marked topics': None, 'Neutral gradient': None, 'Marked focus': None}}

    def interpret(self, ps):
        log(f'\n\t\tTransferring {ps} into the conceptual-intentional system...')
        self.reset_fail_flags()
        self._interpret(ps)
        return self.semantic_interpretation_failed

    def reset_fail_flags(self):
        self.semantic_interpretation_failed = False
        self.phi_interpretation_failed = False
        self.operator_variable_module.interpretation_failed = False
        self.discourse_module.interpretation_failed = False
        self.LF_recovery_module.interpretation_failed = False

    def _interpret(self, ps):
        """
        Generates a semantic interpretation for a node if it primitive, otherwise calls the function recursively.

        Each lexical item is subjected to several types of semantic interpretation, in this version
        (i) LF-recovery for predicates that have unsaturated arguments
        (ii) detection of phi-feature conflicts
        (iii) tail-feature interpretation
        (iv) variable binding.
         """
        if ps.is_primitive():
            self.LF_recovery_module.perform_LF_recovery(ps, self.semantic_interpretation)
            self.detect_phi_conflicts(ps)
            self.interpret_tail_features(ps)
            self.operator_variable_module.bind_variable(ps, self.semantic_interpretation)
            self.discourse_module.reconstruct_discourse(ps, self.semantic_interpretation)
            if self.failure():
                return
        else:
            if not ps.left_const.find_me_elsewhere:
                self._interpret(ps.left_const)
            if not ps.right_const.find_me_elsewhere:
                self._interpret(ps.right_const)

    def failure(self):
        if self.LF_recovery_module.interpretation_failed or \
                self.phi_interpretation_failed or \
                self.operator_variable_module.interpretation_failed or \
                self.discourse_module.interpretation_failed:
            self.semantic_interpretation_failed = True
            return True

    def forget_referent(self, referring_head):
        """
        Removes an element from the semantic space referred by [referring_head], if any. This function is
        used during backtracking.
        """
        if self.controlling_parsing_process.first_solution_found:
            return
        idx = self.get_semantic_wiring(referring_head)
        if idx:
            log(f'Removing reference [{idx}] of \"{referring_head.illustrate()}\" from semantic space...')
            self.semantic_bookkeeping.pop(idx, None)

    def update_references(self, ps):
        """
        Updates information concerning referential relations.
        """
        if self.controlling_parsing_process.first_solution_found:
            return
        if ps.is_complex():
            if ps.left_const.is_primitive() and self.get_semantic_wiring(ps.left_const):
                self.update_reference(ps.left_const)
            if ps.right_const.is_primitive() and self.get_semantic_wiring(ps.right_const):
                self.update_reference(ps.right_const)
            else:
                if ps.right_const.adjunct:
                    self.update_references(ps.right_const)
                    self.update_references(ps.left_const)
                else:
                    self.update_references(ps.right_const)

    def update_reference(self, ps):
        head = ps.head()
        idx = self.get_semantic_wiring(head)
        if idx:
            self.semantic_bookkeeping[idx]['Reference'] = f'{head.max().illustrate()}'

    def wire_semantics(self, ps):
        """
        Wires constituents in [ps] recursively with objects inside the semantic space and adds them to semantic bookkeeping.
        Creates an IDX feature for the constituent and creates the corresponding object into the semantic space
        (semantic bookkeeping). This version is still unable to create co-reference dependencies. Semantic bookkeeping
        holds a ranked gradient which records the prominence of the item in the input structure.

        Travels on the right edge and wires all referential heads that have not been wired already.
        Right adjuncts are visited separately, after which the right edge travel continues
        """
        if self.controlling_parsing_process.first_solution_found:
            return
        if ps.is_complex():
            if ps.right_const.adjunct:
                self.wire_semantics(ps.right_const) # Visit and wired the externalized right adjuncts
                self.wire_semantics(ps.left_const)  # Continue from the right edge of the main structure
                self.try_wire_semantics(ps)
            self.wire_semantics(ps.right_const)
        else:
            self.try_wire_semantics(ps)

    def try_wire_semantics(self, ps):
        """
        Wires semantics for [ps] if possible (ps is referential) and required (no wiring exists)
        """
        if not self.get_semantic_wiring(ps) and ps.head().referential():
            self.wire(ps)

    def wire(self, ps):
        self.create_wiring(ps)
        self.add_to_semantic_bookkeeping(ps)
        self.index_counter += 1  # This will be identifier for the next object

    def create_wiring(self, ps):
        """
        Wires constituent ps (its head) with an object inside the semantic space. THis module will later
        include the binding theory.
        """
        log(f'Wiring semantics ')
        idx_feature = 'IDX:' + str(self.index_counter)
        log(f'[{str(self.index_counter)}] for {ps}...')
        ps.head().features.add(idx_feature)

    def add_to_semantic_bookkeeping(self, ps):
        """
        Adds the element to semantic space (semantic bookkeeping)
        """
        # Ranked gradient that will go into information structure module
        idx = str(self.index_counter)
        self.semantic_bookkeeping[idx] = {'Referring constituent': f'{ps}', 'Order gradient': self.index_counter}
        self.semantic_bookkeeping[idx]['Reference'] = f'{ps.illustrate()}'
        self.update_semantic_type(ps)
        if self.operator_variable_module.scan_criterial_features(ps) and 'FIN' not in ps.features:
            self.semantic_bookkeeping[idx]['Operator'] = True
        else:
            self.semantic_bookkeeping[idx]['Operator'] = False

    def update_semantic_type(self, ps):
        """
        If ps has been wired semantically, then its syntactic features are used to update
        its semantic type inside semantic bookkeeping
        """
        idx = self.get_semantic_wiring(ps)
        if idx:
            if 'Semantic type' not in self.semantic_bookkeeping[idx]:
                self.semantic_bookkeeping[idx]['Semantic type'] = set()
            for f in ps.features:
                if f in self.semantic_type:
                    self.semantic_bookkeeping[idx]['Semantic type'].add(self.semantic_type[f])

    def get_semantic_wiring(self, ps):
        """
        Returns a referential index pointing to objects in the semantic space. If there are several index
        features, then a random feature is returned. Notice for a referential index feature is [IDX:n],
        only n is returned.
        """
        idx_set = {f[4:] for f in ps.head().features if f[:3] == 'IDX'}
        if idx_set:
            return list(idx_set)[0]

    def update_semantics_for_marked_gradient(self, ps, starting_point_head):
        """
        Allows communication between adjunct reconstruction and semantic bookkeeping.

        When constituent is reconstructed by adjunct reconstruction, semantic bookkeeping is updated to
        record the operation, which will be then used by information structure module
        """
        idx = self.get_semantic_wiring(ps)
        if idx:
            feature_vector_set = set(ps.head().feature_vector())        # Take reconstructed floaters feature vector
            if starting_point_head in feature_vector_set:               # If starting point is in the feature vector,
                direction = 'High'                                      # then reconstructed was rightward and the
                log(f'Topicalization...')                               # production movement was leftward
            else:
                direction = 'Low'                                       # Starting point was not in the feature vector,
                log(f'Focussing...')                                    # then reconstruction was leftward and the
                                                                        # production movement was rightward

            self.update_semantics_for_attribute(idx, 'Marked gradient', direction)

    def update_semantics_for_attribute(self, sem_object, attribute, value):
        """
        Updates attribute:value for semantic object [sem_object]
        """
        if self.semantic_bookkeeping[sem_object]:
            self.semantic_bookkeeping[sem_object][attribute] = value

    def detect_phi_conflicts(self, ps):
        """
        Detects phi-feature conflicts inside a head, and marks failed interpretation is found.
        """
        for phi in ps.get_phi_set():
            if phi[-1] == '*':
                log(f'{ps} induces a phi-feature conflict...')
                self.phi_interpretation_failed = True

    def interpret_tail_features(self, ps):
        """
        Interprets semantic interpretation relying on tail-features.

        Currently only implements the aspectual ACC-PAR alteration in Finnish aspect.
        Vainikka (1989), Kiparsky (1997, 2001), Brattico (2020, submitted).
        """
        for tail_set in ps.get_tail_sets():
            self.interpret_argument_tailing(ps, self.get_tailed_head(ps, tail_set))

    def interpret_argument_tailing(self, ps, tailed_head):
        if tailed_head and 'ASP:BOUNDED' in tailed_head.features:
            if 'PAR' in ps.features and not ps.bind_to_scope_operator('POL:NEG'):
                self.semantic_interpretation['Aspect'].append('Aspectually anomalous')
            else:
                self.semantic_interpretation['Aspect'].append('Aspectually bounded')

    def get_tailed_head(self, ps, tail_set):
        for head in ps.feature_vector()[1:]:
            if head.match_features(tail_set) == 'complete match':
                return head