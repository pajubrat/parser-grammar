
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
        if ps.is_primitive():
            self.head_integrity_test(ps)
            self.probe_goal_test(ps)
            self.internal_tail_test(ps)
            self.double_spec_filter(ps)
            self.semantic_complement_test(ps)
            self.selection_tests(ps)
            self.criterial_feature_test(ps)
            self.projection_principle(ps)
            self.adjunct_interpretation_test(ps)
            self.bind_variables(ps)
        else:
            if not ps.left_const.find_me_elsewhere:
                self.test(ps.left_const)
            if not ps.right_const.find_me_elsewhere:
                self.test(ps.right_const)

    def adjunct_interpretation_test(self, h):
        if 'D' in h.features and \
                h.max() and h.max().adjunct and \
                h.max().is_right() and \
                h.max().mother and 'D' in h.max().mother.head().features:
            log(f'\t\t\t\t{h.mother.mother} in uninterpretable.')
            self.adjunct_test_result = False

    def head_integrity_test(self, h):
        if not h.features or 'CAT:?' in h.features:
            log('\t\t\t\t\tAn uninterpretable grammatical head without lexical category was detected.')
            self.head_integrity_test_result = False

    def probe_goal_test(self, h):
        for f in sorted(for_lf_interface(h.features)):
            if f.startswith('!PROBE:'):
                if not h.probe(set(h.features), f[7:]):
                    log(f'\t\t\t\t{h} probing for {f[7:]} failed.')
                    self.probe_goal_test_result = False

    def internal_tail_test(self, h):
        if 'D' in h.features and not h.internal_tail_head_test():
            log(f'\t\t\t\t{h}({h.mother}) failed internal tail test for {h.get_tail_sets()}.')
            self.tail_head_test_result = False

    def double_spec_filter(self, h):
        if '2SPEC' not in h.features:
            count = 0
            list_ = h.edge()
            if list_:
                for spec_ in list_:
                    if not spec_.adjunct and 'D' in spec_.head().features and not spec_.find_me_elsewhere:
                        count = count + 1
            if count > 1:
                self.head_integrity_test_result = False
                log(f'\t\t\t\t{h} has double specifiers.')

    def semantic_complement_test(self, h):
        if h.complement():
            if not LF.semantic_match(h, h.complement()):
                self.semantic_test_result = False
                log(f'\t\t\t\t{ps} fails semantic match with {h.complement()}')

    def criterial_feature_test(self, h):
        if 'D' in h.features and 'REL' not in h.features and h.mother:
            if h.mother.contains_feature('REL') and not h.mother.contains_feature('T/fin'):
                log(f'\t\t\t\tCriterial legibility failed for "{h}".')
                self.criterial_feature_test_result = False

    def projection_principle(self, h):
        if 'D' in h.features and h.mother and not h.mother.find_me_elsewhere:
            DP_target = h.mother
            if DP_target.container_head() and DP_target in DP_target.container_head().edge():
                container_head = DP_target.container_head()
                if container_head.EPP():
                    log(f'\t\t\t\t{DP_target} has no thematic role due to being at SPEC of EPP head.')
                    self.projection_principle_test_result = False
                elif container_head.selector() and 'ARG' not in container_head.selector().features:
                    log(f'\t\t\t\t{DP_target} has no thematic role due to a selecting -ARG head.')
                    self.projection_principle_test_result = False
                elif 'D' not in container_head.specs():
                    if container_head.sister() != DP_target:
                        log(f'\t\t\t\t{DP_target} has no thematic role at the SPEC of {container_head}')
                        self.projection_principle_test_result = False
            elif DP_target.adjunct:
                if not DP_target.contains_feature('adjoinable'):
                    self.projection_principle_test_result = False
                else:
                    if not DP_target.get_theta_assigner() and not DP_target.contains_feature('SEM:nonreferential'):
                            self.projection_principle_test_result = False

    def selection_tests(self, h):
        comp = h.complement()
        local_edge = h.local_edge()
        for f in sorted(for_lf_interface(h.features)):
            if f.startswith('-SPEC:'):
                for spec_ in h.edge():
                    if spec_ and f[6:] in spec_.head().features:
                        if not spec_.adjunct:
                            log(f'\t\t\t\t{h} has unacceptable specifier {spec_}.')
                            self.selection_test_result = False

            # No specifier of any kind allowed (e.g., English P).
            # This excludes pro
            if f == '-SPEC:*':
                if local_edge:
                    if not local_edge.adjunct and not local_edge.find_me_elsewhere and 'pro' not in local_edge.head().features:
                        log(f'\t\t\t\t{h} ({h.illustrate()}) has a specifier {local_edge}({local_edge.head().features}) '
                            f'but is marked for -EPP behavior.')
                        self.selection_test_result = False

            # Obligatory complement
            if f.startswith('!COMP:') and not f == '!COMP:*':
                if not h.selected_sister():
                    log(f'\t\t\t\t{h} is missing complement {f[6:]}')
                    self.selection_test_result = False
                else:
                    if f[6:] not in h.selected_sister().head().features:
                        log(f'\t\t\t\t\t{h} is missing a mandatory complement {f[6:]}')
                        self.selection_test_result = False

            # Complement restriction
            if f.startswith('-COMP:'):
                if h.is_left() and comp and f[6:] in comp.head().features:
                    log(f'\t\t\t\t"{h}\" has wrong complement {comp}.')
                    self.selection_test_result = False
                    self.wrong_complement_test_result = False

            if f == '-COMP:*':
                if h.is_left() and comp:
                    log(f'\t\t\t\t{h} does not accept complements.')
                    self.selection_test_result = False

            # !COMP:* heads must have complements (=functional head)
            if f == '!COMP:*':
                if not h.selected_sister():
                    log(f'\t\t\t\t"{h}" lacks complement.')
                    self.selection_test_result = False

            # !SPEC:* heads require a specifier
            if f == '!SPEC:*' and not local_edge:
                log(f'\t\t\t\tAn EPP-head "{h}" lacks specifier.')
                self.selection_test_result = False

            # !SPEC:F, head requires specifier with label F
            # This feature must be satisfied by local edge (local specifier)
            if f.startswith('!SPEC:') and not f == '!SPEC:*':
                if not local_edge:
                    log(f'\t\t\t\tAn EPP-head "{h}" lacks specifier {f[6:]} that it requires.')
                    self.selection_test_result = False
                else:
                    if f[6:] in local_edge.head().features or f[7:] in local_edge.head().features:
                        pass
                    else:
                        log(f'\t\t\t\tAn EPP-head "{h}" has wrong specifier {local_edge}, needs {f[6:]}')
                        self.selection_test_result = False

    def bind_variables(self, ps):
        if 'C' not in ps.head().features:
            for f in ps.head().features:
                if f[:3] == 'OP:' and f != 'OP:_':
                    if not self.bind_to_operator(ps, 'OP'):
                        log(f'\t\t\t\t{ps} with feature {f} is not properly bound by an operator.')
                        self.transfer_to_CI_crash = True
                    else:
                        log(f'\t\t\t\t{ps} with feature {f} was bound to an operator.')
                        self.semantic_interpretation.add(f'{ps} with feature {f} was bound to an operator.')
        return

    def bind_to_operator(self, ps , operator):
        ps_ = ps
        while ps_:
            if ps_.is_primitive():
                if ps_.match_features({operator}) == 'complete match' and 'FIN' in ps_.head().features:
                    return ps_
            elif ps_.left_const.head().match_features({operator}) == 'complete match' and \
                    'FIN' in ps_.left_const.head().features:
                return ps_
            ps_ = ps_.walk_upstream()

    # This function will try to transfer the phrase structure into the conceptual-intentional system
    def transfer_to_CI(self, ps):
        log(f'\t\t\tTransferring {ps} into the conceptual-intentional system...')
        self.transfer_to_CI_crash = False
        self.semantic_interpretation = self.create_semantic_interpretation(ps)
        if not self.semantic_interpretation:
            log('\t\t\t\tSemantic interpretation failed, transfer to C-I crashed.')
            self.transfer_to_CI_crash = True
            return set()
        else:
            log('\t\t\t\tTransfer to C-I successful.')
            self.transfer_to_CI_crash = False
            return sorted(self.semantic_interpretation)

    # Definition for transfer to the conceptual-intentional system
    def create_semantic_interpretation(self, ps):
        if ps.is_primitive():
            self.perform_LF_recovery(ps)
            self.detect_phi_conflicts(ps)
            self.interpret_tail_features(ps)
        else:
            if not ps.left_const.find_me_elsewhere:
                self.create_semantic_interpretation(ps.left_const)
            if not ps.right_const.find_me_elsewhere:
                self.create_semantic_interpretation(ps.right_const)
            if self.transfer_to_CI_crash:
                return set()
            else:
                return self.semantic_interpretation | {' '}

    def interpret_tail_features(self, ps):
        tail_sets = ps.get_tail_sets()
        if tail_sets:
            for tail_set in tail_sets:
                tailed_head = self.get_target_head(ps, tail_set)
                self.interpret_tailing(ps, tailed_head)

    def interpret_tailing(self, ps, tailed_head):
        if tailed_head:
            self.interpret_argument_tailing(ps, tailed_head)
            self.interpret_adjunct_predication(ps, tailed_head)

    def interpret_argument_tailing(self, ps, tailed_head):
        if 'ASP:BOUNDED' in tailed_head.features:
            self.semantic_interpretation.add('Aspectually bounded')
            if 'PAR' in ps.features:
                if not self.bind_to_operator(ps, 'POL:NEG'):
                    self.semantic_interpretation.discard('Aspectually bounded')
                    self.semantic_interpretation.add('Aspectually anomalous')

    def interpret_adjunct_predication(self, ps, tailed_head):
        pass

    def get_target_head(self, ps, tail_set):
        for head in ps.feature_vector()[1:]:
            if head.match_features(tail_set) == 'complete match':
                return head

    def perform_LF_recovery(self, ps):
        unvalued_phi_features = self.must_be_valued(ps.get_unvalued_features())
        if unvalued_phi_features:
            log(f'\t\t\t\t{ps.illustrate()} with {sorted(unvalued_phi_features)} was associated at LF with:')
            list_of_antecedents = self.LF_recovery(ps, unvalued_phi_features)
            if list_of_antecedents:
                self.semantic_interpretation.add(self.format_antecedent(ps, list_of_antecedents[0]))
            else:
                self.semantic_interpretation.add(f'{ps}(' + self.failed_recovery_outcome(ps, unvalued_phi_features) + ')')
            self.report_to_log(ps, list_of_antecedents, unvalued_phi_features)

    def detect_phi_conflicts(self, ps):
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
    def relevant_phi_at_LF(self, phi):
        if phi[:7] == 'PHI:NUM' or phi[:7] == 'PHI:PER' or phi[:7] == 'PHI:DET':
            return True
        else:
            return False

    # Definition for LF-recovery
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
                if ps_.sister() and 'SEM:external' in ps_.sister().head().features:
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
                if ps_.sister() and 'SEM:external' in ps_.sister().head().features:
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
                    if ps_.sister() and 'D' not in ps_.sister().head().features:
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


    def semantic_match(a, b):

        a_head = a.head()
        b_head = b.head()

        pos_sem_a = {f[5:] for f in a_head.features if f.startswith('+SEM:')}
        neg_sem_a = {f[5:] for f in a_head.features if f.startswith('-SEM:')}

        pos_sem_b = {f[5:] for f in b_head.features if f.startswith('+SEM:')}
        neg_sem_b = {f[5:] for f in b_head.features if f.startswith('-SEM:')}

        return not ((pos_sem_a & neg_sem_b) or (pos_sem_b & neg_sem_a))

    # LF-interface check for the final phrase structure
    @staticmethod
    def final_tail_check(goal):

        if goal.is_primitive():
            if not goal.get_tail_sets():
                return True
            if goal.external_tail_head_test():
                return True
            else:
                feature_vector = goal.feature_vector()
                log(f'\t\t\t{goal}<{feature_vector}> failed to tail {illu(goal.get_tail_sets())}')
                return False
        else:
            if not goal.left_const.find_me_elsewhere and not LF.final_tail_check(goal.left_const):
                return False
            if not goal.right_const.find_me_elsewhere and not LF.final_tail_check(goal.right_const):
                return False
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

        if 'D' in antecedent_head.features:
            if antecedent_head.sister() and 'N' in antecedent_head.sister().head().features:
                arg_str = antecedent_head.sister().head().illustrate()
            else:
                arg_str = antecedent.illustrate()
        elif 'C' in antecedent_head.features or 'FORCE' in antecedent_head.features and antecedent.is_complex():
            arg_str = 'C-proposition'
        elif 'V' in antecedent_head.features and antecedent.is_complex():
            arg_str = 'agent of V-event'
        elif 'T' in antecedent_head.features:
            if antecedent.is_complex():
                arg_str = 'agent of T-event'
            else:
                arg_str = f'{sorted(antecedent.get_valued_phi_set())}'
        else:
            arg_str = antecedent.illustrate()

        return prefix + f' {trigger.illustrate()}({arg_str})'

    # Merges with constituents from the syntactic working memory if licensed by selection at LF
    def LFmerge(self, head, controlling_process):

        def hit_from_memory_buffer(h):
            for const in controlling_process.syntactic_working_memory:
                if h.get_comps() & const.head().features:
                    return const

        ps = head.get_specifier_anchor()

        # Try to fill in SPEC by operator
        if head.has_op_feature():
            for constituent_in_working_memory in controlling_process.syntactic_working_memory:
                if constituent_in_working_memory.scan_criterial_features():
                    if constituent_in_working_memory not in head.edge():
                        new_const = constituent_in_working_memory.copy_from_memory_buffer(controlling_process.babtize())
                        ps.merge(new_const, 'left')
                        log(f'\t\t\t\t\tMerging operator {constituent_in_working_memory} to Spec{head.get_cats_string()}P')
                        controlling_process.syntactic_working_memory.remove(constituent_in_working_memory)
                        controlling_process.number_of_phrasal_Move = + 1
                        break

        # Try to fill in SPEC by thematic selection
        specs = [spec for spec in head.edge() if not spec.is_primitive()]
        if not specs or (specs and specs[0].adjunct):
            for constituent_in_working_memory in controlling_process.syntactic_working_memory:
                if head.spec_match(constituent_in_working_memory):
                    if not head.EPP():
                        ps.merge(constituent_in_working_memory.copy(), 'left')
                        if ps.geometrical_sister().head().external_tail_head_test():
                            log(f'\t\t\t\t\tMerging constituent {constituent_in_working_memory} from memory buffer into Spec{head.get_cats_string()}P')
                            # Replace the hypothetical candidate (above) with proper chain (below) if the solution works
                            ps.geometrical_sister().remove()
                            new_const = constituent_in_working_memory.copy_from_memory_buffer(controlling_process.babtize())
                            ps.merge(new_const, 'left')
                            controlling_process.syntactic_working_memory.remove(constituent_in_working_memory)
                            controlling_process.number_of_phrasal_Move =+ 1
                            log(f'\t\t\t\t\t={ps.top()}')
                            break
                        else:
                            # If there was a tail-head violation, dropping is cancelled
                            ps.geometrical_sister().remove()

        # Try to fill COMP
        # Condition 1. H is a primitive head without complements that it needs
        if head.is_primitive() and not head.complement() and head.get_comps():
            const = hit_from_memory_buffer(head)
            if const:
                head.merge(const.copy_from_memory_buffer(controlling_process.babtize()), 'right')
                controlling_process.syntactic_working_memory.remove(const)
                log(f'\t\t\t\t\tMerging {repr(const)}(=' + const.spellout() + f') from memory buffer into Comp{head.get_cats_string()}P.')
                log(f'\t\t\t\t\tResult {head.top()}')
                controlling_process.number_of_phrasal_Move = + 1

        #  Condition 2. The head has a non-matching complement
        if head.is_left() and head.complement() and not (head.get_comps() & head.complement().features):
            const = hit_from_memory_buffer(head)
            if const and const.features & head.get_comps():
                head.complement().merge(const.copy_from_memory_buffer(controlling_process.babtize()), 'left')
                controlling_process.syntactic_working_memory.remove(const)
                log(f'\t\t\t\t\tMerging {repr(const)}(=' + const.spellout() + f') from memory buffer into Comp{head.get_cats_string()}P'
                                                                               f'due to the presence of mismatching complement {head.complement()}.')
                controlling_process.self.number_of_phrasal_Move = + 1
                # Mismatching complement will be made floater
                if head.complement().right_const.is_adjoinable():
                    log('\t\t\t\t\tThe mismatching complement will be transformed into floater adjunct.')
                    controlling_process.adjunct_constructor.create_adjunct(head.complement().right_const)


