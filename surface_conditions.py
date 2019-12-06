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
            if ps_.is_complex():
                test_constituent = ps_.left_const
            else:
                test_constituent = ps_

            # Ad hoc clitic test (experimental, for testing purposes)
            if not self.clitic_test(test_constituent):
                self.all_pass = False

            ps_ = ps_.walk_downstream()

        return self.all_pass

    # Defines the condition for adjacency at the pre-Transfer surface structure
    # This version is purely ad hoc and stipulative, to test the main idea
    def clitic_test(self, test_constituent):

        clitic_head = test_constituent.get_head()
        if 'CAT:CL' in clitic_head.features:
            constituent_to_left = self.get_left(clitic_head)
            left_incorporation_features = {feature[5:] for feature in clitic_head.features if feature[:5] == 'LEFT:'}
            right_incorporation_features = {feature[6:] for feature in clitic_head.features if feature[:6] == 'RIGHT:'}

            if constituent_to_left and constituent_to_left.get_head().features & left_incorporation_features and 'INCORPORATED' in constituent_to_left.get_head().features:
                return True

            if test_constituent.get_container_head().features & right_incorporation_features and 'INCORPORATED' in clitic_head.features:
                return True

            return False  # if not licensed

        return True  # if not a clitic

    def get_left(self, ps):
        ps_ = ps
        while ps_:
            if ps_.sister() and ps_.sister().is_left():
                return ps_.sister()
            ps_ = ps_.walk_upstream()
        return None

