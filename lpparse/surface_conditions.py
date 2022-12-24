from support import log

# Surface conditions operate at the SS structure and typically refer also to linear order
class SurfaceConditions:
    def __init__(self):
        self.all_pass = True

    def reconstruct(self, ps):
        log('Checking surface conditions...')
        # ----------------------- minimal search ---------------------------- #
        ps_ = ps.top()
        for node in ps_:
            if node.is_complex():
                if node.left.clitic() and not self.is_clitic_licensed(node.left):
                    log(f'Failed.')
                    return False
                elif node.right.clitic() and not self.is_clitic_licensed(node.right):
                    log('Failed.')
                    return False
            elif node.clitic() and not self.is_clitic_licensed(node):
                    log('Failed.')
                    return False
        # -------------------------------------------------------------------- #
        log('OK')
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
        def incorporation_features(node, direction):
            if direction == 'left':
                return {frozenset(feature[5:].split(",")) for feature in node.head().features if feature[:5] == 'LEFT:'}
            if direction == 'right':
                return {frozenset(feature[6:].split(",")) for feature in node.head().features if
                        feature[:6] == 'RIGHT:'}

        for feature_set in incorporation_features(test_constituent, direction):
            if host.head().features_of_complex_word() & feature_set == feature_set:
                if self.climbing_condition(test_constituent, direction, host):
                    return True

    def climbing_condition(self, test_constituent, direction, host):
        def is_quasi_auxiliary(host):
            return 'SEM:internal' in host.features_of_complex_word() and \
                   'ASP' not in host.features_of_complex_word()
        if direction=='left':
            if self.clitic_is_between_two_verbs(test_constituent, host):
                if not is_quasi_auxiliary(host):
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
        def walk_upstream(node):
            while node.mother:
                node = node.mother
                if not node.right.adjunct:
                    return node

        if direction=='left':
            ps_ = head
            while ps_:
                if ps_.sister() and ps_.sister().is_left():
                    return ps_.sister()
                ps_ = walk_upstream(ps_)
            return None
        if direction=='right':
            ps_ = head.max()
            while ps_:
                if ps_.sister() and ps_.sister().is_right():
                    if ps_.sister().is_primitive:
                        return ps_.sister()
                    else:
                        return self.left_edge(ps_)
                ps_ = walk_upstream(ps_)
            return None

    # Recursive definition for left edge of a constituent
    def left_edge(self, ps):
        if ps.is_complex():
            return self.left_edge(ps.left)
        else:
            return ps

    # Filter for incorporation into a non-word phrase
    def illicit_phrasal_incorporation(self, test_constituent):
        constituent_to_left = self.get_host_from_linear_order(test_constituent.head(), 'left')
        return 'INCORPORATED' not in test_constituent.head().features and \
               constituent_to_left and \
               constituent_to_left.is_complex() and \
               'D' not in constituent_to_left.head().features