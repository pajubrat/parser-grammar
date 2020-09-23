from support import set_logging, log, get_number_of_operations, reset_number_of_operations, log_result, illu
import phrase_structure

# Surface conditions operate at the SS structure and typically refer also to linear order
class SurfaceConditions:
    def __init__(self):
        self.all_pass = True

    def reconstruct(self, ps):
        self.all_pass = True
        # ----------------------- minimal search ---------------------------- #
        ps_ = ps.top()
        for node in ps_:
            if node.is_complex() and node.left_const.is_clitic():
                if not self.is_clitic_licensed(node.left_const):
                    self.all_pass = False
            elif node.is_complex() and node.right_const.is_clitic():
                if not self.is_clitic_licensed(node.right_const):
                    self.all_pass = False
                return self.all_pass
            elif node.is_primitive() and node.is_clitic():
                if not self.is_clitic_licensed(node):
                    self.all_pass = False
        # -------------------------------------------------------------------- #
        return self.all_pass

    def is_clitic_licensed(self, test_constituent):
        if self.illicit_phrasal_incorporation(test_constituent):
            log('\t\t\t\tClitic adjoined to complex phrase, not word')
            return False
        for direction in ['left', 'right']:
            if self.incorporated(test_constituent, direction):
                log(f'\t\t\tClitic {test_constituent} has been incorporated to {direction}.')
                return True
        log(f'\t\t\tClitic {test_constituent} not licensed.')

    # Tests whether {test constituent} could have been incorporated into {direction}
    def incorporated(self, test_constituent, direction):
        host = self.get_host_from_linear_order(test_constituent.head(), direction)
        if host:
            if self.clitic_has_been_incorporated(test_constituent, direction, host):
                if self.clitic_is_licensed(test_constituent, direction, host):
                    return True

    # Definition for whether {test constituent} has been incorporated into {direction} to {host}
    # Note. Takes care of the asymmetry in the distribution of {incorporated}, which always
    # occurs at the left, X=Y ~ X{incorporated}.
    def clitic_has_been_incorporated(self, test_constituent, direction, host):
        if direction=='left':
            if 'INCORPORATED' in host.head().features:
                return True
        if direction=='right':
            if 'INCORPORATED' in test_constituent.head().features:
                return True

    # Definition for the property a {test constituent} has if and only if it can be incorporated into {direction} into {host}
    def clitic_is_licensed(self, test_constituent, direction, host):
        for feature_set in test_constituent.incorporation_features(direction):
            if host.head().features_of_complex_word() & feature_set == feature_set:
                if self.climbing_condition(test_constituent, direction, host):
                    return True

    # Definition for the clitic climbing condition
    def climbing_condition(self, test_constituent, direction, host):
        if direction=='left':
            if self.clitic_is_between_two_verbs(test_constituent, host):
                if not host.quasi_auxiliary():
                    return False
        return True

    # Definition for a property that a constituent has if and only if it occurs between two verbs in the linear input
    def clitic_is_between_two_verbs(self, test_constituent, host):
        if test_constituent.is_left():
            if 'V' in test_constituent.sister().head().features_of_complex_word():
                if 'V' in host.features_of_complex_word():
                    return True

    # Definition for left/right host
    def get_host_from_linear_order(self, head, direction):
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