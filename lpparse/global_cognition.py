from support import log

class GlobalCognition:
    def __init__(self):
        self.discourse_inventory = {}
        self.index_counter = 1
        self.excluded_fields = {'Denotations', 'Semantic space', 'Denotation weights'}

    def end_conversation(self):
        self.discourse_inventory = {}
        self.index_counter = 1
        log('CONVERSATION ENDED.')

    def consume_index(self):
        idx = self.index_counter
        self.index_counter += 1
        return idx

    def get_index_counter(self):
        return self.index_counter

    def remove_object(self, idx):
        self.discourse_inventory.pop(str(idx), None)

    def get_object(self, idx):
        return self.discourse_inventory[idx]

    def update_discourse_inventory(self, idx, criteria):
        self.discourse_inventory[str(idx)].update(criteria)

    def create_object(self, criteria):
        """
        Creates a new object into the discourse inventory in the global space on the basis of input
        criteria (data fields in the dictionary).
        """
        idx = self.consume_index()
        self.discourse_inventory[str(idx)] = criteria
        self.discourse_inventory[str(idx)]['Semantic space'] = 'GLOBAL'
        log(f'Object [{idx}] was created into global space...')
        return str(idx)

    def get_compatible_objects(self, filter_criteria):
        """
        Returns a list of indexes in the global discourse inventory that match with the filter criteria.
        """
        idx_list = []
        for idx in self.discourse_inventory:
            select_this_item = True
            # Examine all fields in the object in the discourse inventory...
            for field in self.discourse_inventory[idx]:
                # ...with the exception of the excluded fields
                if field not in self.excluded_fields:
                    if field in filter_criteria and filter_criteria[field] != self.discourse_inventory[idx][field]:
                        select_this_item = False  # The object is rejected if a mismatching (field, value) pair is found.
                        break
            if select_this_item:
                idx_list.append(idx)
        return idx_list

    def select_cognitive_objects(self, cognitive_objects, weights, instructions, strength=1):
        """
        NOT USED IN THE PRESENT IMPLEMENTATION

        Selects (ranks) cognitive objects in the set {cognitive_objects} on the basis of input instructions.
        This is a global cognitive operation that is used to weight and rank alternatives.

        The set {objects} contains a list of cognitive objects, in this case they are indexes to objects
        in the global discourse inventory (thus, cognitive objects in current discourse).

        The dictionary {weights} contains the weights of cognitive objects in {objects}. This will be
        modified by the function.

        Instructions contains a tuple (rule, reference_set) which tells how the weights should be
        modified. The reference_set contains cognitive objects (possibly overlapping with {objects}) and
        rule is either NEW or OLD, with the following interpretations:

        NEW against the reference set: weights of objects that are also in the reference set are lowered
        OLD against the reference set: weights of objects that are also in the reference set are increased

        Strength gives the strength of the modification (1 = full)
        """

        rule, reference_set = instructions

        for obj in reference_set:
            if rule == 'NEW':
                if obj in cognitive_objects:
                    weights[obj] = weights[obj] * (1 - strength)
            elif rule == 'OLD':
                if obj in cognitive_objects:
                    if strength == 1:
                        weights[obj] = 1
                    else:
                        weights[obj] = weights[obj] * (1 + strength)
        return weights

