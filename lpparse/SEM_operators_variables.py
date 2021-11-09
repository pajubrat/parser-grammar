
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
        log(f'Project ({idx}, OP) for {ps.head().illustrate()}P ({ps.head().max().illustrate()})...')

    def remove_object(self, idx):
        self.inventory.pop(idx, None)

    def present(self, head):
        return f'{head.max().illustrate()}'

    def bind_operator(self, head, semantic_interpretation):
        if 'C' in head.features or 'C/fin' in head.features:
            return
        for operator_feature in head.features:
            if self.is_operator_feature(operator_feature):
                scope_marker_lst = self.bind_to_propositional_scope_marker(head, operator_feature)
                if not scope_marker_lst:
                    log(f'{head.illustrate()} with feature {operator_feature} is not properly bound by an operator. ')
                    self.interpretation_failed = True
                    break
                else:
                    scope_marker = scope_marker_lst[0]
                    semantic_interpretation['Operator bindings'].append((f'{head.illustrate()}', f'{scope_marker}[{operator_feature}]'))
                    self.interpret_operator_at_lexical_item(operator_feature, head, semantic_interpretation)
                    idx, space = self.narrow_semantics.get_referential_index_tuples(head, 'OP')
                    if idx:
                        self.narrow_semantics.query['OP']['Get'](idx)['Bound by'] = scope_marker

    def interpret_operator_at_lexical_item(self, operator_feature, head, semantic_interpretation):
        log(f'\n\t\t\tInterpreting operator feature {operator_feature} at ')
        heads = head.find_occurrences_from(self.narrow_semantics.access_interface['spellout structure'])
        if heads:
            head = heads[0]     # We consider only the first occurrence (there should be only one)
            log(f'{head}. ')
            if self.narrow_semantics.is_concept(head):
                if 'Predicates targeted by operator interpretation' not in semantic_interpretation:
                    semantic_interpretation['Predicates targeted by operator interpretation'] = [f'[{operator_feature}] at {head}']
                else:
                    semantic_interpretation['Predicates targeted by operator interpretation'].append(f'[{operator_feature}] at {head}')
            else:
                log(f'Not enough lexical content. ')
        else:
            log(f'{head}, predicate not found from spellout structure.')    # This should never occur

        if self.reflexive_operator_binding(head):
            log('Verum focus interpretation. ')
            semantic_interpretation['Verum focus interpretation'] = True

    def bind_to_propositional_scope_marker(self, head, operator_feature):
        scope_binder_lst = []
        # --------------- upstream path --------------------------------------------------------------------------- #
        for node in head.upward_path():
            target_head = node.inside_path()    # Left primitive constituent of [node] or [node] itself if it is primitive.
            if self.is_obligatory_scope_binder(target_head, operator_feature):
                scope_binder_lst = [target_head]
                break
            if self.is_last_resort_binder(target_head) and 'OVERT_SCOPE' not in head.features:
                scope_binder_lst.append(target_head)
        # --------------------------------------------------------------------------------------------------------- #
        return scope_binder_lst

    def reflexive_operator_binding(self, ps):
        return 'FIN' in ps.features

    def full_proposition(self, scope_operator):
        return 'OP:REL' not in scope_operator

    def is_operator(self, head):
        return {f for f in head.features if f[:3] == 'OP:' and f[-1] != '_'}

    def is_operator_feature(self, feature):
        return feature[:2] == 'OP' and feature [-1] != '_'

    def get_operator_features(self, features):
        return {f for f in features if self.is_operator_feature(f)}

    def is_obligatory_scope_binder(self, target_head, operator_feature):
        if {operator_feature, 'FIN'} & target_head.features == {operator_feature, 'FIN'}:
            return True

    def is_last_resort_binder(self, target_head):
        if 'T/fin' in target_head.features:
            return True
        if {'T', 'FIN'} & target_head.features == {'T', 'FIN'}:
            return True

    # Recursive definition for criterial features (type ABAR:_) inside phrase
    def scan_criterial_features(self, ps):
        set_ = set()
        if ps.left_const and not ps.left_const.find_me_elsewhere:
            set_ = self.scan_criterial_features(ps.left_const)
        if not set_ and ps.right_const and not ps.right_const.externalized() and not {'T/fin', 'C'} & ps.right_const.head().features:
            set_ = self.scan_criterial_features(ps.right_const)
        if not set_ and ps.is_primitive():
            set_ = self.get_operator_features(ps.features)
        return set_
