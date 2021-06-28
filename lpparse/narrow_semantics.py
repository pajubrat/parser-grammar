from support import log
from SEM_operators_variables import OperatorVariableModule
from SEM_pragmatic_pathway import Discourse
from SEM_LF_recovery import LF_Recovery
from SEM_quantifiers_numerals_denotations import QuantifiersNumeralsDenotations
from global_cognition import GlobalCognition

class NarrowSemantics:
    """
    Narrow semantics is responsible for creating semantic interpretation for isolated sentences. The result of
    narrow semantic interpretation will be combined with broad semantic interpretation that takes context
    into account. It mediates between the syntactic pathway and global cognition. Thus, narrow semantics
    can be thought of as a wrapped around the syntactic pathway, encapsulating it.

    Narrow semantics takes a phrase structure object as input and tries map it into object(s) in the
    global semantic space processed by global cognition. The expression is linked either to an existing
    object in the global space or an object is created. The module utilizes two distinct methods for
    semantic interpretation: (1) immediate incremental linking of referential elements H (e.g. D) from
    the lexical stream and (2) compositional updating which is performed after transfer for a whole
    phrase HP so that other constituents of HP (modifiers, heads) are taken into account.

    Semantic objects are provided in discourse inventories which are dictionaries of dictionaries.
    The first dictionary hosts a data file for each element, and the data file dict then hosts
    semantic information. When the field contains a simple property, it is called criterion.

    Compositional updating performs minimal search on HP and reacts to features in primitive heads.
    Features are interpreted by criterion functions inside the specialized modules (e.g., QND module).
    Currently complex phrases are added to a special 'criterion' field as strings.
    """
    def __init__(self, controlling_parsing_process):
        # Separate modules responding to different features in the linguistic input
        self.operator_variable_module = OperatorVariableModule(self)
        self.LF_recovery_module = LF_Recovery(controlling_parsing_process)
        self.quantifiers_numerals_denotations_module = QuantifiersNumeralsDenotations(self)
        self.pragmatic_pathway = Discourse(self)
        self.global_cognition = GlobalCognition()

        # Discourse inventory maintained by narrow semantics hosting primitive objects
        self.semantic_interpretation = {}
        self.semantic_interpretation_failed = False

        # Provides unique numerical identifiers to all objects created inside any semantic space
        self.controlling_parsing_process = controlling_parsing_process
        self.phi_interpretation_failed = False

        # Provides semantic types on the basis of linguistic features
        self.semantic_type = {'T/fin':'§Proposition',
                              'D': '§Thing',
                              'φ': '§Thing',
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
                              'OP:REL': '§Predicate',
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
        self.global_cognition.initialize()
        self.pragmatic_pathway.initialize()
        self.semantic_interpretation_failed = False
        self.semantic_interpretation = {'Recovery': [],
                                        'Aspect': [],
                                        'DIS-features': [],
                                        'Operator bindings': [],
                                        'Semantic space': '',
                                        'Speaker attitude': [],
                                        'Information structure': {}}

    def interpret(self, ps):
        log(f'\n\t\tTransferring {ps} into the conceptual-intentional system...')
        self.reset_for_new_interpretation()
        self._interpret(ps)
        return self.semantic_interpretation_failed

    def reset_for_new_interpretation(self):
        log('\n\t\tResetting semantic interpretation...')
        self.semantic_interpretation_failed = False
        self.phi_interpretation_failed = False
        self.operator_variable_module.interpretation_failed = False
        self.pragmatic_pathway.interpretation_failed = False
        self.LF_recovery_module.interpretation_failed = False
        self.semantic_interpretation = {}
        self.semantic_interpretation = {'Recovery': [],
                                        'Aspect': [],
                                        'DIS-features': [],
                                        'Operator bindings': [],
                                        'Semantic space': '',
                                        'Speaker attitude': [],
                                        'Information structure': {'Marked topics': None, 'Neutral gradient': None,
                                                                  'Marked focus': None}}

    def _interpret(self, ps):
        """
        Generates a semantic interpretation for a node if primitive, otherwise calls the function recursively.
        This function is called only when processing is complete (not for each transfer object).

        Each lexical item is subjected to several types of semantic interpretation:
        (i) LF-recovery for predicates that have unsaturated arguments,
        (ii) detection of phi-feature conflicts,
        (iii) tail-feature interpretation,
        (iv) variable binding,
        (v) pragmatic pathway processing.
        """
        if ps.is_primitive():
            self.LF_recovery_module.perform_LF_recovery(ps, self.semantic_interpretation)
            self.detect_phi_conflicts(ps)
            self.interpret_tail_features(ps)
            self.operator_variable_module.bind_operator(ps, self.semantic_interpretation)
            self.pragmatic_pathway.reconstruct_discourse(ps, self.semantic_interpretation)
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
                self.pragmatic_pathway.interpretation_failed:
            self.semantic_interpretation_failed = True
            return True

    def forget_referent(self, referring_head):
        """
        Removes an element from the semantic space referred by [referring_head], if any. This function is
        used during backtracking.
        """
        if self.controlling_parsing_process.first_solution_found or not referring_head:
            return
        idx, space = self.get_referential_index_tuple(referring_head)
        if idx:
            log(f'Removing reference [{idx}] of \"{referring_head.illustrate()}\" from semantic space...')
            if space == 'GLOBAL':
                self.global_cognition.remove_object(idx)
            if space == 'QND':
                self.quantifiers_numerals_denotations_module.remove_object(idx)

    def compositional_semantic_update(self, ps):
        """
        Updates information concerning referential relations inside [ps] recursively.

        The function searches through [ps] and finds any [X YP] or [YP X] where X has
        referential index, then updates the reference for X. Updating is done by
        calling 'compositional_interpretation' which examines the relevant domain inside
        ps.max() by minimal search and applies criterion functions and adds phrasal criteria (if any).

        The function finds phrases that require compositional interpretation, and then triggers it.

        """
        if self.controlling_parsing_process.first_solution_found:
            return
        if ps.is_complex():
            if ps.left_const.is_primitive() and self.get_referential_index_tuple(ps.left_const):
                self.compositional_interpretation(ps.left_const)
            if ps.right_const.is_primitive() and self.get_referential_index_tuple(ps.right_const):
                self.compositional_interpretation(ps.right_const)
            else:
                if ps.right_const.adjunct:
                    self.compositional_semantic_update(ps.right_const)
                    self.compositional_semantic_update(ps.left_const)
                else:
                    self.compositional_semantic_update(ps.right_const)

    def compositional_interpretation(self, ps):
        """
        This system implements "compositional interpretation" on phrases that are
        headed by elements that are referential and pick up objects from the global space,
        directly or indirectly.
        """
        # If the head of [ps] does not have referential index, the object will not have
        # semantic interpretation
        if not self.has_denotation(ps):
            return None

        idx_tuple = self.get_referential_index_tuple(ps)
        idx, space = idx_tuple
        log(f'Interpreting {ps.max()}({space}) compositionally...')

        # Get handle to the semantic object dict
        semantic_object = self.get_semantic_object(idx_tuple)

        # Add the reference field for readability reasons (not used for other purposes)
        semantic_object['Reference'] = f'{ps.max().illustrate()}'

        # Determine intervention features (major category features of [ps])
        intervention_feature_set = ps.head().major_category_features()

        # ----- minimal search ----------------------------------------------------
        for node in ps.max().minimal_search():
            # Determine if search should be terminated
            if self.termination_condition(node, intervention_feature_set, space, ps):
                break
            # Update the semantic object by using information available at [node]
            semantic_object.update(self.interpret_node(node, semantic_object))
        #---------------------------------------------------------------------------

        # Create one new object corresponding to the updated expression to the global semantic space
        idx_set = self.create_global_object(ps, semantic_object)

        # Determine the denotations set for the updated semantic object
        self.determine_denotations_set(semantic_object, idx_set)
        log('Done.\n\t\t')

    def determine_denotations_set(self, semantic_object, idx_set):
        """
        Determines the denotations set for the semantic object. The denotations set contains
        a referential index to all objects inside the global space that could be denoted by
        this expression. The actual denotations are determined by the global cognition module. A compatible
        object is one which does not induce any (type, value) mismatch with the semantic object.
        """
        log(f'Calculating denotations...')
        # Add the new object
        semantic_object['Denotations'] = idx_set
        # Get and add all compatible semantic objects
        semantic_object['Denotations'].update(self.global_cognition.filter_compatible_objects(semantic_object))

    def create_global_object(self, ps, semantic_object):
        log(f'Creating global inventory object...')
        global_object_criteria = self.default_criteria(ps)
        global_object_criteria.update(semantic_object)
        self.interpret_phi_features(global_object_criteria)
        idx_set = self.global_cognition.create_object(global_object_criteria)
        return idx_set


    def interpret_phi_features(self, global_object_criteria):
        """
        Converts grammaticalized phi-features intpectuo semantic criteria understood by global cognition.
        The function is currently implemented as a simple table lookup in order to make it readable.
        This is obviously not the correct version, only an approximation to give away the general idea
        and to make testing possible.
        """
        if 'Phi-set' in global_object_criteria:
            if self.feature_match(global_object_criteria['Phi-set'], {'PHI:NUM:SG', 'PHI:PER:1'}):
                global_object_criteria['Participant role'] = 'Speaker'
            if self.feature_match(global_object_criteria['Phi-set'], {'PHI:NUM:SG', 'PHI:PER:2'}):
                global_object_criteria['Participant role'] = 'Hearer'
            if self.feature_match(global_object_criteria['Phi-set'], {'PHI:NUM:PL', 'PHI:PER:1'}):
                global_object_criteria['Participant role'] = 'Speaker + others'
            if self.feature_match(global_object_criteria['Phi-set'], {'PHI:NUM:PL', 'PHI:PER:2'}):
                global_object_criteria['Participant role'] = 'Hearer + others'
            if self.feature_match(global_object_criteria['Phi-set'], {'PHI:NUM:SG', 'PHI:PER:3'}):
                global_object_criteria['Participant role'] = 'Third party'
            if self.feature_match(global_object_criteria['Phi-set'], {'PHI:NUM:PL', 'PHI:PER:3'}):
                global_object_criteria['Participant role'] = 'Third party + others'
            del global_object_criteria['Phi-set']

    def feature_match(self, set1, set2):
        return set2 == set1 & set2

    def termination_condition(self, node, intervention_feature_set, space, ps):
        """
        Determines whether minimal search should terminate at [node].
        """
        if node.is_complex():
            if node.left_const.is_primitive():
                # Condition 1. Do not search over head that has the same category as the triggering head
                if self.H_over_H_condition(node.left_const, intervention_feature_set, ps):
                    return True
                # Condition 2. Do not search out of the domain, e.g. into [H XP] if the relevant module
                # does not recognize H.
                if self.out_of_domain(node.left_const, space):
                    return True

    def H_over_H_condition(self, head, intervention_feature_set, ps):
        if ps.head() != head and head.features & intervention_feature_set:
            return True

    def out_of_domain(self, head, space):
        if space == 'QND':
            if not self.quantifiers_numerals_denotations_module.recognize(head):
                return True
        else:
            # All other spaces remain unimplemented, hence search into anything else
            # than QND space will be terminated immediately
            return True

    def interpret_node(self, node, semantic_object):
        """
        Implements one step in the compositional interpretation process.

        Applies contents of the [node] to the [semantic_object], the
        latter which is a dict object from a semantic space (determined before this
        function is called). The function is applied to every node accessed by
        minimal search.
        """
        if node.is_complex():
            if node.left_const.is_complex():
                semantic_object = self.add_criteria_from_phrase(semantic_object, node.left_const)
            if node.right_const.is_complex() and node.right_const.adjunct:
                semantic_object = self.add_criteria_from_phrase(semantic_object, node.right_const)
            if node.left_const.is_primitive():
                semantic_object = self.apply_criterion_function(semantic_object, node.left_const)
        elif node.is_primitive():
            semantic_object = self.apply_criterion_function(semantic_object, node)
        return semantic_object

    def add_criteria_from_phrase(self, semantic_object, constituent):
        """
        Adds criteria into [semantic object] from a left or right (adjunct) phrase.
        Currently adds the phrases as strings, but later we will add the objects.
        """
        if 'Criteria' in semantic_object:
            semantic_object['Criteria'].add(f'{constituent}')
        else:
            semantic_object['Criteria'] = {f'{constituent}'}
        log(f'Added criteria {constituent}...')
        return semantic_object

    def apply_criterion_function(self, semantic_object, left_head):
        """
        Takes a primitive left head [left_head] as input and applies all
        criterion functions to the semantic object triggered by features of the head.
        """
        semantic_object = self.quantifiers_numerals_denotations_module.apply_criteria(semantic_object, left_head)
        return semantic_object

    def wire_semantics(self, ps):
        """
        Wires [ps] recursively. Only primitive constituents are wired.
        Creates an IDX feature for the constituent and the corresponding object into the semantic space.
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
        Wires semantics for [ps] if and only if referential and no prior wiring exists
        """
        if self.get_referential_index_tuple(ps) == (None, None) and ps.head().referential():
            self.wire(ps)

    def wire(self, ps):
        """
        Adds referential index to the expression and updates the discourse inventory
        Updating is mediated by separate cognitive systems depending on the label of
        the incoming structure [ps]
        """
        log(f'Computing semantics for {ps}')

        # Add referential index to the expression
        self.add_referential_index(ps)

        # Update discourse inventories (all semantic spaces)
        self.update_discourse_inventories(ps)

        # Register the changes inside the pragmatic pathway
        self.pragmatic_pathway.allocate_attention_resources(self.get_referential_index_tuple(ps))

        log('Done.')

    def update_discourse_inventories(self, ps):
        if 'QND' == self.get_index_space(ps):
            self.quantifiers_numerals_denotations_module.set_denotation(ps)
        else:
            self.set_default_denotation(ps)
            log(f'Added {ps} to global discourse inventory.')

    def default_criteria(self, ps):
        default_criteria = {'Referring constituent': f'{ps}',
                    'Reference': f'{ps.illustrate()}',
                    'Semantic space': 'GLOBAL',
                    'Semantic type': self.get_semantic_types(ps)}
        return default_criteria

    def set_default_denotation(self, ps):
        self.global_cognition.create_object(self.default_criteria(ps))

    def get_semantic_types(self, ps):
        semantic_types = set()
        for f in ps.head().features:
            if f in self.semantic_type:
                semantic_types.add(self.semantic_type[f])
        return semantic_types

    def add_referential_index(self, ps):
        """
        Wires constituent ps (its head) with an object inside the semantic space. THis module will later
        include the binding theory.
        """
        space = self.determine_index_space(ps)
        idx_feature = 'IDX:' + str(self.global_cognition.get_index_counter()) + ',' + space
        log(f'({idx_feature})...')
        ps.head().features.add(idx_feature)

    def determine_index_space(self, ps):
        if 'D' in ps.head().features:
            return 'QND'
        else:
            return 'GLOBAL'

    def get_index_space(self, ps):
        """
        Determines which semantic space will be linked by the referential index.
        Currently DI is default behavior
        """
        idx, space = self.get_referential_index_tuple(ps)
        if idx:
            if space:
                return space
            else:
                return 'GLOBAL'
        return ''

    def get_referential_index_tuple(self, ps):
        """
        Returns a referential index tuple (idx, space) of some phrase pointing to objects
        in some semantic space, (None, None) if none exists
        IDX = index feature in the semantic space
        SPACE = semantic space
        """
        idx_set = {self.unpack_index_string(f) for f in ps.head().features if f[:3] == 'IDX'}
        if idx_set:
            return list(idx_set)[0]
        else:
            return None, None

    def get_semantic_object(self, idx_tuple):
        (idx, space) = idx_tuple
        if space == 'QND':
            return self.quantifiers_numerals_denotations_module.get_object(idx)
        else:
            return self.global_cognition.get_object(idx)

    def unpack_index_string(self, feature_string):
        # If the feature is not an index feature, return nothing
        if feature_string[:3] != 'IDX':
            return None, None
        # If semantic space has not been determined, assume default
        if ',' not in feature_string:
            return feature_string[4:], 'GLOBAL'
        idx, space = feature_string[4:].split(',')
        return idx, space

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
        """
        Interprets argument tailing. ps = head with tail feature, tailed_head = the head that is being tailed.
        """
        if tailed_head and 'ASP:BOUNDED' in tailed_head.features:
            if 'PAR' in ps.features and not ps.in_scope_of({'POL:NEG'}):
                self.semantic_interpretation['Aspect'].append('Aspectually anomalous')
            else:
                self.semantic_interpretation['Aspect'].append('Aspectually bounded')

    def get_tailed_head(self, ps, tail_set):
        for head in ps.feature_vector()[1:]:
            if head.match_features(tail_set) == 'complete match':
                return head

    def update_semantics_for_attribute(self, sem_object, attribute, value):
        """
        Updates attribute:value for semantic object [sem_object]
        """
        criteria = {attribute: value}
        (idx, space) = sem_object
        if not idx:
            return
        if space == 'QND':
            self.quantifiers_numerals_denotations_module.update_discourse_inventory_compositionally(idx, criteria)
        else:
            self.global_cognition.update_discourse_inventory(idx, criteria)

    def is_operator(self, idx_tuple):
        object_dict = self.get_semantic_object(idx_tuple)
        if 'Operator' in object_dict and object_dict['Operator']:
            return True

    def all_inventories(self):
        dict = {}
        dict.update(self.global_cognition.discourse_inventory)
        dict.update(self.quantifiers_numerals_denotations_module.discourse_inventory)
        return dict

    def has_denotation(self, ps):
        if self.get_referential_index_tuple(ps) != (None, None):
            return True