
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

    # Checks LF-legibility for primitive constituents (not phrases)
    def test(self, ps):

        #
        # Internal function
        #
        # Definition for selected sister of head H
        # X(P) is the selected sister of H if and only if
        # Condition 1.  H is primitive and has a sister AND
        # Condition 2   If X(P) is a complex, then either a) or b)
        #               a)  X(P) is a right non-adjunct
        #               b)  X(P) is a left
        # Condition 3. If X(P) is primitive, then a)
        #               a)  X(P) is right
        #
        # Note: use of sister instead of geometrical sister ensures that is licensed [XP [H <YP>]]
        def selected_sister(h):

            # Condition 1. H is primitive and has a sister
            if h.is_primitive() and not h.sister():
                return None

            # Condition 2a-b
            if h.sister().is_complex():

                # b) X(P) is a left (XP H)
                if h.sister().is_left():
                    return h.sister()

                # a) X(P) is a right non-adjunct (H XP)
                elif h.sister().is_right() and not h.sister().adjunct:
                    return h.sister()

            # Condition 3. If X(P) is primitive, then it must be right (H X)
            else:
                if h.sister().is_right():
                    return h.sister()
                else:

                    # Right primitive head cannot be selected sister (because it must select)
                    return None

        # --- test function beings ---#

        if not ps.is_primitive():
            if not ps.left_const.find_me_elsewhere:
                self.test(ps.left_const)
            if not ps.right_const.find_me_elsewhere:
                self.test(ps.right_const)
            return

        h = ps  # keep track of the fact that we are operated with a primitive head

        local_edge = h.local_edge()
        edge = h.edge()
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
        if 'D' in h.labels() and not h.internal_tail_head_test():
            log(f'\t\t\t\t{h}({h.mother}) failed internal tail test for {h.get_tail_sets()}.')
            self.tail_head_test_result = False

        #
        # 4. Double Spec test for DP arguments
        #
        if '2SPEC' not in h.features:
            count = 0
            list_ = h.edge()
            if list_:
                for spec_ in list_:
                    if not spec_.adjunct and 'D' in spec_.labels() and not spec_.find_me_elsewhere:
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
                for spec_ in edge:

                    if spec_ and f[6:] in spec_.labels():
                        if not spec_.adjunct:
                            log(f'\t\t\t\t{ps} has unacceptable specifier {spec_}.')
                            self.selection_test_result = False

            # 3.2. No specifier of any kind allowed (e.g., English P).
            #       This excludes pro
            if f == '-SPEC:*':
                if local_edge:
                    if not local_edge.adjunct and not local_edge.find_me_elsewhere and 'pro' not in local_edge.features:
                        log(f'\t\t\t\t{h} ({h.illustrate()}) has a specifier {local_edge}({local_edge.features}) '
                            f'but is marked for -EPP behavior.')
                        self.selection_test_result = False

            # 3.3. Obligatory complement
            if f.startswith('!COMP:') and not f == '!COMP:*':
                if not selected_sister(h):
                    log(f'\t\t\t\t{h} ({h.illustrate()}) is missing complement {f[6:]}')
                    self.selection_test_result = False
                else:
                    if f[6:] not in selected_sister(ps).labels():
                        log(f'\t\t\t\t\t{h} ({h.illustrate()}) is missing a mandatory complement {f[6:]}')
                        self.selection_test_result = False

            # 3.4. Complement restriction
            if f.startswith('-COMP:'):
                if h.is_left() and comp and f[6:] in comp.labels():
                    log(f'\t\t\t\t"{ps}\" has wrong complement {comp} {illu(comp.labels())}P')
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
            if f == '!SPEC:*' and not local_edge:

                # This condition takes care of the curious fact that overt C cancels !SPEC:*
                # if h.get_selector() and 'C/fin' in h.get_selector().get_labels():
                #    pass
                # else:

                log(f'\t\t\t\tAn EPP-head "{h}" lacks specifier.')
                self.selection_test_result = False

            # 3.7. !SPEC:F, head requires specific specifier
            # Left adjunct can satisfy this, left non-adjunct must satisfy it
            if f.startswith('!SPEC:') and not f == '!SPEC:*':
                if not edge:
                    log(f'\t\t\t\tAn EPP-head "{h}" lacks specifier {f[6:]} that it requires.')
                    self.selection_test_result = False
                else:
                    found = False
                    for s in edge:
                        # First left adjunct CAN satisfy SPEC requirement
                        if s.adjunct:
                            if f[6:] in s.labels() or f[7:] in s.labels():
                                found = True
                                break
                        # First non-adjunct MUST satisfy SPEC requirement
                        else:
                            if f[6:] in s.labels() or f[7:] in s.labels():
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
        if 'D' in h.labels() and 'R' not in h.labels() and h.mother:
            # Check that if there is relative pronoun there is also T/fin
            if h.mother.contains_feature('CAT:R') and not h.mother.contains_feature('CAT:T/fin'):
                log(f'\t\t\t\tCriterial legibility failed for "{h}".')
                self.criterial_feature_test_result = False

        #
        # 8. Projection principle test for referential arguments
        #
        # Condition 1. Only target DPs that have not been copied elsewhere (check LF-positions)
        if 'D' in h.labels() and h.mother and not h.mother.find_me_elsewhere:

            # This is the DP to be tested
            DP_target = h.mother

            # Condition 2. DPs cannot occur at non-thematic SPEC positions
            if DP_target.container_head() and DP_target in DP_target.container_head().edge():

                # The head that contains the DP (and thus assigns it a thematic role)
                container_head = DP_target.container_head()

                # Condition 2.1 EPP heads
                if container_head.EPP():
                    log(f'\t\t\t\t{DP_target} has no thematic role due to being at SPEC of EPP head.')
                    self.projection_principle_test_result = False

                # Condition 2.2 Heads selected by -AGR heads
                elif container_head.selector() and 'ARG' not in container_head.selector().features:
                    log(f'\t\t\t\t{DP_target} has no thematic role due to a selecting -ARG head.')
                    self.projection_principle_test_result = False

                # Condition 2.3 The head does not select for a DP specifier
                elif 'D' not in container_head.specs():
                    if container_head.sister() != DP_target:
                        log(f'\t\t\t\t{DP_target} has no thematic role at the SPEC of {container_head}')
                        self.projection_principle_test_result = False

            # Condition 3. non-SPEC adjunct DPs must be licensed by 'adjoinable'
            elif DP_target.adjunct and not DP_target.contains_feature('adjoinable'):
                self.projection_principle_test_result = False

        # 9. Discourse/pragmatic tests
        #
        # 9.1 This test accumulates discourse violations for each SPEC that cannot (easily) be topicalized
        list_ = ps.edge()
        if list_:
            if len(list_) > 1:
                # Discourse penalty for multiple specifiers
                self.discourse_test_result = self.discourse_test_result + len(list_)*0.5
                if 'Neg/fin' in ps.labels(): # Negation increases the penalty
                    self.discourse_test_result = self.discourse_test_result + len(list_)
            for local_edge in list_:
                if 'INF' in local_edge.labels():
                    self.discourse_test_result = self.discourse_test_result + 2

        #
        # 10. Adjunct interpretation tests
        #
        # Condition 1. A DP right-adjunct cannot be interpreted inside another DP (e.g. [John <Mary>]
        if 'D' in h.labels() and \
                h.max() and h.max().adjunct and \
                h.max().is_right() and \
                h.max().mother and 'D' in h.max().mother.head().labels():
            log(f'\t\t\t\t{h.mother.mother} in uninterpretable.')
            self.adjunct_test_result = False

    # This function will try to transfer the phrase structure into the conceptual-intentional system
    # It represents the "outer edge of LF"
    def transfer_to_CI(self, ps):
        log(f'\t\t\tTransferring {ps} into the conceptual-intentional system...')
        self.transfer_to_CI_crash = False

        # Construction of semantic interpretation
        self.semantic_interpretation = self.check_for_transfer(ps)

        # If no semantic interpretation results, transfer crashes
        if not self.semantic_interpretation:
            log('\t\t\t\tSemantic interpretation failed, transfer to C-I crashed.')
            self.transfer_to_CI_crash = True
            return set()
        else:
            log('\t\t\t\tTransfer to C-I successful.')
            self.transfer_to_CI_crash = False
            return sorted(self.semantic_interpretation)

    # Definition for transfer to the conceptual-intentional system
    # XP is accepted for CI transfer if and only if
    # Condition 1. Operator-variable constructions satisfy operator binding conditions,
    # Condition 2. Unvalued phi-features can be linked with antecedents by LF-recovery
    # Condition 3. There are no phi-feature conflicts
    #
    # The operation returns a set of semantic interpretations when successful. It operates at the outer edge of
    # LF-interface right before the phrase structure is handed over to CI and is not longer inside syntax.
    def check_for_transfer(self, ps):

        # Recursion
        if ps.is_complex():
            if not ps.left_const.find_me_elsewhere:
                self.check_for_transfer(ps.left_const)
            if not ps.right_const.find_me_elsewhere:
                self.check_for_transfer(ps.right_const)

            # If the operation fails, the set of semantic interpretations will be empty
            if self.transfer_to_CI_crash:
                return set()
            else:
                # If the operation succeeds, semantic interpretation (set) is send back
                self.semantic_interpretation.add(' ')
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
        # Transfer condition 2. LF-recovery
        #
        # Head H requires LF-recovery if and only if
        # H has phi-features which are a) unvalued and b) must be valued for interpretation
        unvalued_phi_features = self.must_be_valued(ps.get_unvalued_features())
        if unvalued_phi_features:

            log(f'\t\t\t\t{ps} with {sorted(unvalued_phi_features)} was associated at LF with:')

            # Provides a list of antecedents and adds the local antecedent to semantic interpretation if available,
            # otherwise provides an interpretation for a "failed recovery"
            list_of_antecedents = self.LF_recovery(ps, unvalued_phi_features)
            # Provide the local antecedent to semantic interpretation (index 0 = local antecedent)
            if list_of_antecedents:
                self.semantic_interpretation.add(self.format_antecedent(ps, list_of_antecedents[0]))
            else:
                self.semantic_interpretation.add(f'{ps}(' + self.failed_recovery_outcome(ps, unvalued_phi_features) + ')')
            self.report_to_log(ps, list_of_antecedents, unvalued_phi_features)

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

    # Definition for phi-features which require antecedents at LF/C-I
    # Feature PHI requires antecedents at LF/C-I if and only if
    # Condition 1. PHI is a number feature OR
    # Condition 2. PHI is a person feature OR
    # Condition 3. Phi is a D-feature.
    def relevant_phi_at_LF(self, phi):
        if phi[:7] == 'PHI:NUM' or phi[:7] == 'PHI:PER' or phi[:7] == 'PHI:DET':
            return True
        else:
            return False

    # Definition for LF-recovery
    # [X1...Xn] is a list of possible antecedents for H with unvalued phi-set PHI if and only if
    # Condition 1. All X1...Xn are sisters of a node that is reached by geometrical upstream walk from H
    # Condition 2. All X1...Xn are possible antecedents for PHI.
    # Condition 3. All X1...Xn satisfy special conditions depending on the nature of PHI. Currently:
    #   a) If PHI contains PHI:NUM:_ and PHI:PER:_, search must terminate at v*; ELSE
    #   b) If PHI contains PHI:PER:_ but not PHI:NUM:, same as a) (used in radical pro-drop)
    #   c) If PHI contains PHI:DET but neither PHI:NUM:_ nor PHI:PER:_, search must terminate at first
    #   phrasal candidate inside H's edge which is recorded as 'generic' if it is not DP; if edge has no
    #   local specifier, search is uses (1-2). If nothing is found, the derivation crashes.
    #   Comment: condition c) is relevant for Finnish partial pro-drop (Holmberg hypothesis)
    # Condition 4. X1...Xn are ordered with respect to locality to H, X1 being the closest. Typically only the
    # local is used for semantic interpretation, but not necessarily, hence all antecedents are provided here.
    def LF_recovery(self, ps, unvalued_phi):
        ps_ = ps
        head = ps

        list_of_antecedents = []
        #
        # Alternative 1: H has unvalued per/num features: standard control
        #
        if 'PHI:NUM:_' in unvalued_phi and 'PHI:PER:_' in unvalued_phi:
            while ps_:
                #
                # Termination condition: sister is a strong phase head
                # (Strong phase head = Force or v*)
                if ps_.sister() and 'SEM:external' in ps_.sister().features:
                    break
                #
                # XP is an antecedent is anf only if
                # Condition 1. Antecedent must be a sister of the node reached by upstream walk from H, and
                # Condition 2. The phrase must evaluate as a possible antecedent.
                if ps_.geometrical_sister() and self.is_possible_antecedent(ps_.geometrical_sister(), ps):
                    list_of_antecedents.append(ps_.geometrical_sister())
                ps_ = ps_.walk_upstream_geometrically()
            return list_of_antecedents
        #
        # Alternative 2. Only PER_ remains unvalued: standard control (currently, used in radical pro-drop)
        #
        elif 'PHI:PER:_' in unvalued_phi:
            while ps_:
                #
                # Termination condition: presence of SEM-external (control boundary)
                if ps_.sister() and 'SEM:external' in ps_.sister().features:
                    break
                #
                # Condition 1. Antecedent must be a sister of the node at the spine we climb up
                # Condition 2. The phrase must evaluate as a possible antecedent
                if ps_.sister() and self.is_possible_antecedent(ps_.sister(), ps):
                    list_of_antecedents.append(ps_.sister())
                ps_ = ps_.walk_upstream_geometrically()
            return list_of_antecedents
        #
        # Alternative 3. Only D_ remains unvalued: nonlocal/discourse antecedents
        #
        elif 'PHI:DET:_' in unvalued_phi:
            while ps_:
                #
                # Termination condition: presence of local specifier
                # Example: tässä istuu mukavasti 'here sit.3sg comfortably'
                if ps_.sister() and ps_.sister() == ps.local_edge():
                    #
                    # If the local candidate is not a DP, it will be interpreted as generic
                    if ps_.sister() and 'CAT:D' not in ps_.sister().head().features:
                        self.semantic_interpretation.add(f'{ps}(generic)')
                        list_of_antecedents.append(ps_.sister())
                        head.features.add('PHI:DET:GEN')
                    #
                    # If the local candidate is DP, it will be the antecedent
                    else:
                        list_of_antecedents.append(ps_.sister())
                    #
                    # Nothing else is searched (currently)
                    break
                #
                # If there is no local antecedent inside the edge of H, then we get all antecedents.
                if ps_.sister() and self.is_possible_antecedent(ps_.sister(), ps):
                    list_of_antecedents.append(ps_.sister())
                ps_ = ps_.walk_upstream_geometrically()

            # Condition 3c: if no antecedent is found, LF-recovery crashes
            if not list_of_antecedents:
                log(f'\t\t\t\t\tNo antecedent found, LF-object crashes.')
                self.transfer_to_CI_crash = True
            return list_of_antecedents

    # Defines the category of possible antecedent for a goal head H
    # X is a possible antecedent for H if and only H
    # Condition 1. X has not been moved into another position
    # Condition 2. X check all H's relevant phi-features (valued, unvalued). A valued feature F at X checks
    # feature G at H if and only if
    #   a) F = G, or
    #   b) G is unvalued and F can value G.
    def is_possible_antecedent(self, antecedent, h):

        # Condition 1. X has not been moved into another position
        if antecedent.find_me_elsewhere:
            return False

        # Set of relevant phi-features at H (valued and unvalued)
        h_phi_features = {f for f in h.features if self.relevant_phi_at_LF(f)}

        # Set of unchecked features at H (will be checked by features of the antecedent)
        unchecked_features_at_h = h_phi_features.copy()

        # Condition 2. Antecedent X can check all H's relevant phi-features.
        for F in {phi for phi in antecedent.head().features if phi[:4] == 'PHI:' and phi[-1] != '_'}:
            for G in h_phi_features:

                # Condition 2a) Valued feature F at antecedent X checks G at H if F = G.
                if F == G:
                    unchecked_features_at_h.discard(G)  # Check feature

                # Condition 2b) Valued feature F at antecedent X checks G at H if F can value G.
                else:
                    if G[-1] == '_':
                        if F[:len(G)-1] == G[:-1]:
                            unchecked_features_at_h.discard(G)  # Check feature

        # If features remain unchecked, the antecedent is rejected
        if unchecked_features_at_h:
            return False
        else:
            return True

    # Definition for the notion of phrasal phase
    # XP is a phrasal phase if and only if
    # Condition 1. XP's sister is a phase head
    def phase(self, ps_):
        if ps_.sister() and ps_.sister().is_phase():
            return True
        else:
            return False

    def report_to_log(self, ps, list_of_antecedents, unvalued_phi_features):
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
                log(f'\t\t\t\t\t{ps}{self.failed_recovery_outcome(ps, unvalued_phi_features)}')
            return True

    # Definition for failed LF-recovery outcome
    # Presupposition. LF-recovery fails if and only if no antecedent is found
    # A failed outcome for LF-recovery for head H depends on unvalued phi-features:
    #   a) NUM_, PER_: "clausal argument" if the sister is a clause, "generic" otherwise;
    #   b) PER_: "discourse";
    #   c) "uninterpretable" otherwise
    def failed_recovery_outcome(self, ps, features):
        if 'PHI:NUM:_' in features and 'PHI:PER:_' in features:
            if ps.sister() and ps.sister().is_complex() and \
                    ('CAT:INF' in ps.sister().head().features or 'CAT:FIN' in ps.sister().head().features):
                return 'clausal argument'
            else:
                return 'generic'
        elif 'PHI:PER:_' in features and 'PHI:NUM:_' not in features:
            return 'discourse antecedent'
        else:
            return 'uninterpretable'

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
                if ps_.match_features(antecedent) == 'complete match' and 'FIN' in ps_.get_labels():
                    return ps_
            elif ps_.left_const.head().match_features(antecedent) == 'complete match' and 'FIN' in ps_.labels():
                return ps_
            ps_ = ps_.walk_upstream()

        return None             # Nothing was found

    def semantic_match(a, b):

        a = a.head()
        b = b.head()

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
                feature_vector = goal.feature_vector()
                log(f'\t\t\t{goal}<{feature_vector}> failed to tail features {illu(goal.get_tail_sets())}')
                return False

        else:
            if not goal.left_const.find_me_elsewhere and not LF.final_tail_check(goal.left_const):
                return False
            if not goal.right_const.find_me_elsewhere and not LF.final_tail_check(goal.right_const):
                return False
        # If we are here, then it means we have [XP YP] that does not allow us to search any further
        return True

    # Provides a more readable alternative reading form for antecedents
    def format_antecedent(self, trigger, antecedent):

        antecedent_head = antecedent.head()

        arg_str = ''
        # This is a rudimentary thematic theory that has not yet been implemented
        # These notions are simply returned as heuristic semantic interpretation to the user, and they have
        # no effect on anything
        if trigger.sister() and trigger.is_left() and antecedent == trigger.sister() and antecedent.is_right():
            prefix = 'Patient of'
        else:
            prefix = 'Agent of'

        if 'CAT:D' in antecedent_head.features:
            if antecedent_head.sister() and 'CAT:N' in antecedent_head.sister().head().features:
                arg_str = antecedent_head.sister().head().get_pf()
            else:
                arg_str = antecedent.illustrate()
        elif 'CAT:C' in antecedent_head.features or 'CAT:FORCE' in antecedent_head.features and antecedent.is_complex():
            arg_str = 'C-proposition'
        elif 'CAT:V' in antecedent_head.features and antecedent.is_complex():
            arg_str = 'agent of V-event'
        elif 'CAT:T' in antecedent_head.features:
            if antecedent.is_complex():
                arg_str = 'agent of T-event'
            else:
                arg_str = f'{sorted(antecedent.get_valued_phi_set())}'
        else:
            arg_str = antecedent.illustrate()

        return prefix + f' {trigger}({arg_str})'
