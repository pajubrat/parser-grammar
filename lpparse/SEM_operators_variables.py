
from support import log
from collections import namedtuple

BindingDependency = namedtuple('BindingDependency', ['OperatorHead', 'ScopeMarker', 'Overt'])


class OperatorVariableModule:
    def __init__(self, speaker_model):
        self.interpretation_failed = False
        self.speaker_model = speaker_model
        self.bindings = []
        self.operator_interpretation = {'OP:WH': 'Interrogative',
                                         'OP:TOP': 'Topic',
                                         'OP:FAM': 'Familiarity topic',
                                         'OP:FOC': 'Contrastive focus',
                                         'OP:POL': 'Polarity topic',
                                         'OP:Q': 'Yes/no interrogative',
                                         'OP:REL': 'Relativization',
                                         'OP:C/OP': 'Generic operator'}
        self.inventory = {}

    def bind_operator(self, head):
        self.bindings = []
        for operator_feature in (f for f in head.features if not self.scope_marker(head) and self.is_operator_feature(f)):
            binding = self.interpret_covert_scope(self.find_overt_scope(head, operator_feature))
            self.interpret_operator_variable_chain(binding, operator_feature)
        return self.bindings

    @staticmethod
    def find_overt_scope(head, operator_feature):
        return next(({'Head': head, 'Scope': scope, 'Overt': True} for scope in head.upward_path() if
                     {operator_feature, 'Fin'}.issubset(scope.features)), {'Head': head, 'Scope': None, 'Overt': False})

    @staticmethod
    def interpret_covert_scope(binding):
        if not binding['Scope'] and '!SCOPE' not in binding['Head'].features:
            return next(({'Head': binding['Head'], 'Scope': scope, 'Overt': False}
                         for scope in binding['Head'].upward_path() if
                         scope.finite_left_periphery()),
                        {'Head': binding['Head'], 'Scope': None, 'Overt': False})
        return binding

    def interpret_operator_variable_chain(self, binding, operator_feature):
        if binding['Scope']:
            if binding['Overt']:
                self.bindings.append(f'Operator {binding["Head"].illustrate()}({operator_feature}) bound by {binding["Scope"].illustrate()}({operator_feature})')
            else:
                self.bindings.append(f'Operator {binding["Head"].illustrate()}({operator_feature}) bound by {binding["Scope"].illustrate()} by default. ')
            self.project_operator_objects_into_discourse_inventory(binding)
        else:
            log(f'\n\t\t\t{binding["Head"].illustrate()} with {operator_feature} is not bound by an operator. ')
            if 'SCOPE' in binding["Head"].features:
                log(f'Interpretation fails and the derivation crashes. ')
                self.interpretation_failed = True
            else:
                self.bindings.append(f'Operator {binding["Head"].illustrate()}[{operator_feature}] bound by speaker.')

    def project_operator_objects_into_discourse_inventory(self, binding):
        idx, space = self.speaker_model.narrow_semantics.get_referential_index_tuple(binding["Head"], 'OP')
        if idx:
            self.speaker_model.narrow_semantics.query['OP']['Get'](idx)['Bound by'] = binding["Head"]

    @staticmethod
    def scope_marker(head):
        return {'C', 'C/fin', 'OP:_'} & head.features

    def is_operator(self, head):
        return {f for f in head.features if self.is_operator_feature(f)}

    @staticmethod
    def is_operator_feature(f):
        return f[:3] == 'OP:' and f[-1] != '_'

    def get_object(self, idx):
        return self.inventory[idx]

    @staticmethod
    def accept(ps):
        return False

    def update(self, idx, criteria):
        self.inventory[idx].update(criteria)

    def project(self, ps, idx):
        self.inventory[idx] = self.speaker_model.narrow_semantics.default_criteria(ps, 'OP')
        self.inventory[idx]['Semantic type'].add('§Operator')
        log(f'{ps.max().illustrate()}: ({idx}, OP)')

    def remove_object(self, idx):
        self.inventory.pop(idx, None)

    def present(self, head):
        return f'{head.max().illustrate()}'
