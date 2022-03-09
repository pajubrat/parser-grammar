from support import log

class GlobalCognition:
    def __init__(self, narrow_semantics):
        self.inventory = {}
        self.narrow_semantics = narrow_semantics
        self.index_counter = 1
        self.excluded_fields = {'Denotations', 'Semantic space', 'Denotation weights', 'Reference', 'Operator', 'Referring constituent'}

    def end_conversation(self):
        self.inventory = {}
        self.index_counter = 1
        log('CONVERSATION ENDED.')

    def present(self, head):
        return f'{head.max().illustrate()}'

    def consume_index(self):
        idx = self.index_counter
        self.index_counter += 1
        return idx

    def get_index_counter(self):
        return self.index_counter

    def remove_object(self, idx):
        self.inventory.pop(str(idx), None)

    def get_object(self, idx):
        return self.inventory[idx]

    def update_discourse_inventory(self, idx, criteria):
        self.inventory[str(idx)].update(criteria)

    def project(self, ps, semantic_object):
        criteria_for_new_global_object = self.narrow_semantics.default_criteria(ps, 'GLOBAL')
        semantic_object['Semantic space'] = 'GLOBAL'
        criteria_for_new_global_object.update(semantic_object)
        criteria_for_new_global_object.pop('Phi-set', None)
        string = self.create_object(criteria_for_new_global_object)
        return string

    def create_object(self, criteria):
        idx = self.consume_index()
        self.inventory[str(idx)] = criteria
        log(f'({idx}, GLOBAL)')
        return str(idx)

    def get_compatible_objects(self, filter_criteria):
        idx_list = []
        for idx in self.inventory:
            select_this_item = True
            for field in self.inventory[idx]:
                if field not in self.excluded_fields:
                    if field in filter_criteria and filter_criteria[field] != self.inventory[idx][field]:
                        select_this_item = False  # The object is rejected if a mismatching (field, value) pair is found.
                        break
            if select_this_item:
                idx_list.append(idx)
        return idx_list

    def general_evaluation(self, mental_object, rule, reference_set):
        if 'NEW' in rule:
            return not {mental_object} & reference_set
        if 'OLD' in rule:
            return {mental_object} & reference_set