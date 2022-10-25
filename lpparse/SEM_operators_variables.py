
from support import log
from collections import namedtuple

BindingDependency = namedtuple('BindingDependency', ['OperatorHead', 'ScopeMarker', 'Overt'])


class OperatorVariableModule:
    def __init__(self, narrow_semantics):
        self.narrow_semantics = narrow_semantics
        self.interpretation_failed = False
        self.operator_interpretation = {'OP:WH': 'Interrogative',
                                         'OP:TOP': 'Topic',
                                         'OP:FAM': 'Familiarity topic',
                                         'OP:FOC': 'Contrastive focus',
                                         'OP:POL': 'Polarity topic',
                                         'OP:Q': 'Yes/no interrogative',
                                         'OP:REL': 'Relativization',
                                         'OP:C/OP': 'Generic operator'}
        self.inventory = {}

    def bind_operator(self, head, semantic_interpretation):
        for operator_feature in (f for f in head.features if not self.scope_marker(head) and self.is_operator_feature(f)):
            binding = self.interpret_covert_scope(self.find_overt_scope(head, operator_feature))
            self.interpret_operator_variable_chain(binding, operator_feature, semantic_interpretation)

    @staticmethod
    def find_overt_scope(head, operator_feature):
        return next(({'Head': head, 'Scope': scope, 'Overt': True} for scope in head.working_memory_path() if
                     {operator_feature, 'Fin'}.issubset(scope.features)), {'Head': head, 'Scope': None, 'Overt': False})

    @staticmethod
    def interpret_covert_scope(binding):
        if not binding['Scope'] and '!SCOPE' not in binding['Head'].features:
            return next(({'Head': binding['Head'], 'Scope': scope, 'Overt': False}
                         for scope in binding['Head'].working_memory_path() if
                         scope.finite_left_periphery()),
                        {'Head': binding['Head'], 'Scope': None, 'Overt': False})
        return binding

    def interpret_operator_variable_chain(self, binding, operator_feature, semantic_interpretation):
        if binding['Scope']:
            if binding['Overt']:
                semantic_interpretation['Operator bindings'].append(f'Operator {binding["Head"].illustrate()}({operator_feature}) bound by {binding["Scope"].illustrate()}({operator_feature})')
            else:
                semantic_interpretation['Operator bindings'].append(f'Operator {binding["Head"].illustrate()}({operator_feature}) bound by {binding["Scope"].illustrate()} by default. ')
            self.interpret_operator_at_lexical_item(binding, operator_feature, semantic_interpretation)
            self.project_operator_objects_into_discourse_inventory(binding)
        else:
            log(f'\n\t\t\t{binding["Head"].illustrate()} with {operator_feature} is not bound by an operator. ')
            if '!SCOPE' in binding["Head"].features:
                log(f'Interpretation fails and the derivation crashes. ')
                self.interpretation_failed = True
            else:
                semantic_interpretation['Operator bindings'].append(f'Operator {binding["Head"].illustrate()}[{operator_feature}] bound by speaker.')

    def project_operator_objects_into_discourse_inventory(self, binding):
        idx, space = self.narrow_semantics.get_referential_index_tuples(binding["Head"], 'OP')
        if idx:
            self.narrow_semantics.query['OP']['Get'](idx)['Bound by'] = binding["Head"]

    @staticmethod
    def scope_marker(head):
        return {'C', 'C/fin', 'OP:_'} & head.features

    def interpret_operator_at_lexical_item(self, binding, operator_feature, semantic_interpretation):
        log(f'\n\t\t\tInterpreting [{operator_feature}] at ')
        head_chain = binding["Head"].find_occurrences_from(self.narrow_semantics.access_interface['spellout structure'])
        log(f'{head_chain[0].illustrate()}. ')
        if self.narrow_semantics.is_concept(head_chain[0]):
            log('Interpretation successful.')
            if 'Predicates targeted by operator interpretation' not in semantic_interpretation:
                semantic_interpretation['Predicates targeted by operator interpretation'] = [f'[{operator_feature}] at {head_chain[0]}']
            else:
                semantic_interpretation['Predicates targeted by operator interpretation'].append(f'[{operator_feature}] at {head_chain[0]}')
        else:
            log('Not enough lexical content. ')

        if head_chain[0].finite():
            log('Verum focus/polarity question interpretation. ')
            semantic_interpretation['Verum focus/polarity question interpretation'] = True

    def is_operator(self, head):
        return {f for f in head.features if self.is_operator_feature(f)}

    @staticmethod
    def is_operator_feature(f):
        return f[:3] == 'OP:' and f[-1] != '_'

    @staticmethod
    def is_feature_in_operator_system(feature):
        return feature[:2] == 'OP' and feature[-1] != '_'

    def get_operator_features(self, features):
        return {f for f in features if self.is_feature_in_operator_system(f)}

    def scan_criterial_features(self, ps):
        # Note: we only take the first operator
        set_ = set()
        if ps.left_const and not ps.left_const.find_me_elsewhere:
            set_ = self.scan_criterial_features(ps.left_const)
        if not set_ and ps.right_const and not ps.right_const.find_me_elsewhere and not {'T/fin', 'C'} & ps.right_const.head().features:
            set_ = self.scan_criterial_features(ps.right_const)
        if not set_ and ps.is_primitive():
            set_ = self.get_operator_features(ps.features)
        return set_


    def get_object(self, idx):
        return self.inventory[idx]

    @staticmethod
    def accept(ps):
        return False
        # return {f for f in ps.head().features if f[:3] == 'OP:'}

    def update(self, idx, criteria):
        self.inventory[idx].update(criteria)

    def project(self, ps, idx):
        self.inventory[idx] = self.narrow_semantics.default_criteria(ps, 'OP')
        self.inventory[idx]['Semantic type'].add('§Operator')
        log(f'{ps.max().illustrate()}: ({idx}, OP)')

    def remove_object(self, idx):
        self.inventory.pop(idx, None)

    def present(self, head):
        return f'{head.max().illustrate()}'
