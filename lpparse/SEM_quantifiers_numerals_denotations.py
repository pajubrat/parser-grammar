# This class implements numerical and quantificational cognition
# It mediates between the syntax-semantics interface and the discourse inventory
from support import log

class QuantifiersNumeralsDenotations:
    def __init__(self, narrow_semantics):
        self.narrow_semantics = narrow_semantics    # Access to narrow semantics (if needed)
        self.discourse_inventory = {}               # Bookkeeping for fixed denotation sets
        self.denotations_dict = {}                  # Holds temporary denotations
        self.criteria_function = {'D:REF:PROPER_NAME': self.criterion_proper_name,
                                  'PHI': self.criterion_phi_features,
                                  }

    def reset(self):
        self.discourse_inventory = {}

    def is_Dfeature(self, feature):
        if feature.split(':')[0] == 'D' or feature.split(':')[0] == 'PHI':
            return True

    def get_Dfeatures(self, ps):
        Dfeatures = set()
        for f in ps.head().features:
            if self.is_D_feature(f):
                Dfeatures.add(f)
        return Dfeatures

    def analyse_Dfeature(self, feature):
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
        return {'D', 'NUM', 'Q', 'DEM', 'n', 'D/rel'} & head.features

    def set_denotation(self, ps):
        """
        This function will create a dictionary holding the denotations for the expression [ps] inside the QND space.
        """

        # Create object to QND space
        idx = str(self.narrow_semantics.global_cognition.consume_index())
        self.discourse_inventory[idx] = self.apply_criteria(self.default_criteria(ps), ps)
        log(f'Denotation for {ps} was created into QND space...')

    def default_criteria(self, ps):
        return {'Referring constituent': f'{ps}',
                      'Reference': f'{ps.illustrate()}',
                      'Semantic space': 'QND',
                      'Semantic type': self.narrow_semantics.get_semantic_types(ps),
                      'Operator': self.is_operator(ps)
                      }

    def is_operator(self, ps):
        if self.narrow_semantics.operator_variable_module.scan_criterial_features(ps) and 'FIN' not in ps.features:
            return True

    def remove_object(self, idx):
        self.discourse_inventory.pop(idx, None)

    def get_object(self, idx):
        return self.discourse_inventory[idx]

    def update_discourse_inventory_compositionally(self, idx, criteria):
        self.discourse_inventory[idx].update(criteria)

    def apply_criteria(self, criteria, ps):
        log(f'Applying semantic criteria...')
        for feature in ps.head().features:
            if self.is_Dfeature(feature):
                feature_type = feature.split(':')[0]
                if feature in self.criteria_function:
                    self.criteria_function[feature](criteria, ps, feature)
                elif feature_type in self.criteria_function:
                    self.criteria_function[feature_type](criteria, ps, feature)
        log(f'Done.')
        return criteria

    def criterion_proper_name(self, criteria, ps, feature):
        log(f'{feature}, ')
        pf_features = sorted(ps.get_pf())
        if not pf_features:
            pf_features = ['Unknown name']
        criteria.update({'Proper name': pf_features[0]})

    def criterion_phi_features(self, criteria, ps, feature):
        log(f'{feature}, ')
        if 'Phi-set' in criteria:
            criteria['Phi-set'].add(feature)
        else:
            criteria['Phi-set'] = {feature}
