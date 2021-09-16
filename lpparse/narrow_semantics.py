from support import log
from SEM_operators_variables import OperatorVariableModule
from SEM_pragmatic_pathway import Discourse
from SEM_LF_recovery import LF_Recovery
from SEM_quantifiers_numerals_denotations import QuantifiersNumeralsDenotations
from SEM_predicates_relations_events import PredicatesRelationsEvents
from global_cognition import GlobalCognition

class NarrowSemantics:
    """
    Narrow semantics is responsible for creating semantic interpretation for isolated sentences. The result of
    narrow semantic interpretation will be combined with broad semantic interpretation that takes context
    into account. It mediates between the syntactic pathway and global cognition. Thus, narrow semantics
    can be thought of as a wrapper of the syntactic pathway.

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
        self.predicates_relations_events_module = PredicatesRelationsEvents(self)
        self.global_cognition = GlobalCognition(self)

        # Discourse inventory maintained by narrow semantics hosting primitive objects
        self.semantic_interpretation = {}
        self.semantic_interpretation_failed = False

        # Provides unique numerical identifiers to all objects created inside any semantic space
        self.controlling_parsing_process = controlling_parsing_process
        self.phi_interpretation_failed = False

        # Branches processing based on semantic space
        self.query = \
            {'GLOBAL': {'Remove': self.global_cognition.remove_object,
                        'Project': self.global_cognition.project_GLOBAL_entry_into_inventory,
                        'Get': self.global_cognition.get_object,
                        'Update': self.global_cognition.update_discourse_inventory,
                        'Present': self.global_cognition.present},
             'QND': {'Remove': self.quantifiers_numerals_denotations_module.remove_object,
                     'Project': self.quantifiers_numerals_denotations_module.project_QND_entry_into_inventory,
                     'Get': self.quantifiers_numerals_denotations_module.get_object,
                     'Update': self.quantifiers_numerals_denotations_module.update_discourse_inventory,
                     'Accept': self.quantifiers_numerals_denotations_module.accept,
                     'Present': self.quantifiers_numerals_denotations_module.present},
             'PRE': {'Remove': self.predicates_relations_events_module.remove_object,
                     'Project': self.predicates_relations_events_module.project_PRE_entry_into_inventory,
                     'Get': self.predicates_relations_events_module.get_object,
                     'Update': self.predicates_relations_events_module.update_discourse_inventory,
                     'Accept': self.predicates_relations_events_module.accept,
                     'Present': self.predicates_relations_events_module.present}}

        # Grammatical features mapped into semantic feature types
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
                              'P': '§Relator',
                              'v': '§Valency',
                              'T': '§Tense',
                              'ASP': '§Eventive',
                              'ARG': '§Unsaturated',
                              'SEM:internal': '§Internal',
                              'SEM:external': '§External',
                              'FORCE': '§Proposition'
                              }

    def initialize(self):
        self.pragmatic_pathway.initialize()
        self.quantifiers_numerals_denotations_module.reset()
        self.predicates_relations_events_module.reset()
        self.semantic_interpretation_failed = False
        self.semantic_interpretation = {'Recovery': [],
                                        'Aspect': [],
                                        'DIS-features': [],
                                        'Operator bindings': [],
                                        'Semantic space': '',
                                        'Speaker attitude': [],
                                        'Information structure': {},
                                        'Assignments': []}

    def global_interpretation(self, ps):
        """
        Wrapper function for recursive semantic interpretation. This interpretation is applied to
        a completed LF interface object, thus it corresponds to a global semantic interpretation. It will
        interpret all primitive heads and performs assignment evaluation.
        """
        log(f'\n\t\tTransferring {ps} into the conceptual-intentional system...')
        # Reset the system for new interpretation
        self.reset_for_new_interpretation()

        # Create local interpretations for lexical elements
        self.interpret_(ps)

        # Create global assignments (possible denotations)
        self.quantifiers_numerals_denotations_module.reconstruct_assignments(ps)

        return self.semantic_interpretation_failed

    def reset_for_new_interpretation(self):
        """
        Resets everything before semantic interpretation is attempted.
        """
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
                                        'Assignments': [],
                                        'Information structure': {'Marked topics': None, 'Neutral gradient': None,
                                                                  'Marked focus': None}}

    def interpret_(self, ps):
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
            self.quantifiers_numerals_denotations_module.detect_phi_conflicts(ps)
            self.operator_variable_module.bind_operator(ps, self.semantic_interpretation)
            self.pragmatic_pathway.reconstruct_discourse(ps, self.semantic_interpretation)
            self.interpret_tail_features(ps)
            if self.failure():
                return
        else:
            # Recursion
            if not ps.left_const.find_me_elsewhere:
                self.interpret_(ps.left_const)
            if not ps.right_const.find_me_elsewhere:
                self.interpret_(ps.right_const)

    def failure(self):
        """
        Returns True if something went wrong during semantic interpretation.
        """
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
        if self.controlling_parsing_process.first_solution_found:
            return
        for idx, space in self.get_referential_index_tuples(referring_head):
            self.query[space]['Remove'](idx)
            log(f'Removing [{idx}] of \"{referring_head.illustrate()}\" from {space}...')

    def compositional_semantics_update(self, ps):
        """
        Updates information concerning referential relations inside [ps] recursively. This is called for XP when
        (1) [XP, w] is created during parsing or (2) XP is completed. The function does not enter
        complex left branches but does update right adjuncts. The idea is that under configuration {X YP},
        YP is understood as a modifier for X.

        The function searches through [ps] and finds any [X YP] or [YP X] where X has
        referential index, then updates the reference for X on the basis of YP. Updating is done by
        calling compositional_interpretation() which examines the relevant domain inside
        ps.max() by minimal search and applies criterion functions and adds phrasal criteria (if any).

        There is much that remains to be done, but this requires systematic empirical study and data both which
        are unavailable.
        """
        if self.controlling_parsing_process.first_solution_found:
            return
        if ps.is_complex():
            # [X, YP], X referential, interpret X (which will examine YP)
            if ps.left_const.is_primitive() and self.has_referential_index(ps.left_const):
                self.compositional_interpretation(ps.left_const)
            # [YP, X], X referential, interpret X (which will examine YP)
            if ps.right_const.is_primitive() and self.has_referential_index(ps.right_const):
                self.compositional_interpretation(ps.right_const)
            # [XP, YP], recursive clause
            else:
                # Recursion
                # [XP, <YP>]
                if ps.right_const.adjunct:
                    # Update both branches
                    self.compositional_semantics_update(ps.right_const)
                    self.compositional_semantics_update(ps.left_const)
                else:
                    # [XP YP], update YP (ignore left branch XP)
                    self.compositional_semantics_update(ps.right_const)

    def compositional_interpretation(self, ps):
        """
        Implements compositional interpretation on phrases that are headed by elements that are referential
        (i.e., have referential index) and picks up objects from the global space, directly or indirectly. This
        is performed during compositional semantics update dynamically and incrementally throughout the
        derivation.

        """
        # Process  all referential indexes
        for idx, space in self.get_referential_index_tuples(ps):
            log(f'Interpreting {ps.max()}({space}, {idx})...')

            semantic_object = self.query[space]['Get'](idx)
            semantic_object['Reference'] = self.query[space]['Present'](ps)
            intervention_feature_set = ps.head().major_category_features()

            # ----- minimal search ----------------------------------------------------
            for node in ps.max().minimal_search():
                # Determine if search should be terminated
                if self.termination_condition(node, intervention_feature_set, space, ps):
                    break
                # Update the semantic object by using information available at the node. This will
                # add information concerning all phrasal objects adjacent to the minimal search path.
                semantic_object.update(self.interpret_node(node, semantic_object))
            #---------------------------------------------------------------------------

            # Creates new object corresponding to the updated expression to the global semantic
            semantic_object['Denotations'] = [self.query['GLOBAL']['Project'](ps, semantic_object.copy())]

    def projects_referring_nominal_phrase(self, head):
        return head.features & {'D', 'φ'}

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
        """
        Returns True if (1) ps != head and (2) head does not have the intervention feature
        """
        if ps.head() != head and head.features & intervention_feature_set:
            return True

    def out_of_domain(self, head, space):
        if space == 'QND':
            return not self.query['QND']['Accept'](head)
        else:
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
        Currently adds the phrases as strings, but later we will add the objects. This function is therefore
        just a placeholder. The matter remains to be studied.
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
        Wires [ps] recursively. Only primitive constituents are wired. Called from complete processing and
        incrementally during lexical stream

        Creates an IDX feature for the constituent and the corresponding object into the semantic space.
        Travels on the right edge and wires all referential heads that have not been wired already.
        Right adjuncts are visited separately, after which the right edge travel continues.
        """
        if self.controlling_parsing_process.first_solution_found:
            return
        # [X Y]
        if ps.is_complex():
            # [X <YP>]
            if ps.right_const.adjunct:
                self.wire_semantics(ps.right_const) # Visit and wire externalized right adjuncts
                self.wire_semantics(ps.left_const)  # Continue from the right edge of the main structure
                self.try_wire_semantics(ps)
            self.wire_semantics(ps.right_const)
        # X (X is primitive)
        else:
            self.try_wire_semantics(ps)

    def try_wire_semantics(self, ps):
        """
        Wires semantics for [ps] if and only if
        (1) ps has no referential index AND
        (2) ps can be understood by one of the semantic modules inside narrow semantics (currently QND, PE)
        """
        if not self.has_referential_index(ps):
            if self.query['QND']['Accept'](ps) or self.query['PRE']['Accept'](ps):
                self.wire(ps)

    def wire(self, ps):
        """
        Adds referential index to the expression and updates the discourse inventory
        Updating is mediated by separate cognitive systems depending on the label of
        the incoming structure [ps]
        """
        log(f'Computing semantics for {ps}')

        # Add referential indexes to the expression
        self.add_referential_indexes(ps)

        # Update discourse inventories (all semantic spaces)
        self.update_discourse_inventories(ps)

        # Register the changes inside the pragmatic pathway
        # This implements the early syntax-pragmatics interface
        if (None, None) != self.get_referential_index_tuples(ps, 'QND'):
            self.pragmatic_pathway.allocate_attention_resources(self.get_referential_index_tuples(ps, 'QND'))

        log('Done.')

    def update_discourse_inventories(self, ps):
        for idx, space in self.get_referential_index_tuples(ps):
            self.query[space]['Project'](ps, idx)

    def get_semantic_types(self, ps):
        return  {self.semantic_type[feature] for feature in ps.head().features if feature in self.semantic_type}

    def add_referential_indexes(self, ps):
        """
        Wires constituent ps (its head) with an object inside the semantic space.
        """
        for space in self.determine_index_spaces(ps):
            idx_feature = 'IDX:' + str(self.global_cognition.consume_index()) + ',' + space
            log(f'({idx_feature}) ')
            ps.head().features.add(idx_feature)

            # This a simple feature which represents the fact that this head has established a referential
            # link to QND space
            if space == 'QND':
                ps.head().features.add('REF')

    def determine_index_spaces(self, ps):
        """
        Determines the type of index space this element will be mapped. Currently QND, PRE and GLOBAL.
        """
        space_list = []
        for space in ['PRE', 'QND']:
            if self.query[space]['Accept'](ps.head()):
                space_list.append(space)

        # Default value if nothing else is accepted
        if not space_list:
            space_list = ['GLOBAL']

        return space_list

    def delete_pro(self, head):
        if self.exists(head, 'QND') and not self.projects_referring_nominal_phrase(head):
            idx, space = self.get_referential_index_tuples(head, 'QND')
            self.query[space]['Remove'](idx)
            self.delete_referential_index_tuple(head, idx, space)

    def delete_referential_index_tuple(self, head, idx, space):
        head.features.discard('IDX:'+idx+','+space)
        head.features.discard('REF')

    def get_referential_index(self, ps, space):
        idx_tuples_list = [tuple(f[4:].split(',')) for f in ps.head().features if f[:3] == 'IDX']
        return [idx for idx, space_ in idx_tuples_list if space_ == space][0]

    def exists(self, head, space):
        for idx, space_ in self.get_referential_index_tuples(head):
            if space == space_:
                return True

    def get_referential_index_tuples(self, ps, space_query=''):
        """
        If space query is empty, returns the list of referential index tuple (idx, space).
        Otherwise returns one referential index from that space (there should be only 1 if space is defined)
        """
        idx_lst = [tuple(f[4:].split(',')) for f in ps.head().features if f[:3] == 'IDX']
        # Get all index tuples from the head
        if space_query == '':
            return idx_lst
        else:
            lst = [(idx, space) for idx, space in idx_lst if space == space_query]
            if lst:
                return lst[0]
            else:
                return None, None

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

    def update_semantics_for_attribute(self, idx, space, attribute, value):
        self.query[space]['Update'](idx, {attribute: value})

    def is_operator(self, idx_tuple):
        idx, space = idx_tuple
        object_dict = self.query[space]['Get'](idx)
        if 'Operator' in object_dict and object_dict['Operator']:
            return True

    def all_inventories(self):
        dict = {}
        dict.update(self.global_cognition.inventory)
        dict.update(self.quantifiers_numerals_denotations_module.inventory)
        dict.update(self.predicates_relations_events_module.inventory)
        return dict

    def has_referential_index(self, ps, space_query=''):
        for idx, space in self.get_referential_index_tuples(ps):
            if space_query == '':
                return True
            else:
                if space == space_query:
                    return True

    def default_criteria(self, ps, space):
        """
        Definition for default criteria applied to all objects in the QND space. Some of these fields exist
        for readability only.
        """
        return {'Referring constituent': f'{ps}',
                      'Reference': self.query[space]['Present'](ps),
                      'Semantic space': space,
                      'Semantic type': self.get_semantic_types(ps),
                      'Operator': self.operator_variable_module.is_operator(ps)
                      }