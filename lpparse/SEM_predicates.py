from support import log


class Predicates:
    def __init__(self):
        self.operation_failed = False
        # structure of the type: (name of the operation, target and trigger, antecedent, integrity test)
        self.edge = [('zero merge',
                      lambda x: x.extract_pro() and not x.phi_needs_valuation(),
                      lambda x: x.extract_pro(),
                      lambda x, y: x.agreement_licensing(x.argument_by_agreement())),
                     ('Agree',
                      lambda x: x.argument_by_agreement() and x.check({'d'}),
                      lambda x: x.argument_by_agreement().max(),
                      lambda x, y: x.agreement_licensing(y)),
                     ('first merge',
                      lambda x: x.sister() and x.sister().referential(),
                      lambda x: x.sister(),
                      lambda x, y: True),
                     ('second merge',
                      lambda x: x.edge(),
                      lambda x: x.edge()[0],
                      lambda x, y: True),
                     ('nth merge',
                      lambda x: x.phi_needs_valuation(),
                      lambda x: x.control(),
                      lambda x, y: x.is_possible_antecedent(y))]

    def reconstruct(self, probe):
        log(f'\n\t\t\tArgument for {probe}°: ')
        for name, condition, acquisition, licensing in self.edge:
            if condition(probe):
                goal = acquisition(probe)
                if goal:
                    if licensing(probe, goal):
                        log(f'{goal.illustrate()}({name})')
                        return f'{probe}°: {goal.illustrate()}'
                    else:
                        log(f'\n\t\t\t*{goal} was not licensed by {probe}.')
                        self.operation_failed = True
                        return
        log(f'\n\t\t\t*{probe} was not linked with an argument.')
        self.operation_failed = True
