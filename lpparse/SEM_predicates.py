from support import log


class Predicates:
    def __init__(self, narrow_semantics):
        self.narrow_semantics = narrow_semantics
        self.edge = [('zero merge', lambda x: x.extract_pro() and not x.phi_needs_valuation(), lambda x: x.extract_pro()),
                     ('Agree', lambda x: x.argument_by_agreement() and x.check({'d'}), lambda x: x.argument_by_agreement().max()),
                     ('first merge', lambda x: x.sister() and x.sister().referential(), lambda x: x.sister()),
                     ('second merge', lambda x: x.edge(), lambda x: x.edge()[0]),
                     ('nth merge', lambda x: x.phi_needs_valuation(), lambda x: x.control())]

    def reconstruct(self, probe):
        log(f'\n\t\t\tArgument for {probe}°: ')
        for name, condition, acquisition in self.edge:
            if condition(probe):
                e = acquisition(probe)
                if e:
                    log(f'{e.illustrate()}({name})')
                    return f'{probe}°: {e.illustrate()}'

