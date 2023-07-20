from support import log


class Predicates:
    def __init__(self):
        self.operation_failed = False
        # structure of the type: (name of the operation, target and trigger, argument selection, legibility)
        self.edge = [('0-merge',
                      lambda x: x.extract_pro() and not x.needs_valuation(),
                      lambda x: x.extract_pro(),
                      lambda x: x.pro_legibility()),
                     ('1-merge',
                      lambda x: x.sister() and x.sister().referential(),
                      lambda x: x.sister(),
                      lambda x: True),
                     ('2-merge',
                      lambda x: x.edge() and x.edge()[0].referential(),
                      lambda x: x.edge()[0],
                      lambda x: True),
                     ('N-merge',
                      lambda x: x.needs_valuation(),
                      lambda x: x.control(),
                      lambda x: True)]

    def reconstruct(self, probe):
        for name, condition, acquisition, legibility in self.edge:
            if condition(probe):
                argument = acquisition(probe)
                if argument:
                    log(f'\n\t\t\tArgument for {probe}°: {self.print_target(probe, argument)} by {name} ')
                    if probe.p_associate_check(probe.get_goal()):
                        log(f'EPP violation. ')
                        break
                    if name == '0-merge':
                        paired_with = probe.pro_legibility()
                        log(f'paired with {paired_with}°.')
                        if not paired_with:
                            log(' *This pro-element cannot be paired with a root predicate/thematic role.')
                            self.operation_failed = True
                    return f'{probe}°: {self.print_target(probe, argument)}'

        log(f'\n\t\t\t*{probe} failed to link with an argument.')
        self.operation_failed = True

    def print_target(self, probe, goal):
        if 'pro' in goal.features:
            phrasal_argument = probe.argument_by_agreement()
            if phrasal_argument:
                return f'pro/{probe.argument_by_agreement().max().illustrate()}'
            else:
                return f'pro'
        return f'{goal.illustrate()}'

    def reconstruct_agreement(self, ps):
        goal = ps.argument_by_agreement()
        if goal:
            return f'Agree({ps}, {goal.illustrate()})'