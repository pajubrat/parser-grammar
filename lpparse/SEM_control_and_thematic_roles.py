from itertools import takewhile


class LF_Recovery:
    def __init__(self, controlling_parsing_process):
        self.brain_model = controlling_parsing_process
        self.LF_recovery_results = []
        self.interpretation_failed = False

    def recover_arguments(self, probe):
        return self.interpret_antecedent(probe, probe.get_antecedent())

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
            arg_str = antecedent.phonological_content().strip()
        else:
            arg_str = f'{antecedent.head().label()}P(pro)'
        return f'{prefix}/{probe.label()}({probe.illustrate()} ʻ{probe.gloss()}ʼ)/{arg_str}'

    def antecedent_absent(self, probe):
        unvalued_phi = probe.phi_needs_valuation()
        if 'PHI:NUM:_' in unvalued_phi and 'PHI:PER:_' in unvalued_phi:
            if probe.sister() and probe.sister().complex() and (probe.sister().head().nonfinite() or probe.sister().head().finite()):
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
        return f'Agent/{probe.label()}({probe.illustrate()} ʻ{probe.gloss()}ʼ)/{arg_str}'
