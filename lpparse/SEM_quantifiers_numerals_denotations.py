# This class implements numerical and quantificational cognition
# It mediates between the syntax-semantics interface and the global discourse inventory
# Responds to R-features ([R:...], [PHI:...])
from support import log

class QuantifiersNumeralsDenotations:
    def __init__(self, narrow_semantics):
        self.narrow_semantics = narrow_semantics
        self.inventory = {}
        self.one_complete_assignment = {}
        self.all_assignments = []
        self.referential_constituents_feed = []
        self.criteria_function = {'R:REF:NAME': self.criterion_proper_name,
                                  'PHI': self.criterion_phi_features}

    def reset(self):
        self.inventory = {}
        self.all_assignments = []
        self.one_complete_assignment = {}

    def accept(self, ps):
        return self.has_adequate_phi_set(ps) or 'φ' in ps.head().features

    def is_operator(self, ps):
        return self.narrow_semantics.operator_variable_module.scan_criterial_features(ps) and 'FIN' not in ps.features

    def remove_object(self, idx):
        self.inventory.pop(idx, None)

    def get_object(self, idx):
        return self.inventory[idx]

    def update_discourse_inventory(self, idx, criteria):
        self.inventory[idx].update(criteria)

    def reconstruct_assignments(self, ps):
        if self.narrow_semantics.controlling_parsing_process.first_solution_found:
            self.narrow_semantics.semantic_interpretation['Assignments'] = []
            return

        log(f'\n\t\tDenotations:')
        self.referential_constituents_feed = self.calculate_possible_denotations_(ps)

        log(f'\n\t\tAssignments: ')
        if not self.referential_constituents_feed:
            return
        self.create_assignments_from_denotations_(0, 0, {})
        self.narrow_semantics.semantic_interpretation['Assignments'] = self.all_assignments

    def calculate_possible_denotations_(self, ps):
        L1 = []
        L2 = []
        if not ps.find_me_elsewhere:
            if ps.is_complex():
                L1 = self.calculate_possible_denotations_(ps.left_const)
                L2 = self.calculate_possible_denotations_(ps.right_const)
            else:
                if self.narrow_semantics.has_referential_index(ps, 'QND'):
                    idx, space = self.narrow_semantics.get_referential_index_tuples(ps, 'QND')
                    self.inventory[idx]['Denotations'] = self.create_all_assignments(ps)
                    log(f'\n\t\t\t{self.inventory[idx]["Reference"]}~{self.inventory[idx]["Denotations"]} ')
                    return [(idx, f'{ps.illustrate()}', ps, self.inventory[idx]['Denotations'])]
        return L1 + L2

    def create_assignments_from_denotations_(self, c_index, d_index, one_complete_assignment):
        idx, const, ps, denotations = self.referential_constituents_feed[c_index]
        denotation = denotations[d_index]
        one_complete_assignment[idx] = denotation
        if len(one_complete_assignment) == len(self.referential_constituents_feed):
            self.all_assignments.append(self.calculate_assignment_weight(one_complete_assignment))
        if c_index < len(self.referential_constituents_feed) - 1:
            self.create_assignments_from_denotations_(c_index + 1, 0, one_complete_assignment.copy())
        if d_index < len(denotations) - 1:
            self.create_assignments_from_denotations_(c_index, d_index + 1, one_complete_assignment.copy())

    def calculate_assignment_weight(self, complete_assignment):
        weighted_assignment = complete_assignment.copy()
        log(f'\n\t\t\tAssignment {complete_assignment} ')
        weighted_assignment['weight'] = 1
        for expression in self.referential_constituents_feed:
            if not self.binding_theory_conditions(expression, complete_assignment):
                weighted_assignment['weight'] = 0
                log('rejected by binding.')
            if not self.predication_theory_conditions(expression, complete_assignment):
                weighted_assignment['weight'] = 0
                log('rejected by predication theory.')
        if weighted_assignment['weight'] > 0:
            log('accepted.')
        return weighted_assignment

    def predication_theory_conditions(self, expression, complete_assignment):
        idx_QND_predicate, name, ps, denotations = expression
        if self.narrow_semantics.query['PRE']['Accept'](ps) and self.narrow_semantics.query['QND']['Accept'](ps):
            idx_pred, space_pred = self.narrow_semantics.get_referential_index_tuples(ps, 'QND')
            for predicate, argument in self.narrow_semantics.predicate_argument_dependencies:
                if ps == predicate:
                    idx_arg, space_arg = self.narrow_semantics.get_referential_index_tuples(argument, 'QND')
                    if complete_assignment[idx_arg] != complete_assignment[idx_pred]:
                        return False
        return True

    def binding_theory_conditions(self, expression, complete_assignment):
        idx, name, ps, denotations = expression
        for feature in list(self.get_R_features(ps)):
            D, rule, intervention_feature = self.open_R_feature(feature)
            if {rule} & {'NEW', 'OLD'}:
                reference_set = self.reference_set(ps, intervention_feature, complete_assignment)
                log(f'(R={reference_set}) ')
                if not self.narrow_semantics.global_cognition.general_evaluation(complete_assignment[idx], rule, reference_set):
                    return False
        return True

    def reference_set(self, ps, intervention_feature, complete_assignment):
        return {complete_assignment[self.narrow_semantics.get_referential_index(head, 'QND')]
                for head in ps.constituent_vector(intervention_feature)
                if self.narrow_semantics.has_referential_index(head) and
                self.narrow_semantics.exists(head, 'QND')}

    def create_all_assignments(self, ps):
        filter_criteria = self.inventory[self.narrow_semantics.get_referential_index(ps, 'QND')]
        return self.narrow_semantics.global_cognition.get_compatible_objects(filter_criteria)

    def R_feature(self, feature):
        feature_list = feature.split(':')
        if feature_list[0] == 'R' and len(feature_list) == 3:
            return True
        if feature_list[0] == 'PHI':
            return True

    def get_R_features(self, ps):
        return {feature for feature in ps.head().features if self.R_feature(feature)}

    def open_R_feature(self, feature):
        if not self.R_feature(feature):
            return None, None, None
        components = feature.split(':')
        if len(components) == 3:
            return components[0], components[1], components[2]
        return None, None, None

    def project(self, ps, idx):
        self.inventory[idx] = self.apply_criteria(self.narrow_semantics.default_criteria(ps, 'QND'), ps)
        log(f'Project ({idx}, QND) for {ps.head().illustrate()}P ({ps.head().max().illustrate()})...')

    def apply_criteria(self, criteria, ps):
        for feature in list(self.get_R_features(ps)):
            feature_type = feature.split(':')[0]
            if feature in self.criteria_function:
                self.criteria_function[feature](criteria, ps, feature)
            elif feature_type in self.criteria_function:
                self.criteria_function[feature_type](criteria, ps, feature)
        criteria['Semantic type'] = {'§Thing'}

        return criteria

    def criterion_proper_name(self, criteria, ps, feature):
        pf_features = sorted(ps.sister().get_pf())
        if not pf_features:
            pf_features = ['Unknown name']
        criteria.update({'Proper name': pf_features[0]})

    def criterion_phi_features(self, criteria, ps, feature):
        def interpret_phi_features(phi_set):
            def match(set1, set2):
                return set2 == set1 & set2
            semantic_fields = {}
            # Person and number
            if match(phi_set, {'PHI:NUM:SG', 'PHI:PER:1'}):
                semantic_fields['Participant role'] = 'Speaker'
            if match(phi_set, {'PHI:NUM:SG', 'PHI:PER:2'}):
                semantic_fields['Participant role'] = 'Hearer'
            if match(phi_set, {'PHI:NUM:PL', 'PHI:PER:1'}):
                semantic_fields['Participant role'] = 'Speaker and others'
            if match(phi_set, {'PHI:NUM:PL', 'PHI:PER:2'}):
                semantic_fields['Participant role'] = 'Hearer and others'
            if match(phi_set, {'PHI:NUM:SG', 'PHI:PER:3'}):
                semantic_fields['Participant role'] = 'Third party'
            if match(phi_set, {'PHI:NUM:PL', 'PHI:PER:3'}):
                semantic_fields['Participant role'] = 'Third party and others'
            if match(phi_set, {'PHI:HUM:HUM'}):
                semantic_fields['Human'] = 'Human'
            if match(phi_set, {'PHI:HUM:NONHUM'}):
                semantic_fields['Human'] = 'Nonhuman'
            if match(phi_set, {'PHI:GEN:M'}):
                semantic_fields['Gender'] = 'M'
            if match(phi_set, {'PHI:GEN:F'}):
                semantic_fields['Gender'] = 'F'
            if match(phi_set, {'PHI:GEN:N'}):
                semantic_fields['Gender'] = 'N'
            return semantic_fields

        #----- main function -----#
        if 'Phi-set' in criteria:
            criteria['Phi-set'].add(feature)
        else:
            criteria['Phi-set'] = {feature}
        criteria.update(interpret_phi_features(criteria['Phi-set']))

    def present(self, head):
        if self.narrow_semantics.query['PRE']['Accept'](head):
            return f'pro({head})'
        elif head.mother:
            return f'[{head.illustrate()} {head.sister().illustrate()}]'
        else:
            return f'{head.illustrate}'

    def detect_phi_conflicts(self, ps):
        for phi in ps.get_phi_set():
            if phi[-1] == '*':
                log(f'{ps} induces a phi-feature conflict...')
                self.narrow_semantics.phi_interpretation_failed = True

    def has_adequate_phi_set(self, h):
        features_detected = {}
        for f in h.features:
            if f[:4] == 'PHI:' and f[-1] != '_':    # Check only valued phi-features
                features_detected[f[:7]] = True              # Record the feature type
                for g in h.features:
                    if g[:4] == 'PHI:' and g[-1] != '_':  # Check only valued phi-features
                        f_type = f.split(':')[1]
                        g_type = g.split(':')[1]
                        f_value = f.split(':')[2]
                        g_value = g.split(':')[2]
                        # If there is a feature type T with two difference values, we have feature conflict
                        if f_type == g_type and f_value != g_value:
                            return False
        if 'PHI:NUM' in features_detected and 'PHI:PER' in features_detected:
            return True

    def format_assignment(self, assignment):
        s = '('
        for i, (idx, denotation) in enumerate(assignment.items()):
            key_str = str(idx)
            den_str = str(denotation)
            s = s + key_str + '~' + den_str
            if i < len(assignment) - 1:
                s = s + ', '
        s = s + ') '
        return s