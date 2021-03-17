
from support import log, illu

# Transforms a set of lexical features to be used in checking LF-interface conditions
def for_lf_interface(features):
    return {f for f in features if f.startswith('!') or f.startswith('-')}

class LF:
    def __init__(self, controlling_parsing_process):
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
        self.controlling_parsing_process = controlling_parsing_process

    def all_pass(self):
        """
        Returns [True] if and only if all LF-legibility tests pass
        """
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
        """
        Returns [True] if an LF-test fails.
        """
        return not self.all_pass()

    def report_lf_status(self):
        log('LF-legibility test...')
        log(f'probe-goal test: {self.probe_goal_test_result}...')
        log(f'selection test: {self.selection_test_result}...')
        log(f'tail-head test: {self.tail_head_test_result}...')
        log(f'head integrity test: {self.head_integrity_test_result}...')
        log(f'criterial test: {self.criterial_feature_test_result}...')
        log(f'semantic test: {self.semantic_test_result}...')
        log(f'projection principle: {self.projection_principle_test_result}...')
        log(f'complement test: {self.wrong_complement_test_result}...')
        log(f'adjunct test: {self.adjunct_test_result}...')

    def reset_flags(self):
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

    #
    #
    # Block 1. LF-interface generation
    #
    #
    # Merges with constituents from the syntactic working memory if licensed by selection at LF
    def try_LFmerge(self, constituent):
        """
        Attempts to merge constituent to the phrase structure [constituent] in such a way that the result would be
        pass LF-legibility. It is assumed that this operation is used in production and when reconstructing
        operators. The constituent comes from the memory buffer.

        We attempt merge to left, right adjunction and into complement position, in this order.
        """
        self.try_merge_to_left(constituent)
        self.try_adjoin_right(constituent)
        self.try_merge_to_comp(constituent)

    # Definition for right merge
    def try_adjoin_right(self, head):
        for constituent_from_MB in self.controlling_parsing_process.syntactic_working_memory:
            if 'ADV' in constituent_from_MB.head().features:
                target_node = head.get_specifier_sister()
                if self.tail_match(target_node, constituent_from_MB, 'right'):
                    new_const = self.LFMerge(constituent_from_MB, target_node, 'right')
                    new_const.adjunct = True
                    log(f'={target_node.top()}')
                    break

    # Definition for Spec-Merge
    def try_merge_to_left(self, head):
        if not head.EPP() and self.free_spec_position(head):
            for constituent_from_MB in self.controlling_parsing_process.syntactic_working_memory:
                target_node = head.get_specifier_sister()
                if self.specifier_match(head, constituent_from_MB) and self.tail_match(target_node, constituent_from_MB, 'left'):
                    self.LFMerge(constituent_from_MB, target_node, 'left')
                    log(f'={target_node.top()}...')
                    break

    # Tail_match
    def tail_match(self, target_node, constituent_from_MB, direction):
        target_node.merge_1(constituent_from_MB.copy(), direction)                      # Test merge
        if direction == 'right':                                                        # Presupposition
            target_node.geometrical_sister().adjunct = True
        result = target_node.geometrical_sister().head().external_tail_head_test()      # Test
        target_node.geometrical_sister().remove()                                       # Remove trial unit
        return result

    # Definition for Comp-Merge
    def try_merge_to_comp(self, head):

        # Case 1. missing complement
        if head.missing_complement():
            for const in self.controlling_parsing_process.syntactic_working_memory:
                if head.complement_match(const):
                    self.LFMerge(const, head, 'right')
                    log(f'={head.top()}...')
                    self.controlling_parsing_process.consume_resources("Move Phrase", f'{const}')
                    break

        # Case 2. Wrong complement
        if head.wrong_complement():
            for const in self.controlling_parsing_process.syntactic_working_memory:
                if head.complement_match(const):
                    old_complement = head.proper_complement()
                    head.proper_complement().merge_1(const.copy_from_memory_buffer(self.controlling_parsing_process.babtize()), 'left')
                    log(f'Merging {const} to Comp{head.get_cats_string()}P due to complement mismatch...')
                    if 'adjoinable' in old_complement.head().features:
                        log(f'Externalizing {old_complement}...')
                        old_complement.adjunct = True
                    self.controlling_parsing_process.syntactic_working_memory.remove(const)
                    self.controlling_parsing_process.consume_resources("Move Phrase", f'{const}')
                    break

    def LFMerge(self, constituent_from_MB, target, direction='left'):
        log(f'Merging {constituent_from_MB} {direction} of {target}...')
        new_const = constituent_from_MB.copy_from_memory_buffer(self.controlling_parsing_process.babtize())
        target.merge_1(new_const, direction)
        self.controlling_parsing_process.consume_resources("Move Phrase", f'{constituent_from_MB}')
        self.controlling_parsing_process.syntactic_working_memory.remove(constituent_from_MB)
        self.controlling_parsing_process.consume_resources("A-bar Move Phrase")
        return new_const

    def specifier_match(self, h, const):
        if 'SPEC:*' in h.features or '!SPEC:*' in h.features:
            return True
        for feature_in_head in h.convert_features_for_parsing(h.licensed_specifiers()):
            for feature_in_spec in const.head().features:
                if feature_in_head == feature_in_spec:
                    return True

    def free_spec_position(self, head):
        specs = [spec for spec in head.edge() if not spec.is_primitive()]
        return not specs or (specs and specs[0].adjunct)

    #
    #
    # Block 2. LF-interface legibility tests
    #
    #
    # Definition for the LF-interface legibility test
    def test(self, ps):
        """
        LF-legibility test for the whole constituent [ps].

        This operation tests all lexical items that are part of [ps] recursively.
        """
        self.reset_flags()
        self.controlling_parsing_process.consume_resources("LF test", f'{ps}')
        log('LF-interface test...')
        if not self._test(ps).all_pass():
            self.controlling_parsing_process.consume_resources("Failed Transfer", f'{ps}')
        return self

    # Recursive LF-legibility test (called from test())
    def _test(self, ps):
        """
        Tests when constituent [ps] satisfies LF-legibility.

        LF-legibility test is applied only to lexical items. If [ps] is a complex constituent,
        this function is called recursively for its left and right constituents. If [ps] is lexical item,
        then the following tests are applied:

        head integrity test
        probe-goal test
        internal tail test
        double spec filter
        semantic complement test
        selection tests
        criterial feature test
        projection principle
        adjunct interpretation tests
        """
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
        else:
            if not ps.left_const.find_me_elsewhere:
                self._test(ps.left_const)
            if not ps.right_const.find_me_elsewhere:
                self._test(ps.right_const)
        return self

    # A right DP-adjunct inside DP is uninterpretable
    def adjunct_interpretation_test(self, h):
        """
        Rules out illegitimate adjunct configurations.

        Currently only rules out right DP-adjuncts inside DPs. A complete solution will examine
        all illegitimate adjunct attachments on the basis of their tail features.
        """
        if 'D' in h.features and \
                h.max() and h.max().adjunct and \
                h.max().is_right() and \
                h.max().mother and 'D' in h.max().mother.head().features:
            log(f'.{h.mother.mother} in uninterpretable because it is inside DP...')
            self.adjunct_test_result = False

    def head_integrity_test(self, h):
        """
        Verifies that all lexical items have legitimate features to be interpretable.

        Unrecognized features are ruled out.
        """
        if not h.features or 'CAT:?' in h.features or '?' in h.features:
            log('.An uninterpretable grammatical head without lexical category was detected...')
            self.head_integrity_test_result = False

    def probe_goal_test(self, h):
        """
        Checks that all probe-features are matched with a goal.
        """
        for f in sorted(for_lf_interface(h.features)):
            if f.startswith('!PROBE:'):
                if not h.probe(set(h.features), f[7:]):
                    log(f'{h} probing for [{f[7:]}] failed...')
                    self.probe_goal_test_result = False
            if f.startswith('-PROBE:'):
                if h.probe(set(h.features), f[7:]):
                    log(f'{h} failed negative probe-test for [{f[7:]}]...')
                    self.probe_goal_test_result = False

    def internal_tail_test(self, h):
        """
        Checks that all D-elements satisfy their internal tail tests (in essence case checking)
        """
        if 'D' in h.features and not h.internal_tail_head_test():
            log(f'.{h}({h.mother}) failed internal tail test...')
            self.tail_head_test_result = False

    def double_spec_filter(self, h):
        """
        Checks that no lexical item has two specifiers unless specifically marked by [2SPEC] feature.

        The nontrivial part is how to distinguish the relevant specifiers from adjuncts. This problem
        is further aggravated by the fact that in some languages, such as Finnish, regular DP arguments
        can be interpreted as adjuncts. We will also have to take into account whether the element
        has been moved elsewhere.
        """
        if '2SPEC' not in h.features:
            count = 0
            list_ = h.edge()
            if list_:
                for spec_ in list_:
                    if not spec_.adjunct and 'D' in spec_.head().features and not spec_.find_me_elsewhere:
                        count = count + 1
            if count > 1:
                self.head_integrity_test_result = False
                log(f'{h} has double specifiers...')

    def semantic_complement_test(self, head):
        """
        Checks that a head-complement configuration does not violate semantic (SEM) features.
        """
        if head.proper_complement():
            if not LF.semantic_match(head, head.proper_complement()):
                self.semantic_test_result = False
                log(f'{head} fails semantic match with {head.proper_complement()}...')

    def criterial_feature_test(self, h):
        """
        Checks that criterial features are legitimate.

        Currently this function checks only that we don't have a relative pronoun inside
        a DP that contains no finite clause. For example, we rule out [the man who].
        """
        if 'D' in h.features and 'REL' not in h.features and h.mother:
            if h.mother.contains_feature('REL') and not h.mother.contains_feature('T/fin'):
                log(f'Criterial legibility failed for {h}...')
                self.criterial_feature_test_result = False

    def projection_principle(self, h):
        """
        Checks that all DP arguments have thematic roles, and that all thematic roles are assigned
        to some DP.

        The rule is very nontrivial due to the many ways DP argument may and may not be assigned
        thematic roles. The operation is broken down to several independent components which are

        (i) If the DP is contained inside a projection from a head that assigns a thematic role to it;
        if not, then we accept the configuration sill if and only if
        (ii) the DP is adjoinable and can be interpreted as nonreferential (DP adverbs);
        (iii) its thematic role can be identified by agreement (DP argument is adjunct);
        (iv) its thematic role can be identified by tailing (not yet implemented).

        """
        if self.projection_principle_applies_to(h):
            if h.max().container_head() and self.container_assigns_theta_role_to(h):
                return True
            else:
                if h.max().contains_feature('adjoinable') and h.max().contains_feature('SEM:nonreferential'):
                    return True
                if self.identify_thematic_role_by_agreement(h):
                    return True
                if self.identify_thematic_role_by_tailing(h):
                    return True
            self.projection_principle_test_result = False
            log(f'{h.max()} has no thematic role at {h.max().container_head().max()}. ')

    def identify_thematic_role_by_tailing(self, h):
        return False

    def identify_thematic_role_by_agreement(self, h):
        """
        Checks whether a constituent's thematic role can be identified by agreement.

        This happens if DP is inside projection from H and the phi-features between H and DP match, and if
        the local edge of H is not filled in by a complex phrase (that would block the agreement). The motivation
        is to project thematic roles to DP-arguments that are adjuncts.
        """
        if h.max().container_head():
            if h.max().container_head().get_valued_features() & h.max().head().get_valued_features() == h.max().head().get_valued_features():
                if not (h.max().container_head().local_edge() and h.max().container_head().local_edge().is_complex()):
                    return True

    def projection_principle_applies_to(self, h):
        """
        Determines whether the projection principles applied to some constituent.

        The projection principle applies H if and only if
        (i) H is a DP or projects DP
        (ii) H has not been moved elsewhere
        (iii) H is not the top node (isolated therefore)
        """
        if 'D' in h.features and \
            h.max() and \
            not h.max().find_me_elsewhere and \
            h.max().mother:
            return True

    def container_assigns_theta_role_to(self, h):
        """
        Determines whether the head of the projection that contains a constituent (DP) can assign a thematic role to it.

        X assigns a thematic role to HP (DP) if and only if
        (i) H selects DP as its complement;
        (ii) DP constitutes a licensed specifier of HP and (ii-a) H is not an EPP head, (ii-b) H has ARG,
        (ii-c) H's thematic role is not assignment to some other constituent.
        """
        if h.is_selected():
            return True
        if h.max().get_theta_assigner() and h.max().container_head().licensed_specifier() and h.max() == h.max().container_head().licensed_specifier():
            if h.max().container_head().EPP():
                return False
            if h.max().container_head().selector() and 'ARG' not in h.max().container_head().selector().features:
                return False
            if 'D' not in h.max().container_head().licensed_specifiers():
                if h.max().container_head().sister() != h.max():
                    return False
            return True

    def selection_tests(self, h):
        """
        Ensures that the selection features of [h] are checked.
        """
        comp = h.proper_complement()
        local_edge = h.local_edge()
        for f in sorted(for_lf_interface(h.features)):
            if f.startswith('-SPEC:'):
                for spec_ in h.edge():
                    if spec_ and f[6:] in spec_.head().features:
                        if not spec_.adjunct:
                            log(f'{h} has unacceptable specifier {spec_}...')
                            self.selection_test_result = False

            # No specifier of any kind allowed (e.g., English P).
            # This excludes pro and adjuncts
            if f == '-SPEC:*':
                if local_edge:
                    if not local_edge.adjunct and not local_edge.find_me_elsewhere and 'pro' not in local_edge.head().features:
                        log(f'"{h}" has a specifier {local_edge} but is marked for -EPP behavior...')
                        self.selection_test_result = False

            # No edge (second Merge-1) allowed (i.,.e V2 phenomenon, Finnish that)
            if f == '-EDGE:*' and local_edge:
                log(f'{h} has {local_edge} but does not accept second Merge-1 [-EDGE:*]')
                self.selection_test_result = False

            if f == '!1EDGE' and len(h.edge()) > 1:
                log(f'{h} is only allowed to host one edge element. ')
                self.selection_test_result = False

            # Obligatory complement
            if f.startswith('!COMP:') and not f == '!COMP:*':
                if not h.selected_sister():
                    log(f'.{h} is missing complement {f[6:]}...')
                    self.selection_test_result = False
                else:
                    if f[6:] not in h.selected_sister().head().features:
                        log(f'{h} is missing a mandatory complement {f[6:]}...')
                        self.selection_test_result = False

            # Complement restriction
            if f.startswith('-COMP:'):
                if h.is_left() and comp and f[6:] in comp.head().features:
                    log(f'"{h}\" has wrong complement {comp}...')
                    self.selection_test_result = False
                    self.wrong_complement_test_result = False

            if f == '-COMP:*':
                if h.is_left() and comp:
                    log(f'{h} does not accept complements...')
                    self.selection_test_result = False

            # !COMP:* heads must have complements (=functional head)
            if f == '!COMP:*':
                if not h.selected_sister():
                    log(f'"{h}" lacks complement...')
                    self.selection_test_result = False

            # !SPEC:* heads require a specifier
            if f == '!SPEC:*':
                if not local_edge:
                    log(f'An EPP-head "{h}" lacks specifier...')
                    self.selection_test_result = False

            # !SPEC:F, head requires specifier with label F
            # This feature must be satisfied by local edge (local specifier)
            if f.startswith('!SPEC:') and not f == '!SPEC:*':
                if not local_edge:
                    log(f'An EPP-head "{h}" lacks specifier {f[6:]} that it requires...')
                    self.selection_test_result = False
                else:
                    if f[6:] in local_edge.head().features or f[7:] in local_edge.head().features:
                        pass
                    else:
                        log(f'An EPP-head "{h}" has wrong specifier {local_edge}, needs {f[6:]}...')
                        self.selection_test_result = False

    # LF-interface check for the final phrase structure
    @staticmethod
    def final_tail_check(goal):
        if goal.is_complex():
            if not goal.left_const.find_me_elsewhere and not LF.final_tail_check(goal.left_const):
                return False
            if not goal.right_const.find_me_elsewhere and not LF.final_tail_check(goal.right_const):
                return False
        if goal.is_primitive():
            if goal.get_tail_sets() and not goal.external_tail_head_test():
                log(f'"{goal.illustrate()}" failed final tail test...')
                return False
        return True

    @staticmethod
    def semantic_match(a, b):
        a_head = a.head()
        b_head = b.head()
        pos_sem_a = {f[5:] for f in a_head.features if f.startswith('+SEM:')}
        neg_sem_a = {f[5:] for f in a_head.features if f.startswith('-SEM:')}
        pos_sem_b = {f[5:] for f in b_head.features if f.startswith('+SEM:')}
        neg_sem_b = {f[5:] for f in b_head.features if f.startswith('-SEM:')}
        return not ((pos_sem_a & neg_sem_b) or (pos_sem_b & neg_sem_a))