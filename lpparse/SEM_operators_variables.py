
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

    def bind_operator(self, operator_ps, semantic_interpretation):
        if 'C' in operator_ps.features or 'C/fin' in operator_ps.features:
            return
        for f in operator_ps.head().features:
            if self.is_operator_feature(f):
                scope_marker_lst = self.bind_to_propositional_scope_marker(operator_ps, f)
                if not scope_marker_lst:
                    log(f'{operator_ps.illustrate()} with feature {f} is not properly bound by an operator. ')
                    self.interpretation_failed = True
                    break
                else:
                    semantic_interpretation['Operator bindings'].append((f'{operator_ps.illustrate()}', f'{scope_marker_lst[0]}[{f}]'))
                    # todo: bookkeeping into QND/G spaces? Or separate OP space?

    def bind_to_propositional_scope_marker(self, head, operator_feature):
        scope_binder_lst = []
        # --------------- upstream path --------------------------------------------------------------------------- #
        for node in head.upstream_search():
            target_head = node.inside_path()    # Left primitive constituent of [node] or [node] itself if it is primitive.
            if self.is_obligatory_scope_binder(target_head, operator_feature):
                scope_binder_lst = [target_head]
                break
            if self.is_last_resort_binder(target_head) and 'OVERT_SCOPE' not in head.features:
                scope_binder_lst.append(target_head)
        # --------------------------------------------------------------------------------------------------------- #
        return scope_binder_lst

    def full_proposition(self, scope_operator):
        return 'OP:REL' not in scope_operator

    def is_operator(self, head):
        return {f for f in head.features if f[:3] == 'OP:' and f[-1] != '_'}

    def is_operator_feature(self, feature):
        return feature[:3] == 'OP:' and feature [-1] != '_'

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
