from support import set_logging, log, get_number_of_operations, reset_number_of_operations, log_result, illu
import phrase_structure


class SurfaceConditions:
    def __init__(self):
        self.all_pass = True

    # Definition for surface reconstruction
    def reconstruct(self, ps):
        # Set the iterator
        ps_ = ps.get_top()

        while ps_:
            if ps_.is_complex() and 'CAT:CL' in ps_.left_const.get_head().features:
                if not self.clitic_test(ps_.left_const):
                    self.all_pass = False
            if ps_.is_complex() and 'CAT:CL' in ps_.right_const.get_head().features:
                if not self.clitic_test(ps_.right_const):
                    self.all_pass = False
            if ps_.is_primitive() and 'CAT:CL' in ps_.get_head().features:
                if not self.clitic_test(ps_):
                    self.all_pass = False
            ps_ = ps_.walk_downstream()

        return self.all_pass

    # Defines the condition for adjacency-based incorporation at the Morphology-Syntax Interface
    def clitic_test(self, test_constituent):

        clitic_head = test_constituent.get_head()
        constituent_to_left = self.get_left(clitic_head)

        # Incorporation to left cannot adjoin a word to a complex phrase (D is excluded because DPs are opened at this stage)
        if constituent_to_left and constituent_to_left.is_complex() and 'D' not in constituent_to_left.get_head().get_labels():
            log('\t\t\t\tClitic adjoined to complex phrase, not word')
            return False

        # Collect the incorporation features (which are ultimately morphological properties)
        left_incorporation_feature_sets = {frozenset(feature[5:].split(",")) for feature in clitic_head.features if feature[:5] == 'LEFT:'}
        right_incorporation_feature_sets = {frozenset(feature[6:].split(",")) for feature in clitic_head.features if feature[:6] == 'RIGHT:'}

        # Condition 1. X_CL is licensed if X (including all its affixes) can check the left incorporation features of CL
        for feature_set in left_incorporation_feature_sets:
            if constituent_to_left and constituent_to_left.get_all_features_of_complex_word() & feature_set == feature_set and 'INCORPORATED' in constituent_to_left.get_head().features:
                log(f'\t\t\tClitic {test_constituent} left-incorporated to {constituent_to_left}')
                return True

        # Condition 1. CL_[..X..] is licensed if X (including all its affixes) can check right incorporation features of CL
        for feature_set in right_incorporation_feature_sets:
            if test_constituent.get_container_head().get_all_features_of_complex_word() & feature_set == feature_set and 'INCORPORATED' in clitic_head.features:
                log(f'\t\t\tClitic {test_constituent} right-incorporated to {test_constituent.get_container_head().get_max()}')
                return True

        log(f'\t\t\tClitic {test_constituent} not licensed.')
        return False  # if not licensed

    def get_left(self, ps):
        ps_ = ps
        while ps_:
            if ps_.sister() and ps_.sister().is_left():
                return ps_.sister()
            ps_ = ps_.walk_upstream()
        return None

