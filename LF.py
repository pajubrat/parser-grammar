
from support import log, illu

# Transforms a set of lexical features to be used in checking LF-interface conditions
def for_lf_interface(features):
    return {f for f in features if f.startswith('!') or f.startswith('-')}

class LF:

    def __init__(self):
        # Test result variables
        self.probe_goal_test_result = True
        self.selection_test_result = True
        self.wrong_complement_test_result = True
        self.tail_head_test_result = True
        self.head_integrity_test_result = True
        self.criterial_feature_test_result = True
        self.semantic_test_result = True
        self.adjunct_test_result = True
        self.discourse_test_result = 0
        self.projection_principle_test_result = True
        self.transfer_to_CI_crash = False

        # This stores facts concerning semantic interpretation resulting from transfer to CI
        # The report is a set of strings; later this will be in some formal notation
        self.semantic_interpretation = set()

    def all_pass(self):
        return (self.probe_goal_test_result and
                self.selection_test_result and
                self.tail_head_test_result and
                self.head_integrity_test_result and
                self.criterial_feature_test_result and
                self.semantic_test_result and
                self.projection_principle_test_result and
                self.wrong_complement_test_result and
                self.adjunct_test_result)

    def fail(self):
        return not self.all_pass()

    # LF-tests that checks LF-legibility for primitive constituents (not phrases)
    def test(self, ps):

        # Returns the selected sister (if any) of the constituent
        def selected_sister(ps):

            # Only primitive constituents with geometrical sisters can select sisters
            if ps.is_primitive() and not ps.geometrical_sister():
                return None

            # H~YP, YP~H => YP is selected sister
            if ps.geometrical_sister().is_complex():
                return ps.geometrical_sister()
            else:
                # H~Y => Y is selected sister
                if ps.geometrical_sister().is_right():
                    return ps.geometrical_sister()
                else:
                    # Y~H => Y is not selected sister for H
                    return None

        # --- test function beings ---#
        if not ps.is_primitive():
            if not ps.left_const.find_me_elsewhere:
                self.test(ps.left_const)
            if not ps.right_const.find_me_elsewhere:
                self.test(ps.right_const)
            return

        h = ps  # keep track of the fact that we have selected primitive head

        spec = h.get_local_edge()
        specs = h.get_edge()
        comp = h.complement()
        lf_features = sorted(for_lf_interface(h.features))

        #
        # 1. Head integrity test
        #
        if not h.get_cats() or 'CAT:?' in h.get_cats():
            log('\t\t\t\t\tAn uninterpretable grammatical head without lexical category was detected.')
            self.head_integrity_test_result = False

        #
        # 2. Probe-goal test
        #
        for f in lf_features:
            if f.startswith('!PROBE:'):
                if not h.probe(set(h.get_cats()), f[7:]):
                    log(f'\t\t\t\t{ps} probing for {f[7:]} failed.')
                    self.probe_goal_test_result = False

        #
        # 3. Internal tail-head test for case (DPs)
        #
        if 'D' in h.get_labels() and not h.internal_tail_head_test():
            log(f'\t\t\t\t{h}({h.mother}) failed internal tail test for {h.get_tail_sets()}.')
            self.tail_head_test_result = False

        #
        # 4. Double Spec test for DP arguments
        #
        if '2SPEC' not in h.features:
            count = 0
            list_ = h.get_edge()
            if list_:
                for spec_ in list_:
                    if not spec_.adjunct and 'D' in spec_.get_labels() and not spec_.find_me_elsewhere:
                        count = count + 1

            if count > 1:
                self.head_integrity_test_result = False
                log(f'\t\t\t\t{ps} has double specifiers.')

        #
        # 5. Semantic match test between H and Comp,H
        #
        if comp:
            if not LF.semantic_match(h, h.complement()):
                self.semantic_test_result = False
                log(f'\t\t\t\t{ps} fails semantic match with {h.complement()}')

        #
        # 6. Selection tests
        #
        for f in lf_features:
            # 3.1. Specifier selection
            if f.startswith('-SPEC:'):
                for spec_ in specs:
                    if spec_ and f[6:] in spec_.get_labels():
                        if not spec_.adjunct:
                            log(f'\t\t\t\t{ps} has unacceptable specifier {spec_}.')
                            self.selection_test_result = False

            # 3.2. No specifier of any kind allowed (e.g., English P).
            #       This excludes pro
            if f == '-SPEC:*':
                if spec:
                    if not spec.adjunct and not spec.find_me_elsewhere and 'pro' not in spec.features:
                        log(f'\t\t\t\t{h} ({h.illustrate()}) has a specifier {spec}({spec.features}) '
                            f'but is marked for -EPP behavior.')
                        self.selection_test_result = False

            # 3.3. Obligatory complement
            if f.startswith('!COMP:') and not f == '!COMP:*':
                if not selected_sister(h):
                    log(f'\t\t\t\t{h} ({h.illustrate()}) is missing complement {f[6:]}')
                    self.selection_test_result = False
                else:
                    if f[6:] not in selected_sister(ps).get_labels():
                        log(f'\t\t\t\t\t{h} ({h.illustrate()}) is missing a mandatory complement {f[6:]}')
                        self.selection_test_result = False

            # 3.4. Complement restriction
            if f.startswith('-COMP:'):
                if h.is_left() and comp and f[6:] in comp.get_labels():
                    log(f'\t\t\t\t"{ps}\" has wrong complement {comp} {illu(comp.get_labels())}P')
                    self.selection_test_result = False
                    self.wrong_complement_test_result = False

            if f == '-COMP:*':
                if h.is_left() and comp:
                    log(f'\t\t\t\t{h} does not accept complements.')
                    self.selection_test_result = False

            # 3.5. !COMP:* heads must have complements (=functional head)
            if f == '!COMP:*':
                if not selected_sister(h):
                    log(f'\t\t\t\t"{h}" lacks complement.')
                    self.selection_test_result = False

            # 3.6. !SPEC:* heads require a specifier
            if f == '!SPEC:*' and not spec:
                # This condition takes care of the curious fact that overt C cancels !SPEC:*
                if h.get_selector() and 'C/fin' in h.get_selector().get_labels():
                    pass
                else:
                    log(f'\t\t\t\tAn EPP-head "{h}" lacks specifier.')
                    self.selection_test_result = False

            # 3.7. !SPEC:F, head requires specific specifier
            # Left adjunct can satisfy this, left non-adjunct must satisfy it
            if f.startswith('!SPEC:') and not f == '!SPEC:*':
                if not specs:
                    log(f'\t\t\t\tAn EPP-head "{h}" lacks specifier {f[6:]} that it requires.')
                    self.selection_test_result = False
                else:
                    found = False
                    for s in specs:
                        # First left adjunct CAN satisfy SPEC requirement
                        if s.adjunct:
                            if f[6:] in s.get_labels() or f[7:] in s.get_labels():
                                found = True
                                break
                        # First non-adjunct MUST satisfy SPEC requirement
                        else:
                            if f[6:] in s.get_labels() or f[7:] in s.get_labels():
                                found = True
                                break
                            else:
                                found = False
                                break

                    if not found:
                        log(f'\t\t\t\tAn EPP-head "{h}" has wrong specifier {s}, needs {f[6:]}')
                        self.selection_test_result = False

        #
        # 7. Criterial feature legibility test(s)
        #
        # 7.1 test for relative pronoun
        # For every DP that it not a relative pronoun
        if 'D' in h.get_labels() and 'R' not in h.get_labels() and h.mother:
            # Check that if there is relative pronoun there is also T/fin
            if h.mother.contains_feature('CAT:R') and not h.mother.contains_feature('CAT:T/fin'):
                log(f'\t\t\t\tCriterial legibility failed for "{h}".')
                self.criterial_feature_test_result = False

        #
        # 8. Projection principle test for complex referential non-adjunct arguments
        #
        # Check only non-adjunct arguments
        if spec and not spec.adjunct and spec.is_complex() and 'D' in spec.get_labels() and not spec.find_me_elsewhere:
            # Arguments cannot be left to the SPEC of non-thematic head
            if h.EPP():
                log(f'\t\t\t\t{spec} has no thematic role.')
                self.projection_principle_test_result = False
            # or to the SPEC of a head without PHI specification that is c-commanded closest by -ARG.
            else:
                if h.get_selector() and 'ARG' not in h.get_selector().features:
                    log(f'\t\t\t\t{spec} has no thematic role due to a selecting -PHI head.')
                    self.projection_principle_test_result = False

        #
        # 9. Discourse/pragmatic tests
        #
        # 9.1 This test accumulates discourse violations for each SPEC that cannot (easily) be topicalized
        list_ = ps.get_edge()
        if list_:
            if len(list_) > 1:
                # Discourse penalty for multiple specifiers
                self.discourse_test_result = self.discourse_test_result + len(list_)*0.5
                if 'Neg/fin' in ps.get_labels(): # Negation increases the penalty
                    self.discourse_test_result = self.discourse_test_result + len(list_)
            for spec in list_:
                if 'INF' in spec.get_labels():
                    self.discourse_test_result = self.discourse_test_result + 2

        #
        # 10. Adjunct interpretation tests
        #
        # Condition 1. A DP right-adjunct cannot be interpreted inside another DP (e.g. [John <Mary>]
        if 'D' in h.get_labels() and \
                h.get_max() and h.get_max().adjunct and \
                h.get_max().is_right() and \
                h.get_max().mother and 'D' in h.get_max().mother.get_head().get_labels():
            log(f'\t\t\t\t{h.mother.mother} in uninterpretable.')
            self.adjunct_test_result = False

    # This function will try to transfer the phrase structure into the conceptual-intentional system
    # It represents the "outer edge of LF"
    def transfer_to_CI(self, ps):
        log(f'\t\t\tTransferring {ps} into Conceptual-Intentional system...')
        self.transfer_to_CI_crash = False

        # Construction of semantic interpretation
        self.semantic_interpretation = self.check_for_transfer(ps)

        # If no semantic interpretation results, transfer crashes
        if not self.semantic_interpretation:
            log('\t\t\t\tTransfer to C-I crashed.')
            self.transfer_to_CI_crash = True
            return set()
        else:
            log('\t\t\t\tTransfer to C-I successful.')
            self.transfer_to_CI_crash = False
            return self.semantic_interpretation

    # Attempts to transfer the LF-object into Conceptual-Intentional system
    def check_for_transfer(self, ps):

        # Recursion
        if ps.is_complex():
            if not ps.left_const.find_me_elsewhere:
                self.check_for_transfer(ps.left_const)
            if not ps.right_const.find_me_elsewhere:
                self.check_for_transfer(ps.right_const)

            if self.transfer_to_CI_crash:
                return set()
            else:
                return self.semantic_interpretation

        #
        # Transfer condition 1. Operator-variable constructions, binding of variables (ABAR)
        #
        for f in ps.features:
            if f[:4] == 'ABAR':
                if not self.bind(ps):
                    log(f'\t\t\t\t{ps}['+f+'] is not properly bound, the expression is uninterpretable.')
                    self.transfer_to_CI_crash = True
                else:
                    log(f'\t\t\t\t{ps}['+f+'] was bound to an operator.')
                    self.semantic_interpretation.add(f'{ps}['+f+'] was bound to an operator.')

        #
        # Transfer condition 2. Antecedents for unvalued phi-features (D, phi)
        #
        unvalued_phi_features = self.must_be_valued(ps.get_unvalued_features())

        if unvalued_phi_features:
            log(f'\t\t\t\t{ps} with {sorted(unvalued_phi_features)} was associated at LF with:')

            # Condition. If unvalued features are detected, they must be supplied with antecedents
            list_of_antecedents = self.search_phi_antecedents(ps, unvalued_phi_features)

            # Store the results for later reporting
            # If antecedents were found, they are stored as such
            if list_of_antecedents:
                self.semantic_interpretation.add(f'{ps}({list_of_antecedents[0].illustrate()})')
            else:
                self.semantic_interpretation.add(self.failed_recovery(unvalued_phi_features))

            # Report the results to the log file
            self.report_to_log(list_of_antecedents, unvalued_phi_features)

        #
        # Transfer condition 3. Phi-feature conflicts are not tolerated
        #
        phi_set = ps.get_phi_set()
        for phi in phi_set:
            if phi[-1] == '*':
                log(f'\t\t\t\t{ps} induces a phi-feature conflict.')
                self.transfer_to_CI_crash = True
                return
        return

    def must_be_valued(self, phi_set):
        return {phi for phi in phi_set if self.relevant_phi_at_LF(phi)}

    # Definition of phi-features that are relevant at LF
    def relevant_phi_at_LF(self, phi):
        if phi[:7] == 'PHI:NUM' or phi[:7] == 'PHI:PER' or phi[:7] == 'PHI:DET':
            return True
        else:
            return False

    # Searches a (prioritized) list of antecedents for a set of unvalued phi-feature
    def search_phi_antecedents(self, ps, unvalued_phi):
        ps_ = ps
        list_of_antecedents = []
        #
        # Alternative 1: unvalued per/num features: standard control
        #
        if 'PHI:NUM:_' in unvalued_phi and 'PHI:PER:_' in unvalued_phi:
            while ps_:
                # Termination condition: presence of SEM-external (control boundary)
                if ps_.sister() and 'SEM:external' in ps_.sister().features:
                    break
                # Condition 1. Antecedent must be a sister of the node at the spine we climb up
                # Condition 2. The phrase must evaluate as a possible antecedent
                if ps_.sister() and self.evaluate_antecedent(ps_.sister(), ps):
                    list_of_antecedents.append(ps_.sister())
                ps_ = ps_.walk_upstream_geometrically()
            return list_of_antecedents
        #
        # Alternative 2. Only PER_ remains unvalued
        #
        elif 'PHI:PER:_' in unvalued_phi:
            while ps_:
                # Termination condition: presence of SEM-external (control boundary)
                if ps_.sister() and 'SEM:external' in ps_.sister().features:
                    break
                # Condition 1. Antecedent must be a sister of the node at the spine we climb up
                # Condition 2. The phrase must evaluate as a possible antecedent
                if ps_.sister() and self.evaluate_antecedent(ps_.sister(), ps):
                    list_of_antecedents.append(ps_.sister())
                ps_ = ps_.walk_upstream_geometrically()
            return list_of_antecedents
        #
        # Alternative 3. Only D_ remains unvalued: nonlocal/discourse antecedents
        #
        elif 'PHI:DET:_' in unvalued_phi:
            while ps_:
                # Termination condition: presence of local specifier
                # Note: the reason is because any XP containing D can value D_, will be implemented later in this way
                if ps_.sister() and ps_.sister() == ps.get_local_edge():
                    if ps_.sister() and 'CAT:D' not in ps_.sister().get_head().features:
                        self.semantic_interpretation.add('Generic')
                        list_of_antecedents.append(ps_.sister())
                    else:
                        list_of_antecedents.append(ps_.sister())
                    break
                if ps_.sister() and self.evaluate_antecedent(ps_.sister(), ps):
                    list_of_antecedents.append(ps_.sister())
                ps_ = ps_.walk_upstream_geometrically()
            if not list_of_antecedents:
                log(f'\t\t\t\t\tNo antecedent found, LF-object crashes.')
                self.transfer_to_CI_crash = True
            return list_of_antecedents

    # Evaluates whether 'probe' could provide semantic support for 'goal'
    def evaluate_antecedent(self, antecedent, goal):

        if antecedent.find_me_elsewhere:
            return False

        # A list of all phi-features present at the goal (valued, unvalued)
        goal_phi_features = {f for f in goal.features if self.relevant_phi_at_LF(f)}

        # A list of unchecked features (all must eventually be checked by the antecedent)
        unchecked_features_at_goal = goal_phi_features.copy()

        # Go through phi-features at the probe
        for probe_feature in antecedent.get_head().features:

            # Only valued phi-features can be used for valuation
            if probe_feature[:4] == 'PHI:' and probe_feature[-1] != '_':
                for goal_feature in goal_phi_features:

                    # Check identical features
                    if goal_feature == probe_feature:
                        unchecked_features_at_goal.discard(goal_feature)  # Check feature

                    # Check unvalued features if they could be valued
                    else:
                        if goal_feature[-1] == '_':
                            if probe_feature[:len(goal_feature)-1] == goal_feature[:-1]:
                                unchecked_features_at_goal.discard(goal_feature)  # Check feature

        # If features remain unchecked, the antecedent is rejected
        if unchecked_features_at_goal:  # If unchecked features remain, evaluation is negative
            return False
        else:
            return True

    # Check if the sister is a phase head (v, C, copula, Force)
    def phase(self, ps_):
        if ps_.sister() and ps_.sister().is_phase():
            return True
        else:
            return False

    def report_to_log(self, list_of_antecedents, unvalued_phi_features):
        s = ''
        i = 1
        if list_of_antecedents:
            for a in list_of_antecedents:
                s = s + str(i) + '. ' + a.illustrate() + ' '
                i = i + 1
                if i == 2:
                    s = s + '   (alternatives: '
            if i > 1:
                s = s + ')'
            if s:
                log(f'\t\t\t\t\t' + s)
            else:
                log(f'\t\t\t\t\t{self.failed_recovery(unvalued_phi_features)}')
            return True

    # This function will later be moved to its own class that contains discourse computations.
    # Now it is here to speed up processing
    def failed_recovery(self, features):

        if 'PHI:NUM:_' in features and 'PHI:PER:_' in features:
            return 'Generic'
        else:
            return 'Person feature is missing'

    # This functions binds a binding operator/antecedent at LF
    # = element that provides semantic interpretation for 'ps'.
    # Return the antecedent is found, otherwise None
    # The type of antecedent depends on uninterpretable features at 'ps'
    def bind(self, ps):

        ps_ = ps

        antecedent = set()      # Set that contains features that must be present in a legitimate antecedent
        for f in ps.features:   # Populate the set
            if f[:4] == 'ABAR':  # Only abar variables implemented for now
                antecedent.add('CAT:u'+f[5:])

        if not antecedent:      # If everything is interpretable, then we return the constituent itself
            return ps

        while ps_:
            if ps_.is_primitive():
                if ps_.check_features(antecedent) and 'FIN' in ps_.get_labels():
                    return ps_
            elif ps_.left_const.get_head().check_features(antecedent) and 'FIN' in ps_.get_labels():
                return ps_
            ps_ = ps_.walk_upstream()

        return None             # Nothing was found

    def semantic_match(a, b):

        a = a.get_head()
        b = b.get_head()

        pos_sem_a = {f[5:] for f in a.features if f.startswith('+SEM:')}
        neg_sem_a = {f[5:] for f in a.features if f.startswith('-SEM:')}

        pos_sem_b = {f[5:] for f in b.features if f.startswith('+SEM:')}
        neg_sem_b = {f[5:] for f in b.features if f.startswith('-SEM:')}

        return not ((pos_sem_a & neg_sem_b) or (pos_sem_b & neg_sem_a))

    # LF-interface check for the final phrase structure
    @staticmethod
    def final_tail_check(goal):

        if goal.is_primitive():
            # Tail-head test for one constituent

            # Case 1
            # If there are no tail features, the test is trivially accepted
            if not goal.get_tail_sets():
                return True

            # Case 2
            # Perform external tail-head test
            if goal.external_tail_head_test():
                return True
            else:
                feature_vector = goal.get_feature_vector()
                log(f'\t\t\t{goal}<{feature_vector}> failed to tail features {illu(goal.get_tail_sets())}')
                return False

        else:
            if not goal.left_const.find_me_elsewhere and not LF.final_tail_check(goal.left_const):
                return False
            if not goal.right_const.find_me_elsewhere and not LF.final_tail_check(goal.right_const):
                return False
        # If we are here, then it means we have [XP YP] that does not allow us to search any further
        return True
