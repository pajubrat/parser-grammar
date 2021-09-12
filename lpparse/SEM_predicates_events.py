from support import log

class PredicatesEvents:
    def __init__(self, narrow_semantics):
        self.narrow_semantics = narrow_semantics    # Access to narrow semantics
        self.inventory = {}                         # PE space for semantic objects

    def reset(self):
        self.inventory = {}

    def is_predicate(self, ps):
        return 'ARG' in ps.head().features

    def get_object(self, idx):
        return self.inventory[idx]

    def update_discourse_inventory(self, idx, criteria):
        self.inventory[idx].update(criteria)

    def project_PE_entry_into_inventory(self, ps, idx):
        self.inventory[idx] = self.narrow_semantics.default_criteria(ps, 'PE')
        log(f'Denotation for {ps} (index {idx}) created into PE space...')

    def remove_object(self, idx):
        self.inventory.pop(idx, None)

    def link_predicate_to_argument(self, predicate_head, list_of_antecedents):
        """
        Links a predicate with its argument in the PE and GLOBAL spaces.

        This function is called by Agreement reconstruction and/or LF recovery when a predicate
        is paired with its argument.

        A presupposition is that the predicate_head has a referential index, because there are few
        edge cases where this is not the case (i.e. when head is ?ARG and later turned into ARG). This
        matter should be attended in future.
        """
        if self.narrow_semantics.has_referential_index(predicate_head):
            selected_antecedent = list_of_antecedents[0]
            idx, space = self.narrow_semantics.get_referential_index_tuples(predicate_head, 'PE')
            if idx:
                self.inventory[idx]['Argument'] = selected_antecedent.max().illustrate()