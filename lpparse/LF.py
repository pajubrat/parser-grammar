from support import log, set_logging
from phrase_structure import PhraseStructure

def for_lf_interface(features):
    return {f for f in features if f.startswith('!') or f.startswith('-')}

class LF:
    def __init__(self, controlling_parsing_process):
        self.brain_model = controlling_parsing_process
        self.LF_legibility_tests = [('Edge feature test', PhraseStructure.edge_feature_tests),
                                    ('Selection test', self.selection_test),
                                    ('Projection Principle', PhraseStructure.projection_principle_failure),
                                    ('Head Integrity test', PhraseStructure.unrecognized_label),
                                    ('Feature Conflict test', PhraseStructure.feature_conflict),
                                    ('Probe-Goal test', PhraseStructure.probe_goal_test),
                                    ('Semantic Complement test', PhraseStructure.semantic_complement),
                                    ('Double Specifier Filter', PhraseStructure.double_spec_filter),
                                    ('Criterial Feature test', PhraseStructure.legitimate_criterial_feature),
                                    ('Adjunct Interpretation test', PhraseStructure.interpretable_adjunct)]

        self.selection_violation_test = {'!1EDG': PhraseStructure.selection__negative_one_edge,
                                         '-SPEC': PhraseStructure.selection__negative_specifier,
                                         '-COMP': PhraseStructure.selection__negative_complement,
                                         '!COMP': PhraseStructure.selection__positive_obligatory_complement,
                                         '!SELF': PhraseStructure.selection__positive_self_selection,
                                         '-SELF': PhraseStructure.selection__negative_self_selection,
                                         '-ΦPF':  PhraseStructure.selection__phonological_AGREE,
                                         '!p': PhraseStructure.selection__p_test}

        self.active_test_battery = self.LF_legibility_tests
        self.error_report_for_external_callers = ''

    def LF_legibility_test(self, ps, test_battery=None):
        if test_battery:
            self.active_test_battery = test_battery
        else:
            self.active_test_battery = self.LF_legibility_tests
        return self.pass_LF_legibility(ps)

    def pass_LF_legibility(self, ps):
        if not ps.find_me_elsewhere:
            if ps.primitive():
                for (test_name, test_failure) in self.active_test_battery:
                    if test_failure(ps):
                        log(f'\n\t\t{ps} failed {test_name} ')
                        self.error_report_for_external_callers = f'{ps} failed {test_name}'  # For plausibility metrics calculations and output
                        return False
            else:
                if not self.pass_LF_legibility(ps.left):
                    return False
                if not self.pass_LF_legibility(ps.right):
                    return False
        return True

    def selection_test(self, probe):
        for selected_feature in sorted(for_lf_interface(probe.features)):
            if selected_feature[:5] in self.selection_violation_test.keys() and \
                    not self.selection_violation_test[selected_feature[:5]](probe, selected_feature[6:]):
                log(f'\n\t\t{probe} failed feature {selected_feature} ')
                return True

    def final_tail_check(self, goal):
        if goal.complex():
            if not goal.left.find_me_elsewhere and not self.final_tail_check(goal.left):
                return False
            if not goal.right.find_me_elsewhere and not self.final_tail_check(goal.right):
                return False
        if goal.primitive() and goal.get_tail_sets() and not goal.tail_test():
            log(f'\n\t\tPost-syntactic tail test for \'{goal.illustrate()}\' failed. ')
            return False
        return True

    def LF_legibility_test_detached(self, ps):
        def detached(ps):
            ps.mother = None
            return ps
        result = self.LF_legibility_test(detached(ps.copy()))
        return result

