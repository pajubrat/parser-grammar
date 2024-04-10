from support import log


class Predicates:
    def __init__(self):
        self.operation_failed = False

    def reconstruct(self, probe):
        log(f'\n\t\t\tArgument for {probe}°')
        arg = probe.identify_argument()
        if arg:
            log(f': {self.print_target(probe, arg)}')
            return f'{probe}: {self.print_target(probe, arg)}'
        log(f' NOT FOUND.')
        self.operation_failed = True

    def print_target(self, probe, argument):
        indexing = ''
        if {phi for phi in probe.features if phi.startswith('PHI:IDX:')}:
            if probe.argument_by_agreement():
                indexing = f', indexed to {probe.argument_by_agreement().max().illustrate()}'
        if 'pro' in argument.features:
            return f'pro' + indexing
        else:
            return f'{argument.max().illustrate()}' + indexing

    def reconstruct_agreement(self, ps):
        goal = ps.argument_by_agreement()
        if goal:
            return f'Agree({ps}, {goal.illustrate()})'
