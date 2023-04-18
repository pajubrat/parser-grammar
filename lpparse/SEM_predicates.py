from support import log

class Predicates:
    def __init__(self, narrow_semantics):
        self.narrow_semantics = narrow_semantics

    def reconstruct(self, probe):
        scope_head = next((x for x in probe.upward_path() if x.check({'d'}) and not x.check({'φ'})), None)
        if scope_head:
            log(f'\n\t\t\tPredicate scope for {probe.max().illustrate()} is {scope_head}.')
            return f'Predicate scope for {probe.max().illustrate()} is {scope_head}'
        log(f'\n\t\t\tPredicate scope for {probe.max().illustrate()} is not available => REJECTED.')
        self.narrow_semantics.semantic_interpretation_failed = True
        return f'\n\t\tPredicate scope for {probe.max().illustrate()} is not available'
