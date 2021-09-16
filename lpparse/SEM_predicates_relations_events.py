from support import log

class PredicatesRelationsEvents:
    def __init__(self, narrow_semantics):
        self.narrow_semantics = narrow_semantics    # Access to narrow semantics
        self.inventory = {}                         # PRE space for semantic objects

    def reset(self):
        self.inventory = {}

    def present(self, head):
        return f'{head.illustrate()}'

    def accept(self, ps):
        return 'ARG' in ps.head().features and not {'D', 'φ'} & ps.head().features

    def has_PE_index(self, ps):
        if (None, None) != self.narrow_semantics.get_referential_index_tuples(ps, 'PRE'):
            return True

    def get_object(self, idx):
        return self.inventory[idx]

    def update_discourse_inventory(self, idx, criteria):
        self.inventory[idx].update(criteria)

    def project_PRE_entry_into_inventory(self, ps, idx):
        self.inventory[idx] = self.narrow_semantics.default_criteria(ps, 'PRE')
        log(f'Denotation for {ps} (index {idx}) created into PE space...')

    def remove_object(self, idx):
        self.inventory.pop(idx, None)

    def link_predicate_to_argument(self, predicate_head, list_of_antecedents):
        """
        Links a predicate with its argument in the PE and GLOBAL spaces.

        This function is called by LF recovery when a predicate is paired with its argument.

        A presupposition is that the predicate_head has a referential index, because there are few
        edge cases where this is not the case (i.e. when head is ?ARG and later turned into ARG). This
        matter should be attended in future.
        """
        if self.narrow_semantics.has_referential_index(predicate_head):

            # We consider only the first (most local) antecedent in this version
            selected_antecedent = list_of_antecedents[0]

            # Retrieve the index for the predicate in PE space
            idx, space = self.narrow_semantics.get_referential_index_tuples(predicate_head, 'PRE')

            # Retrieve the index to the argument
            idx_arg, space_arg = self.narrow_semantics.get_referential_index_tuples(selected_antecedent.head(), 'QND')

            # Add information about the argument
            if idx:
                self.inventory[idx]['Argument'] = idx_arg