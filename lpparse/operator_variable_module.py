
class OperatorVariableModule:
    """
    Interprets operator-variable constructions (operator features), which correspond to the notion
    of 'complex predicate', i.e. Fregean unsaturation applied to propositions.

    An operator feature has the form [OP...]. All features of this type go to this module for interpretation.
    Operator features are features which are bound by a scope element. A scope element must be in a head that
    is finite (propositional). Bare operator-variable construction is interpreted as lambda x: P(...x...), where the
    Fregean unsaturation is targeted to a whole proposition P. The resulting predicate is predicated of the
    operator element which can occur either in situ or in the scope position (A-bar position, phrase or head).

    Operator features (in the operator element itself, moved or insitu)
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
    def __init__(self):
        pass

    def bind_to_scope_operator(self, head, operator_feature):
        """
        Finds a list of binding scope operators for head (it is assumed that head has operator feature).
        If there is a specifically marked obligatory binder, it alone will be selected; if not, a
        list of T/fin heads will be returned. Return a list of scope marker constituents.
        """
        scope_binder_lst = []
        # --------------- upstream path --------------------------------------------------------------------------- #
        for node in head.upstream_search():
            target_head = node.inside_path()    # Left primitive constituent of [node] or [node] itself if it is primitive.
            if target_head != head and self.termination_condition_for_operator_binding(node):
                break
            if self.is_obligatory_scope_binder(target_head, operator_feature):
                scope_binder_lst = [target_head]
                break
            if self.is_last_resort_binder(target_head) and 'OVERT_SCOPE' not in head.features:
                scope_binder_lst.append(target_head)
        # --------------------------------------------------------------------------------------------------------- #
        return scope_binder_lst

    def termination_condition_for_operator_binding(self, node):
        if node.is_complex() and 'D' in node.left_const.features:
            return True

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