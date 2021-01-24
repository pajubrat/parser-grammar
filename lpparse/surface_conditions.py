from support import log

# Surface conditions operate at the SS structure and typically refer also to linear order
class SurfaceConditions:
    def __init__(self):
        self.all_pass = True

    def reconstruct(self, ps):
        """
        Examines the spellout structure and whether it is well-formed. Currently handles only incorporation
        (and by extension clitics). The algorithm detects clitics and return False ('fail') immediate if the
        clitic is not licensed. If no problems are detected, returns True ('pass').

        Looking at these procedures I now think that this cannot be the correct way to formulate these properties.
        This is because by doing it at the spellout structure we are forced to mimic left-right properties of the
        linear order inside SS structure. A more natural approach would be to handle this by manipulating the
        lexical stream, but this requires then that we posit a processing buffer between lexico-morphological
        component and syntax that hosts the lexical stream, possibly for each word at a time. Then we can formulate the
        incorporation tests inside that pipeline. To be useful there should be some other independent reasons why
        this structure should exist.
        """
        # ----------------------- minimal search ---------------------------- #
        ps_ = ps.top()
        for node in ps_:
            if node.is_complex():
                if node.left_const.is_clitic() and not self.is_clitic_licensed(node.left_const):
                    return False
                elif node.right_const.is_clitic() and not self.is_clitic_licensed(node.right_const):
                    return False
            elif node.is_clitic() and not self.is_clitic_licensed(node):
                    return False
        # -------------------------------------------------------------------- #
        return True

    def is_clitic_licensed(self, test_constituent):
        """
        Tests if the clitic is licensed.

        Tests three conditions:
        (1) The clitic has not been adjoined to a phrase.
        (2) The clitic has been incorporated to something (phonological weakness)
        (3) Incorporation is licensed by incorporation feature
        """
        # Condition (1): clitic has been incorporated to a word, not phrase
        if self.illicit_phrasal_incorporation(test_constituent):
            log('Clitic adjoined to complex phrase, not word...')
            return False
        # Condition (2-3): Tests that the clitic has been incorporated left or right and that the operation is
        # licensed by an incorporation feature.
        for direction in ['left', 'right']:
            if self.incorporated(test_constituent, direction):
                log(f'Clitic {test_constituent} has been incorporated to {direction}...')
                return True
        log(f'Clitic {test_constituent} not licensed...')

    def incorporated(self, test_constituent, direction):
        """
         # Tests whether {test constituent} could have been incorporated into {direction}
        """
        host = self.get_host_from_linear_order(test_constituent.head(), direction)
        if host:
            if self.clitic_has_been_incorporated(test_constituent, direction, host):
                if self.clitic_is_licensed(test_constituent, direction, host):
                    return True

    def clitic_has_been_incorporated(self, test_constituent, direction, host):
        """
        Tests for whether {test constituent} has been incorporated into {direction} to {host} in the sensory input.
        Incorporation is transmitted to syntax by using feature [INCORPORATED] that is here examined. It corresponds
        to the incorporation boundary = in the input. Incorporation to left requires that this feature is in the head
        of the host at the left. Incorporation to right requires that the feature is in the head of the clitic. The logic
        is because [INCORPORATED] represent = in the morphological decomposition.
        """
        if direction=='left':
            if 'INCORPORATED' in host.head().features:
                return True
        if direction=='right':
            if 'INCORPORATED' in test_constituent.head().features:
                return True

    def clitic_is_licensed(self, test_constituent, direction, host):
        """
        Tests if {test constituent} can be incorporated into {direction} into {host} by using lexical features.
        """
        for feature_set in test_constituent.incorporation_features(direction):
            if host.head().features_of_complex_word() & feature_set == feature_set:
                if self.climbing_condition(test_constituent, direction, host):
                    return True

    def climbing_condition(self, test_constituent, direction, host):
        """
        Definition for the clitic climbing condition.
        """
        if direction=='left':
            if self.clitic_is_between_two_verbs(test_constituent, host):
                if not host.quasi_auxiliary():
                    return False
        return True

    def clitic_is_between_two_verbs(self, test_constituent, host):
        """
        Definition for a property that a constituent has if and only if it occurs between two verbs in the linear input
        """
        if test_constituent.is_left():
            if 'V' in test_constituent.sister().head().features_of_complex_word():
                if 'V' in host.features_of_complex_word():
                    return True

    def get_host_from_linear_order(self, head, direction):
        """
        Definition for left/right host.

        It is very suspicious that we need these properties here, because what we are doing is formulating the trivial
        property of left versus right at the sensory input by relying on the geometrical properties of the spellout structure.
        """
        if direction=='left':
            ps_ = head
            while ps_:
                if ps_.sister() and ps_.sister().is_left():
                    return ps_.sister()
                ps_ = ps_.walk_upstream()
            return None
        if direction=='right':
            ps_ = head.max()
            while ps_:
                if ps_.sister() and ps_.sister().is_right():
                    if ps_.sister().is_primitive:
                        return ps_.sister()
                    else:
                        return self.left_edge(ps_)
                ps_ = ps_.walk_upstream()
            return None

    # Recursive definition for left edge of a constituent
    def left_edge(self, ps):
        if ps.is_complex():
            return self.left_edge(ps.left_const)
        else:
            return ps

    # Filter for incorporation into a non-word phrase
    def illicit_phrasal_incorporation(self, test_constituent):
        constituent_to_left = self.get_host_from_linear_order(test_constituent.head(), 'left')
        return 'INCORPORATED' not in test_constituent.head().features and \
               constituent_to_left and \
               constituent_to_left.is_complex() and \
               'D' not in constituent_to_left.head().features