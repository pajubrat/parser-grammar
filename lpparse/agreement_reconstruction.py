from support import log

def is_unvalued(head):
    for f in head.features:
        if unvalued(f):
            return True

def unvalued(f):
    return f[:4] == 'PHI:' and f[-1] == '_'
def valued(f):
    return not unvalued(f)
def mark_bad(p):
    return p + '*'
def phi(f):
    return f[:4] == 'PHI:'
def get_type(f):
    return f.split(':')[1]

class AgreementReconstruction:
    def __init__(self, controlling_parsing_process):
        self.brain_model = controlling_parsing_process

    def reconstruct(self, ps):
        self.brain_model.narrow_semantics.predicate_argument_dependencies = []
        # ---------------------------- minimal search ----------------------------------------#
        for node in ps:
            if node.left_const and node.left_const.is_primitive() and 'VAL' in node.left_const.features:
                self.Agree_1(node.left_const)
        # ------------------------------------------------------------------------------------#

    def Agree_1(self, probe):
        self.brain_model.consume_resources("Agree")
        self.brain_model.consume_resources("Phi")

        if probe.sister():
            goal, phi = self.Agree_1_from_sister(probe)
            if phi:
                self.brain_model.narrow_semantics.predicate_argument_dependencies.append((probe, goal))
                probe.features.add('-pro')
                if not {'D', 'φ', 'n'} & probe.features: # This is currently stipulation
                    probe.features.add('BLOCK_NS')
                for p in phi:
                    self.value(probe, goal, p, 'sister')
                if not is_unvalued(probe):
                    return

        goal2, phi = self.Agree_1_from_edge(probe)
        if goal2:
            for p in phi:
                if {f for f in probe.features if unvalued(f) and f[:-1] == p[:len(f[:-1])]}:
                    self.value(probe, goal2, p, 'edge')
            if not {'D', 'φ', 'n'} & probe.features and 'pro' not in goal2.features:
                probe.features.add('BLOCK_NS')

    def Agree_1_from_sister(self, probe):
        #===========================================================
        for node in probe.sister():
            if node.left_const:
                if node.left_const.is_complex() and self.agreement_condition(probe, node.left_const):
                    return node.left_const.head(), sorted({f for f in node.left_const.head().features if phi(f) and f[:7] != 'PHI:DET' and valued(f)})
                else:
                    break
        return None, None
        #===========================================================

    def Agree_1_from_edge(self, head):
        return next(((const.head(), sorted({f for f in const.head().features if phi(f) and valued(f)}))
                     for const in [const for const in head.edge()] + [head.extract_pro()] if
                     const and self.agreement_condition(head, const)), (None, {}))

    def agreement_condition(self, probe, goal):
        if {'D', 'φ'} & goal.head().features:
            if self.brain_model.language != 'LANG:FI':
                return True
            else:
                if 'pro' in goal.head().features:
                    return True
                else:
                    if 'FIN' in probe.features and 'NOM' in goal.head().features:
                        return True
                    if 'INF' in probe.features and 'GEN' in goal.head().features:
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