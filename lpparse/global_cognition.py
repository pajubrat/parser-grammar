from support import log

class GlobalCognition:
    def __init__(self):
        self.inventory = {}
        self.index_counter = {'QND': 1, 'GLOBAL': 1, 'PRE': 1}

    def end_conversation(self):
        self.inventory = {}
        self.index_counter = {'QND': 1, 'GLOBAL': 1, 'PRE': 1}
        log('\tCONVERSATION ENDED.')

    def present(self, head):
        return f'{head.max().illustrate()}'

    def consume_index(self, space='GLOBAL'):
        idx = self.index_counter[space]
        self.index_counter[space] += 1
        return idx

    def remove_object(self, idx):
        self.inventory.pop(str(idx), None)

    def get_object(self, idx):
        return self.inventory[idx]

    def update_discourse_inventory(self, idx, criteria):
        self.inventory[str(idx)].update_contents(criteria)

    def project(self, X, semantic_object_dict):
        return self.create_object({'Semantic space': 'GLOBAL',
                                   'Reference': semantic_object_dict['Reference'],
                                   'Semantic type': semantic_object_dict.get('Semantic type', 'unknown'),
                                   'Phi properties': semantic_object_dict.get('Phi properties', '')})

    def create_object(self, ontology_attributes_dict):
        idx = self.consume_index()
        self.inventory[str(idx)] = ontology_attributes_dict
        log(f'\n\t\t\tProject object ({idx}, GLOBAL) for {ontology_attributes_dict["Reference"]}')
        return str(idx)

    def get_compatible_objects(self, filter_criteria):
        # filter_criterial = QND attributes dict

        def inclusion(field):
            return field not in {'Denotations', 'Semantic space', 'Denotation weights', 'Reference', 'Operator', 'Referring constituent'}

        idx_list = []
        for idx in self.inventory:
            mismatches = [field for field in self.inventory[idx].keys() if inclusion(field) and
                          filter_criteria.get(field, None) != self.inventory[idx][field]]
            if not mismatches:
                idx_list.append(idx)
        return idx_list
