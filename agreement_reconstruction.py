from support import log

# Abbreviations
def get_type(f):
    return f.split(':')[1]  # Notice that 0 = first element, 1 = second element
def get_value(f):
    return f.split(':')[2]  # Notice that 0 = first element, 1 = second element, 2 = third element
def unvalued(input_feature):
    if input_feature:
        return {f for f in {input_feature} if f[-1] == '_'}
def valued(input_feature):
    return {f for f in {input_feature} if not unvalued(f)}
def find_unvalued_target(h, phi):
    return {f for f in h.features if unvalued(f) and f[:-1] == phi[:len(f[:-1])]}
def mark_bad(phi):
    return phi + '*'
def phi(input_feature):
    return {f for f in {input_feature} if f[:4] == 'PHI:'}


class AgreementReconstruction:
    def __init__(self, controlling_parsing_process):
        self.controlling_parsing_process = controlling_parsing_process

    # Definition for agreement reconstruction
    def reconstruct(self, ps):
        # ---------------------------- minimal search -------------------------------------- #
        for node in ps.minimal_search():
            if node.left_primitive() and 'VAL' in node.left_const.features:
                self.Agree_1(node.left_const)
        # ------------------------------------------------------------------------------------#

    # Definition for phi-feature acquisition (Agree-1)
    def Agree_1(self, head):

        self.controlling_parsing_process.consume_resources("Agree")

        goal, phi_features = self.Agree_1_from_sister(head)
        for phi in phi_features:
            self.value(head, goal, phi)

        if not head.is_unvalued():
            return

        goal, phi_features = self.Agree_1_from_edge(head)
        for phi in phi_features:
            self.value(head, goal, phi)

    # Definition for phi-acquisition from sister
    def Agree_1_from_sister(self, head):
        if head.sister():
            # ---------------------------- minimal search ----------------------------#
            for node in head.sister().minimal_search():
                if node.left_complex():
                    if node.left_const.head().is_functional():
                        break
                    if 'D' in node.left_const.head().features:
                        return node.left_const.head(), \
                               sorted({f for f in node.left_const.head().features
                                       if phi(f) and f[:7] != 'PHI:DET' and valued(f)})
            # ---------------------------------------------------------------------------#
        return head.sister(), {}    # This line is executed only if nothing is found

    # Definition for phi-acquisition from the edge
    def Agree_1_from_edge(self, h):
        if self.edge_for_Agree(h):
            for e in self.edge_for_Agree(h):
                if 'D' in e.head().features:
                    phi_features = {f for f in e.head().features if phi(f) and valued(f)}
                    return e.head(), sorted(phi_features)
        return None, {}

    # Definition for phi-feature valuation
    def value(self, h, goal, phi):
        if h.get_valued_features() and self.valuation_blocked(h, phi):
            h.features.add(mark_bad(phi))
        if find_unvalued_target(h, phi):
            h.features = h.features - find_unvalued_target(h, phi)
            h.features.add(phi)
            log(f'\t\t\t\t\t{h} acquired ' + str(phi) + f' by Agree-1 from {goal}.')
            h.features.add('PHI_CHECKED')

    # Definition for blocked valuation
    def valuation_blocked(self, h, f):
        valued_input_feature_type = get_type(f)
        heads_phi_set = h.get_phi_set()
        valued_phi_in_h = {phi for phi in heads_phi_set if valued(phi) and get_type(phi) == valued_input_feature_type}
        if valued_phi_in_h:
            type_value_matches = {phi for phi in valued_phi_in_h if phi == f}
            if type_value_matches:
                return False
            else:
                log(f'\t\t\t\t\t\tFeature {f} cannot be valued into {h}. Reason:')
                log(f'\t\t\t\t\t\t{h} already has a feature with the same type but with different value.')
                return True
        return False

    # Definition of edge (for Agree-1)
    def edge_for_Agree(self, h):
        edge_list = []
        if h.is_complex():
            return None
        if h.is_right():
            ps_ = h
        else:
            ps_ = h.mother
        if h.extract_pro():
            edge_list.append(h.extract_pro())
        while ps_ and ps_.sister() and (ps_.sister().is_left() and ps_.sister().is_complex()):
            edge_list.append(ps_.sister())
            ps_ = ps_.walk_upstream()
        return edge_list[::-1]