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
            selector = clitic_head.get_selector()
            left_incorporation_labels = {feature[5:] for feature in clitic_head.features if feature[:5] == 'LEFT:'}
            right_incorporation_labels = {feature[6:] for feature in clitic_head.features if feature[:6] == 'RIGHT:'}

            if selector and selector.get_labels() & left_incorporation_labels and 'INCORPORATED' in selector.features:
                return True

            if test_constituent.get_container_head().get_labels() & right_incorporation_labels and 'INCORPORATED' in clitic_head.features:
                return True

            return False  # if not licensed

        return True  # if not a clitic

