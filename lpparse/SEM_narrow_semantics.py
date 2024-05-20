from support import log
from SEM_operators_variables import OperatorVariableModule
from SEM_pragmatic_pathway import Discourse
from SEM_quantifiers_numerals_denotations import QuantifiersNumeralsDenotations
from SEM_predicates_relations_events import PredicatesRelationsEvents
from SEM_thematic_roles import ThematicRoles
from SEM_predicates import Predicates
from global_cognition import GlobalCognition

class NarrowSemantics:
    def __init__(self, speaker_model):
        self.operator_variable_module = OperatorVariableModule(speaker_model)
        self.thematic_roles_module = ThematicRoles()
        self.quantifiers_numerals_denotations_module = QuantifiersNumeralsDenotations(self)
        self.pragmatic_pathway = Discourse(self)
        self.predicates_relations_events_module = PredicatesRelationsEvents(self)
        self.global_cognition = GlobalCognition(self)
        self.predicates = Predicates()
        self.semantic_interpretation_failed = False
        self.speaker_model = speaker_model
        self.phi_interpretation_failed = False
        self.semantic_action = \
            {'GLOBAL': {'Remove': self.global_cognition.remove_object,
                        'Project': self.global_cognition.project,
                        'Get': self.global_cognition.get_object,
                        'Update': self.global_cognition.update_discourse_inventory,
                        'Presentation': self.global_cognition.present},
             'QND': {'Remove': self.quantifiers_numerals_denotations_module.remove_object,
                     'Project': self.quantifiers_numerals_denotations_module.project,
                     'Get': self.quantifiers_numerals_denotations_module.get_object,
                     'Update': self.quantifiers_numerals_denotations_module.update_discourse_inventory,
                     'Accept': self.quantifiers_numerals_denotations_module.accept,
                     'Presentation': self.quantifiers_numerals_denotations_module.object_presentation},
             'PRE': {'Remove': self.predicates_relations_events_module.remove_object,
                     'Project': self.predicates_relations_events_module.project,
                     'Get': self.predicates_relations_events_module.get_object,
                     'Update': self.predicates_relations_events_module.update_discourse_inventory,
                     'Accept': self.predicates_relations_events_module.accept,
                     'Presentation': self.predicates_relations_events_module.present},
             'OP':  {'Remove': self.operator_variable_module.remove_object,
                     'Project': self.operator_variable_module.project,
                     'Get': self.operator_variable_module.get_object,
                     'Update': self.operator_variable_module.update,
                     'Accept': self.operator_variable_module.accept,
                     'Presentation': self.operator_variable_module.present}}

        self.semantic_spaces = ['QND', 'PRE']

        self.semantic_type = {'T/fin':'§Event',
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
                              'T': '§T-Event',
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

    def reset_for_new_interpretation(self):
        self.semantic_interpretation_failed = False
        self.phi_interpretation_failed = False
        self.predicates.operation_failed = False
        self.thematic_roles_module.failure = False
        self.operator_variable_module.interpretation_failed = False
        self.pragmatic_pathway.interpretation_failed = False

    def postsyntactic_semantic_interpretation(self, ps):
        self.reset_for_new_interpretation()
        self.interpret_(ps)
        if self.speaker_model.settings.retrieve('general_parameter_project_objects', True) and not self.speaker_model.results.first_solution_found:
            self.inventory_projection(ps)
        # Assignments
        if self.speaker_model.settings.retrieve('general_parameter_calculate_assignments', False) and not self.speaker_model.results.first_solution_found:
            self.speaker_model.results.store_semantic_interpretation('Assignments', self.quantifiers_numerals_denotations_module.reconstruct_assignments(ps))
        # Information structure
        if self.speaker_model.settings.retrieve('general_parameter_calculate_pragmatics', False) and ps.finite():
            self.speaker_model.results.store_semantic_interpretation('Information structure', self.pragmatic_pathway.calculate_information_structure(ps))
        # Speaker attitude
        self.speaker_model.results.store_semantic_interpretation('Speaker attitude', self.pragmatic_pathway.calculate_speaker_attitude(ps))
        # Project objects into ontology and narrow semantics

        return not self.semantic_interpretation_failed

    def interpret_(self, X):
        if not X.copied:
            if X.zero_level():
                # Thematic roles
                if self.speaker_model.settings.retrieve('general_parameter_calculate_thematic_roles', True) and X.theta_predicate():
                    self.speaker_model.results.store_semantic_interpretation('Thematic roles', self.thematic_roles_module.reconstruct(X))
                # Argument-predicate pairs
                if self.speaker_model.settings.retrieve('general_parameter_calculate_predicates', True) and X.check_some({'Φ', 'Φ*'}):
                    self.speaker_model.results.store_semantic_interpretation('Predicates', self.predicates.reconstruct(X))
                    if self.speaker_model.settings.retrieve('UG_parameter_Agree', 'revised') == 'standard':
                        self.predicates.operation_failed = False
                if X.indexed_argument():
                    self.speaker_model.results.store_semantic_interpretation('Indexing by Agree', self.predicates.reconstruct_agreement(X))
                self.quantifiers_numerals_denotations_module.detect_phi_conflicts(X)
                self.interpret_tail_features(X)
                self.speaker_model.results.store_semantic_interpretation('Operator bindings', self.operator_variable_module.bind_operator(X))
                self.speaker_model.results.store_semantic_interpretation('DIS-features', self.pragmatic_pathway.interpret_discourse_features(X))
                if self.failure():
                    return
            else:
                self.interpret_(X.left())
                self.interpret_(X.right())

    def inventory_projection(self, X):
        for space in self.semantic_spaces:
            self.inventory_projection_(X, space)

    def inventory_projection_(self, X, space):
        if not X.copied:
            if X.complex():
                self.inventory_projection_(X.left(), space)
                self.inventory_projection_(X.right(), space)
            else:
                    if self.semantic_action[space]['Accept'](X):
                        idx = str(self.global_cognition.consume_index())
                        X.features.add(f'IDX:{idx},{space}')
                        new_semantic_object_dict = self.semantic_action[space]['Project'](X, idx)
                        global_idx = self.semantic_action['GLOBAL']['Project'](X, new_semantic_object_dict.copy())
                        self.semantic_action[space]['Update'](idx, {'Denotation': global_idx})

                        # For heuristic purposes so that referential arguments are recognized by BT
                        if space == 'QND':
                            X.head().features.add('REF')

    def failure(self):
        if self.phi_interpretation_failed or \
                self.operator_variable_module.interpretation_failed or \
                self.pragmatic_pathway.interpretation_failed or \
                self.predicates.operation_failed or \
                self.thematic_roles_module.failure:
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
        return [(idx, space) for idx, space in [tuple(f[4:].split(',')) for f in ps.head().features if f[:3] == 'IDX'] if space == space_query or space_query == '']

    def get_referential_index_tuple(self, ps, space_query):
        for idx, space in [tuple(f[4:].split(',')) for f in ps.head().features if f[:3] == 'IDX']:
            if space == space_query:
                return idx, space
        return None, None

    def interpret_tail_features(self, ps):
        def in_scope_of(ps, feature_set):
            return next((const for const in ps.upward_path() if feature_set.issubset(const.features)), None)

        def get_tailed_head(ps, tail_set):
            return next((const for const in ps.upward_path() if const.zero_level() and const.check_some(tail_set) and const.check(tail_set)), None)

        def interpret_argument_tailing(ps, tailed_head):
            if tailed_head:
                if 'ASP:BOUNDED' in tailed_head.features:
                    if 'PAR' in ps.features and not in_scope_of(ps, {'POL:NEG'}):
                        self.speaker_model.results.semantic_interpretation['Aspect'].append('Aspectually anomalous')
                    else:
                        self.speaker_model.results.semantic_interpretation['Aspect'].append('Aspectually bounded')

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
        for idx, space in self.get_referential_index_tuples(ps, space_query):
            if space_query == '':
                return True
            else:
                if space == space_query:
                    return True

    def default_attributes(self, X, space):
        return {'Referring constituent': f'{X}',
                'Reference': self.semantic_action[space]['Presentation'](X),
                'Semantic space': space,
                'Semantic type': {self.semantic_type[feature] for feature in X.head().features if feature in self.semantic_type},
                'Operator': self.operator_variable_module.is_operator(X)}
