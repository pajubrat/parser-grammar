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

        # Walk downward and check clitic conditions
        while ps_:
            if ps_.is_complex() and self.is_clitic(ps_.left_const):
                if not self.is_clitic_licensed(ps_.left_const):
                    self.all_pass = False
            elif ps_.is_complex() and self.is_clitic(ps_.right_const):
                if not self.is_clitic_licensed(ps_.right_const):
                    self.all_pass = False
                return self.all_pass
            elif ps_.is_primitive() and self.is_clitic(ps_):
                if not self.is_clitic_licensed(ps_):
                    self.all_pass = False
            ps_ = ps_.walk_downstream()

        return self.all_pass

    # Defines what constitutes a clitic
    # Trivial condition: ps is a clitic if ps has 'CAT:CL'
    # Condition 1: If the head H of ps is a clitic, then ps can be clitic if and only if
    # Condition 2.1. H has no affixes, and
    # Condition 2.2. H is internal.

    # Comment:  Conditions (2.1) and (2.2) try to capture the fact that [D N] can be a clitic when D and N are inside
    #           same phonological word (mi = DP)

    def is_clitic(self, ps):

        # Trivial condition. If ps is a clitic, then ps is trivially a clitic
        if 'CAT:CL' in ps.features:
            return True

        # Condition 1. ps can be a clitic only if its head is a clitic;
        if 'CAT:CL' in ps.head().features:
            # Condition 2.1 If ps has no affixes and (2.2) is internal, then ps is clitic (e.g., D_CL N)
            if not ps.head().has_affix() and ps.head().internal:
                return True
            else:
                return False
        else:
            return False

    # Defines the condition for adjacency-based incorporation at the Morphology-Syntax Interface
    def is_clitic_licensed(self, test_constituent):

        clitic_head = test_constituent.head()
        constituent_to_left = self.get_constituent_to_left_in_linear_order(clitic_head)

        # Incorporation to left cannot adjoin a word to a complex phrase (D is excluded because DPs are opened at this stage)
        if 'INCORPORATED' not in clitic_head.features and constituent_to_left and constituent_to_left.is_complex() and 'D' not in constituent_to_left.get_head().labels():
            log('\t\t\t\tClitic adjoined to complex phrase, not word')
            return False

        # Collect the incorporation features (which are ultimately morphological properties)
        left_incorporation_feature_sets = {frozenset(feature[5:].split(",")) for feature in clitic_head.features if feature[:5] == 'LEFT:'}
        right_incorporation_feature_sets = {frozenset(feature[6:].split(",")) for feature in clitic_head.features if feature[:6] == 'RIGHT:'}

        # Left incorporation
        # Condition 1. The clitic was left incorporated
        if constituent_to_left and 'INCORPORATED' in constituent_to_left.get_head().features:
            # Condition 2. Left-incorporation features license the operation
            for feature_set in left_incorporation_feature_sets:
                if constituent_to_left.get_all_features_of_complex_word() & feature_set == feature_set:
                    # Condition 3. Incorporation condition: do not incorporate out of a predicate
                    if self.incorporation_condition(test_constituent):
                        log(f'\t\t\tClitic {test_constituent} left-incorporated to {constituent_to_left}')
                        return True

        # Condition 1. Right incorporation. CL_[..X..] is licensed if X (including all its affixes) can check right incorporation features of CL
        constituent_to_right = self.get_constituent_to_right_in_linear_order(test_constituent)
        if 'INCORPORATED' in clitic_head.features and constituent_to_right:
            for feature_set in right_incorporation_feature_sets:
                if constituent_to_right.get_all_features_of_complex_word() & feature_set == feature_set:
                    log(f'\t\t\tClitic {test_constituent} right-incorporated to {test_constituent.container_head()}')
                    return True

        log(f'\t\t\tClitic {test_constituent} not licensed.')
        return False  # if not licensed

    def incorporation_condition(self, test_constituent):

        # Condition 1. There is a right sister element that contains label V
        if test_constituent.is_left() and 'CAT:V' in test_constituent.sister().head().get_all_features_of_complex_word():

            # Condition 2. The left element is not V
            if 'CAT:V' not in self.get_constituent_to_left_in_linear_order(test_constituent).get_all_features_of_complex_word():
                return True
            else:
                # Condition 3. The left element is V but has 'SEM:internal' and does not have 'ASP'
                if 'SEM:internal' in self.get_constituent_to_left_in_linear_order(test_constituent).get_all_features_of_complex_word() and \
                        'ASP' not in self.get_constituent_to_left_in_linear_order(test_constituent).get_all_features_of_complex_word():
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
