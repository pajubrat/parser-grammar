
from support import log, illu


# Transforms a set of lexical features to be used in checking LF-interface conditions
def for_lf_interface(features):
    return {f for f in features if f.startswith('!') or f.startswith('-')}


class LF:

    def __init__(self):
        # Test result variables
        self.probe_goal_test_result = True
        self.selection_test_result = True
        self.tail_head_test_result = True
        self.head_integrity_test_result = True
        self.criterial_feature_test_result = True
        self.semantic_test_result = True
        self.discourse_test_result = 0
        self.projection_principle_test_result = True
        self.transfer_crash = False

    def all_pass(self):
        return (self.probe_goal_test_result and
                self.selection_test_result and
                self.tail_head_test_result and
                self.head_integrity_test_result and
                self.criterial_feature_test_result and
                self.semantic_test_result and
                self.projection_principle_test_result)

    def fail(self):
        return not self.all_pass()

    # LF-tests that checks LF-legibility for primitive constituents (not phrases)
    # todo THE CORRECTNESS OF THIS CHANGE HAS TO BE VERIFIED CAREFULLY
    def test(self, ps):
        # Returns the selected sister (if any) of the constituent
        def selected_sister(ps):

            # Only primitive constituents with sisters can select sisters
            if ps.is_primitive() and not ps.sister():
                return None

            # H~YP, YP~H => YP is selected sister
            if not ps.sister().is_primitive():
                return ps.sister()
            else:
                # H~Y => Y is selected sister
                if ps.sister().is_right():
                    return ps.sister()
                else:
                    # Y~H => Y is not selected sister for H
                    return None

        # --- test function beings ---#
        if ps.has_children():
            if not ps.left_const.find_me_elsewhere:
                self.test(ps.left_const)
            if not ps.right_const.find_me_elsewhere:
                self.test(ps.right_const)
            return

        h = ps  # Just to keep track of the fact that we have selected primitive head

        spec = h.specifier()
        specs = h.get_specifiers()

        comp = h.complement()
        lf_features = sorted(for_lf_interface(h.features))

        # 1. Head integrity test
        if not h.get_cats():
            log('\t\t\t\tAn uninterpretable grammatical head without lexical category was detected.')
            self.head_integrity_test_result = False

        # 2. Probe-goal test
        for f in lf_features:
            if f.startswith('!PROBE:'):
                if not h.probe(set(h.get_cats()), f[7:]):
                    log(f'\t\t\t\t{ps} probing for {f[7:]} failed.')
                    self.probe_goal_test_result = False

        # 3. Internal tail-head test for case (DPs)
        if 'D' in h.get_labels() and not h.internal_tail_head_test():
            log(f'\t\t\t\th{h} failed internal tail test.')
            self.tail_head_test_result = False

        # 4. Double Spec test for DP arguments
        if '2SPEC' not in h.features:
            """
            Returns False if the head is associated with more than one non-adjunct DP specifier at LF
            
            The test ignores adjuncts, non-DPs and DPs that have been moved out from SPEC
            """
            count = 0
            list_ = h.get_specifiers()
            if list_:
                for spec_ in list_:
                    if not spec_.adjunct and 'D' in spec_.get_labels() and not spec_.find_me_elsewhere:
                        count = count + 1

            if count > 1:
                self.head_integrity_test_result = False
                log(f'\t\t\t\t{ps} has double specifiers.')

        # 5. Semantic match test between H and Comp,H
        if comp:
            if not LF.semantic_match(h, h.complement()):
                self.semantic_test_result = False
                log(f'\t\t\t\t{ps} fails semantic match with {h.complement()}')

        # 6. Selection tests
        for f in lf_features:

            # 3.1. Specifier selection
            if f.startswith('-SPEC:'):
                if spec and f[6:] in spec.get_labels():
                    if not spec.adjunct:
                        log(f'\t\t\t\t{ps} has unaccetable specifier {spec}.')
                        self.selection_test_result = False

            # 3.2. No specifier of any kind allowed (e.g., English P)
            if f == '-SPEC:*':
                if spec:
                    if not (spec.adjunct and spec.find_me_elsewhere):
                        log(f'\t\t\t\t{h} ({h.illustrate()}) has a specifier {spec} '
                            f'but is marked for -EPP behavior.')
                        self.selection_test_result = False

            # 3.3. Obligatory complement
            if f.startswith('!COMP:') and not f == '!COMP:*':
                if not selected_sister(h):
                    log(f'\t\t\t\t{h} ({h.illustrate()}) is missing complement {f[6:]}')
                    self.selection_test_result = False
                else:
                    if f[6:] not in selected_sister(ps).get_labels():
                        log(f'\t\t\t\t{h} ({h.illustrate()}) is missing a mandatory complement {f[6:]}')
                        self.selection_test_result = False

            # 3.4. Complement restriction
            if f.startswith('-COMP:'):
                if h.is_left() and comp and f[6:] in comp.get_labels():
                    log(f'\t\t\t\t"{ps}\" has wrong complement {comp} {illu(comp.get_labels())}P')
                    self.selection_test_result = False

            if f == '-COMP:*':
                if h.is_left() and comp:
                    log(f'\t\t\t\t{h} does not accept complements.')
                    self.selection_test_result = False

            # 3.5. !COMP:* heads must have complements (=functional head)
            if f == '!COMP:*':
                if not comp:
                    log(f'\t\t\t\tA phi-marked head "{ps}" lacks complement')
                    self.selection_test_result = False

            # 3.6. !SPEC:* heads require a specifier
            if f == '!SPEC:*' and not spec:
                # This condition takes care of the curious fact that overt C cancels !SPEC:*
                if h.get_selector() and 'FIN' in h.get_selector().get_labels():
                    pass
                else:
                    log(f'\t\t\t\tAn EPP-head "{h}" lacks specifier but needs one.')
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
                        # Suitable left adjunct can satisfy SPEC requirement
                        if s.adjunct:
                            if f[6:] in s.get_labels() or f[7:] in s.get_labels():
                                found = True
                                break
                        # Suitable non-adjunct must satisfy SPEC requirement
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

        # 7. Criterial feature legibility test(s)
        # 7.1 test for relative pronoun
        # For every DP that it not a relative pronoun
        if 'D' in h.get_labels() and 'R' not in h.get_labels() and h.mother:
            # Check that if there is relative pronoun there is also T/fin
            if h.mother.contains_feature('CAT:R') and not h.mother.contains_feature('CAT:T/fin'):
                log(f'\t\t\t\tCriterial legibility failed for "{h}".')
                self.criterial_feature_test_result = False

        # 8. Projection principle test for referential non-adjunct arguments
        # Check only non-adjunct arguments
        # It is very interesting if the first condition could reduce to the second, then we dont need
        # EPP condition anymore (PPs however)
        if spec and not spec.adjunct and 'D' in spec.get_labels() and not spec.find_me_elsewhere:
            # They cannot be left to the SPEC of non-thematic head
            if h.EPP():
                log(f'\t\t\t\t{spec}" has no thematic role.')
                self.projection_principle_test_result = False
            # or to the SPEC of a head that is selected by -PHI head.
            else:
                if h.get_selector() and '+PHI' not in h.get_selector().features:
                    log(f'\t\t\t\t{spec} has no thematic role due to a selecting -PHI head.')
                    self.projection_principle_test_result = False

        # 9. Discourse/pragmatic tests
        # 9.1 This test accumulates discourse violations for each SPEC that cannot (easily) be topicalized
        list_ = ps.get_specifiers()
        if list_:
            if len(list_) > 1:
                # Discourse penalty for multiple specifiers
                self.discourse_test_result = self.discourse_test_result + len(list_)*0.5
                if 'Neg/fin' in ps.get_labels(): # Negation increases the penalty
                    self.discourse_test_result = self.discourse_test_result + len(list_)
            for spec in list_:
                if 'INF' in spec.get_labels():
                    self.discourse_test_result = self.discourse_test_result + 2

    # This function will try to transfer the phrase structure into LF out of syntactic working memory
    # It represents the "outer edge of LF"
    def transfer_to_LF(self, ps):
        log(f'\t\t\tTrying to transfer {ps} into LF...')
        self.transfer_crash = False
        self.check_for_transfer(ps)
        if self.transfer_crash:
            log('\t\t\t\tTransfer to LF crashed.')
            return False
        else:
            log('\t\t\t\tTransfer to LF successful.')
            return True

    # Checks if the phrase structure constitutes a legitimate LF-object
    # It is assumed that this represents the output from LF/C-I during an attempt at Transfer
    # Checks for (a) binding and (b) null subject/anaphora recovery
    def check_for_transfer(self, ps):
        if ps.has_children():                           # Check primitive constituents only
            if not ps.left_const.find_me_elsewhere:
                self.check_for_transfer(ps.left_const)
            if not ps.right_const.find_me_elsewhere:
                self.check_for_transfer(ps.right_const)
            return

        # All variables and uninterpretable phi-features must be bound before transfer
        for f in ps.features:
            if f[:4] == 'ABAR':
                if not self.bind(ps):
                    log(f'\t\t\t\t{ps}['+f+'] is not properly bound, the expression is uninterpretable.')
                    self.transfer_crash = True
                    return
                else:
                    log(f'\t\t\t\t{ps}['+f+'] was bound to an operator.' )

        # Unvalued phi-features D, NUM, PER must be matched with antecedents by recovery
        unvalued_phi_features = self.must_be_valued(ps.get_unvalued_features())

        if unvalued_phi_features:
            log(f'\t\t\t\t{ps} with {unvalued_phi_features} was associated at LF with:')
            list_of_antecedents = self.search_phi_antecedents(ps)
            self.report_to_log(list_of_antecedents, unvalued_phi_features)

        # Feature conflicts are not tolerated
        phi_set = ps.get_phi_set()
        for phi in phi_set:
            if phi[-1] == '*':
                log(f'\t\t\t\t{ps} induces a phi-feature conflict.')
                self.transfer_crash = True
                return
        return

    def must_be_valued(self, phi_set):
        return {phi for phi in phi_set if phi.split(':')[1]=='DET' or phi.split(':')[1]=='PER' or phi.split(':')[1]=='NUM'}


    # Searches a (prioritized) list of antecedents for a set of unvalued phi-feature
    # This function will be unified with the binding function below, but for now I will keep them separate
    # to be able to focus on one problem at a time
    def search_phi_antecedents(self, ps):
        ps_ = ps
        list_of_antecedents = []
        while ps_:
            if self.phase(ps_):
                break
            if ps_.sister() and self.evaluate_antecedent(ps_.sister(), ps):
                list_of_antecedents.append(ps_.sister())
            ps_ = ps_.walk_upstream()
        return list_of_antecedents

    # Evaluates whether 'probe' could provide semantic support for 'goal'
    def evaluate_antecedent(self, probe, goal):
        goal_phi_features = {f for f in goal.features if f[:4] == 'PHI:'}
        unchecked_features_at_goal = goal_phi_features.copy()
        for probe_feature in probe.get_head().features:
            # Only phi-features can be used for valuation
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

    def phase(self, ps_):
        if ps_.sister() and ps_.sister().is_phase():
            return True
        else:
            return False

    def report_to_log(self, list_of_antecedents, unvalued_phi_features):
        s = ''
        i = 1
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
            log(f'\t\t\t\t\t{self.conceptual_intentional_system(unvalued_phi_features)}')
        return True

    # This function will later be moved to its own class that contains discourse computations.
    # No it is here to speed up processing
    def conceptual_intentional_system(self, features):
        generic_criteria = {'PHI:DET:_', 'PHI:NUM:_', 'PHI:PER:_'}
        discourse_criteria = {'PHI:DET:_'}

        if features & generic_criteria == generic_criteria:
            return '(Generic interpretation)'
        if features & discourse_criteria == discourse_criteria:
            self.transfer_crash = True
            return '(Salient discourse antecedent or ungrammatical if not found)'
        return '(Cannot be interpreted at C-I, ungrammatical)'


    # This functions binds a binding operator/antecedent at LF
    # = element that provides semantic interpretation for 'ps'.
    # Return the antecedent is found, otherwise None
    # The type of antecedent depends on uninterpretable features at 'ps'
    def bind(self, ps):

        ps_ = ps

        antecedent = set()      # Set that contains features that must be present in a legitimate antecedent
        for f in ps.features:   # Populate the set
            if f[:4] == 'ABAR': # Only abar variables implemented for now
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
                for head in feature_vector:
                    log(head.get_pf())
                return False

        else:
            if not goal.left_const.find_me_elsewhere and not LF.final_tail_check(goal.left_const):
                return False
            if not goal.right_const.find_me_elsewhere and not LF.final_tail_check(goal.right_const):
                return False
        # If we are here, then it means we have [XP YP] that does not allow us to search any further
        return True
