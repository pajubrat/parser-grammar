from support import log
import itertools


class GlobalCognition:
    def __init__(self):
        self.inventory = {}
        self.index_counter = {'QND': 1, 'GLOBAL': 1, 'PRE': 1}

    def reset(self):
        self.inventory = {}
        self.index_counter = {'QND': 1, 'GLOBAL': 1, 'PRE': 1}

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
        idx = self.create_object(semantic_object_dict)
        self.inventory[idx]['Semantic space'] = 'GLOBAL'
        return self.inventory[idx]

    def create_object(self, ontology_attributes_dict):
        idx = self.consume_index()
        self.inventory[str(idx)] = ontology_attributes_dict
        log(f'\n\t\tProject object ({idx}, GLOBAL) for {ontology_attributes_dict["Reference"]}')
        return str(idx)

    def ontological_compatibility(self, attribute_dict1, attribute_dict2):
        def included(field):
            """Defines which ontological attributes are included in the comparisons"""
            return field in {'Semantic type', 'Number', 'Person', 'Class', 'Gender'}

        for attribute_pair in itertools.product(attribute_dict1.items(), attribute_dict2.items()):
            if included(attribute_pair[0][0]) and included(attribute_pair[0][0]) and \
                    attribute_pair[0][0] == attribute_pair[1][0] and \
                    attribute_pair[0][1] != attribute_pair[1][1]:
                return False
        return True

    def get_compatible_objects(self, filter_criteria):
        return [idx for idx in self.inventory.keys() if self.ontological_compatibility(filter_criteria, self.inventory[idx])]
