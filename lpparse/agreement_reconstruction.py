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
def mark_bad(phi):
    return phi + '*'
def phi(input_feature):
    return {f for f in {input_feature} if f[:4] == 'PHI:'}


class AgreementReconstruction:
    def __init__(self, controlling_parsing_process):
        self.brain_model = controlling_parsing_process

    def reconstruct(self, ps):
        self.brain_model.narrow_semantics.predicate_argument_dependencies = []
        # ---------------------------- minimal search ----------------------------------------#
        for node in ps.minimal_search():
            if node.left_const and node.left_const.is_primitive() and 'VAL' in node.left_const.features:
                self.Agree_1(node.left_const)
        # ------------------------------------------------------------------------------------#

    def Agree_1(self, head):

        self.brain_model.consume_resources("Agree")
        self.brain_model.consume_resources("Phi")

        # 1. Acquisition of phi-features from the sister
        if head.sister():
            goal1, phi_features = self.Agree_1_from_sister(head)
            if phi_features:
                self.brain_model.narrow_semantics.predicate_argument_dependencies.append((head, goal1))
                if not {'D', 'φ', 'n'} & head.features: # This is currently stipulation
                    head.features.add('BLOCK_NS')
                for phi in phi_features:
                    self.value(head, goal1, phi, 'sister')
                if not head.is_unvalued():
                    return

        # 1. Acquisition of phi-features from the edge
        goal2, phi_features = self.Agree_1_from_edge(head)
        if goal2:
            for phi in phi_features:
                if {f for f in head.features if unvalued(f) and f[:-1] == phi[:len(f[:-1])]}:
                    self.value(head, goal2, phi, 'edge')
            if not {'D', 'φ', 'n'} & head.features and 'pro' not in goal2.features:
                head.features.add('BLOCK_NS')

    def Agree_1_from_sister(self, head):
        #===========================================================
        for node in head.sister().minimal_search():
            if node.left_const:
                if node.left_const.is_complex() and self.agreement_condition(head, node.left_const):
                    return node.left_const.head(),sorted({f for f in node.left_const.head().features if phi(f) and f[:7] != 'PHI:DET' and valued(f)})
                else:
                    break
        return None, None
        #===========================================================

    def Agree_1_from_edge(self, head):
        return next(((const.head(), sorted({f for f in const.head().features if phi(f) and valued(f)}))
                     for const in [const for const in head.edge()] + [head.extract_pro()] if
                     const and self.agreement_condition(head, const)), (None, {}))

    def agreement_condition(self, head, const):
        if {'D', 'φ'} & const.head().features:
            if self.brain_model.language != 'LANG:FI':
                return True
            else:
                if 'pro' in const.head().features:
                    return True
                else:
                    if 'FIN' in head.features and 'NOM' in const.head().features:
                        return True
                    if 'INF' in head.features and 'GEN' in const.head().features:
                        return True

    def value(self, h, goal, phi, location):
        if h.get_valued_features() and self.valuation_blocked(h, phi):
            log(f'Valuation of {h} was blocked for {phi}...')
            h.features.add(mark_bad(phi))

        if {f for f in h.features if unvalued(f) and f[:-1] == phi[:len(f[:-1])]}:
            h.features = h.features - {f for f in h.features if unvalued(f) and f[:-1] == phi[:len(f[:-1])]}
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
                log(f'Feature {f} cannot be valued into {head}.')
                return True
        return False