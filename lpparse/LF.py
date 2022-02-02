
from support import log

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
        self.test_problem_report = []
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
        self.test_problem_report = []

    def try_LFmerge(self, constituent):
        self.try_merge_to_left(constituent)
        self.try_adjoin_right(constituent)
        self.try_merge_to_comp(constituent)

    def try_adjoin_right(self, head):
        for constituent_from_MB in self.controlling_parsing_process.syntactic_working_memory:
            if 'ADV' in constituent_from_MB.head().features:
                target_node = self.specifier_sister(head)
                if self.tail_match(target_node, constituent_from_MB, 'right'):
                    new_const = self.LFMerge(constituent_from_MB, target_node, 'right')
                    new_const.adjunct = True
                    log(f'={target_node.top()}')
                    break

    def try_merge_to_left(self, head):
        if not head.EPP() and self.free_spec_position(head):
            for constituent_from_MB in self.controlling_parsing_process.syntactic_working_memory:
                target_node = self.specifier_sister(head)
                if self.specifier_match(head, constituent_from_MB) and self.tail_match(target_node, constituent_from_MB, 'left'):
                    self.LFMerge(constituent_from_MB, target_node, 'left')
                    log(f'={target_node.top()}...')
                    break

    def specifier_sister(self, head):
        if head.is_left():
            return head.mother
        else:
            return head

    def tail_match(self, target_node, constituent_from_MB, direction):
        target_node.merge_1(constituent_from_MB.copy(), direction)                      # Test merge
        if direction == 'right':                                                        # Presupposition
            target_node.geometrical_sister().adjunct = True
        result = target_node.geometrical_sister().head().external_tail_head_test()      # Test
        target_node.geometrical_sister().remove()                                       # Remove trial unit
        return result

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
        specs = [spec for spec in head.working_memory_edge() if spec.is_complex()]
        return (not specs) or (specs and specs[0].adjunct)

    def LF_legibility_test(self, ps):
        self.reset_flags()
        self.controlling_parsing_process.consume_resources("LF test", f'{ps}')
        log('LF-interface test...')
        if not self._test(ps).all_pass():
            self.controlling_parsing_process.consume_resources("Failed Transfer", f'{ps}')
        return self

    def _test(self, ps):
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

    def adjunct_interpretation_test(self, h):
        if 'φ' in h.features and \
                h.max() and h.max().adjunct and \
                h.max().is_right() and \
                h.max().mother and 'φ' in h.max().mother.head().features:
            log(f'.{h.mother.mother} in uninterpretable because it is inside DP...')
            self.adjunct_test_result = False

    def head_integrity_test(self, h):
        if not h.features or 'CAT:?' in h.features or '?' in h.features:
            log('Head without lexical category was detected...')
            self.test_problem_report.append('Head without lexical category')
            self.head_integrity_test_result = False

    def probe_goal_test(self, h):
        for f in sorted(for_lf_interface(h.features)):
            if f.startswith('!PROBE:'):
                if not h.probe(h.features, f[7:]):
                    log(f'{h.illustrate()} probing for {f[7:]} failed...')
                    self.test_problem_report.append(f'{h} probing for  {f[7:]} failed')
                    self.probe_goal_test_result = False
            if f.startswith('-PROBE:'):
                if h.probe(set(h.features), f[7:]):
                    log(f'{h} failed negative probe-test for [{f[7:]}]...')
                    self.test_problem_report.append(f'{h} negative probing for {f[7:]} failed')
                    self.probe_goal_test_result = False

    def internal_tail_test(self, h):
        if 'φ' in h.features and not h.internal_tail_head_test():
            log(f'.{h}({h.mother}) failed internal tail test...')
            self.test_problem_report.append(f'{h} failed internal tail test')
            self.tail_head_test_result = False

    def double_spec_filter(self, h):
        if '2SPEC' not in h.features and \
                len([spec for spec in h.working_memory_edge() if
                     not spec.adjunct and
                     spec.is_complex() and
                     'φ' in spec.head().features and
                     not spec.find_me_elsewhere]) > 1:
                self.head_integrity_test_result = False
                log(f'{h} has double specifiers...')
                self.test_problem_report.append(f'{h} has double specifiers')

    def semantic_complement_test(self, head):
        if head.proper_complement():
            if not LF.semantic_match(head, head.proper_complement()):
                self.semantic_test_result = False
                log(f'{head} fails semantic match with {head.proper_complement()}...')
                self.test_problem_report.append(f'{head} fails semantic match with {head.proper_complement()}')

    def criterial_feature_test(self, h):
        if 'φ' in h.features and 'REL' not in h.features and h.mother:
            if h.mother.contains_feature('REL') and not h.mother.contains_feature('T/fin'):
                log(f'Criterial legibility failed for {h}...')
                self.test_problem_report.append(f'{h} fails criterial legibility')
                self.criterial_feature_test_result = False

    def projection_principle(self, h, test_strength='strong'):
        if self.projection_principle_applies_to(h):
            # If XP is inside a projection from head H and H assigns it a thematic role, then return True
            if h.max().container_head() and self.container_assigns_theta_role_to(h, test_strength):
                return True
            else:
                if h.max().contains_feature('adjoinable') and h.max().contains_feature('SEM:nonreferential'):
                    return True
                if self.identify_thematic_role_by_agreement(h):
                    return True
                if self.identify_thematic_role_by_tailing(h):
                    return True
            self.projection_principle_test_result = False
            log(f'{h.max().illustrate()} has no θ role inside {h.max().container_head().max().illustrate()}. ')
            self.test_problem_report.append(f'{h.max()} has no θ-role')

    def identify_thematic_role_by_tailing(self, h):
        return False

    def identify_thematic_role_by_agreement(self, h):
        if h.max().container_head():
            if h.max().container_head().get_valued_features() & h.max().head().get_valued_features() == h.max().head().get_valued_features():
                if not (h.max().container_head().working_memory_edge() and next((const for const in h.max().container_head().working_memory_edge()), None).is_complex()):
                    return True

    def projection_principle_applies_to(self, h):
        if {'D', 'φ'} & h.features and \
            h.max() and \
            not h.max().find_me_elsewhere and \
            h.max().mother:
            return True

    def container_assigns_theta_role_to(self, h, test_strength):
        # (i) H receives a thematic role if it is selected
        if h.is_selected():
            return True
        container_head = h.max().container_head()
        # (ii) Thematic assignment to specifier position
        if h.max().get_theta_assigner() and container_head.licensed_phrasal_specifier() and h.max() == container_head.licensed_phrasal_specifier():
            # (ii-1) H does not receive a thematic role from an EPP head
            if container_head.EPP():
                return False
            # (ii-2) H does not receive a thematic role from a sandwich position [K[-arg]...H...]
            # This is the strange thematic nullifying observed in OC constructions
            if container_head.selector() and 'ARG' not in container_head.selector().features:
                return False
            # (ii-3) H does not receive a thematic role from heads K... that do not assign thematic roles
            if not container_head.assigns_theta_role():
                return False
            # Condition (ii-4) One head K cannot assign two roles unless otherwise stated [DP1 [K DP2]]
            if container_head.sister() != h.max() and {'D', 'φ'} & container_head.sister().head().features:
                if 'COPULA' not in container_head.features and test_strength == 'strong':
                    return False
            return True

    def selection_tests(self, h):
        comp = h.proper_complement()
        local_edge = next((const for const in h.working_memory_edge()), None)
        for f in sorted(for_lf_interface(h.features)):
            if f.startswith('-SPEC:'):
                for spec_ in h.working_memory_edge():
                    if spec_ and f[6:] in spec_.head().features:
                        if not spec_.adjunct:
                            log(f'{h} has unacceptable specifier {spec_}...')
                            self.test_problem_report.append(f'{h} has wrong specifier {spec_.illustrate()} ({f})')
                            self.selection_test_result = False

            # No specifier of any kind allowed (e.g., English P).
            # This excludes pro and adjuncts
            if f == '-SPEC:*':
                if local_edge:
                    if not local_edge.adjunct and 'pro' not in local_edge.head().features:
                        log(f'-EPP head {h} has a specifier {local_edge}...')
                        self.test_problem_report.append(f'-EPP head {h} has wrong specifier {local_edge}')
                        self.selection_test_result = False

            # No edge (second Merge-1) allowed (i.,.e V2 phenomenon, Finnish that)
            if f == '-EDGE:*' and local_edge:
                log(f'{h} has {local_edge} but has -EDGE:*')
                self.test_problem_report.append(f'edgeless {h} has specifier {local_edge}')
                self.selection_test_result = False

            if f == '!1EDGE' and len([const for const in h.working_memory_edge() if const.is_complex()]) > 1:
                log(f'{h} is only allowed to host one edge element...')
                self.test_problem_report.append(f'{h} can has only one edge element')
                self.selection_test_result = False

            # Obligatory complement
            if f.startswith('!COMP:') and not f == '!COMP:*':
                if not h.selected_sister():
                    log(f'.{h} misses complement {f[6:]}...')
                    self.test_problem_report.append(f'{h} misses complement {f[6:]}')
                    self.selection_test_result = False
                else:
                    if f[6:] not in h.selected_sister().head().features:
                        log(f'{h} misses complement {f[6:]}...')
                        self.test_problem_report.append(f'{h} misses complement {f[6:]}')
                        self.selection_test_result = False

            # Complement restriction
            if f.startswith('-COMP:'):
                if h.is_left() and comp and f[6:] in comp.head().features:
                    log(f'{h} has wrong complement {comp}...')
                    self.test_problem_report.append(f'{h} has wrong complement {comp}')
                    self.selection_test_result = False
                    self.wrong_complement_test_result = False

            if f == '-COMP:*':
                if h.is_left() and comp:
                    log(f'{h} does not accept complements...')
                    self.test_problem_report.append(f'{h} cannot have a complement')
                    self.selection_test_result = False

            # !COMP:* heads must have complements (=functional head)
            if f == '!COMP:*':
                if not h.selected_sister():
                    log(f'{h} lacks complement...')
                    self.test_problem_report.append(f'{h} lacks a complement')
                    self.selection_test_result = False

            # !SPEC:* heads require a specifier
            if f == '!SPEC:*':
                if not local_edge:
                    log(f'EPP-head {h} lacks specifier...')
                    self.test_problem_report.append(f'{h} lacks EPP specifier')
                    self.selection_test_result = False

            # !SPEC:F, head requires specifier with label F
            # This feature must be satisfied by local edge (local specifier)
            if f.startswith('!SPEC:') and not f == '!SPEC:*':
                if not local_edge:
                    log(f'EPP-head {h} lacks specifier {f[6:]} that it requires...')
                    self.test_problem_report.append(f'{h} lacks specifier {f[6:]}')
                    self.selection_test_result = False
                else:
                    if f[6:] in local_edge.head().features or f[7:] in local_edge.head().features:
                        pass
                    else:
                        log(f'An EPP-head {h} has wrong specifier {local_edge}...')
                        self.test_problem_report.append(f'{h} has wrong specifier {local_edge}')
                        self.selection_test_result = False

    def final_tail_check(self, goal):
        if goal.is_complex():
            if not goal.left_const.find_me_elsewhere and not self.final_tail_check(goal.left_const):
                return False
            if not goal.right_const.find_me_elsewhere and not self.final_tail_check(goal.right_const):
                return False
        if goal.is_primitive():
            if goal.get_tail_sets() and not goal.external_tail_head_test():
                log(f'{goal.illustrate()} failed final tail test...')
                self.test_problem_report.append(f'{goal.illustrate()} failed final tail test')
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