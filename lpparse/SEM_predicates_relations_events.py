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
        return 'π' in X.H().features

    def has_PE_index(self, X):
        return self.narrow_semantics.get_idx_tuple(X.H(), 'PRE')

    def get_object(self, idx):
        return self.inventory[idx]

    def update_discourse_inventory(self, idx, criteria):
        self.inventory[idx].update_contents(criteria)

    def project(self, X, idx):
        log(f'\n\t\tProject {X.label()}-event ({idx}, PRE)')
        self.inventory[idx] = self.default_attributes(X)
        return self.inventory[idx]

    def default_attributes(self, X):
        Pred = X.predicate_composition()
        Part = self.participant_composition(Pred)
        return {'Semantic space': 'PRE',
                'Predicate': X,
                'Composition': Pred,
                'Participants': Part,
                'Semantic type': [self.narrow_semantics.semantic_type[X.label()]],
                'Reference': self.present(X)}

    def participant_composition(self, Pred):
        return list({x.identify_argument().H().semantic_index('QND') for x in Pred if x.identify_argument()})

    def remove_object(self, idx):
        self.inventory.pop(idx, None)