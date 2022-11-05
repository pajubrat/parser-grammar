from support import log
from itertools import takewhile

def must_be_valued(phi_set):
    return {phi for phi in phi_set if semantically_relevant_phi(phi)}
def semantically_relevant_phi(phi):
    return phi[:7] == 'PHI:NUM' or phi[:7] == 'PHI:PER' or phi[:7] == 'PHI:DET'
def get_semantically_relevant_phi(h):
    return {f for f in h.features if semantically_relevant_phi(f)}

class LF_Recovery:
    def __init__(self, controlling_parsing_process):
        self.brain_model = controlling_parsing_process
        self.LF_recovery_results = []
        self.interpretation_failed = False

    def perform_LF_recovery(self, probe, semantic_interpretation_dict):
        unvalued = must_be_valued({f for f in probe.features if f[:4] == 'PHI:' and f[-1] == '_'})
        if unvalued:
            antecedent = self.LF_recovery(probe, unvalued)  # This version returns only the local antecedent
            self.interpret_antecedent(antecedent, probe, unvalued, semantic_interpretation_dict)

    def LF_recovery(self, probe, unvalued_phi):
        log(f'\n\t\t\t\"{probe.illustrate()}\" was controlled by ')
        list_of_antecedents = []
        working_memory = []

        # Standard control
        if 'PHI:NUM:_' in unvalued_phi and 'PHI:PER:_' in unvalued_phi:
            # Add the sister
            if probe.is_primitive() and probe.is_left() and probe.sister().is_complex():
                working_memory.append(probe.sister())
            # Add from the upward path
            working_memory.extend(list(takewhile(self.recovery_termination, probe.working_memory_path())))
            antecedent = next((const for const in working_memory if self.is_possible_antecedent(const, probe)), None)
            return antecedent

        # Finite control in Finnish
        if 'PHI:DET:_' in unvalued_phi:
            # ---------------- minimal search----------------------------------------------------
            for const in probe.working_memory_path():
                if self.special_local_edge_antecedent_rule(const, probe, list_of_antecedents):
                    break
                if self.is_possible_antecedent(const, probe):
                    list_of_antecedents.append(const)
            #------------------------------------------------------------------------------------

        # One exception due to the lack of analysis of φ control
        if not list_of_antecedents:
            log(f'nothing. ')
            if not {'φ', 'T/prt', 'MODAL'} & probe.features:
                # self.interpretation_failed = True
                return None
        if list_of_antecedents:
            return list_of_antecedents[0]

    def is_possible_antecedent(self, antecedent, probe):
        def check(antecedent_feature, probe_feature):
            # features are the same OR feature in the antecedent can value an unvalued feature in the probe
            return antecedent_feature == probe_feature or \
                   (probe_feature[-1] == '_' and antecedent_feature[:len(probe_feature[:-1])] == probe_feature[:-1])

        phi_to_check = {phi for phi in probe.features if phi[:7] == 'PHI:NUM' or phi[:7] == 'PHI:PER'}
        if not antecedent.find_me_elsewhere:
            return phi_to_check == {phi2 for phi1 in antecedent.head().get_valued_features()
                                                   for phi2 in phi_to_check
                                                   if check(phi1, phi2)}

    def recovery_termination(self, node):
        return 'SEM:external' not in node.features

    def special_local_edge_antecedent_rule(self, const, probe, list_of_antecedents):
        if probe.finite() and probe.edge_specifiers() and const == next((const for const in probe.edge_specifiers()), None):
            if not const.head().referential():
                self.LF_recovery_results.append(f'{probe}(generic)')
                list_of_antecedents.append(const)
                probe.features.add('PHI:DET:GEN')
            else:
                list_of_antecedents.append(const)
            return True

    def interpret_antecedent(self, list_of_antecedents, probe, unvalued, semantic_interpretation_dict):
        self.LF_recovery_results = []
        if list_of_antecedents:
            antecedent = self.interpret_antecedent_for_output(probe, list_of_antecedents[0])
            self.LF_recovery_results.append(antecedent)
            self.brain_model.narrow_semantics.predicate_argument_dependencies.append((probe, list_of_antecedents[0].head()))
            semantic_interpretation_dict['Recovery'].append(f'{antecedent}')
        else:
            self.LF_recovery_results.append(self.antecedent_does_not_exist(probe, unvalued))
            semantic_interpretation_dict['Recovery'].append(f'Agent/{probe.major_cat()}({probe.illustrate()} ʻ{probe.gloss()}ʼ)/{self.antecedent_does_not_exist(probe, unvalued)}')
        self.report_to_log(probe, list_of_antecedents, unvalued)

    def interpret_antecedent_for_output(self, probe, antecedent):
        if probe.sister() and probe.is_left() and antecedent == probe.sister() and antecedent.is_right():
            prefix = 'Patient'
        else:
            prefix = 'Agent'

        if antecedent.head().referential():
            if antecedent.head().sister() and 'N' in antecedent.head().sister().head().features:
                arg_str = antecedent.head().sister().head().illustrate()
            else:
                arg_str = antecedent.illustrate()
        else:
            arg_str = f'{antecedent.head().major_cat()}(pro)'

        return f'{prefix}/{probe.major_cat()}({probe.illustrate()} ʻ{probe.gloss()}ʼ)/{arg_str}'

    def antecedent_does_not_exist(self, ps, features):
        if 'PHI:NUM:_' in features and 'PHI:PER:_' in features:
            if ps.sister() and ps.sister().is_complex() and \
                    (ps.sister().head().nonfinite() or ps.sister().head().finite()):
                return 'Clausal'
            else:
                return 'Generic'
        elif 'PHI:PER:_' in features and 'PHI:NUM:_' not in features:
            return 'Discourse antecedent'
        else:
            if 'T/fin' in ps.head().features or 'Neg/fin' in ps.head().features:    # Finnish EPP ad hoc rule
                self.interpretation_failed = True                                   # I still don't fully understand this
                return 'Uninterpretable, interpretation failed.'
            else:
                return 'Generic'

    def report_to_log(self, ps, list_of_antecedents, unvalued_phi_features):
        s = ''
        i = 1
        if list_of_antecedents:
            for a in list_of_antecedents:
                s = s + str(i) + '. ' + a.illustrate() + ' '
                i = i + 1
                if i == 2:
                    s = s + '   (alternatives: '
            if i > 1:
                s = s + ')'
            if s:
                log(s)
        else:
            log(f'({self.antecedent_does_not_exist(ps, unvalued_phi_features)})')
        log('. ')