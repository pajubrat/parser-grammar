from support import log


class Predicates:
    def __init__(self):
        self.operation_failed = False

    def reconstruct(self, probe):
        log(f'\n\t\t\tArgument for {probe}°')
        arg = probe.identify_argument()
        if arg:
            log(f': {self.print_target(probe, arg)}')
            return f'{self.print_target(probe, arg)}'
        log(f' not found.')
        self.operation_failed = True

    def print_target(self, probe, argument):
        if 'pro' in argument.features:
            phrasal_argument = probe.argument_by_agreement()
            if phrasal_argument:
                return f'φ/pro, indexed to {probe.argument_by_agreement().max().illustrate()}'
            else:
                return f'φ/pro'
        return f'{argument.max().illustrate()}'

    def reconstruct_agreement(self, ps):
        goal = ps.argument_by_agreement()
        if goal:
            return f'Agree({ps}, {goal.illustrate()})'