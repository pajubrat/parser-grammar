from support import log
from SEM_operators_variables import OperatorVariableModule
from SEM_pragmatic_pathway import Discourse
from SEM_control_and_thematic_roles import LF_Recovery
from SEM_quantifiers_numerals_denotations import QuantifiersNumeralsDenotations
from SEM_predicates_relations_events import PredicatesRelationsEvents
from global_cognition import GlobalCognition

class NarrowSemantics:
    def __init__(self, controlling_parsing_process):
        self.operator_variable_module = OperatorVariableModule(self)
        self.argument_recovery_module = LF_Recovery(controlling_parsing_process)
        self.quantifiers_numerals_denotations_module = QuantifiersNumeralsDenotations(self)
        self.pragmatic_pathway = Discourse(self)
        self.predicates_relations_events_module = PredicatesRelationsEvents(self)
        self.global_cognition = GlobalCognition(self)
        self.semantic_interpretation = {}
        self.semantic_interpretation_failed = False
        self.predicate_argument_dependencies = []
        self.brain_model = controlling_parsing_process
        self.phi_interpretation_failed = False
        self.query = \
            {'GLOBAL': {'Remove': self.global_cognition.remove_object,
                        'Project': self.global_cognition.project,
                        'Get': self.global_cognition.get_object,
                        'Update': self.global_cognition.update_discourse_inventory,
                        'Present': self.global_cognition.present},
             'QND': {'Remove': self.quantifiers_numerals_denotations_module.remove_object,
                     'Project': self.quantifiers_numerals_denotations_module.project,
                     'Get': self.quantifiers_numerals_denotations_module.get_object,
                     'Update': self.quantifiers_numerals_denotations_module.update_discourse_inventory,
                     'Accept': self.quantifiers_numerals_denotations_module.accept,
                     'Present': self.quantifiers_numerals_denotations_module.present},
             'PRE': {'Remove': self.predicates_relations_events_module.remove_object,
                     'Project': self.predicates_relations_events_module.project,
                     'Get': self.predicates_relations_events_module.get_object,
                     'Update': self.predicates_relations_events_module.update_discourse_inventory,
                     'Accept': self.predicates_relations_events_module.accept,
                     'Present': self.predicates_relations_events_module.present},
             'OP':  {'Remove': self.operator_variable_module.remove_object,
                     'Project': self.operator_variable_module.project,
                     'Get': self.operator_variable_module.get_object,
                     'Update': self.operator_variable_module.update,
                     'Accept': self.operator_variable_module.accept,
                     'Present': self.operator_variable_module.present}}

        self.semantic_spaces = ['PRE', 'QND', 'OP']

        self.semantic_type = {'T/fin':'§Proposition',
                              'D': '§Thing',
                              'φ': '§Thing',
                              'Q': '§Quantifier',
                              'Num': '§Quantity',
                              'Neg': '§Polarity',
                              'C/fin': '§Proposition',
                              'C': '§Proposition',
                              'N': '§Predicate',
                              'V': '§Predicate',
                              'A': '§Predicate',
                              'a': '§Predicate',
                              'Adv': '§Predicate',
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

        # This dictionary implements syntax-semantics interfaces as assumed in the multiple interface hypothesis
        self.access_interface = {}

    def initialize(self):
        self.access_interface = {}
        self.pragmatic_pathway.initialize()
        self.quantifiers_numerals_denotations_module.reset()
        self.predicates_relations_events_module.reset()
        self.semantic_interpretation_failed = False
        self.predicate_argument_dependencies = []
        self.semantic_interpretation = {'Recovery': [],
                                        'Aspect': [],
                                        'DIS-features': [],
                                        'Operator bindings': [],
                                        'Semantic space': '',
                                        'Speaker attitude': [],
                                        'Information structure': {},
                                        'Assignments': []}

    def reset_for_new_interpretation(self):
        self.semantic_interpretation_failed = False
        self.phi_interpretation_failed = False
        self.operator_variable_module.interpretation_failed = False
        self.pragmatic_pathway.interpretation_failed = False
        self.argument_recovery_module.interpretation_failed = False
        self.semantic_interpretation = {'Recovery': [],
                                        'Aspect': [],
                                        'DIS-features': [],
                                        'Operator bindings': [],
                                        'Semantic space': '',
                                        'Speaker attitude': [],
                                        'Assignments': [],
                                        'Information structure': {'Marked topics': None, 'Neutral gradient': None,
                                                                  'Marked focus': None}}

    def postsyntactic_semantic_interpretation(self, root_node):
        log(f'\n\t\tInterpreting {root_node.head()}P globally: ')
        self.reset_for_new_interpretation()
        self.interpret_(root_node)
        self.quantifiers_numerals_denotations_module.reconstruct_assignments(root_node)
        self.pragmatic_pathway.calculate_information_structure(root_node, self.semantic_interpretation)
        self.document_interface_content_for_user()
        return not self.semantic_interpretation_failed

    def interpret_(self, ps):
        if ps.is_primitive():
            if ps.phi_needs_valuation():
                self.semantic_interpretation['Recovery'].append(self.argument_recovery_module.recover_arguments(ps))
            self.quantifiers_numerals_denotations_module.detect_phi_conflicts(ps)
            self.interpret_tail_features(ps)
            self.inventory_projection(ps)
            self.operator_variable_module.bind_operator(ps, self.semantic_interpretation)
            self.pragmatic_pathway.interpret_discourse_features(ps, self.semantic_interpretation)
            if self.failure():
                return
        else:
            if not ps.left_const.find_me_elsewhere:
                self.interpret_(ps.left_const)
            if not ps.right_const.find_me_elsewhere:
                self.interpret_(ps.right_const)

    def inventory_projection(self, ps):
        def preconditions(ps):
            return not self.brain_model.first_solution_found and \
                   not ps.find_me_elsewhere and \
                   'BLOCK_NS' not in ps.features

        if preconditions(ps):
            for space in self.semantic_spaces:
                if self.query[space]['Accept'](ps.head()):
                    idx = str(self.global_cognition.consume_index())
                    ps.head().features.add('IDX:' + idx + ',' + space)
                    log('\n\t\t\tProject ')
                    self.query[space]['Project'](ps, idx)
                    self.query[space]['Denotation'] = self.query['GLOBAL']['Project'](ps, self.transform_for_global(self.query[space]['Get'](idx)))

                    # For heuristic purposes so that referential arguments are recognized by BT
                    if space == 'QND':
                        ps.head().features.add('REF')

    def transform_for_global(self, semantic_object):
        filtered_object = semantic_object.copy()
        filtered_object.pop('Phi-set', None)
        return filtered_object

    def document_interface_content_for_user(self):
        self.semantic_interpretation.update(self.access_interface)

    def failure(self):
        if self.argument_recovery_module.interpretation_failed or \
                self.phi_interpretation_failed or \
                self.operator_variable_module.interpretation_failed or \
                self.pragmatic_pathway.interpretation_failed:
            self.semantic_interpretation_failed = True
            return True

    def get_referential_index(self, ps, space):
        idx_tuples_list = [tuple(f[4:].split(',')) for f in ps.head().features if f[:3] == 'IDX']
        return [idx for idx, space_ in idx_tuples_list if space_ == space][0]

    def exists(self, head, space):
        for idx, space_ in self.get_referential_index_tuples(head):
            if space == space_:
                return True

    def get_referential_index_tuples(self, ps, space_query=''):
        idx_lst = [tuple(f[4:].split(',')) for f in ps.head().features if f[:3] == 'IDX']
        if space_query == '':
            return idx_lst
        else:
            lst = [(idx, space) for idx, space in idx_lst if space == space_query]
            if lst:
                return lst[0]
            else:
                return None, None

    def interpret_tail_features(self, ps):
        def in_scope_of(ps, feature_set):
            return next((const for const in ps.working_memory_path() if feature_set.issubset(const.features)), None)

        def get_tailed_head(ps, tail_set):
            return next((const for const in ps.working_memory_path() if const.is_primitive() and const.match_features(tail_set).match_occurred and const.match_features(tail_set).outcome), None)

        def interpret_argument_tailing(ps, tailed_head):
            if tailed_head:
                if 'ASP:BOUNDED' in tailed_head.features:
                    if 'PAR' in ps.features and not in_scope_of(ps, {'POL:NEG'}):
                        self.semantic_interpretation['Aspect'].append('Aspectually anomalous')
                    else:
                        self.semantic_interpretation['Aspect'].append('Aspectually bounded')

        # ------------ main function ----------------------------------- #
        for tail_set in ps.get_tail_sets():
            interpret_argument_tailing(ps, get_tailed_head(ps, tail_set))
        # -------------------------------------------------------------- #

    def all_inventories(self):
        dict = {}
        dict.update(self.global_cognition.inventory)
        dict.update(self.quantifiers_numerals_denotations_module.inventory)
        dict.update(self.predicates_relations_events_module.inventory)
        dict.update(self.operator_variable_module.inventory)
        return dict

    def has_referential_index(self, ps, space_query=''):
        for idx, space in self.get_referential_index_tuples(ps):
            if space_query == '':
                return True
            else:
                if space == space_query:
                    return True

    def default_criteria(self, ps, space):
        def get_semantic_types(ps):
            return {self.semantic_type[feature] for feature in ps.head().features if feature in self.semantic_type}

        return {'Referring constituent': f'{ps}',
                      'Reference': self.query[space]['Present'](ps),
                      'Semantic space': space,
                      'Semantic type': get_semantic_types(ps),
                      'Operator': self.operator_variable_module.is_operator(ps)
                      }
