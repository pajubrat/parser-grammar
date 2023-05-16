from support import log

class LF_Recovery:
    def __init__(self, speaker_model):
        self.brain_model = speaker_model
        self.LF_recovery_results = []
        self.interpretation_failed = False

    def calculate_arguments(self, probe):
        argument_lst = []
        dPHI_set = probe.get_dPHI()
        for dPHI in dPHI_set:
            feature_to_search = dPHI.split(':')[2]
            argument = probe.top().return_constituent_with(feature_to_search)
            log(f'\n\t\t\t{probe} ~ {argument.max().illustrate()}. ')
            if argument:
                argument_lst.append(f'{probe}° ~ {argument.max().illustrate()}')
        return argument_lst

    def interpret_antecedent(self, probe, antecedent_package):
        antecedent, finite_control = antecedent_package
        if antecedent:
            self.brain_model.narrow_semantics.predicate_argument_dependencies.append((probe, antecedent.head()))
            return self.antecedent_present(probe, antecedent)
        else:
            if finite_control:
                self.interpretation_failed = True
            return self.antecedent_absent(probe)

    @staticmethod
    def antecedent_present(probe, antecedent):
        if antecedent.referential():
            arg_str = antecedent.phonological_content().strip()
        else:
            if antecedent == probe.sister():
                arg_str = f'{antecedent.head().label()}P'
            elif antecedent.check({'EXPL'}):
                arg_str = f'generic'
            else:
                arg_str = f'pro at {antecedent.head().label()}'
        return f'{arg_str}'

    def antecedent_absent(self, probe):
        unvalued_phi = probe.phi_needs_valuation()
        arg_str = ''
        if 'PHI:NUM:_' in unvalued_phi and 'PHI:PER:_' in unvalued_phi:
            if probe.sister() and probe.sister().complex() and (probe.sister().head().nonfinite() or probe.sister().head().finite()):
                arg_str = f'{probe.sister().label()}'
            else:
                arg_str = 'generic'
        if 'PHI:DET:_' in unvalued_phi and probe.check({'LANG:FI'}):
            if 'T/fin' in probe.head().features or 'Neg/fin' in probe.head().features:   # Finnish EPP ad hoc rule
                self.interpretation_failed = True
                log(f'Missing argument for {probe} crashes the derivation.')
                arg_str = 'uninterpretable (crash).'
            if probe.head().check({'-Fin'}):
                self.interpretation_failed = True
                log(f'Missing argument crashes the derivation (generic reading is impossible for PX).')
                arg_str = 'uninterpretable (crash).'
            else:
                arg_str = 'generic'
            if 'PHI:PER:_' in unvalued_phi and 'PHI:NUM:_' not in unvalued_phi:
                arg_str = 'discourse argument'

        return f'{arg_str}'
