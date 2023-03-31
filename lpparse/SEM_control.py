from itertools import takewhile
from support import log

class LF_Recovery:
    def __init__(self, brain_model):
        self.brain_model = brain_model
        self.LF_recovery_results = []
        self.interpretation_failed = False

    def calculate_arguments(self, probe):
        argument_lst = []
        dPHI_set = probe.get_dPHI()
        for dPHI in dPHI_set:
            feature_to_search = dPHI.split(':')[2]
            argument = probe.top().return_constituent_with(feature_to_search)
            log(f'\n\t\t\tEstablishing argument link for {probe}: {argument.max().illustrate()}. ')
            if argument:
                argument_lst.append(f'Argument for {probe}° is {argument.max().illustrate()}')
        return argument_lst

    def control(self, probe):
        return self.interpret_antecedent(probe, probe.get_antecedent())

    def interpret_antecedent(self, probe, antecedent):
        if antecedent:
            self.brain_model.narrow_semantics.predicate_argument_dependencies.append((probe, antecedent.head()))
            return self.antecedent_present(probe, antecedent)
        return self.antecedent_absent(probe)

    @staticmethod
    def antecedent_present(probe, antecedent):
        if probe.sister() and probe.is_left() and antecedent == probe.sister() and antecedent.is_right():
            prefix = 'Antecedent'
        else:
            prefix = 'Antecedent'
        if antecedent.head().referential():
            arg_str = antecedent.phonological_content().strip()
        else:
            arg_str = f'pro at {antecedent.head().label()}'
        return f'{prefix} for {probe.label()}°({probe.gloss()}) is {arg_str}'

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
                log(f'Missing antecedent crashes the derivation.')
                arg_str = 'uninterpretable (crash).'
            if probe.head().check({'-Fin'}):
                self.interpretation_failed = True
                log(f'Missing antecedent crashes the derivation (generic reading is impossible for PX).')
                arg_str = 'uninterpretable (crash).'
            else:
                arg_str = 'generic'
            if 'PHI:PER:_' in unvalued_phi and 'PHI:NUM:_' not in unvalued_phi:
                arg_str = 'discourse antecedent'

        return f'Antecedent of {probe.label()} is {arg_str}'
