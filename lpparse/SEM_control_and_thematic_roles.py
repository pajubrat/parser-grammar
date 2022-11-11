from itertools import takewhile

class LF_Recovery:
    def __init__(self, controlling_parsing_process):
        self.brain_model = controlling_parsing_process
        self.LF_recovery_results = []
        self.interpretation_failed = False

    def recover_arguments(self, probe):
        return self.interpret_antecedent(probe, self.get_antecedent(probe))

    def get_antecedent(self, probe):
        unvalued_phi = probe.phi_needs_valuation()
        if {'PHI:NUM:_', 'PHI:PER:_'} & unvalued_phi:
            return self.control(probe)
        elif {'PHI:DET:_'} & unvalued_phi:
            return self.finite_control(probe)

    def control(self, probe):
        working_memory = []
        if probe.is_primitive() and probe.is_left() and probe.sister().is_complex():
            working_memory.append(probe.sister())
        working_memory.extend(list(takewhile(self.recovery_termination, probe.working_memory_path())))
        return next((const for const in working_memory if self.is_possible_antecedent(const, probe)), None)

    @staticmethod
    def recovery_termination(node):
        return 'SEM:external' not in node.features

    def finite_control(self, probe):
        for const in probe.working_memory_path():
            if self.is_possible_antecedent(const, probe) or self.special_rule(const, probe):
                return const

    def is_possible_antecedent(self, antecedent, probe):
        if not antecedent.find_me_elsewhere:
            phi_to_check = {phi for phi in probe.features if phi[:7] == 'PHI:NUM' or phi[:7] == 'PHI:PER'}
            phi_checked = {phi2 for phi1 in antecedent.head().get_valued_features() for phi2 in phi_to_check if self.feature_check(phi1, phi2)}
            return phi_to_check == phi_checked

    @staticmethod
    def feature_check(antecedent_feature, probe_feature):
        return antecedent_feature == probe_feature or (probe_feature[-1] == '_' and antecedent_feature[:len(probe_feature[:-1])] == probe_feature[:-1])

    @staticmethod
    def special_rule(const, probe):
        if probe.finite() and probe.edge_specifiers() and const == next((const for const in probe.edge_specifiers()), None):
            if not const.head().referential():
                probe.features.add('PHI:DET:GEN')
            return const

    def interpret_antecedent(self, probe, antecedent):
        if antecedent:
            self.brain_model.narrow_semantics.predicate_argument_dependencies.append((probe, antecedent.head()))
            return self.antecedent_present(probe, antecedent)
        return self.antecedent_absent(probe)

    @staticmethod
    def antecedent_present(probe, antecedent):
        if probe.sister() and probe.is_left() and antecedent == probe.sister() and antecedent.is_right():
            prefix = 'Patient'
        else:
            prefix = 'Agent'
        if antecedent.head().referential():
            arg_str = antecedent.illustrate()
        else:
            arg_str = f'{antecedent.head().major_cat()}(pro)'
        return f'{prefix}/{probe.major_cat()}({probe.illustrate()} ʻ{probe.gloss()}ʼ)/{arg_str}'

    def antecedent_absent(self, probe):
        unvalued_phi = probe.phi_needs_valuation()
        if 'PHI:NUM:_' in unvalued_phi and 'PHI:PER:_' in unvalued_phi:
            if probe.sister() and probe.sister().is_complex() and (probe.sister().head().nonfinite() or probe.sister().head().finite()):
                arg_str = 'Clausal'
            else:
                arg_str = 'Generic'
        elif 'PHI:PER:_' in unvalued_phi and 'PHI:NUM:_' not in unvalued_phi:
            arg_str = 'Discourse antecedent'
        else:
            if 'T/fin' in probe.head().features or 'Neg/fin' in probe.head().features:   # Finnish EPP ad hoc rule
                self.interpretation_failed = True
                arg_str = 'Uninterpretable, interpretation failed.'
            else:
                arg_str = 'Generic'
        return f'Agent/{probe.major_cat()}({probe.illustrate()} ʻ{probe.gloss()}ʼ)/{arg_str}'
