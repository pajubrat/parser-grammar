from support import log


class Predicates:
    def __init__(self):
        self.operation_failed = False
        # structure of the type: (name of the operation, target and trigger, antecedent, integrity test)
        self.edge = [('zero merge',
                      lambda x: x.extract_pro() and not x.phi_needs_valuation(),
                      lambda x: x.extract_pro()),
                     ('Agree',
                      lambda x: x.argument_by_agreement() and x.check({'d'}),
                      lambda x: x.argument_by_agreement().max()),
                     ('first merge',
                      lambda x: x.sister() and x.sister().referential(),
                      lambda x: x.sister()),
                     ('second merge',
                      lambda x: x.edge(),
                      lambda x: x.edge()[0]),
                     ('N merge',
                      lambda x: x.phi_needs_valuation(),
                      lambda x: x.control())]

    def reconstruct(self, probe):
        log(f'\n\t\t\tArgument for {probe}°: ')
        for name, condition, acquisition in self.edge:
            if condition(probe):
                goal = acquisition(probe)
                if goal:
                    log(f'{goal.illustrate()} (by {name}).')
                    return f'{probe}°: {goal.illustrate()}'
        log(f'\n\t\t\t*{probe} was not linked with an argument.')
        self.operation_failed = True
