
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
    OP      -       Scope-marking operator for all operator features, must be combined with finiteness
                    This is currently generated from copying criterial features to a head. Alternative is
                    the question-particles of in situ languages, not currently implemented.
    OP:_    -       Unvalued operator feature which is generated when moved operator is present.
                    This therefore implies that movement of an operator phrase has occurred
                    To capture edge generalization in Finnish, this implies [!SPEC:OP:_]
    """
    def __init__(self):
        pass

    def bind_to_scope_operator(self, head, operator_feature='OP'):
        """
        Finds a binding scope operator for head (it is assumed that head has operator feature). A scope operator
        can be defined by parameter [operator_feature].
        """
        # --------------- upstream path --------------------------------------------------------------------------- #
        for node in head.upstream_search():
            target_head = node.inside_path()
            if target_head.match_features({operator_feature}) == 'complete match' and 'FIN' in target_head.features:
                return target_head
        # --------------------------------------------------------------------------------------------------------- #

    def is_operator(self, head):
        """
        An operator is a constituent that is interpreted as such in the semantic module. Formally it is defined as a primitive
        lexical item that has some valued operator feature [OP:V].
        """
        return {f for f in head.features if f[:3] == 'OP:' and f[-1] != '_'}

    def is_operator_feature(self, feature):
        return feature[:3] == 'OP:' and feature [-1] != '_'

    def contains_operator_feature(self, features):
        return {f for f in features if self.is_operator_feature(f)}