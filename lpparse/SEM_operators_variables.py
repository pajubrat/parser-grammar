
from support import log

class OperatorVariableModule:
    """
    Interprets operator-variable constructions (operator features), which correspond to the notion
    of 'complex predicate', i.e. Fregean unsaturation applied to propositions.

    An operator feature has the form [OP...]. All features of this type go to this module for interpretation.
    Operator features are features which are bound by a scope element. A scope element must be in a head that
    is finite (propositional). Bare operator-variable construction is interpreted as lambda x: P(...x...), where the
    Fregean unsaturation is targeted to a whole proposition P. The resulting predicate is predicated of the
    operator element which can occur either in situ or in the scope position (A-bar position, phrase or head).

    Operator features (in the operator element itself, moved or in situ)
    Feature lexicon Explanation
    OP:REL          Relative clause operator feature (pure lambda feature)
    OP:WH   wh      Interrogative operator feature
    OP:FOC  foc     Contrastive focus operator feature (Finnish prosodic emphasis)
    OP:FAM  fam     Familiarity operator feature (Finnish -hAn)
    OP:TOP  top     Topic operator feature
    OP:POL  pol     Polarity operator feature (Finnish -pA)
    OP:Q    Q       Yes/no operator feature (Finnish -kO)

    Scope-marking element which binds the operator:
    OP:_    -       Unvalued operator feature which is generated when moved operator is present.
                    This therefore implies that movement of an operator phrase has occurred
                    To capture edge generalization in Finnish, this implies [!SPEC:OP:_]
    """
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
        """
        Binds an operator to a scope-element. An operator is a non-finite constituent that has valued [OP:XX] feature,
        with XX being the value. It is bound necessarily by a head with [OP:XX][FIN]. Binding projects the proposition
        into semantic bookkeeping and provides referential index for the scope head.
        """
        if 'C' in operator_ps.features or 'C/fin' in operator_ps.features:
            return
        feature_set = operator_ps.head().features.copy()
        for f in feature_set:
            if self.is_operator_feature(f):
                scope_marker_lst = self.bind_to_propositional_scope_marker(operator_ps, f)
                if not scope_marker_lst:
                    log(f'{operator_ps.illustrate()} with feature {f} is not properly bound by an operator. ')
                    self.interpretation_failed = True
                    break
                else:
                    # Update binding information to semantic interpretation dict
                    semantic_interpretation['Operator bindings'].append((f'{operator_ps.illustrate()}', f'{scope_marker_lst[0]}[{f}]'))

                    # Update binding information for the operator in semantic bookkeeping
                    idx = self.narrow_semantics.get_referential_index_tuple(operator_ps)
                    if not idx:
                        self.narrow_semantics.wire(operator_ps)
                        idx = self.narrow_semantics.get_referential_index_tuple(operator_ps)
                    self.narrow_semantics.update_semantics_for_attribute(idx, 'Bound by', scope_marker_lst)
                    self.interpret_and_update_operator_feature(idx, f)
                    log(f'{operator_ps.illustrate()} was bound by {scope_marker_lst[0]}...')

                    # Create referential index for the proposition and project it to semantic bookkeeping
                    # Only applies to full propositions, not to relative clauses
                    if not self.narrow_semantics.controlling_parsing_process.first_solution_found and not self.narrow_semantics.get_referential_index_tuple(scope_marker_lst[0]):
                        if self.full_proposition(scope_marker_lst[0]):
                            self.narrow_semantics.wire(scope_marker_lst[0])

    def bind_to_propositional_scope_marker(self, head, operator_feature):
        """
        Finds a list of binding scope operators for [head] (it is assumed that head has operator feature).
        If there is a specifically marked obligatory binder, it alone will be selected; if not, a
        list of T/fin heads will be returned. Returns a list of scope marker constituents.
        """
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
        """
        An operator is a constituent that is interpreted as such in the semantic module. Formally it is defined as a primitive
        lexical item that has some valued operator feature [OP:V].
        """
        return {f for f in head.features if f[:3] == 'OP:' and f[-1] != '_'}

    def is_operator_feature(self, feature):
        return feature[:3] == 'OP:' and feature [-1] != '_'

    def get_operator_features(self, features):
        return {f for f in features if self.is_operator_feature(f)}

    def is_obligatory_scope_binder(self, target_head, operator_feature):
        """
        Determines if target_head could constitute the scope marker for operator_feature.
        """
        if {operator_feature, 'FIN'} & target_head.features == {operator_feature, 'FIN'}:
            return True

    def is_last_resort_binder(self, target_head):
        if 'T/fin' in target_head.features:
            return True
        if {'T', 'FIN'} & target_head.features == {'T', 'FIN'}:
            return True

    # Recursive definition for criterial features (type ABAR:_) inside phrase
    def scan_criterial_features(self, ps):
        """
        Scans the phrase for criterial features. Once (a set of) criterial features are found from a head,
        search is terminated.
        """
        set_ = set()
        if ps.left_const and not ps.left_const.find_me_elsewhere:
            set_ = self.scan_criterial_features(ps.left_const)
        if not set_ and ps.right_const and not ps.right_const.externalized() and not {'T/fin', 'C'} & ps.right_const.head().features:
            set_ = self.scan_criterial_features(ps.right_const)
        if not set_ and ps.is_primitive():
            set_ = self.get_operator_features(ps.features)
        return set_

    def interpret_and_update_operator_feature(self, idx, f):
        """
        Provides English language description for the operator interpretation into semantic bookkeeping
        """
        return
        if 'Operator interpretation' not in self.narrow_semantics.global_cognition.discourse_inventory[idx]:
            self.narrow_semantics.global_cognition.discourse_inventory[idx]['Operator interpretation'] = set()
        self.narrow_semantics.global_cognition.discourse_inventory[idx]['Operator interpretation'].add(self.operator_interpretation[f])