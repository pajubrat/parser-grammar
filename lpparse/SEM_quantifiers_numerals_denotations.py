# This class implements numerical and quantificational cognition
# It mediates between the syntax-semantics interface and the global discourse inventory
# Responds to R-features ([R:...], [PHI:...])
from support import log
from phrase_structure import PhraseStructure
import itertools

phi_map_dict = {'PER:1': ('Person', 'first'),
                'PER:2': ('Person', 'second'),
                'PER:3': ('Person', 'third'),
                'NUM:PL': ('Number', 'plural'),
                'NUM:SG': ('Number', 'singular'),
                'HUM:HUM': ('Class', 'human'),
                'HUM:NONHUM': ('Class', 'nonhuman'),
                'GEN:M': ('Gender', 'm'),
                'GEN:F': ('Gender', 'f')}


class QuantifiersNumeralsDenotations:
    def __init__(self, narrow_semantics):
        self.narrow_semantics = narrow_semantics

        # Inventory of QND objects

        self.inventory = {}

        # Stores all assignments

        self.all_assignments = []

    def reset(self):
        self.inventory = {}
        self.all_assignments = []

    def project(self, X, idx):
        log(f'\n\t\tProject object ({idx}, QND) for {X.max().illustrate()}')
        self.inventory[idx] = self.extrapolate_semantic_attributes(X)
        return self.inventory[idx]

    def phi_map(self, phi_feature):
        return phi_map_dict.get(phi_feature, ())

    def accept(self, X):

        # To project a WND-object, the element ("referential phrase") must be able to sustain coherent reference,
        # it should not have agreed, and it must be referential

        return (X.core.overt_phi_sustains_reference() and not X.core('AgreeLF_occurred')) or X.core('referential')

    def remove_object(self, idx):
        self.inventory.pop(idx, None)

    def get_object(self, idx):
        return self.inventory[idx]

    def update_discourse_inventory(self, idx, criteria):
        self.inventory[idx].update(criteria)

    def object_presentation(self, X):

        # Referential expressions are presented as phrases

        if X.core('referential'):
            return f'{X.max().illustrate()}'

        # Sublexical pro-elements are presented as pro

        return f'pro({X})'

    def compatible(self, idx1, idx2):
        def included(field):

            # Defines which ontological attributes are included in the comparisons
            # Currently number, person, class and gender

            return field in {'Number', 'Person', 'Class', 'Gender'}

        # Verifies that there are no value-mismatches
        # We consider all attributes of each object projected into QND-space, then target only those
        # which are included (see above) and detect value-mismatches.

        for attribute_pair in itertools.product(self.inventory[idx1].items(), self.inventory[idx2].items()):

            if included(attribute_pair[0][0]) and \
                    attribute_pair[0][0] == attribute_pair[1][0] and \
                    attribute_pair[0][1] != attribute_pair[1][1]:
                return False

        return True

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
        log(f'\n\tDenotations:')

        # Stores all assignments into the object variable self.all_assignments
        # Created on the basis of possible denotations for each referential expression

        self.create_assignments_from_denotations(self.calculate_possible_denotations(X))

        # Currently return only assignments for printout which have nonzero weight

        weighted_assignments = [assignment for assignment in self.all_assignments if assignment.get('weight', 0) > 0]

        # Return the number of assignments and the assignments themselves for the caller (narrow semantics)
        # which stores them into the output dictionary

        log(f'\n\t\tSummary: {self.assignment_output_string(X)}')
        return len(weighted_assignments), self.print_assignments(weighted_assignments), self.assignment_output_string(X)[1:]

    def calculate_possible_denotations(self, X):
        referential_expressions_lst = []

        # Copies are ignored

        if not X.copied:

            # Recursion for complex phrases

            if X.complex():
                referential_expressions_lst += self.calculate_possible_denotations(X.L())
                referential_expressions_lst += self.calculate_possible_denotations(X.R())

            # Primitive heads

            else:

                # If the head contains an index to QND-object, it will be considered

                if X.core.has_idx('QND'):

                    # Get the idx, space pair

                    idx, space = X.core.get_idx_tuple('QND')

                    # The field "Denotations" is used to store all denotations (objects in the global space)

                    self.inventory[idx]['Denotations'] = self.create_all_denotations(X)
                    log(f'\n\t\t{self.inventory[idx]["Reference"]}~{self.inventory[idx]["Denotations"]} ')

                    # Return the list of denotations, which will be added together as the recursion proceeds

                    referential_expressions_lst = [(idx, f'{X.illustrate()}', X, self.inventory[idx]['Denotations'])]

        return referential_expressions_lst

    def create_assignments_from_denotations(self, referential_expressions_lst):

        #  Create all possible assignments (tup[3] = denotations)

        log(f'\n\tAssignments: ')

        for assignment in itertools.product(*[tup[3] for tup in referential_expressions_lst]):

            #   Create assignment dict

            assignment_dict = {tup[0]: assignment[i] for i, tup in enumerate(referential_expressions_lst)}

            #   Calculate assignment weights and add the (assignment, weight) pair into all_assignments

            self.all_assignments.append(self.calculate_assignment_weight(assignment_dict, referential_expressions_lst))

    def calculate_assignment_weight(self, assignment, ref_constituents_lst):
        """
        Calculates weights for assignments and returns a weighted assignment.
        Assignment = dictionary {IDX(QND): IDX(GLOBAL) for all referential expressions in the sentence
        ref_constituent_lst = list of tuples (IDX, head (str), X, list of possible denotations)
        """
        weighted_assignment = assignment.copy()
        weighted_assignment['weight'] = 1
        log(f'\n\t\tAssignment {self.print_assignment(weighted_assignment)} ')

        for expression in ref_constituents_lst:

            # Violations of binding conditions reduce the weight to 0

            if not self.binding_conditions(expression, assignment):
                weighted_assignment['weight'] = 0

        # Check semantic compatibility (e.g., *John admires herself)

        if not self.semantic_compability(assignment):
            weighted_assignment['weight'] = 0

        # Check internal constituency (See Brattico 2025)

        if self.internal_inconsistency(assignment):
            weighted_assignment['weight'] = 0

        # If no violations apply, log the assignment as accepted

        if weighted_assignment['weight'] > 0:
            log('+')

        return weighted_assignment

    def semantic_compability(self, assignment):
        """Examines if the assignment contains semantic clashes between the meaning of the expression (QND space)
        and the semantic object in the global inventory. This version is limited to verifying phi-information.
        """
        for QND_idx, G_idx in assignment.items():
            object1 = self.inventory[QND_idx]
            object2 = self.narrow_semantics.global_cognition.inventory[G_idx]
            if not self.narrow_semantics.global_cognition.ontological_compatibility(object1, object2):
                log(f'-Semantic incongruity between {object1} and {object2}')
                return False
        return True

    def internal_inconsistency(self, assignment):
        """Verifies that the assignments are internally consistent.
        Internal consistency means that if two expressions A and B denote the same object O,
        A and B do not mismatch in their semantic attributes. This test is needed in cases where
        the relevant attribute is not defined at O. See Brattico 2025
        """
        for QND_idx, G_idx in assignment.items():
            for QND_idx2, G_idx2 in assignment.items():
                if QND_idx2 != QND_idx and G_idx2 == G_idx:
                    if not self.compatible(QND_idx, QND_idx2):
                        log('-Internal inconsistency')
                        return True

    def print_assignment(self, assignment):
        return ', '.join(f'{self.get_object(item[0])["Reference"]} ~ {item[1]}' for item in assignment.items() if item[0].isdigit() and assignment.get('weight', 0) > 0)

    def print_assignments(self, assignments_dict):
        return '; '.join(self.print_assignment(assignment) for assignment in assignments_dict)

    def binding_conditions(self, exp, assignment):

        # The binding conditions proposed in Brattico 2025

        def binding_violation(semantic_object, rule_, semantic_working_memory, X):

            # Semantic working memory (whether complete, limited) is constructed by the caller and
            # is here provided as a set

            # RULE 1
            # If the same semantic object denoted by X is inside (complete, limited) semantic working memory but
            # X marked as NEW, raise violation

            if 'NEW' in rule_ and {semantic_object} & semantic_working_memory:
                log(f'-Illegitimate binder for {X.max().illustrate()}({semantic_object}) in WM ')
                return True

            # RULE 2
            # If the same semantic object denoted by X is not inside (complete, limited) semantic working memory
            # but X is marked for OLD, raise violation

            if 'OLD' in rule_ and not {semantic_object} & semantic_working_memory:
                log(f'-Binder missing for {X.max().illustrate()}({semantic_object}) from WM ({semantic_working_memory})')
                return True

        # Extract the index, name, X and denotations fields from the expression tuple

        idx, name, X, denotations = exp

        # Examine each R-feature, i.e. features which must be verified against binding

        for f in self.get_R_features(X):
            R, rule, intervention = self.parse_R_feature(f)

            # Check that no binding conditions are not violated
            # Function construct_semantic_working_memory will create a set of object based on attributes complete, limited

            if binding_violation(assignment[idx],
                                 rule,
                                 X.construct_semantic_working_memory(intervention, assignment),
                                 X):
                return False

        return True

    def assignment_output_string(self, X):

        # Maps assignments into a simple summary string

        # Creates symbol content (words) for primitive constituents for the output string
        def relevant_content(Y):
            if ['V', 'N', 'A', 'P', 'Adv', 'D'] in Y.core:
                return ''.join([f[3:] for f in Y.core.features() if f.startswith('PF:') and f[3:] not in PhraseStructure.major_cats and f[3:] != "'s"])

        stri = ''

        if not X.copied:

            # Recursion

            if X.complex():
                stri += self.assignment_output_string(X.L())
                stri += self.assignment_output_string(X.R())

            # Primitive constituents are turned into string symbols

            if X.zero_level() and relevant_content(X):
                stri += ' ' + relevant_content(X)

            # Create binding tags at the end of referential expressions

            # Binding for pro-elements

            if X.zero_level() and not X('referential') and X.core.get_idx_tuple('QND'):
                idx = X.core.get_idx_tuple('QND')[0]
                self.determine_BindingIndexes(idx)
                stri += f' {X.label()}/pro[{",".join(sorted(list(self.inventory[idx]["BindingIndexes"])))}]'

            # Binding for other constituents

            # We target constituents [K N] where K (=phi- or D-head) has been associated with QND-object and N is a nominal
            # todo Should be replaced with function which targets phi/D-head, the nontrivial issue is placement of the binding
            # todo index which should be positioned at the end of the whole DP...

            elif X.M() and X('nominal') and X.is_R() and X.sister() and X.sister().core.get_idx_tuple('QND'):
                idx = X.sister().core.get_idx_tuple('QND')[0]
                self.determine_BindingIndexes(idx)
                stri += f'[{",".join(sorted(list(self.inventory[idx]["BindingIndexes"])))}]'

        return stri

    def determine_BindingIndexes(self, idx):

        # Every expression initially has its own binding index

        if 'BindingIndexes' not in self.inventory[idx]:
            self.inventory[idx]['BindingIndexes'] = {chr(int(idx)+96)}

        # Calculate coreference and disjointness properties

        for i in self.inventory.keys():
            if i == idx:
                break

            # If X and Y co-refer, they must have the same binding index

            if self.coreference(i, idx):
                self.inventory[i]['BindingIndexes'] = {chr(int(i)+96)}
                self.inventory[idx]['BindingIndexes'] = {chr(int(i)+96)}

            # If X and Y overlap in denotation, both binding indexes are shown

            if self.overlapping_reference(i, idx):
                self.inventory[idx]['BindingIndexes'].add(chr(int(i)+96))

    def coreference(self, idx1, idx2):
        assignments = [a for a in self.all_assignments if a['weight'] > 0]
        disjoint_assignments = [a for a in assignments if idx1 in a.keys() and idx2 in a.keys() and a[idx1] != a[idx2]]
        return assignments and not disjoint_assignments

    def disjoint_reference(self, idx1, idx2):
        return next((False for a in self.all_assignments if idx1 in a.keys() and idx2 in a.keys() and a[idx1] == a[idx2] and a['weight'] > 0), True)

    def overlapping_reference(self, idx1, idx2):
        return not self.coreference(idx1, idx2) and not self.disjoint_reference(idx1, idx2)

    def create_all_denotations(self, X):
        return self.narrow_semantics.global_cognition.get_compatible_objects(
            self.inventory[X.head().core.get_referential_index('QND')])

    def R_feature(self, feature):
        return feature.split(':')[0] == 'R'

    def get_R_features(self, ps):
        return [f for f in ps.head().core.features() if self.R_feature(f)]

    def parse_R_feature(self, R_feature):
        components = R_feature.split(':')
        if len(components) == 2:
            return components[0], components[1], ''
        return components[0], components[1], components[2]

    def extrapolate_semantic_attributes(self, X):
        semantic_attributes_dict = self.narrow_semantics.default_attributes(X, 'QND')
        semantic_attributes_dict.update(self.project_phi_features(X))
        semantic_attributes_dict['Semantic type'] = {'§Thing'}
        return semantic_attributes_dict

    def project_phi_features(self, X):
        interpreted_phi_dict = {}
        PHI = [f.split(',') for f in X.core.features(type=['phi', 'valued'], format='reduced')]
        for phi_lst in PHI:
            for phi in phi_lst:
                sem_phi = self.phi_map(phi)
                if sem_phi:
                    interpreted_phi_dict[sem_phi[0]] = sem_phi[1]
        return interpreted_phi_dict

    def detect_phi_conflicts(self, X):
        for phi in X.head().core.features(type=['phi']):
            if phi[-1] == '*':
                log(f'\n\t\t\t{X.illustrate()} has a phi-feature conflict with {phi}.')
                self.narrow_semantics.phi_interpretation_failed = True
