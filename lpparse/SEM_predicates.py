from support import log


class Predicates:
    def __init__(self, narrow_semantics):
        self.narrow_semantics = narrow_semantics

    def reconstruct(self, probe):
        edge_list = []
        if probe.extract_pro():
            if self.argument_by_agreement(probe):
                edge_list.append(self.argument_by_agreement(probe).max())
            else:
                edge_list.append(probe.extract_pro())
        if probe.sister() and probe.sister().referential():
            edge_list.append(probe.sister())
        if probe.edge():
            edge_list = edge_list + probe.edge()
        if probe.phi_needs_valuation():
            unvalued_phi = probe.phi_needs_valuation()
            if unvalued_phi & {'PHI:NUM:_', 'PHI:PER:_'}:
                if probe.control():
                    edge_list.append(probe.control())
            elif unvalued_phi & {'PHI:DET:_'}:
                if probe.finite_control():
                    edge_list.append(probe.finite_control())
        arguments_str = ''
        for i, a in enumerate(edge_list):
            if i == 1:
                arguments_str += '('
            arguments_str += f'{a.illustrate()}'
        if i > 0:
            arguments_str += ')'
        return f'{probe}: {arguments_str}'

    def argument_by_agreement(self, probe):
        for x in probe.features:
            if x.startswith('dPHI'):
                if probe.sister():
                    return self.constituent_by_index(probe.sister(), x.split(':')[2])

    def constituent_by_index(self, ps, idx):
        const = None
        if ps.complex():
            const = self.constituent_by_index(ps.left, idx)
            if not const:
                const = self.constituent_by_index(ps.right, idx)
        else:
            if idx in ps.features:
                return ps
        return const
