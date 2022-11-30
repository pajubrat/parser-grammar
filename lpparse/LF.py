from support import log
from phrase_structure import PhraseStructure

def for_lf_interface(features):
    return {f for f in features if f.startswith('!') or f.startswith('-')}

class LF:
    def __init__(self, controlling_parsing_process):
        self.brain_model = controlling_parsing_process
        self.LF_legibility_tests = [('Selection test', self.selection_test),
                                    ('Projection Principle', PhraseStructure.projection_principle),
                                    ('Head Integrity test', PhraseStructure.unrecognized_label),
                                    ('Feature Conflict test', PhraseStructure.feature_conflict),
                                    ('Probe-Goal test', PhraseStructure.probe_goal_test),
                                    ('Semantic Complement test', PhraseStructure.semantic_complement),
                                    ('Double Specifier Filter', PhraseStructure.double_spec_filter),
                                    ('Criterial Feature test', PhraseStructure.legitimate_criterial_feature),
                                    ('Adjunct Interpretation test', PhraseStructure.interpretable_adjunct)]

        self.selection_violation_test = {'-EF:φ': PhraseStructure.selection__negative_SUBJECT_edge,
                                         '!EF:φ': PhraseStructure.selection__positive_SUBJECT_edge,
                                         '-EF:*': PhraseStructure.selection__unselective_negative_edge,
                                         '!EF:*': PhraseStructure.selection__unselective_edge,
                                         '!1EDG': PhraseStructure.selection__negative_one_edge,
                                         '!SEF':  PhraseStructure.selection__positive_shared_edge,
                                         '-SPEC': PhraseStructure.selection__negative_specifier,
                                         '!SPEC': PhraseStructure.selection__positive_selective_specifier,
                                         '-COMP': PhraseStructure.selection__negative_complement,
                                         '!COMP': PhraseStructure.selection__positive_obligatory_complement}

        self.active_test_battery = self.LF_legibility_tests
        self.error_report_for_external_callers = ''

    def LF_legibility_test(self, ps, test_battery=None):
        if test_battery:
            self.active_test_battery = test_battery
        else:
            self.active_test_battery = self.LF_legibility_tests
        return self.pass_LF_legibility(ps)

    def pass_LF_legibility(self, ps):
        if ps.is_primitive():
            for (test_name, test_failure) in self.active_test_battery:
                if test_failure(ps):
                    log(f'{ps} failed {test_name}. ')
                    self.error_report_for_external_callers = f'{ps} failed {test_name}'  # For plausibility metrics calculations and output
                    return False
        else:
            if not ps.left.find_me_elsewhere:
                if not self.pass_LF_legibility(ps.left):
                    return False
            if not ps.right.find_me_elsewhere:
                if not self.pass_LF_legibility(ps.right):
                    return False
        return True

    def selection_test(self, probe):
        for lexical_feature in sorted(for_lf_interface(probe.features)):
            if lexical_feature[:5] in self.selection_violation_test.keys() and not self.selection_violation_test[lexical_feature[:5]](probe, lexical_feature):
                log(f'{probe} failed feature {lexical_feature}. ')
                return True

    def final_tail_check(self, goal):
        if goal.is_complex():
            if not goal.left.find_me_elsewhere and not self.final_tail_check(goal.left):
                return False
            if not goal.right.find_me_elsewhere and not self.final_tail_check(goal.right):
                return False
        if goal.is_primitive() and goal.get_tail_sets() and not goal.tail_test():
            log(f'Post-syntactic tail test for \'{goal.illustrate()}\', {goal.max().illustrate()} failed. ')
            return False
        return True

    #
    # LF Merge operations (these operations will be replaced with whatever operations are used in enumeration)
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
                if old_complement.check({'adjoinable'}):
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
        if not head.finite() and not head.edge():
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
