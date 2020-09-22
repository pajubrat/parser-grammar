from support import set_logging, log, get_number_of_operations, reset_number_of_operations, log_result, illu
import phrase_structure


class SurfaceConditions:
    def __init__(self):
        self.all_pass = True

    # Definition for surface reconstruction
    def reconstruct(self, ps):

        # Set the iterator
        ps_ = ps.top()
        self.all_pass = True

        # ----------------------- minimal search ---------------------------- #
        for node in ps_:
            if node.is_complex() and self.is_clitic(node.left_const):
                if not self.is_clitic_licensed(node.left_const):
                    self.all_pass = False
            elif node.is_complex() and self.is_clitic(node.right_const):
                if not self.is_clitic_licensed(node.right_const):
                    self.all_pass = False
                return self.all_pass
            elif node.is_primitive() and self.is_clitic(node):
                if not self.is_clitic_licensed(node):
                    self.all_pass = False
        # -------------------------------------------------------------------- #
        return self.all_pass

    def is_clitic(self, ps):
        if 'CL' in ps.features:
            return True
        if 'CL' in ps.head().features:
            if not ps.head().has_affix() and ps.head().internal:
                return True

    def is_clitic_licensed(self, test_constituent):

        left_incorporation_feature_sets, right_incorporation_feature_sets = self.retrieve_local_context(test_constituent)

        constituent_to_left = self.get_constituent_to_left_in_linear_order(test_constituent.head())
        if self.illicit_phrasal_incorporation(test_constituent, constituent_to_left):
            log('\t\t\t\tClitic adjoined to complex phrase, not word')
            return False

        if constituent_to_left and 'INCORPORATED' in constituent_to_left.head().features:
            for feature_set in left_incorporation_feature_sets:
                if constituent_to_left.head() and constituent_to_left.head().features_of_complex_word() & feature_set == feature_set:
                    if self.incorporation_condition(test_constituent):
                        log(f'\t\t\tClitic {test_constituent} left-incorporated to {constituent_to_left}')
                        return True

        constituent_to_right = self.get_constituent_to_right_in_linear_order(test_constituent)
        if constituent_to_right and 'INCORPORATED' in test_constituent.head().features and constituent_to_right:
            for feature_set in right_incorporation_feature_sets:
                if constituent_to_right.head() and constituent_to_right.head().features_of_complex_word() & feature_set == feature_set:
                    log(f'\t\t\tClitic {test_constituent} right-incorporated to {test_constituent.container_head()}')
                    return True

        log(f'\t\t\tClitic {test_constituent} not licensed.')
        return False

    def retrieve_local_context(self, test_constituent):

        left_incorporation_feature_sets = {frozenset(feature[5:].split(",")) for feature in test_constituent.head().features if feature[:5] == 'LEFT:'}
        right_incorporation_feature_sets = {frozenset(feature[6:].split(",")) for feature in test_constituent.head().features if feature[:6] == 'RIGHT:'}
        return left_incorporation_feature_sets, right_incorporation_feature_sets


    def illicit_phrasal_incorporation(self, test_constituent, constituent_to_left):
        return 'INCORPORATED' not in test_constituent.head().features and \
               constituent_to_left and \
               constituent_to_left.is_complex() and \
               'D' not in constituent_to_left.head().features


    def incorporation_condition(self, test_constituent):
        if test_constituent.is_left() and 'V' in test_constituent.sister().head().features_of_complex_word():
            if self.get_constituent_to_left_in_linear_order(test_constituent) and 'V' not in self.get_constituent_to_left_in_linear_order(test_constituent).features_of_complex_word():
                return True
            else:
                if self.get_constituent_to_left_in_linear_order(test_constituent) and 'SEM:internal' in self.get_constituent_to_left_in_linear_order(test_constituent).features_of_complex_word() and \
                        'ASP' not in self.get_constituent_to_left_in_linear_order(test_constituent).features_of_complex_word():
                    return True
                else:
                    return False
        return True

    def get_constituent_to_left_in_linear_order(self, ps):
        ps_ = ps
        while ps_:
            if ps_.sister() and ps_.sister().is_left():
                return ps_.sister()
            ps_ = ps_.walk_upstream()
        return None

    def get_constituent_to_right_in_linear_order(self, ps):
        ps_ = ps
        while ps_:
            if ps_.sister() and ps_.sister().is_right():
                if ps_.sister().is_primitive:
                    return ps_.sister()
                else:
                    return self.left_edge(ps_)
            ps_ = ps_.walk_upstream()
        return None

    def left_edge(self, ps):
        if ps.is_complex():
            return self.left_edge(ps.left_const)
        else:
            return ps