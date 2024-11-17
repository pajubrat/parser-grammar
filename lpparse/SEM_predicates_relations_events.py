from support import log

class PredicatesRelationsEvents:
    def __init__(self, narrow_semantics):
        self.narrow_semantics = narrow_semantics
        self.inventory = {}

    def reset(self):
        self.inventory = {}

    def present(self, X):
        return f'{self.narrow_semantics.semantic_type[X.label()][1:]}'

    def accept(self, X):
        return ['π', 'κ'] in X.H().core

    def has_PE_index(self, X):
        return self.narrow_semantics.get_idx_tuple(X.H(), 'PRE')

    def get_object(self, idx):
        return self.inventory[idx]

    def update_discourse_inventory(self, idx, criteria):
        self.inventory[idx].update(criteria)

    def project(self, X, idx):
        self.inventory[idx] = self.default_attributes(X)
        if 'π' in X.core.features():
            log(f'\n\t\tProject {X.label()}-event ({idx}, PRE)')
            Pred = X.predicate_composition()
            self.inventory[idx].update({'Composition': Pred, 'Participants': self.participant_composition(Pred)})
        if 'κ' in X.core.features():
            log(f'\n\t\tProject {X.label()}-concept ({idx}, PRE)')
            self.inventory[idx].update({'Concept': f'\'{".".join(X.core.get_lf())}\''})
        return self.inventory[idx]

    def default_attributes(self, X):
        return {'Semantic space': 'PRE',
                'Predicate': X,
                'Semantic type': [self.narrow_semantics.semantic_type.get(X.label(), '?')],
                'Reference': self.present(X)}

    def participant_composition(self, Pred):
        return list({x.identify_argument().H().core.semantic_index('QND') for x in Pred if x.identify_argument()})

    def remove_object(self, idx):
        self.inventory.pop(idx, None)