
from support import log

# Transforms a set of lexical features to be used in checking LF-interface conditions
def for_lf_interface(features):
    return {f for f in features if f.startswith('!') or f.startswith('-')}

class LF:
    def __init__(self, controlling_parsing_process):
        self.controlling_parsing_process = controlling_parsing_process
        self.LF_legibility_tests = [self.selection_test,
                                    self.projection_principle,
                                    self.head_integrity_test,
                                    self.feature_conflict_test,
                                    self.probe_goal_test,
                                    self.semantic_complement_test,
                                    self.double_spec_filter,
                                    self.criterial_feature_test,
                                    self.adjunct_interpretation_test]

        self.active_test_battery = self.LF_legibility_tests

        self.complete_edge = None
        self.edge_for_EF = None

        self.selection_violation_tests = [self.selection__negative_specifier_violation,
                                          self.selection__positive_SUBJECT_edge_violation,
                                          self.selection__negative_SUBJECT_edge_violation,
                                          self.selection__positive_mandatory_unselective_edge_violation,
                                          self.selection__positive_selective_edge_violation,
                                          self.selection__unselective_negative_edge_violation,
                                          self.selection__negative_one_edge_violation,
                                          self.selection__positive_selective_specifier_violation,
                                          self.selection__positive_shared_edge_violation,
                                          self.selection__positive_obligatory_complement_violation,
                                          self.selection__negative_complement_violation,
                                          self.selection__unselective_negative_complement_violation,
                                          self.selection__positive_unselective_complement_violation]

    def LF_legibility_test(self, ps, special_test_battery=None):
        if special_test_battery:
            self.active_test_battery = special_test_battery
        else:
            self.active_test_battery = self.LF_legibility_tests
        return self.pass_LF_legibility(ps)

    def pass_LF_legibility(self, ps):
        if ps.is_primitive():
            self.complete_edge = [const for const in ps.edge_specifiers()]
            self.edge_for_EF = [const for const in ps.edge_specifiers()]
            pro = ps.extract_pro()
            if pro:
                self.complete_edge += [pro]
                if pro.sustains_reference():
                    self.edge_for_EF += [pro]
            for LF_test in self.active_test_battery:
                if not LF_test(ps):
                    return False
        else:
            if not ps.left_const.find_me_elsewhere:
                if not self.pass_LF_legibility(ps.left_const):
                    return False
            if not ps.right_const.find_me_elsewhere:
                if not self.pass_LF_legibility(ps.right_const):
                    return False
        return True

    def adjunct_interpretation_test(self, h):
        if 'φ' in h.features and \
                h.max() and h.max().adjunct and \
                h.max().is_right() and \
                h.max().mother and 'φ' in h.max().mother.head().features:
            log(f'.{h.mother.mother} in uninterpretable because it is inside DP. ')
            return False
        return True

    def feature_conflict_test(self, h):
        def remove_exclamation(g):
            if g[0] == '!':
                return g[1:]
            else:
                return g

        for feature1 in h.features:
            if feature1[0] == '-':
                for feature2 in h.features:
                    if feature1[1:] == remove_exclamation(feature2):
                        log(f'Head {h.illustrate()} triggers feature conflict between {feature1} and {feature2}.')
                        return False
        return True

    def head_integrity_test(self, h):
        if h.features:
            if {'CAT:?', '?'} & h.features:
                log('Head without lexical category. ')
                return False
        return True

    def probe_goal_test(self, h):
        for f in sorted(for_lf_interface(h.features)):
            if f.startswith('!PROBE:'):
                if not h.probe(h.features, f[7:]):
                    log(f'{h.illustrate()} failed probe-goal test {f}. ')
                    return False
            if f.startswith('-PROBE:'):
                if h.probe(set(h.features), f[7:]):
                    log(f'{h} failed negative probe-test for [{f[7:]}]. ')
                    return False
        return True

    def double_spec_filter(self, h):
        if '2SPEC' not in h.features and \
                len({spec for spec in h.edge_specifiers() if not spec.adjunct}) > 1:
                log(f'{h} has double specifiers. ')
                return False
        return True

    def semantic_complement_test(self, head):
        if head.proper_complement():
            if not LF.semantic_match(head, head.proper_complement()):
                log(f'{head} fails semantic match with {head.proper_complement()}. ')
                return False
        return True

    def criterial_feature_test(self, h):
        if 'φ' in h.features and 'REL' not in h.features and h.mother:
            if h.mother.contains_feature('REL') and not h.mother.contains_feature('T/fin'):
                log(f'Criterial legibility failed for {h}. ')
                return False
        return True

    def projection_principle(self, h, test_strength='strong'):
        if self.projection_principle_applies_to(h):
            # If XP is inside a projection from head H and H assigns it a thematic role, then return True
            if h.max().container() and self.container_assigns_theta_role_to(h, test_strength):
                return True
            else:
                if h.max().contains_feature('adjoinable') and h.max().contains_feature('SEM:nonreferential'):
                    return True
                if self.identify_thematic_role_by_agreement(h):
                    return True
            log(f'{h.max().illustrate()} has no θ role in {h.max().container().max()}. ')
            return False
        return True

    def identify_thematic_role_by_agreement(self, h):
        if h.max().container():
            if h.max().container().get_valued_features() & h.max().head().get_valued_features() == h.max().head().get_valued_features():
                if not (h.max().container().edge_specifiers() and next((const for const in h.max().container().edge_specifiers()), None).is_complex()):
                    return True

    def projection_principle_applies_to(self, h):
        if h.is_referential() and h.max() and not h.max().find_me_elsewhere and h.max().mother:
            return True

    def container_assigns_theta_role_to(self, h, test_strength):
        def get_theta_assigner(node):
            if node.sister() and node.sister().is_primitive():
                return node.sister()
            if node.container() and node.container().edge_specifiers() and node == \
                    node.container().edge_specifiers()[0]:
                return node.container()

        # (i) H receives a thematic role if it is selected
        if h.max().sister() and h.max().sister().is_primitive():
            return True
        container_head = h.max().container()
        # (ii) Thematic assignment to specifier position
        if get_theta_assigner(h.max()) and container_head.licensed_phrasal_specifier() and h.max() == container_head.licensed_phrasal_specifier():
            # (ii-1) H does not receive a thematic role from an EPP head
            if container_head.EF():
                return False
            if container_head.selector() and 'ARG' not in container_head.selector().features:
                return False
            # (ii-3) H does not receive a thematic role from heads K... that do not assign thematic roles
            if not {'SPEC:φ', 'COMP:φ', '!SPEC:φ', '!COMP:φ'} & container_head.features or {'-SPEC:φ'} & container_head.features:
                return False
            # Condition (ii-4) One head K cannot assign two roles unless otherwise stated [DP1 [K DP2]]
            if container_head.sister() != h.max() and container_head.sister().head().is_referential():
                if 'COPULA' not in container_head.features and test_strength == 'strong':
                    return False
            return True

    def final_tail_check(self, goal):
        if goal.is_complex():
            if not goal.left_const.find_me_elsewhere and not self.final_tail_check(goal.left_const):
                return False
            if not goal.right_const.find_me_elsewhere and not self.final_tail_check(goal.right_const):
                return False
        if goal.is_primitive():
            if goal.get_tail_sets():
                if not goal.tail_test():
                    log(f'Tail test for {goal.illustrate()}[{goal.get_tail_sets()}] Failed. ')
                    return False
        return True

    # Selection tests ----------------------------------------------------------

    def selection_test(self, head):
        return next((False for lexical_feature in sorted(for_lf_interface(head.features))
                     for test in self.selection_violation_tests if test(head, lexical_feature)), True)

    def selection__negative_specifier_violation(self, head, lexical_feature):
        if lexical_feature.startswith('-SPEC:'):
            for spec_ in head.edge_specifiers():
                if lexical_feature[6:] in spec_.head().features:
                    if not spec_.adjunct:
                        log(f'{head} has unacceptable specifier {spec_}. ')
                        return True  # Violation was detected

    def selection__positive_selective_specifier_violation(self, head, lexical_feature):
        if lexical_feature.startswith('!SPEC:'):
            if self.complete_edge:
                for edge_object in self.complete_edge:
                    if lexical_feature[6:] in edge_object.head().features:
                        return True
            log(f'Head {head} has wrong specifier. ')

    def selection__positive_mandatory_unselective_edge_violation(self, head, lexical_feature):
        if lexical_feature == '!EF:*' and not self.edge_for_EF:
            log(f'EPP-head {head} lacks specifier. ')
            return True  # Violation was detected

    def selection__unselective_negative_edge_violation(self, head, lexical_feature):
        if '-EF:*' == lexical_feature and self.edge_for_EF:
            log(f'{head} has illegitimate edge: ')
            for edge_object in self.complete_edge:
                log(f'{edge_object} ')
            log('. ')
            return True # Violation was detected

    def selection__negative_one_edge_violation(self, head, lexical_feature):
        if lexical_feature == '!1EDGE' and len(head.edge_specifiers()) > 1:
            log(f'{head} is only allowed to host one edge element. ')
            return True  # Violation was detected

    def selection__positive_SUBJECT_edge_violation(self, head, lexical_feature):
        def all_tail_features(head):
            return {feature for feature_set in head.get_tail_sets() for feature in feature_set}

        if lexical_feature == '!EF:φ':
            if self.complete_edge:
                for edge_object in self.edge_for_EF:
                    if 'φ' in edge_object.head().features:
                        if not edge_object.head().get_tail_sets():
                            return False
                        elif {'EF:φ', '!EF:φ'} & all_tail_features(edge_object.head()) or 'pro' in edge_object.head().features:
                            return False
            log(f'Subject edge violation at {head}. ')
            return True  # Violation was detected

    def selection__negative_SUBJECT_edge_violation(self, head, lexical_feature):
        def all_tail_features(head):
            return {feature for feature_set in head.get_tail_sets() for feature in feature_set}
        if lexical_feature == '-EF:φ':
            if self.complete_edge:
                for edge_object in self.edge_for_EF:
                    if 'φ' in edge_object.head().features:
                        if {'EF:φ', '!EF:φ'} & all_tail_features(edge_object.head()) or 'pro' in edge_object.head().features:
                            log(f'Negative subject edge violation at {head}. ')
                            return True

    def selection__positive_selective_edge_violation(self, head, lexical_feature):
        if lexical_feature.startswith('!EF:') and lexical_feature != '!EF:*' and lexical_feature != '!EF:φ':
            if self.complete_edge:
                for edge_object in self.edge_for_EF:
                    if lexical_feature[4:] in edge_object.head().features:
                        return False
            log(f'Head {head} has wrong edge {self.complete_edge}. ')
            return True  # Violation was detected

    def selection__positive_shared_edge_violation(self, head, lexical_feature):
        if lexical_feature == '!SEF':
            if not head.edge_specifiers():
                if head.proper_complement():
                    if head.proper_complement().head().is_referential():
                        log(f'Shared edge violation at \'{head}\'. ')
                        return True  # Violation was detected (e.g., [P_sef DP])
                    if head.proper_complement().head().licensed_phrasal_specifier() and \
                            head.proper_complement().head().licensed_phrasal_specifier().head().is_referential():
                        log(f'Shared edge violation at \'{head}\'. ')
                        return True  # Violation was detected (e.g., A/inf [DP VP])


    def selection__positive_obligatory_complement_violation(self, head, lexical_feature):
        if lexical_feature.startswith('!COMP:') and not lexical_feature == '!COMP:*':
            if not head.selected_sister() or (head.selected_sister() and lexical_feature[6:] not in head.selected_sister().head().features):
                log(f'Head \"{head}\" lacks complement.')
                return True  # Violation was detected

    def selection__negative_complement_violation(self, head, lexical_feature):
        if lexical_feature.startswith('-COMP:'):
            if head.is_left() and head.proper_complement() and lexical_feature[6:] in head.proper_complement().head().features:
                return True  # Violation was detected

    def selection__unselective_negative_complement_violation(self, head, lexical_feature):
        if lexical_feature == '-COMP:*' and head.is_left() and head.proper_complement():
            log(f'{head} does not accept complements. ')
            return True  # Violation was detected

    def selection__positive_unselective_complement_violation(self, head, lexical_feature):
        if lexical_feature == '!COMP:*' and not head.selected_sister():
            log(f'Head \'{head}\' lacks complement. ')
            return True  # Violation was detected

    # end of selection tests -------------------------------------------------------------

    #
    # LF Merge operations
    #

    def try_merge_to_comp(self, head):

        # Case 1. missing complement
        if head.is_primitive() and not head.proper_complement() and head.licensed_complements():
            for const in self.controlling_parsing_process.syntactic_working_memory:
                if head.complement_match(const):
                    self.LFMerge(const, head, 'right')
                    log(f'={head.top()}...')
                    self.controlling_parsing_process.consume_resources("Move Phrase", f'{const}')
                    break

        # Case 2. Wrong complement
        if head.is_left() and head.proper_complement() and not (head.licensed_complements() & head.proper_complement().head().features):
            for const in self.controlling_parsing_process.syntactic_working_memory:
                if head.complement_match(const):
                    old_complement = head.proper_complement()
                    head.proper_complement().merge_1(const.copy_from_memory_buffer(self.controlling_parsing_process.babtize()), 'left')
                    log(f'Merging {const} to Comp{head.get_cats_string()}P due to complement mismatch. ')
                    if 'adjoinable' in old_complement.head().features:
                        log(f'Externalizing {old_complement}. ')
                        old_complement.adjunct = True
                    self.controlling_parsing_process.syntactic_working_memory.remove(const)
                    self.controlling_parsing_process.consume_resources("Move Phrase", f'{const}')
                    break

    def LFMerge(self, constituent_from_MB, target, direction='left'):
        log(f'Merging {constituent_from_MB} {direction} of \'{target}\'...')
        new_const = constituent_from_MB.copy_from_memory_buffer(self.controlling_parsing_process.babtize())
        target.merge_1(new_const, direction)
        self.controlling_parsing_process.consume_resources("Ā-Chain", f'{constituent_from_MB}')
        self.controlling_parsing_process.syntactic_working_memory.remove(constituent_from_MB)
        return new_const

    def try_LFmerge(self, node):
        self.try_merge_to_left(node)
        self.try_adjoin_right(node)
        self.try_merge_to_comp(node)

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
        if not {'FIN', 'T/fin'} & head.features and not head.edge_specifiers():
            for constituent_from_MB in self.controlling_parsing_process.syntactic_working_memory:
                target_node = self.specifier_sister(head)
                if self.specifier_match(head, constituent_from_MB) and self.tail_match(target_node, constituent_from_MB, 'left'):
                    self.LFMerge(constituent_from_MB, target_node, 'left')
                    log(f'={target_node.top()}...')
                    break

    def specifier_match(self, h, const):
        for feature_in_head in h.convert_features_for_parsing(h.licensed_specifiers()):
            for feature_in_spec in const.head().features:
                if feature_in_head == feature_in_spec:
                    return True

    def specifier_sister(self, head):
        if head.is_left():
            return head.mother
        else:
            return head

    def tail_match(self, target_node, constituent_from_MB, direction):
        target_node.merge_1(constituent_from_MB.copy(), direction)        # Test merge
        if direction == 'right':                                          # Presupposition
            target_node.geometrical_sister().adjunct = True
        result = target_node.geometrical_sister().head().tail_test()      # Test
        target_node.geometrical_sister().remove()                         # Remove trial unit
        return result

    @staticmethod
    def semantic_match(a, b):
        a_head = a.head()
        b_head = b.head()
        pos_sem_a = {f[5:] for f in a_head.features if f.startswith('+SEM:')}
        neg_sem_a = {f[5:] for f in a_head.features if f.startswith('-SEM:')}
        pos_sem_b = {f[5:] for f in b_head.features if f.startswith('+SEM:')}
        neg_sem_b = {f[5:] for f in b_head.features if f.startswith('-SEM:')}
        return not ((pos_sem_a & neg_sem_b) or (pos_sem_b & neg_sem_a))