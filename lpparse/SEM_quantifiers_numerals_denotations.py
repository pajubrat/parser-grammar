# This class implements numerical and quantificational cognition
# It mediates between the syntax-semantics interface and the global discourse inventory
# Responds to D-features ([D:...], [PHI:...])
from support import log

class QuantifiersNumeralsDenotations:
    def __init__(self, narrow_semantics):
        self.narrow_semantics = narrow_semantics    # Access to narrow semantics (if needed)
        self.inventory = {}                         # Bookkeeping for fixed denotation sets
        self.one_complete_assignment = {}           # Assignment dictionary (temporary)
        self.all_assignments = []                   # Stored and weighted assignments
        self.referential_constituents_feed = []     # list of tuples [(idx, illustrated, ps, denotations)...]

        # All (or many) D-features are associated with a separate interpretation function
        self.criteria_function = {'D:REF:PROPER_NAME': self.criterion_proper_name,
                                  'PHI': self.criterion_phi_features,
                                  }

    def reconstruct_assignments(self, ps):
        """
        Wrapper for recursive assignment.

        1.  Referential expressions are provided with possible denotation lists, and then the expressions are collected into
            a feed list called [referential_constituents_feed]. These processes keep within the QND space.
            For example, pronoun "he" may be associated with possible denotations 'John', 'Paul' and 'Simon', depending
            on what is currently in the global discourse inventory.
        2.  The feed is used to create a list of actual assignments, which are stored into semantics results field.
            An actual assignment is a pairing between QND-handle and a global discourse handle, for example,
            some particular interpretation for pronoun "he", say 'Paul'. Complete assignment contains this information
            for each referential expression in an expression.
        """

        # We do not compute assignments for secondary solutions, because they will potentially
        # generate new confusing objects into the QND/GLOBAL spaces, breaking the conversation
        # mechanism which presupposes disambiguation.
        if self.narrow_semantics.controlling_parsing_process.first_solution_found:
            log('\n\t\tAssignments are not computed for secondary solutions.')
            self.narrow_semantics.semantic_interpretation['Assignments'] = []
            return

        log(f'\n\t\tComputing assignments...')

        # Feed is list of referential constituents in the current LF object,
        # in a list of tuples (idx, constituent name, link to const object, denotations).
        # This could be considered an auxiliary structure, the information is available in the original
        # LF object as well.
        log('Possible denotations: ')
        self.referential_constituents_feed = self.calculate_possible_denotations_(ps)

        # Creates the list of all possible assignments, each a dictionary {denoting const idx: denoted G-element idx...}
        # The assignments are stored in to [self.all_assignments]
        log('Assignments: ')
        self.create_assignments_from_denotations_(0, 0, {})

        # Report results
        self.narrow_semantics.semantic_interpretation['Assignments'] = self.all_assignments

    def calculate_possible_denotations_(self, ps):
        """
        Recursively associate any head (with referential index) with a denotation list which enumerates
        all possible denotations for that constituent, given the current contents of the discourse inventory.
        For example, "he" ~ ['John', 'Paul', 'Simon']. This information is stored into the QND-entry.
        """

        # These lists are used to compose the referential constituent feed returned by this function
        L1 = []
        L2 = []

        # Copies are ignored
        if not ps.find_me_elsewhere:
            if ps.is_complex():
                # Recursion, referential constituent feed composition
                L1 = self.calculate_possible_denotations_(ps.left_const)
                L2 = self.calculate_possible_denotations_(ps.right_const)

            # Primitive constituent
            else: # If the constituent is referential and in the QND space, we generate assignments for it
                if self.narrow_semantics.has_referential_index(ps, 'QND'):
                    idx, space = self.narrow_semantics.get_referential_index_tuples(ps, 'QND')
                    # Store the list of possible denotations into the QND entry
                    self.inventory[idx]['Denotations'] = self.generate_all_possible_assignments(ps)
                    log(f'({self.inventory[idx]["Reference"]}~{self.inventory[idx]["Denotations"]}), ')
                    # Generate entry for the referential constituent feed list, returned to caller
                    return [(idx, f'{ps.max().illustrate()}', ps, self.inventory[idx]['Denotations'])]

        # Merge the lists for the construction of the referential constituent feed
        return L1 + L2

    def create_assignments_from_denotations_(self, c_index, d_index, one_complete_assignment):
        """
        Creates recursively all possible assignments for constituents in referential_constituents_feed and their
        possible denotations. The position in the recursion is defined by c_index (constituent) and
        d_index (denotation for that constituent). For example, if we have "he admirer her", here we generate
        all possible assignments, e.g. {"he": 'Paul', "her": Mary}, {"he": 'Paul', "her": Paula}, etc.

        Assignments are put into a list [self.all_assignments] of dicts of the form {expression_idx: denotation_idx...}.
        """

        # Get all denotations for the current constituent
        idx, const, ps, denotations = self.referential_constituents_feed[c_index]
        denotation = denotations[d_index]

        # Store (constituent, assignment) pair into dictionary
        one_complete_assignment[idx] = denotation

        # Store complete assignment if all constituents have been provided with assignment
        # Add weight field which determines how likely this assignment will be
        if len(one_complete_assignment) == len(self.referential_constituents_feed):
            self.all_assignments.append(self.calculate_assignment_weight(one_complete_assignment))

        # Recursion
        # Recurse through all constituents
        if c_index < len(self.referential_constituents_feed) - 1:
            self.create_assignments_from_denotations_(c_index + 1, 0, one_complete_assignment.copy())
        # Recurse through all denotations
        if d_index < len(denotations) - 1:
            self.create_assignments_from_denotations_(c_index, d_index + 1, one_complete_assignment.copy())

    def calculate_assignment_weight(self, complete_assignment):
        """
        Calculates grammatical weight for complete assignment, on the basis of grammatical properties and features.
        For example, assignment "John_1 admires he_1" will be ruled out. Pragmatic weighting will be provided
        for the output of this function (not implemented).
        """
        weighted_assignment = complete_assignment.copy()
        weighted_assignment['weight'] = 1

        # Examine every expression in the constituent feed
        for expression in self.referential_constituents_feed:
            if not self.Binding_Theory(expression, complete_assignment):
                log(f'Assignment {complete_assignment} failed. ')
                weighted_assignment['weight'] = 0

        log(f'{self.format_assignment(weighted_assignment)}')
        return weighted_assignment

    def Binding_Theory(self, expression, complete_assignment):
        """
        Applies binding theory.

        Binding theory is interpreted as a mechanism where semantic assignment is affected by grammaticalized
        instructions (linguistic features, in traditional terminology) to the global cognitive selection mechanism
        that handles such operations more generally. Linguistic input constitutes a way to instruct and direct
        these mechanisms.
        """

        # Referential index, name, constituent pointer and denotations of the expression (from constituent feed)
        idx, name, ps, denotations = expression

        # Examine all D-features
        for feature in list(self.get_D_features(ps)):
            D, rule, intervention_feature = self.open_D_feature(feature)

            # React only to NEW and OLD features (current implementation)
            if {rule} & {'NEW', 'OLD'}:

                # Compute reference set, which is the set of global object indexes that are visible for
                # expression, inside constituent vector limited by intervention feature.
                # For example, the reference set for X is {1, 2} for "John_1 gave Mary_2 his(X) address",
                # where the indexes are global discourse inventory objects under assignment. Only expressions
                # denoting into the QND space are considered
                reference_set = self.get_reference_set(ps, intervention_feature, complete_assignment)

                # Inquire whether the object denoted under assignment [complete_assignment[idx]] satisfies
                # instructions contained in [rule] and [reference set]. This implements the interface to the
                # global cognitive operation.
                if not self.narrow_semantics.global_cognition.general_evaluation(complete_assignment[idx], rule, reference_set):
                    # If not, then we return False, which tells the caller that this assignment does not
                    # satisfy a D-feature
                    return False
        return True

    def get_reference_set(self, ps, intervention_feature, complete_assignment):
        """
        Returns the reference set for [ps] under assignment, as limited by constituent vector and intervention feature.
        The reference set for X contains global discourse inventory objects "upward visible" from the point of view of X.
        For example, in sentence "John_1 admires her(X)", X sees 'John' (as a global object in the discourse inventory).
        The intervention feature cuts upward visibility, for example, at finite boundaries. Only objects
        from the QND space are considered potential constituents.
        """

        return {complete_assignment[self.narrow_semantics.get_referential_index(head, 'QND')]
                for head in ps.constituent_vector(intervention_feature)
                if self.narrow_semantics.has_referential_index(head) and self.narrow_semantics.is_in_QND_space(head)}

    def generate_all_possible_assignments(self, ps):
        """
        Generates the denotations set for semantic QND object linked with [ps]
        """

        # Get the QND space object which determines the criteria
        filter_criteria = self.inventory[self.narrow_semantics.get_referential_index(ps, 'QND')]

        # Return all GLOBAL discourse inventory objects which do not violate the criteria
        return self.narrow_semantics.global_cognition.get_compatible_objects(filter_criteria)

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
        feature_list = feature.split(':')
        if feature_list[0] == 'D' and len(feature_list) == 3:
            return True
        if feature_list[0] == 'PHI':
            return True

    def get_D_features(self, ps):
        """
        Returns the set of D-features from the head.
        """
        return {feature for feature in ps.head().features if self.is_D_feature(feature)}

    def open_D_feature(self, feature):
        """
        Returns the three components (d, type, value) of a D-feature, if the input
        feature is a D-feature, otherwise returns (None, None, None)
        """
        if not self.is_D_feature(feature):
            return None, None, None
        components = feature.split(':')
        if len(components) == 3:
            return components[0], components[1], components[2]
        return None, None, None

    def recognize(self, head):
        """
        This function returns True if the module "recognizes" the head. Recognition means
        intuitively that the module is able to interpret the head semantically. A head is currently
        recognized by its lexical category feature, later by the existence of a D-feature.
        The category feature now substitutes for the latter that has not been implemented
        fully.
        """
        return {'D', 'NUM', 'Q', 'DEM', 'n', 'D/rel', 'φ'} & head.features

    def project_QND_entry_into_inventory(self, ps, idx):
        """
        This function will create a dictionary holding the denotations for the expression [ps] inside the QND space.
        """

        self.inventory[idx] = self.apply_criteria(self.narrow_semantics.default_criteria(ps, 'QND'), ps)
        log(f'Denotation for {ps} (index {idx}) was created into QND space...')

    def delete_pro(self, head):
        idx = self.narrow_semantics.get_referential_index(head, 'QND')
        self.remove_object(idx)
        for idx, space in self.narrow_semantics.get_referential_index_tuples(head):
            if space == 'QND':
                self.narrow_semantics.delete_referential_index_tuple(head, (idx, space))

    def apply_criteria(self, criteria, ps):
        """
        Examines all D-features in the head [ps] and translates them into criteria (fields in the QND inventory entry),
        then adds them into input parameter dict [criteria] that will be returned
        """
        log(f'Applying semantic criteria...')
        criteria['Semantic type'] = {'§Thing'} # Currently all QND objects are §things
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


    def is_operator(self, ps):
        """
        Definition for operator
        """
        return self.narrow_semantics.operator_variable_module.scan_criterial_features(ps) and 'FIN' not in ps.features

    def remove_object(self, idx):
        self.inventory.pop(idx, None)

    def get_object(self, idx):
        return self.inventory[idx]

    def update_discourse_inventory(self, idx, criteria):
        self.inventory[idx].update(criteria)

    def interpret_phi_features(self, phi_set):
        """
        Interprets phi-feature set into semantic fields (dict)
        """

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
            semantic_fields['Humanness'] = 'Human'
        if match(phi_set, {'PHI:HUM:NONHUM'}):
            semantic_fields['Humanness'] = 'Nonhuman'

        # Gender
        if match(phi_set, {'PHI:GEN:M'}):
            semantic_fields['Gender'] = 'M'
        if match(phi_set, {'PHI:GEN:F'}):
            semantic_fields['Gender'] = 'F'
        if match(phi_set, {'PHI:GEN:N'}):
            semantic_fields['Gender'] = 'N'

        return semantic_fields

    def reconstruct_phi_features(self, global_object):

        def match(set1, set2):
            return set2 == set1 & set2

        # Person and number
        if match(global_object['Phi-set'], {'PHI:NUM:SG', 'PHI:PER:1'}):
            global_object['Participant role'] = 'Speaker'
        if match(global_object['Phi-set'], {'PHI:NUM:SG', 'PHI:PER:2'}):
            global_object['Participant role'] = 'Hearer'
        if match(global_object['Phi-set'], {'PHI:NUM:PL', 'PHI:PER:1'}):
            global_object['Participant role'] = 'Speaker + others'
        if match(global_object['Phi-set'], {'PHI:NUM:PL', 'PHI:PER:2'}):
            global_object['Participant role'] = 'Hearer + others'
        if match(global_object['Phi-set'], {'PHI:NUM:SG', 'PHI:PER:3'}):
            global_object['Participant role'] = 'Third party'
        if match(global_object['Phi-set'], {'PHI:NUM:PL', 'PHI:PER:3'}):
            global_object['Participant role'] = 'Third party + others'

        # Gender
        if match(global_object['Phi-set'], {'PHI:GEN:M'}):
            global_object['Gender'] = 'M'
        if match(global_object['Phi-set'], {'PHI:GEN:F'}):
            global_object['Gender'] = 'F'
        if match(global_object['Phi-set'], {'PHI:GEN:N'}):
            global_object['Gender'] = 'N'

        del global_object['Phi-set']

    #
    # Criteria functions which translate grammatical features into QND semantic properties
    #
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
        if 'Phi-set' in criteria:
            criteria['Phi-set'].add(feature)
        else:
            criteria['Phi-set'] = {feature}

        criteria.update(self.interpret_phi_features(criteria['Phi-set']))

    def is_referential(self, ps):
        """
        Determines what type of constituents will populate the semantic space by reference.

        Current we examine whether the head has (1) enough phi-features or (2) has a referential label. It is unclear
        if we need latter. The former is needed to link predicates with sufficient phi-features (pro elements)
        to referents (e.g. "söin leipää").
        """
        if self.has_adequate_phi_set(ps):
            return True
        if {'FORCE', 'P', 'φ'} & ps.head().features:
            return True

    def has_adequate_phi_set(self, h):
        """
        Determines whether there are enough phi-features in head [h] to process this constituent inside QND module and
        link it with QND reference. Phi-checked constituents are not linked because this means that the phi-features
        have been neutralized by an overt argument.
        """
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
        if 'PHI:NUM' in features_detected \
                and 'PHI:PER' in features_detected \
                and 'PHI_CHECKED' not in h.features:
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