from support import log

class GlobalCognition:
    def __init__(self):
        self.discourse_inventory = {}
        self.index_counter = 1

    def initialize(self):
        self.discourse_inventory = {}
        self.index_counter = 1

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
        idx = self.consume_index()
        self.discourse_inventory[str(idx)] = criteria
        self.discourse_inventory[str(idx)]['Semantic space'] = 'GLOBAL'
        log(f'Object [{idx}] was created into global space...')
        return {str(idx)}

    def filter_compatible_objects(self, filter_criteria):
        idx_set = set()
        for idx in self.discourse_inventory:
            select = True
            for field in self.discourse_inventory[idx]:
                if field not in {'Denotations', 'Semantic space'}:
                    if field in filter_criteria and filter_criteria[field] != self.discourse_inventory[idx][field]:
                        select = False  # The object is reject if a mismatching (field, value) pair is found.
                        break
            if select:
                idx_set.add(idx)
        return idx_set
