from support import log

class GlobalCognition:
    def __init__(self):
        self.discourse_inventory = {}
        self.index_counter = 1
        self.excluded_fields = {'Denotations', 'Semantic space', 'Denotation weights', 'Reference'}

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
        Those semantic objects are rejected which induce a type:value mismatch. Thus, missing type does
        not constitute rejection.
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

    def general_evaluation(self, mental_object, rule, reference_set):
        """
        Evaluates whether [mental object] satisfies rules contained in [instructions].

        [Instructions] contains a [rule] and a possible [reference set] of other objects, which together determine
        whether the mental object satisfies [instructions].

        [Mental object] is a idx handle to a global object. [Reference set] contains a set of idx handles to global
        objects.
        """

        if 'NEW' in rule:
            return not {mental_object} & reference_set

        if 'OLD' in rule:
            return {mental_object} & reference_set