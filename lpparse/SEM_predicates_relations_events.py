from support import log

class PredicatesRelationsEvents:
    def __init__(self, narrow_semantics):
        self.narrow_semantics = narrow_semantics
        self.inventory = {}

    def reset(self):
        self.inventory = {}

    def present(self, head):
        return f'{head.illustrate()}'

    def accept(self, ps):
        return ps.predicate() and not {'D', 'φ'} & ps.head().features

    def has_PE_index(self, ps):
        if (None, None) != self.narrow_semantics.get_referential_index_tuples(ps, 'PRE'):
            return True

    def get_object(self, idx):
        return self.inventory[idx]

    def update_discourse_inventory(self, idx, criteria):
        self.inventory[idx].update(criteria)

    def project(self, ps, idx):
        self.inventory[idx] = self.narrow_semantics.default_attributes(ps, 'PRE')
        log(f'predicate \'{ps.illustrate()}\': ({idx}, PRE)')

    def remove_object(self, idx):
        self.inventory.pop(idx, None)