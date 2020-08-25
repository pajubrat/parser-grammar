from support import set_logging, log, get_number_of_operations, reset_number_of_operations, log_result, illu

class AgreementReconstruction:
    def __init__(self):
        pass

    # Definition for agreement reconstruction
    def reconstruct(self, ps):

        # ---------------------------- minimal search -------------------------------------- #
        for node in ps.minimal_search():
            if node.left_const and node.left_const.is_primitive():
                h = node.left_const
                if 'VAL' in h.features:
                    log(f'\t\t\t\t\tHead {h} triggers Agree-1:')
                    self.acquire_phi(h)
        # ------------------------------------------------------------------------------------#

    # Definition for phi-feature acquisition (Agree-1)
    def acquire_phi(self, h):

        goal, phi_features = self.acquire_from_sister(h.sister())
        for phi in phi_features:
            if self.value(h, phi):
                log(f'\t\t\t\t\t\t{h} acquired ' + str(phi) + f' by phi-Agree from {goal.mother}.')
                h.features.add('PHI_CHECKED')

        if self.is_unvalued(h):
            goal, phi_features = self.acquire_from_edge(h)
            for phi in phi_features:
                if self.value(h, phi):
                    log(f'\t\t\t\t\t\t{h} acquired ' + str(phi) + f' from the edge of {h}.')


    # Definition for phi-acquisition from sister
    def acquire_from_sister(self, ps):

        # Internal function
        def is_functional(h):
            if '!COMP:*' in h.features:
                return True

        # Main function
        # ---------------------------- minimal search ----------------------------#
        for node in ps.minimal_search():
            if node.left_const and node.is_complex():
                goal = node.left_const.head()
                if is_functional(goal):
                    break
                if 'D' in goal.features:
                    return goal, sorted({f for f in goal.features if self.phi(f) and f[:7] != 'PHI:DET' and self.valued(f)})
        # ---------------------------------------------------------------------------#

        return ps, {}

    # Definition for phi-acquisition from the edge
    def acquire_from_edge(self, h):
        edge_list = self.edge_for_Agree(h)
        if edge_list:
            for edge in edge_list:
                edge_head = edge.head()
                if 'D' in edge_head.features:
                    phi_features = {f for f in edge_head.features if self.phi(f) and self.valued(f)}
                    return edge_head, sorted(phi_features)

        # If nothing is found, we return an empty set (i.e. nothing)
        return None, {}

    # Definition for phi-feature valuation
    def value(self, h, phi):
        if not self.valuation_blocked(h, phi):
            phi = self.mark_bad(phi)
            h.features.add(phi)
            return False

        target = self.find_unvalued_target(h, phi)
        if target:
            h.features = h.features - target
            h.features.add(phi)
            return True

        return False

    # Definition for unvalued target feature
    def find_unvalued_target(self, h, phi):
        return {f for f in h.features if self.unvalued(f) and f[:-1] == phi[:len(f[:-1])]}

    # Definition for the notion of phi-set for head H
    def get_phi_set(self, h):
        return {f for f in h.head().features if f[:4] == 'PHI:' and len(f.split(':')) == 3}

    # Definition for unvalued phi-features of H
    def is_unvalued(self, h):
        return {f for f in h.features if f[:4] == 'PHI:' and f[-1] == '_'}

    # Definition for valued phi-features of H
    def is_valued(self, h):
        return {f for f in h.features if f[:4] == 'PHI:' and f[-1] != '_'}

    # Definition for unvalued feature
    def unvalued(self, input_feature):
        return {f for f in {input_feature} if f[-1] == '_'}

    # Definition for valued faeture
    def valued(self, input_feature):
        return {f for f in {input_feature} if not self.unvalued(f)}

    # Definition of feature TYPE
    def get_type(self, f):
        return f.split(':')[1]  # Notice that 0 = first element, 1 = second element

    # Definition of feature VALUE
    def get_value(self, f):
        return f.split(':')[2]  # Notice that 0 = first element, 1 = second element, 2 = third element

    # Definition for PHI-feature
    def phi(self, input_feature):
        return {f for f in {input_feature} if f[:4] == 'PHI:'}

    # Definition for feature conflict
    def feature_conflict(self, f, phi):
        if self.get_type(f) == self.get_type(phi) and self.get_value(f) != self.get_value(phi) and self.valued(f):
            log(f'\t\t\t\t\t\tFeature conflict between {f} and {phi}.')
            return True
        else:
            return False

    def valuation_blocked(self, h, f):
        if not self.is_valued(h):
            return True

        valued_input_feature_type = self.get_type(f)
        heads_phi_set = self.get_phi_set(h)

        valued_phi_in_h = {phi for phi in heads_phi_set if self.valued(phi) and self.get_type(phi) == valued_input_feature_type}
        if valued_phi_in_h:
            type_value_matches = {phi for phi in valued_phi_in_h if phi == f}
            if type_value_matches:
                return True

            else:
                log(f'\t\t\t\t\t\tFeature {f} cannot be valued into {h}. Reason:')
                log(f'\t\t\t\t\t\t{h} already has a feature with the same type but with different value.')
                return False

        return True

    # Definition for bad agreement
    def mark_bad(self, phi):
        return phi + '*'

    # Definition of edge (for Agree-1)
    def edge_for_Agree(self, h):
        if h.is_complex():
            return None
        if h.is_right():
            ps_ = h
        else:
            ps_ = h.mother
        edge_list = []
        if h.extract_pro():
            edge_list.append(h.extract_pro())
        while ps_ and ps_.sister() and (ps_.sister().is_left() and ps_.sister().is_complex()):
            edge_list.append(ps_.sister())
            ps_ = ps_.walk_upstream()
        return edge_list[::-1]