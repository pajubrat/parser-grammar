# This class implements numerical and quantificational cognition
# It mediates between the syntax-semantics interface and the global discourse inventory
# Responds to D-features ([D:...], [PHI:...])
from support import log

class QuantifiersNumeralsDenotations:
    def __init__(self, narrow_semantics):
        self.narrow_semantics = narrow_semantics    # Access to narrow semantics (if needed)
        self.inventory = {}                         # Bookkeeping for fixed denotation sets
        self.denotations_dict = {}                  # Holds temporary denotations

        # All (or many) D-features are associated with a separate interpretation function
        self.criteria_function = {'D:REF:PROPER_NAME': self.criterion_proper_name,
                                  'PHI': self.criterion_phi_features,
                                  }

    def reset(self):
        """
        Discharges the discourse inventory
        """
        self.inventory = {}

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