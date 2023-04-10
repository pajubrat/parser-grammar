from itertools import takewhile

class Predicates:
    def __init__(self, brain_model):
        self.brain_model = brain_model

    def reconstruct(self, probe):
        scope_head = next((x for x in probe.upward_path() if x.check({'DPF'})), None)
        if scope_head:
            return f'Predicate scope for {probe.max().illustrate()} is {scope_head}'
        return f'Predicate scope for {probe.max().illustrate()} is not available'

