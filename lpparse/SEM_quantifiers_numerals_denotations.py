# This class implements numerical and quantificational cognition
# It mediates between the syntax-semantics interface and the global discourse inventory
# Responds to R-features ([R:...], [PHI:...])
from support import log
from phrase_structure import PhraseStructure
import itertools

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

    def project(self, X, idx):
        log(f'\n\t\t\tProject {X}° in {X.max().illustrate()} ({idx}, QND)')
        self.inventory[idx] = self.extrapolate_semantic_attributes(X)
        return self.inventory[idx]

    def accept(self, X):
        return (X.complete_agreement_suffixes() and not X.AgreeLF_has_occurred()) or X.referential()

    def remove_object(self, idx):
        self.inventory.pop(idx, None)

    def get_object(self, idx):
        return self.inventory[idx]

    def update_discourse_inventory(self, idx, criteria):
        self.inventory[idx].update(criteria)

    def object_presentation(self, X):
        if X.referential():
            return f'{X.max().illustrate()}'
        return f'pro({X})'

    def reconstruct_assignments(self, ps):
        """
        Creates assignments for all referential expressions

        Assignment = interpretation in which all referential expressions in the expressions are provided a denotation,
        for example 'John(1) admires Mary(2)', where (1) and (2) are persons in the global semantic space
        All assignments = a set of possible assignments, for example 'John(1,2) admires Mary(1,2)'.

        Denotations/assignments are attached to semantic entries in the narrow semantics space (e.g. QND), which are linked to
        expressions in narrow syntax (i.e. Exp ~ QND entry ~ global objects). For example, quantifiers like 'some', 'three', 'all'
        have fixed QND entries which allow them to denote different objects and sets of objects in the global inventory.
        Global inventory can be modulated by context (e.g., prior sentences). Semantic entries are dictionaries keyed by an index,
        the latter a feature of the constituent in NS. For example, QND space entry for 'John' holds information about its intension
        such as 'person', 'male', 'singular' etc. which is then used to find possible denotations (e.g., we block 'John' ~ two female cats).
        The index features has form [IDX:n,QND], where n = key.

        If two Exp have the same index, they are synonyms in grammatical sense (e.g., pro and subject). If they have the same denotation,
        they are coreferential. Binding regulates coreferentiality.
        """
        log(f'\n\t\tPossible denotations:')
        # Referential constituents feed contains a list of tuples (index, expression (string), X, denotations) for each referential constituent,
        # where denotations is a list of global indexes compatible with the expression (e.g., male persons for 'John').
        self.referential_constituents_feed = self.calculate_possible_denotations(ps)
        log(f'\n\t\tAssignments: ')
        if self.referential_constituents_feed:
            self.create_assignments_from_denotations()
            self.narrow_semantics.speaker_model.results.store_output_fields('Binding', self.assignment_output_string(ps)[1:])
            return self.all_assignments

    def calculate_possible_denotations(self, X):
        denotations_lst = []
        if not X.copied:
            if X.complex():
                denotations_lst += self.calculate_possible_denotations(X.left())
                denotations_lst += self.calculate_possible_denotations(X.right())
            else:
                if self.narrow_semantics.has_referential_index(X, 'QND'):
                    idx, space = self.narrow_semantics.get_referential_index_tuple(X, 'QND')
                    self.inventory[idx]['Denotations'] = self.create_all_denotations(X)
                    log(f'\n\t\t\t{self.inventory[idx]["Reference"]}~{self.inventory[idx]["Denotations"]} ')
                    # Each denotation is a tuple (index in semantic space, expression, constituent itself, possible denotations)
                    denotations_lst = [(idx, f'{X.illustrate()}', X, self.inventory[idx]['Denotations'])]
        return denotations_lst

    def create_assignments_from_denotations(self):
        for assignment in itertools.product(*[tup[3] for tup in self.referential_constituents_feed]):               #   Create all possible assignments (tup[3] = connection of denotations)
            assignment_dict = {tup[0]: assignment[i] for i, tup in enumerate(self.referential_constituents_feed)}   #   Create assignment dict (because the rest is based on dicts)
            self.all_assignments.append(self.calculate_assignment_weight(assignment_dict))                          #   Calculate assignment weights

    def calculate_assignment_weight(self, complete_assignment_dict):
        weighted_assignment = complete_assignment_dict.copy()
        log(f'\n\t\t\tAssignment {self.print_assignment(complete_assignment_dict)} ')
        weighted_assignment['weight'] = 1
        for expression in self.referential_constituents_feed:
            if not self.binding_theory_conditions(expression, complete_assignment_dict):
                weighted_assignment['weight'] = 0
                log('rejected by binding.')
        if weighted_assignment['weight'] > 0:
            log('accepted.')
        return weighted_assignment

    def print_assignment(self, complete_assignment_dict):
        stri = ''
        if 'weight' in complete_assignment_dict and complete_assignment_dict['weight'] > 0:
            stri += '\t\t\t'
            for key, value in complete_assignment_dict.items():
                if key != 'weight':
                    stri += f'{self.get_object(key)["Reference"]}({key}) ~ {value}, '
            stri += '\n'
        return stri

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

    def assignment_output_string(self, ps):
        """Summarises binding dependencies in one string"""
        stri = ''
        if not ps.copied:
            if ps.left() and ps.right():
                stri += self.assignment_output_string(ps.left())
                stri += self.assignment_output_string(ps.right())
            if ps.zero_level():
                word = ''.join(sorted([f'{f[3:]}' for f in ps.features if f[:2] == 'PF' and f[3:] not in PhraseStructure.major_cats]))
                if word:
                    stri += ' ' + word
            # Create binding tags at the end of referential expressions
            if ps.mother() and ps.is_right() and self.narrow_semantics.get_referential_index_tuple_from_head(ps.sister(), 'QND')[0]:
                idx = self.narrow_semantics.get_referential_index_tuple_from_head(ps.sister(), 'QND')[0]
                self.determine_BindingIndexes(idx)
                stri += '(' + f'{",".join(self.inventory[idx]["BindingIndexes"])}' + ')'
        return stri

    def determine_BindingIndexes(self, idx):
        if 'BindingIndexes' not in self.inventory[idx]:     # Every expression initially has its own binding index
            self.inventory[idx]['BindingIndexes'] = idx
        for i in self.inventory.keys():
            if i == idx:
                break
            if i != idx:
                if self.coreference(i, idx):    # If X and Y co-refer, they must have the same binding index
                    self.inventory[i]['BindingIndexes'] = [i]
                    self.inventory[idx]['BindingIndexes'] = [i]
                if self.overlapping_reference(i, idx):  # If X and Y overlap in denotation, both binding indexes are shown
                    self.inventory[idx]['BindingIndexes'].add(i)

    def coreference(self, idx1, idx2):
        """Returns True if meanings idx1 and idx2 (in QND space) denote the same thing
        under all assignment (i.e. they co-refer)
        """
        for assignment in self.all_assignments:
            if assignment[idx1] != assignment[idx2] and assignment['weight'] > 0:
                return False
        return True

    def disjoint_reference(self, idx1, idx2):
        """Returns True if meanings idx1 and idx2 (in QND space) cannot denote the same thing
        under all assignments (i.e. they are disjoint)"""
        for assignment in self.all_assignments:
            if assignment[idx1] == assignment[idx2] and assignment['weight'] > 0:
                return False
        return True

    def overlapping_reference(self, idx1, idx2):
        """Returns True if meaning idx1 and idx2 (in QND space) can denote same things under
        some assignments (not disjoint) but not all (not coreferential)"""
        return not self.coreference(idx1, idx2) and not self.disjoint_reference(idx1, idx2)

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

    def extrapolate_semantic_attributes(self, X):
        semantic_attributes_dict = self.narrow_semantics.default_attributes(X, 'QND')
        for feature in list(self.get_R_features(X)):
            feature_type = feature.split(':')[0]
            if feature in self.criteria_function:
                self.criteria_function[feature](semantic_attributes_dict, X, feature)
            elif feature_type in self.criteria_function:
                self.criteria_function[feature_type](semantic_attributes_dict, X, feature)
        semantic_attributes_dict['Semantic type'] = {'§Thing'}
        return semantic_attributes_dict

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

    def detect_phi_conflicts(self, ps):
        for phi in ps.head().get_phi_set():
            if phi[-1] == '*':
                log(f'\n\t\t\t{ps.illustrate()} has a phi-feature conflict with {phi}.')
                self.narrow_semantics.phi_interpretation_failed = True
