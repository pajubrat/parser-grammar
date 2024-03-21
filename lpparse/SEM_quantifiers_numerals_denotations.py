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
        return ps.sustains_reference() or ps.referential()

    def remove_object(self, idx):
        self.inventory.pop(idx, None)

    def get_object(self, idx):
        return self.inventory[idx]

    def update_discourse_inventory(self, idx, criteria):
        self.inventory[idx].update(criteria)

    def reconstruct_assignments(self, ps):

        log(f'\n\t\tDenotations:')
        self.referential_constituents_feed = self.calculate_possible_denotations_(ps)
        log(f'\n\t\tAssignments: ')
        if not self.referential_constituents_feed:
            return

        self.create_assignments_from_denotations_(0, 0, {})
        return self.all_assignments

    def calculate_possible_denotations_(self, ps):
        L1 = []
        L2 = []
        if not ps.copied:
            if ps.complex():
                L1 = self.calculate_possible_denotations_(ps.left)
                L2 = self.calculate_possible_denotations_(ps.right)
            else:
                if self.narrow_semantics.has_referential_index(ps, 'QND'):
                    idx, space = self.narrow_semantics.get_referential_index_tuple(ps, 'QND')
                    self.inventory[idx]['Denotations'] = self.create_all_denotations(ps)
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
        log(f'\n\t\t\tAssignment {complete_assignment}: ')
        weighted_assignment['weight'] = 1
        for expression in self.referential_constituents_feed:
            if not self.binding_theory_conditions(expression, complete_assignment):
                weighted_assignment['weight'] = 0
                log('Rejected by binding.')
            if not self.predication_theory_conditions(expression, complete_assignment):
                weighted_assignment['weight'] = 0
                log('Rejected by predication theory.')
        if weighted_assignment['weight'] > 0:
            log('Accepted.')
        return weighted_assignment

    def predication_theory_conditions(self, expression, complete_assignment):
        idx_QND_predicate, name, ps, denotations = expression

        # Apply the condition only to heads which have both predicate and referential argument interpretations
        if self.narrow_semantics.query['PRE']['Accept'](ps) and self.narrow_semantics.query['QND']['Accept'](ps):

            # Get referential interpretation from the predicate
            idx_pred, space_pred = self.narrow_semantics.get_referential_index_tuple(ps, 'QND')

            if idx_pred:
                # Examine if the predicate has been linked with an argument
                for predicate, argument in self.narrow_semantics.speaker_model.predicate_argument_dependencies:
                    if ps == predicate:

                        # Get referential interpretation from the argument
                        idx_arg, space_arg = self.narrow_semantics.get_referential_index_tuple(argument, 'QND')

                        # Predicate theory only applies if the argument is linked with a reference
                        # (This condition is violated exceptionally if the linked argument is EPP-related filler)
                        if idx_arg:

                            # Check that the predicate reference and the argument are the same
                            if complete_assignment[idx_arg] != complete_assignment[idx_pred]:
                                return False
        return True

    def binding_theory_conditions(self, expression, complete_assignment):
        idx, name, ps, denotations = expression
        for feature in list(self.get_R_features(ps)):
            D, rule, intervention_feature, interface = self.open_R_feature(feature)
            if {rule} & {'NEW', 'OLD'}:
                reference_set = self.reference_set(ps, intervention_feature, complete_assignment)
                if not self.narrow_semantics.global_cognition.general_evaluation(complete_assignment[idx], rule, reference_set):
                    return False
        return True

    def reference_set(self, ps, intervention_feature, complete_assignment):
        reference_set = set()
        for const in (node for node in ps.upward_path() if
                      self.narrow_semantics.has_referential_index(node.head()) and
                      self.narrow_semantics.exists(node.head(), 'QND') and
                      node.head() != ps and
                      not node.copied):
            reference_set.add(complete_assignment[self.narrow_semantics.get_referential_index(const.head(), 'QND')])
            if intervention_feature and \
                    not const.copied and \
                    {intervention_feature}.issubset(const.head().features):
                break
        return reference_set

    def create_all_denotations(self, ps):
        return self.narrow_semantics.global_cognition.get_compatible_objects(self.inventory[self.narrow_semantics.get_referential_index(ps, 'QND')])

    def R_feature(self, feature):
        return feature.split(':')[0] == 'R'

    def get_R_features(self, ps):
        return {feature for feature in ps.head().features if self.R_feature(feature)}

    def open_R_feature(self, feature):
        if not self.R_feature(feature) or len(feature.split(':')) != 3:
            return None, None, None, None
        if '/' in feature:
            feature_, interface = feature.split('/')
        else:
            feature_ = feature
            interface = 'LF structure'
        component = feature_.split(':')
        return component[0], component[1], component[2], interface

    def project(self, ps, idx):
        self.inventory[idx] = self.apply_criteria(self.narrow_semantics.default_criteria(ps, 'QND'), ps)
        log(f'{ps.head().max().illustrate()}: ({idx}, QND)')

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
        elif head.mother_ and head.sister():
            return f'[{head.illustrate()} {head.sister().illustrate()}]'
        else:
            return f'{head.illustrate}'

    def detect_phi_conflicts(self, ps):
        for phi in ps.head().get_phi_set():
            if phi[-1] == '*':
                log(f'\n\t\t\t{ps.illustrate()} has a phi-feature conflict with {phi}.')
                self.narrow_semantics.phi_interpretation_failed = True

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
