
from support import log

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
                                         'OP:C/OP': 'Generic operator'
                                         }
        self.inventory = {}

    def get_object(self, idx):
        return self.inventory[idx]

    def accept(self, ps):
        return {f for f in ps.head().features if f[:3] == 'OP:'}

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

    def bind_operator(self, head, semantic_interpretation):
        if not self.scope_marker(head):
            for operator_feature in [feature for feature in head.features if self.is_operator_feature(feature)]:
                non_scope_marked, scope_marker_lst = self.bind_to_propositional_scope_marker(head, operator_feature)
                if len(scope_marker_lst) > 0:
                    if non_scope_marked:
                        semantic_interpretation['Operator bindings'].append(f'Operator {head.illustrate()}[{operator_feature}] bound by {scope_marker_lst[0]} freely')
                    else:
                        semantic_interpretation['Operator bindings'].append(f'Operator {head.illustrate()}[{operator_feature}] bound by {scope_marker_lst[0]}[{operator_feature}]')
                    self.interpret_operator_at_lexical_item(operator_feature, head, semantic_interpretation)
                    idx, space = self.narrow_semantics.get_referential_index_tuples(head, 'OP')
                    if idx:
                        self.narrow_semantics.query['OP']['Get'](idx)['Bound by'] = scope_marker_lst[0]
                else:
                    log(f'\n\t\t\t!! {head.illustrate()} with {operator_feature} is not bound by an operator. ')
                    if 'OVERT_SCOPE' in head.features:
                        self.interpretation_failed = True
                    else:
                        semantic_interpretation['Operator bindings'].append(f'Operator {head.illustrate()}[{operator_feature}] bound by speaker.')
                    break

    def scope_marker(self, head):
        return {'C', 'C/fin', 'OP:_'} & head.features

    def interpret_operator_at_lexical_item(self, operator_feature, head, semantic_interpretation):
        log(f'\n\t\t\tInterpreting [{operator_feature}] at ')
        head_chain = head.find_occurrences_from(self.narrow_semantics.access_interface['spellout structure'])
        log(f'{head_chain[0].illustrate()}. ')
        if self.narrow_semantics.is_concept(head_chain[0]):
            log('Interpretation successful.')
            if 'Predicates targeted by operator interpretation' not in semantic_interpretation:
                semantic_interpretation['Predicates targeted by operator interpretation'] = [f'[{operator_feature}] at {head_chain[0]}']
            else:
                semantic_interpretation['Predicates targeted by operator interpretation'].append(f'[{operator_feature}] at {head_chain[0]}')
        else:
            log('Not enough lexical content. ')

        if 'FIN' in head_chain[0].features: #Reflexive operator interpretation
            log('Verum focus interpretation. ')
            semantic_interpretation['Verum focus interpretation'] = True

    def bind_to_propositional_scope_marker(self, head, operator_feature):
        local_mandatory_binder = next((node for node in head.working_memory_path() if {operator_feature, 'FIN'}.issubset(node.features)), None)
        if not local_mandatory_binder:
            if 'OVERT_SCOPE' not in head.features:
                return True, [node for node in head.working_memory_path() if {'T', 'FIN'}.issubset(node.features) or {'C', 'FIN'}.issubset(node.features)]
            else:
                return True, []
        return False, [local_mandatory_binder]

    def is_operator(self, head):
        return {f for f in head.features if self.is_operator_feature(f)}

    def is_operator_feature(self, f):
        return f[:3] == 'OP:' and f[-1] != '_'

    def is_feature_in_operator_system(self, feature):
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