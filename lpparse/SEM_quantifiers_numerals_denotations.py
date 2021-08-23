# This class implements numerical and quantificational cognition
# It mediates between the syntax-semantics interface and the global discourse inventory
# Responds to D-features ([D:...], [PHI:...])
from support import log

class QuantifiersNumeralsDenotations:
    def __init__(self, narrow_semantics):
        self.narrow_semantics = narrow_semantics    # Access to narrow semantics (if needed)
        self.inventory = {}                         # Bookkeeping for fixed denotation sets
        self.one_complete_assignment = {}                        # Assignment dictionary (temporary)
        self.all_assignments = []                       # Stored and weighted assignments

        # All (or many) D-features are associated with a separate interpretation function
        self.criteria_function = {'D:REF:PROPER_NAME': self.criterion_proper_name,
                                  'PHI': self.criterion_phi_features,
                                  }

    def reconstruct_assignments(self, ps):
        """
        Wrapper for the recursive assignment generation function.
        1. Referential expressions are provided with denotations lists and are collected into a seed list.
        2. The seed list is used to create a list of actual assignments.
        3. Assignments are stored into the QND space object
        """
        log(f'\n\t\tComputing assignments...')
        log('Possible denotations: ')
        referential_constituents_seed_list = self.calculate_possible_denotations_(ps)
        log('Assignments: ')
        self.create_assignments_from_denotations_(referential_constituents_seed_list, 0, 0)
        self.narrow_semantics.semantic_interpretation['Assignments'] = self.all_assignments

    def calculate_possible_denotations_(self, ps):
        """
        Recursively associated any head with referential index with a denotation list which enumerates
        all possible denotations for that constituent, given the current contents of the discourse inventory.
        """
        L1 = []
        L2 = []
        if not ps.find_me_elsewhere:
            if ps.is_complex():
                # Recursion
                L1 = self.calculate_possible_denotations_(ps.left_const)
                L2 = self.calculate_possible_denotations_(ps.right_const)

            # Primitive constituent
            else: # If the primitive constituent is referential, we generate assignments for it
                if self.narrow_semantics.has_referential_index(ps):

                    # Store the list of possible denotations
                    idx, space = self.narrow_semantics.get_referential_index_tuple(ps)
                    self.inventory[idx]['Denotations'] = self.generate_assignments(ps)
                    log(f'({self.inventory[idx]["Reference"]}~{self.inventory[idx]["Denotations"]}), ')

                    # Generate entry for the assignment structure dictionary, returned to caller
                    return [(idx, f'{ps.max().illustrate()}', ps, self.inventory[idx]['Denotations'])]

        # Combine the assignment structures from left and right
        return L1 + L2

    def create_assignments_from_denotations_(self, referential_constituents_seed_list, c_index, d_index):
        # Loop through all referential constituents in the assignment_seed
        for c in range(c_index, len(referential_constituents_seed_list)):
            idx, const, ps, denotations = referential_constituents_seed_list[c]

            # Loop all denotations for the referential constituent
            for d in range(d_index, len(denotations)):
                denotation = denotations[d]

                # Add the denotation to complement_assignment
                self.one_complete_assignment[idx] = denotation

                # Assignment is stored if and only if all constituents are provided denotation
                if len(self.one_complete_assignment) == len(referential_constituents_seed_list):
                    self.all_assignments.append(self.one_complete_assignment.copy())
                    log(f'{self.format_assignment(self.one_complete_assignment)}')
                self.create_assignments_from_denotations_(referential_constituents_seed_list, c + 1, d + 1)

    def generate_assignments(self, ps):
        """
        Generates the denotations set for a semantic QND object
        """
        # Get referential index to the QND semantic object
        idx, space = self.narrow_semantics.get_referential_index_tuple(ps)

        # Get the QND space object which determines the criteria
        filter_criteria = self.inventory[idx]

        # Get all GLOBAL discourse inventory objects which do not violate the criteria
        filter_criteria['Denotations'] = self.narrow_semantics.global_cognition.get_compatible_objects(filter_criteria)

        # Return the denotations
        return filter_criteria['Denotations']

    def reset(self):
        """
        Discharges the discourse inventory
        """
        self.inventory = {}
        self.all_assignments = []
        self.one_complete_assignment = {}

    def is_D_feature(self, feature):
        """
        Recognizes D-features. A D-feature is a feature type that is diverted to this module. It can be one of
        two types, [D:...] or [PHI:...]
        """
        if feature.split(':')[0] == 'D' or feature.split(':')[0] == 'PHI':
            return True

    def get_D_features(self, ps):
        """
        Returns the set of D-features from the head.
        """
        return {feature for feature in ps.head().features if self.is_D_feature(feature)}

    def analyse_D_feature(self, feature):
        """
        Returns the three components (d, type, value) of a D-feature, if the input
        feature is a D-feature, otherwise returns (None, None, None)
        """
        if not self.is_Dfeature(feature):
            return None, None, None
        components = feature.split(':')
        if len(components) != 3:
            return None, None, None
        return components[0], components[1], components[2]

    def recognize(self, head):
        """
        This function returns True if the module "recognizes" the head. Recognition means
        intuitively that the module is able to interpret the head semantically. A head is currently
        recognized by its lexical category feature, later by the existence of a D-feature.
        The category feature now substitutes for the latter that has not been implemented
        fully.
        """
        return {'D', 'NUM', 'Q', 'DEM', 'n', 'D/rel', 'φ'} & head.features

    def project_QND_entry_into_inventory(self, ps):
        """
        This function will create a dictionary holding the denotations for the expression [ps] inside the QND space.
        """

        # Create object to QND space
        idx = str(self.narrow_semantics.global_cognition.consume_index())
        self.inventory[idx] = self.apply_criteria(self.default_criteria(ps), ps)
        log(f'Denotation for {ps} was created into QND space...')

    def apply_criteria(self, criteria, ps):
        """
        Examines all D-features in the head and transforms them into criteria (fields in the QND inventory entry),
        then adds them into input parameter dict [criteria].
        """
        log(f'Applying semantic criteria...')
        for feature in list(self.get_D_features(ps)):
            feature_type = feature.split(':')[0]
            # If the feature has been associated with criteria function, apply it and store result.
            if feature in self.criteria_function:
                self.criteria_function[feature](criteria, ps, feature)
            # If the feature type has been associated with function, apply it and store result.
            elif feature_type in self.criteria_function:
                self.criteria_function[feature_type](criteria, ps, feature)
        log(f'Done.')
        return criteria

    def default_criteria(self, ps):
        """
        Definition for default criteria applied to all objects in the QND space
        """
        return {'Referring constituent': f'{ps}',
                      'Reference': f'{ps.illustrate()}',
                      'Semantic space': 'QND',
                      'Semantic type': self.narrow_semantics.get_semantic_types(ps),
                      'Operator': self.is_operator(ps)
                      }

    def is_operator(self, ps):
        """
        Definition for operator
        """
        return self.narrow_semantics.operator_variable_module.scan_criterial_features(ps) and 'FIN' not in ps.features

    def remove_object(self, idx):
        self.inventory.pop(idx, None)

    def get_object(self, idx):
        return self.inventory[idx]

    def update_discourse_inventory_compositionally(self, idx, criteria):
        self.inventory[idx].update(criteria)

    def criterion_proper_name(self, criteria, ps, feature):
        """
        Criterion function for proper names, which adds the proper name into the QND space inventory entry.
        """
        log(f'{feature}, ')
        pf_features = sorted(ps.get_pf())
        if not pf_features:
            pf_features = ['Unknown name']
        criteria.update({'Proper name': pf_features[0]})

    def criterion_phi_features(self, criteria, ps, feature):
        """
        Criterion function for phi-features, which adds the phi-features into the QND space inventory entry
        """
        log(f'{feature}, ')
        if 'Phi-set' in criteria:
            criteria['Phi-set'].add(feature)
        else:
            criteria['Phi-set'] = {feature}

    def format_assignment(self, assign):
        s = ''
        for i, (idx, denotation) in enumerate(assign.items()):
            s = s + self.inventory[idx]["Reference"] + '~' + denotation + ', '
        return s