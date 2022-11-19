from support import log

# Transforms a set of lexical features to be used in checking LF-interface conditions
def for_lf_interface(features):
    return {f for f in features if f.startswith('!') or f.startswith('-')}

class LF:
    def __init__(self, controlling_parsing_process):
        self.brain_model = controlling_parsing_process
        self.LF_legibility_tests = [('Selection test', self.selection_test),
                                    ('Projection Principle', self.projection_principle),
                                    ('Head Integrity test', self.head_integrity_test),
                                    ('Feature Conflict test', self.feature_conflict_test),
                                    ('Probe-Goal test', self.probe_goal_test),
                                    ('Semantic Complement test', self.semantic_complement_test),
                                    ('Double Specifier Filter', self.double_spec_filter),
                                    ('Criterial Feature test', self.criterial_feature_test),
                                    ('Adjunct Interpretation test', self.adjunct_interpretation_test)]

        self.active_test_battery = self.LF_legibility_tests
        self.error_report_for_external_callers = ''
        self.error_message = ''

        self.complete_edge = None
        self.filtered_edge = None

        self.selection_violation_test = {'-EF:φ': self.selection__negative_SUBJECT_edge,
                                         '!EF:φ': self.selection__positive_SUBJECT_edge,
                                         '-EF:*': self.selection__unselective_negative_edge,
                                         '!EF:*': self.selection__unselective_edge,
                                         '!1EDG': self.selection__negative_one_edge,
                                         '!SEF': self.selection__positive_shared_edge,
                                         '-SPEC': self.selection__negative_specifier,
                                         '!SPEC': self.selection__positive_selective_specifier,
                                         '-COMP': self.selection__negative_complement,
                                         '!COMP': self.selection__positive_obligatory_complement}

        self.interpretation_test = {'adjunct': self.adjunct_legibility,
                                    'head': self.head_legibility,
                                    'phrasal': self.phrasal_legibility}


    def interpretable(self, target, query_type):
        if self.interpretation_test[query_type](target):
            return True
        log(f'{target.illustrate()} requires {query_type} reconstruction. ')

    def adjunct_legibility(self, target):
        if target.is_left():
            return self.left_adjunct_legibility(target)
        if target.is_right():
            return self.adjunct_tail_legibility(target)

    def left_adjunct_legibility(self, target):
        return self.adjunct_tail_legibility(target) and not target.nonthematic()

    def adjunct_tail_legibility(self, target):
        return target.head().tail_test()

    def validate_reconstructed_adjunct(self, target, starting_point_node):
        return self.adjunct_tail_legibility(target) and (target.adverbial_adjunct() or self.non_adverbial_adjunct_extra_conditions(target, starting_point_node))

    # Ad hoc conditions that must be derived from general rules
    def non_adverbial_adjunct_extra_conditions(self, target, starting_point_head):
        if not target.container():
            return True
        if target.check_feature('GEN') and not target.container().referential():
            return True  # Possessives inside referential phrases are not floated
        if target.container() == starting_point_head:
            return False  # Do not reconstruct into the starting position
        if target.nonthematic():
            return False
        if target.referential() and self.projection_principle(target.head()):
            return False
        return True

    def head_legibility(self, target):
        return target.is_complex() or not target.complex_head()

    def validate_reconstructed_head(self, target):
        return target.properly_selected() and not self.extra_condition_violation(target)

    def extra_condition_violation(self, target):
        return target.selector().finite_C() and target.EF() and not target.edge_specifiers()

    def phrasal_legibility(self, target):
        return not target.EF()

    def selection_violation(self, node):
        return node.is_complex() and (node.left_const.nonlicensed_complement() or node.left_const.missing_mandatory_complement())

    def LF_legibility_test(self, ps, test_battery=None):
        if test_battery:
            self.active_test_battery = test_battery
        else:
            self.active_test_battery = self.LF_legibility_tests
        return self.pass_LF_legibility(ps)

    def pass_LF_legibility(self, ps):
        if ps.is_primitive():
            self.complete_edge, self.filtered_edge = self.create_edges(ps)
            for (test_name, test) in self.active_test_battery:
                if test(ps):
                    log(f'{ps} failed {test_name}. ')
                    self.error_report_for_external_callers = f'{ps} failed {test_name}'
                    return False
        else:
            if not ps.left_const.find_me_elsewhere:
                if not self.pass_LF_legibility(ps.left_const):
                    return False
            if not ps.right_const.find_me_elsewhere:
                if not self.pass_LF_legibility(ps.right_const):
                    return False
        return True

    def create_edges(self, ps):
        complete_edge = [const for const in ps.edge_specifiers() + [ps.extract_pro()] if const]
        filtered_edge = self.brain_model.scan_all(complete_edge, lambda x: not (x.check_feature('pro') and not x.head().sustains_reference()))
        return complete_edge, filtered_edge

    # Selection tests ----------------------------------------------------------
    def selection_test(self, probe):
        for lexical_feature in sorted(for_lf_interface(probe.features)):
            if lexical_feature[:5] in self.selection_violation_test.keys() and not self.selection_violation_test[lexical_feature[:5]](probe, lexical_feature):
                log(f'{probe} failed feature {lexical_feature}. ')
                return True

    # Feature !EF:φ
    def selection__positive_SUBJECT_edge(self, head, lexical_feature):
        return self.brain_model.scan_next(self.filtered_edge, lambda x: x.referential() and (not x.has_tail_features() or x.is_extended_subject()))

    # Feature -EF:*
    def selection__unselective_negative_edge(self, probe, lexical_feature):
        return not self.filtered_edge

    # Feature -EF:φ
    def selection__negative_SUBJECT_edge(self, probe, lexical_feature):
        return not self.brain_model.scan_next(self.filtered_edge, lambda x: x.referential() and x.is_extended_subject())

    # Feature !SEF
    @staticmethod
    def selection__positive_shared_edge(probe, lexical_feature):
        def complement_criterion(probe):  # Complement exists and is/has referential argument
            return probe.proper_complement() and (probe.proper_complement().head().referential() or
                                                  (probe.proper_complement().head().licensed_phrasal_specifier() and
                                                   probe.proper_complement().head().licensed_phrasal_specifier().head().referential()))
        return not (not probe.licensed_phrasal_specifier() and complement_criterion(probe))

    # Feature !1EDGE
    @staticmethod
    def selection__negative_one_edge(probe, lexical_feature):
        return len(probe.edge_specifiers()) < 2

    # Feature [!EF:*] ~ not used for calculation of any data
    def selection__unselective_edge(self, probe, lexical_feature):
        return self.filtered_edge

    # Feature !SPEC
    def selection__positive_selective_specifier(self, probe, lexical_feature):
        return self.brain_model.scan_next(self.complete_edge, lambda x: x.check_feature(lexical_feature[6:]))

    # Feature -SPEC
    def selection__negative_specifier(self, probe, lexical_feature):
        return not self.brain_model.scan_next(probe.edge_specifiers(), lambda x: x.check_feature(lexical_feature[6:]) and not x.adjunct)

    # Feature !COMP
    def selection__positive_obligatory_complement(self, probe, lexical_feature):
        return probe.selected_sister() and (lexical_feature[6] == '*' or probe.selected_sister().check_feature(lexical_feature[6:]))

    # Feature -COMP
    def selection__negative_complement(self, probe, lexical_feature):
        return not (probe.is_left() and probe.proper_complement() and
                    (probe.proper_complement().check_feature(lexical_feature[6:]) or lexical_feature[6:] == '*'))

    # end of selection tests -------------------------------------------------------------

    def adjunct_interpretation_test(self, probe):
        return probe.referential() and probe.max() and probe.max().adjunct and probe.max().is_right() and probe.max().mother and probe.max().mother.referential()

    def feature_conflict_test(self, probe):
        def remove_exclamation(g):
            if g[0] == '!':
                return g[1:]
            else:
                return g

        for feature1 in probe.features:
            if feature1[0] == '-':
                for feature2 in probe.features:
                    if feature1[1:] == remove_exclamation(feature2):
                        return True

    def head_integrity_test(self, probe):
        return probe.features and probe.unrecognized_label()

    def probe_goal_test(self, probe):
        for f in sorted(for_lf_interface(probe.features)):
            if f.startswith('!PROBE:'):
                if not probe.probe(probe.features, f[7:]):
                    return True
            if f.startswith('-PROBE:'):
                if probe.probe(set(probe.features), f[7:]):
                    return True

    def double_spec_filter(self, probe):
        return not probe.check_feature('2SPEC') and len({spec for spec in probe.edge_specifiers() if not spec.adjunct}) > 1

    def semantic_complement_test(self, probe):
        return probe.proper_complement() and not LF.semantic_match(probe, probe.proper_complement())

    def criterial_feature_test(self, probe):
        return probe.referential() and not probe.relative() and probe.mother and probe.mother.contains_feature('REL') and not probe.mother.contains_feature('T/fin')

    def projection_principle(self, probe):
        return self.projection_principle_applies(probe) and not self.container_assigns_theta_role(probe)

    def projection_principle_applies(self, probe):
        return probe.referential() and probe.max() and not probe.max().find_me_elsewhere and probe.max().mother and not probe.max().contains_features({'adjoinable', 'SEM:nonreferential'})

    def container_assigns_theta_role(self, probe):
        return probe.max().container() and (probe.selected() or (probe.is_licensed_specifier() and probe.max().container().specifier_theta_role_assigner()))

    def final_tail_check(self, goal):
        if goal.is_complex():
            if not goal.left_const.find_me_elsewhere and not self.final_tail_check(goal.left_const):
                return False
            if not goal.right_const.find_me_elsewhere and not self.final_tail_check(goal.right_const):
                return False
        if goal.is_primitive() and goal.get_tail_sets() and not goal.tail_test():
            log(f'Post-syntactic tail test for \'{goal.illustrate()}\', {goal.max().illustrate()} failed. ')
            return False
        return True

    #
    # LF Merge operations
    #
    def try_LFmerge(self, head, phrase):
        for try_merge in [self.try_merge_to_left, self.try_adjoin_right, self.try_merge_to_comp]:
            if try_merge(head, phrase):
                return True

    def try_merge_to_comp(self, head, phrase):
        if head.complement_match(phrase):
            if not head.proper_complement():
                self.LF_Merge(phrase, head, 'right')
                self.brain_model.consume_resources("Move Phrase", f'{phrase}')
                return True
            if head.complement_not_licensed():
                old_complement = head.proper_complement()
                head.proper_complement().merge_1(phrase.copy_for_reconstruction(self.brain_model.babtize()), 'left')
                if old_complement.check_feature('adjoinable'):
                    old_complement.adjunct = True
                self.brain_model.consume_resources("Move Phrase", f'{phrase}')
                return True

    def try_adjoin_right(self, head, phrase):
        if phrase.head().adverbial():
            target_node = head.specifier_sister()
            if self.tail_match(target_node, phrase, 'right'):
                new_const = self.LF_Merge(phrase, target_node, 'right')
                new_const.adjunct = True
                return True

    def try_merge_to_left(self, head, phrase):
        if not head.finite() and not head.edge_specifiers():
            target_node = head.specifier_sister()
            if head.specifier_match(phrase) and self.tail_match(target_node, phrase, 'left'):
                self.LF_Merge(phrase, target_node, 'left')
                return True

    def LF_Merge(self, phrase, target_head, direction='left'):
        log(f'Merging {phrase} {direction} of \'{target_head}\'...')
        new_const = phrase.copy_for_reconstruction(self.brain_model.babtize())
        target_head.merge_1(new_const, direction)
        self.brain_model.consume_resources("Ā-Chain", f'{phrase}')
        return new_const

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
