from support import log
from SEM_operators_variables import OperatorVariableModule
from SEM_pragmatic_pathway import Discourse
from SEM_quantifiers_numerals_denotations import QuantifiersNumeralsDenotations
from SEM_predicates_relations_events import PredicatesRelationsEvents
from SEM_thematic_roles import ThematicRoles
from SEM_predicates import Predicates
from SEM_focus import Focus
from phrase_structure import some
from global_cognition import GlobalCognition

class NarrowSemantics:
    def __init__(self, speaker_model):
        self.operator_variable_module = OperatorVariableModule(speaker_model)
        self.thematic_roles_module = ThematicRoles()
        self.quantifiers_numerals_denotations = QuantifiersNumeralsDenotations(self)
        self.pragmatic_pathway = Discourse(self)
        self.predicates_relations_events = PredicatesRelationsEvents(self)
        self.global_cognition = GlobalCognition()
        self.focus = Focus(self)
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
             'QND': {'Remove': self.quantifiers_numerals_denotations.remove_object,
                     'Project': self.quantifiers_numerals_denotations.project,
                     'Get': self.quantifiers_numerals_denotations.get_object,
                     'Update': self.quantifiers_numerals_denotations.update_discourse_inventory,
                     'Accept': self.quantifiers_numerals_denotations.accept,
                     'Compatible': self.quantifiers_numerals_denotations.compatible,
                     'Presentation': self.quantifiers_numerals_denotations.object_presentation},
             'PRE': {'Remove': self.predicates_relations_events.remove_object,
                     'Project': self.predicates_relations_events.project,
                     'Get': self.predicates_relations_events.get_object,
                     'Update': self.predicates_relations_events.update_discourse_inventory,
                     'Accept': self.predicates_relations_events.accept,
                     'Presentation': self.predicates_relations_events.present}}

        self.semantic_spaces = ['QND', 'PRE', 'GLOBAL']

        self.semantic_type = {'T/fin': '§Event',
                              'D': '§Thing',
                              'φ': '§Thing',
                              'Q': '§Quantifier',
                              'Num': '§Quantity',
                              'Neg': '§Polarity',
                              'C/fin': '§Proposition',
                              'C': '§Proposition',
                              'N': '§Concept',
                              'V': '§Concept',
                              'A': '§Quality',
                              'a': '§Predicate',
                              'Adv': '§Predicate',
                              '0': '§Predicate',
                              'OP:REL': '§Predicate',
                              'P': '§Relator',
                              'v': '§Valency',
                              'T': '§T-Event',
                              'VA/inf': '§T-Event',
                              'A/inf': '§T-Event',
                              'ASP': '§Eventive',
                              'ARG': '§Unsaturated',
                              'SEM:internal': '§Internal',
                              'SEM:external': '§External',
                              'FORCE': '§Proposition'
                              }

    def initialize(self):
        self.pragmatic_pathway.initialize()
        self.quantifiers_numerals_denotations.reset()
        self.predicates_relations_events.reset()
        self.semantic_interpretation_failed = False

    def reset_for_new_interpretation(self):
        self.semantic_interpretation_failed = False
        self.phi_interpretation_failed = False
        self.predicates.operation_failed = False
        self.thematic_roles_module.failure = False
        self.operator_variable_module.interpretation_failed = False
        self.pragmatic_pathway.interpretation_failed = False
        self.quantifiers_numerals_denotations.reset()
        if not self.speaker_model.ongoing_conversation:
            self.global_cognition.reset()

    def postsyntactic_semantic_interpretation(self, X):
        log(f'\n----Semantic interpretation---------------------------------------------------------------------------\n')
        self.speaker_model.results.store_output_field('LF', f'{X}')

        # Inventory projection and ontology

        if self.speaker_model.settings.retrieve('general_parameter_project_objects', True):  # and not self.speaker_model.results.first_solution_found:
            self.inventory_projection(X)

        self.interpret_(X)

        # Assignments

        if self.speaker_model.settings.retrieve('general_parameter_calculate_assignments', True):
            n, weighted_assignments = self.quantifiers_numerals_denotations.reconstruct_assignments(X)
            self.speaker_model.results.store_output_field('Assignments', weighted_assignments)
            self.speaker_model.results.store_output_field('Number of assignments', str(n))

        # Information structure

        if self.speaker_model.settings.retrieve('general_parameter_calculate_pragmatics', False) and X.property('finite'):
            self.speaker_model.results.store_output_field('Information structure', self.pragmatic_pathway.calculate_information_structure(X))

        # Speaker attitude

        self.speaker_model.results.store_output_field('Speaker attitude', self.pragmatic_pathway.calculate_speaker_attitude(X))
        return not self.semantic_interpretation_failed

    def interpret_(self, X):
        if not X.copied:
            if X.zero_level():

                # Thematic roles

                if self.speaker_model.settings.retrieve('general_parameter_calculate_thematic_roles', True) and X.core('theta_predicate'):
                    self.speaker_model.results.store_output_field('Thematic roles', self.thematic_roles_module.reconstruct(X))

                # Argument-predicate pairs

                if self.speaker_model.settings.retrieve('general_parameter_calculate_predicates', True) and \
                        'Φ' in X.core and not X.core('referential') and not X.INT({'N'}):
                    self.speaker_model.results.store_output_field('Predicates', self.predicates.reconstruct(X))
                    if self.speaker_model.settings.retrieve('UG_parameter_Agree', 'revised') == 'standard':
                        self.predicates.operation_failed = False
                if X.indexed_argument():
                    self.speaker_model.results.store_output_field('Indexing by Agree', self.predicates.reconstruct_agreement(X))
                self.quantifiers_numerals_denotations.detect_phi_conflicts(X)
                self.interpret_tail_features(X)

                # Operator-variable constructions (scope reconstruction)

                if self.speaker_model.settings.retrieve('calculate_operator_bindings', True):
                    self.speaker_model.results.store_output_field('Operator bindings', self.operator_variable_module.bind_operator(X))

                # Discourse features (pragmatic module)

                if self.speaker_model.settings.retrieve('calculate_DIS_features', True):
                    self.speaker_model.results.store_output_field('Pragmatics', self.pragmatic_pathway.interpret_discourse_features(X))

                # Focus features (features with focus interpretation)

                if self.speaker_model.settings.retrieve('calculate_focus', True):
                    self.speaker_model.results.store_output_field('Focus', self.focus.reconstruct(X))
                if self.failure():
                    return
            else:
                self.interpret_(X.L())
                self.interpret_(X.R())

    def inventory_projection(self, X):
        log(f'\n\tObject projections:')
        for space in self.semantic_spaces:
            self.inventory_projection_(X, space)

    def inventory_projection_(self, X, space):
        if not X.copied and space != 'GLOBAL':
            if X.complex():
                self.inventory_projection_(X.L(), space)
                self.inventory_projection_(X.R(), space)
            else:
                if self.semantic_action[space]['Accept'](X):
                    idx = str(self.global_cognition.consume_index(space))
                    X.core.add_features({f'IDX:{idx},{space}'})
                    new_semantic_object_dict = self.semantic_action[space]['Project'](X, idx)
                    self.semantic_action['GLOBAL']['Project'](X, new_semantic_object_dict.copy())

                    # For heuristic purposes so that referential arguments are recognized by BT
                    if space == 'QND':
                        X.head().core.add_features({'REF'})

    def failure(self):
        if self.phi_interpretation_failed or \
                self.operator_variable_module.interpretation_failed or \
                self.pragmatic_pathway.interpretation_failed or \
                self.predicates.operation_failed or \
                self.thematic_roles_module.failure:
            self.semantic_interpretation_failed = True
            return True

    def interpret_tail_features(self, X):
        def in_scope_of(X, feature_set):
            return X.EXT(criteria=lambda x: feature_set.issubset(x.core.features()))

        def get_tailed_head(X, tail_set):
            return X.EXT(criteria=lambda x: x.zero_level() and x.INT(some(tail_set)) and x.INT(tail_set))

        def interpret_argument_tailing(ps, tailed_head):
            if tailed_head:
                if 'ASP:BOUNDED' in tailed_head.core.features():
                    if 'PAR' in ps.core.features() and not in_scope_of(ps, {'POL:NEG'}):
                        self.speaker_model.results.output_fields['Aspect'].append('Aspectually anomalous')
                    else:
                        self.speaker_model.results.output_fields['Aspect'].append('Aspectually bounded')

        # ------------ main function ----------------------------------- #
        for tail_set in X.get_tail_sets():
            interpret_argument_tailing(X, get_tailed_head(X, tail_set))
        # -------------------------------------------------------------- #

    def all_inventories(self):
        return [self.global_cognition.inventory, self.quantifiers_numerals_denotations.inventory, self.predicates_relations_events.inventory]

    def default_attributes(self, X, space):
        return {'Referring constituent': f'{X}',
                'Constituent': X,
                'Reference': self.semantic_action[space]['Presentation'](X),
                'Semantic space': space}
