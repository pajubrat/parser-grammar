from support import log

def get_type(f):
    return f.split(':')[1]
def get_value(f):
    return f.split(':')[2]
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

    def reconstruct(self, ps):
        self.controlling_parsing_process.narrow_semantics.predicate_argument_dependencies = []
        # ---------------------------- minimal search ----------------------------------------#
        for node in ps.minimal_search():
            if node.left_const and node.left_const.is_primitive() and 'VAL' in node.left_const.features:
                self.Agree_1(node.left_const)
        # ------------------------------------------------------------------------------------#

    def Agree_1(self, head):

        self.controlling_parsing_process.consume_resources("Agree")
        self.controlling_parsing_process.consume_resources("Phi")

        # 1. Acquisition of phi-features from the sister
        goal1, phi_features = self.Agree_1_from_sister(head)
        if phi_features:
            self.controlling_parsing_process.narrow_semantics.predicate_argument_dependencies.append((head, goal1))
            if not {'D', 'φ', 'n'} & head.features: # This is currently stipulation
                head.features.add('BLOCK_NS')
            for phi in phi_features:
                self.value(head, goal1, phi, 'sister')
            if not head.is_unvalued():
                return

        # 1. Acquisition of phi-features from the edge
        goal2, phi_features = self.Agree_1_from_edge(head)
        if goal2:
            if not goal1:
                for phi in phi_features:
                    if find_unvalued_target(head, phi):
                       self.value(head, goal2, phi, 'edge')

    def Agree_1_from_sister(self, head):
        if head.sister():
            # ---------------------------- minimal search ----------------------------#
            for node in head.sister().minimal_search():
                if self.termination_condition_for_Agree_search(node):
                    break
                if node.left_complex():
                    if self.agreement_condition(head, node.left_const):
                        return node.left_const.head(), \
                               sorted({f for f in node.left_const.head().features
                                       if phi(f) and f[:7] != 'PHI:DET' and valued(f)})
            # ---------------------------------------------------------------------------#
        return head.sister(), {}

    def termination_condition_for_Agree_search(self, node):
        return node.left_const and node.left_const.is_primitive()

    def Agree_1_from_edge(self, head):
        if self.edge_for_Agree(head):
            for e in self.edge_for_Agree(head):
                if self.agreement_condition(head, e):
                    phi_features = {f for f in e.head().features if phi(f) and valued(f)}
                    return e.head(), sorted(phi_features)
        return None, {}

    def agreement_condition(self, head, phrase):
        if {'D', 'φ'} & phrase.head().features:
            if self.controlling_parsing_process.language != 'LANG:FI':
                return True
            else:
                if 'pro' in phrase.head().features:
                    return True
                else:
                    if 'FIN' in head.features and 'NOM' in phrase.head().features:
                        return True
                    if 'INF' in head.features and 'GEN' in phrase.head().features:
                        return True

    def value(self, h, goal, phi, location):

        if h.get_valued_features() and self.valuation_blocked(h, phi):
            h.features.add(mark_bad(phi))

        if find_unvalued_target(h, phi):
            h.features = h.features - find_unvalued_target(h, phi)
            h.features.add(phi)
            if goal.mother:
                log(f'{h} acquired ' + str(phi) + f' from {goal.mother} inside its {location}...')
            else:
                log(f'{h} acquired ' + str(phi) + f' from {goal} inside its {location}...')
            h.features.add('PHI_CHECKED')

    def valuation_blocked(self, head, f):
        valued_input_feature_type = get_type(f)
        heads_phi_set = head.get_phi_set()
        valued_phi_in_h = {phi for phi in heads_phi_set if valued(phi) and get_type(phi) == valued_input_feature_type}

        if valued_phi_in_h:
            type_value_matches = {phi for phi in valued_phi_in_h if phi == f}
            if type_value_matches:
                return False
            else:
                log(f'Feature {f} cannot be valued into {head}. Reason:')
                log(f'{head} has no matching feature but has a feature with the same type but with different value...')
                return True
        return False

    def edge_for_Agree(self, h):
        edge_list = h.phrasal_edge()
        if h.extract_pro():
            edge_list.append(h.extract_pro())
        return edge_list