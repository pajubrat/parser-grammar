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
        self.all_assignments = []

    def reset(self):
        self.inventory = {}
        self.all_assignments = []

    def project(self, X, idx):
        log(f'\n\t\t\tProject object ({idx}, QND) for {X.max().illustrate()}')
        self.inventory[idx] = self.extrapolate_semantic_attributes(X)
        return self.inventory[idx]

    def accept(self, X):
        return (X.complete_agreement_suffixes() and not X.AgreeLF_has_occurred()) or X.referential()

    def remove_object(self, idx):
        self.inventory.pop(idx, None)

    def get_object(self, idx):
        return self.inventory[idx]

    def update_discourse_inventory(self, idx, criteria):
        self.inventory[idx].update_contents(criteria)

    def object_presentation(self, X):
        if X.referential():
            return f'{X.max().illustrate()}'
        return f'pro({X})'

    def reconstruct_assignments(self, X):
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
        log(f'\n\t\tDenotations:')
        self.create_assignments_from_denotations(self.calculate_possible_denotations(X))
        self.narrow_semantics.speaker_model.results.store_output_field('Binding', self.assignment_output_string(X)[1:])
        log(f'\n\t\t\tSummary: {self.assignment_output_string(X)}')
        return self.all_assignments

    def calculate_possible_denotations(self, X):
        denotations_lst = []
        if not X.copied:
            if X.complex():
                denotations_lst += self.calculate_possible_denotations(X.left())
                denotations_lst += self.calculate_possible_denotations(X.right())
            else:
                if X.has_idx('QND'):
                    idx, space = X.get_idx_tuple('QND')
                    self.inventory[idx]['Denotations'] = self.create_all_denotations(X)
                    log(f'\n\t\t\t{self.inventory[idx]["Reference"]}~{self.inventory[idx]["Denotations"]} ')
                    denotations_lst = [(idx, f'{X.illustrate()}', X, self.inventory[idx]['Denotations'])]
        return denotations_lst

    def create_assignments_from_denotations(self, ref_constituents_lst):
        log(f'\n\t\tAssignments: ')
        for assignment in itertools.product(*[tup[3] for tup in ref_constituents_lst]):                        #   Create all possible assignments (tup[3] = connection of denotations)
            assignment = {tup[0]: assignment[i] for i, tup in enumerate(ref_constituents_lst)}                 #   Create assignment dict (because the rest is based on dicts)
            self.all_assignments.append(self.calculate_assignment_weight(assignment, ref_constituents_lst))    #   Calculate assignment weights

    def calculate_assignment_weight(self, assignment, ref_constituents_lst):
        weighted_assignment = assignment.copy()
        weighted_assignment['weight'] = 1
        log(f'\n\t\t\tAssignment {self.print_assignment(weighted_assignment)} ')

        for expression in ref_constituents_lst:
            if not self.binding_conditions(expression, assignment):
                weighted_assignment['weight'] = 0
                log('-')
        if weighted_assignment['weight'] > 0:
            log('+')
        return weighted_assignment

    def print_assignment(self, assignment):
        stri = ''
        if 'weight' in assignment and assignment['weight'] > 0:
            for key, value in assignment.items():
                if key != 'weight':
                    stri += f'{self.get_object(key)["Reference"]} ~ {value}, '
        return stri

    def binding_conditions(self, exp, assignment):
        def evaluate(semantic_object, rule_, semantic_working_memory):
            return ('NEW' in rule_ and not {semantic_object} & semantic_working_memory) or \
                   ('OLD' in rule_ and {semantic_object} & semantic_working_memory)

        idx, name, X, denotations = exp
        for f in self.get_R_features(X):
            R, rule, intervention = self.parse_R_feature(f)
            if not evaluate(assignment[idx], rule, X.construct_semantic_working_memory(intervention, assignment)):
                return False
        return True

    def assignment_output_string(self, X):
        """Summarises binding dependencies in one string"""
        def relevant_content(Y):
            if Y.check_some({'V', 'N', 'A', 'P', 'Adv', 'D'}):
                return ''.join([f[3:] for f in Y.features if f.startswith('PF:') and f[3:] not in PhraseStructure.major_cats and f[3:] != "'s"])

        stri = ''
        if not X.copied:
            if X.left() and X.right():
                stri += self.assignment_output_string(X.left())
                stri += self.assignment_output_string(X.right())
            if X.zero_level() and relevant_content(X):
                stri += ' ' + relevant_content(X)

            # Create binding tags at the end of referential expressions
            if X.mother() and X.is_right() and X.sister() and X.sister().get_idx_tuple('QND'):
                idx = X.sister().get_idx_tuple('QND')[0]
                self.determine_BindingIndexes(idx)
                stri += f'[{",".join(sorted(list(self.inventory[idx]["BindingIndexes"])))}]'
        return stri

    def determine_BindingIndexes(self, idx):
        if 'BindingIndexes' not in self.inventory[idx]:               # Every expression initially has its own binding index
            self.inventory[idx]['BindingIndexes'] = {chr(int(idx)+96)}
        for i in self.inventory.keys():
            if i == idx:
                break
            if self.coreference(i, idx):    # If X and Y co-refer, they must have the same binding index
                self.inventory[i]['BindingIndexes'] = {chr(int(i)+96)}
                self.inventory[idx]['BindingIndexes'] = {chr(int(i)+96)}
                log(f'===>{i}, {idx}')
            if self.overlapping_reference(i, idx): # If X and Y overlap in denotation, both binding indexes are shown
                self.inventory[idx]['BindingIndexes'].add(chr(int(i)+96))

    def coreference(self, idx1, idx2):
        assignments = [a for a in self.all_assignments if a['weight'] > 0]
        disjoint_assignments = [a for a in assignments if a[idx1] != a[idx2]]
        return assignments and not disjoint_assignments

    def disjoint_reference(self, idx1, idx2):
        return next((False for a in self.all_assignments if a[idx1] == a[idx2] and a['weight'] > 0), True)

    def overlapping_reference(self, idx1, idx2):
        return not self.coreference(idx1, idx2) and not self.disjoint_reference(idx1, idx2)

    def create_all_denotations(self, X):
        return self.narrow_semantics.global_cognition.get_compatible_objects(self.inventory[X.get_referential_index('QND')])

    def R_feature(self, feature):
        return feature.split(':')[0] == 'R'

    def get_R_features(self, ps):
        return [feature for feature in ps.head().features if self.R_feature(feature)]

    def parse_R_feature(self, R_feature):
        components = R_feature.split(':')
        if len(components) == 2:
            return components[0], components[1], ''
        return components[0], components[1], components[2]

    def extrapolate_semantic_attributes(self, X):
        semantic_attributes_dict = self.narrow_semantics.default_attributes(X, 'QND')
        semantic_attributes_dict['Semantic type'] = {'§Thing'}
        return semantic_attributes_dict

    def detect_phi_conflicts(self, ps):
        for phi in ps.head().get_phi_set():
            if phi[-1] == '*':
                log(f'\n\t\t\t{ps.illustrate()} has a phi-feature conflict with {phi}.')
                self.narrow_semantics.phi_interpretation_failed = True
