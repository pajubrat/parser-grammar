from support import log, set_logging
from phrase_structure import PhraseStructure

def for_lf_interface(features):
    return {f for f in features if f.startswith('!') or f.startswith('-') or f.startswith('+') or f == '&P'}

def self_selectional_feature(f):
    return ':' not in f and (f.startswith('!') or f.startswith('+') or f.startswith('-'))

class LF:
    def __init__(self, controlling_parsing_process):
        self.brain_model = controlling_parsing_process
        self.failed_feature = ''
        self.LF_legibility_tests = [('Edge feature test', PhraseStructure.edge_feature_tests),
                                    ('Selection test', self.selection_test),
                                    ('Projection Principle', PhraseStructure.projection_principle_failure),
                                    ('Head Integrity test', PhraseStructure.unrecognized_label),
                                    ('Feature Conflict test', PhraseStructure.feature_conflict),
                                    ('Probe-Goal test', PhraseStructure.probe_goal_test),
                                    ('Semantic Complement test', PhraseStructure.semantic_complement),
                                    ('Double Specifier Filter', PhraseStructure.double_spec_filter),
                                    ('Criterial Feature test', PhraseStructure.legitimate_criterial_feature),
                                    ('Adjunct Interpretation test', PhraseStructure.interpretable_adjunct),
                                    ('External head merge test', PhraseStructure.Complex_Head_Integrity)]

        self.selection_violation_test = {'1EDGE': PhraseStructure.selection__negative_one_edge,
                                         '-SPEC': PhraseStructure.selection__negative_specifier,
                                         '-COMP': PhraseStructure.selection__negative_complement,
                                         '!COMP': PhraseStructure.selection__positive_obligatory_complement,
                                         '+COMP': PhraseStructure.selection__positive_disjunctive_complement,
                                         '!': PhraseStructure.selection__positive_self_selection,
                                         '-': PhraseStructure.selection__negative_self_selection,
                                         '+': PhraseStructure.selection__partial_self_selection}

        self.active_test_battery = self.LF_legibility_tests
        self.error_report_for_external_callers = ''

    def pass_LF_legibility(self, ps, logging=True):
        self.failed_feature = ''
        if not ps.copied:
            if ps.zero_level():
                for (test_name, test_failure) in self.active_test_battery:
                    if test_failure(ps):
                        if logging:
                            log(f'\n\t\t{ps} failed {test_name} ')
                            if self.failed_feature:
                                log(f'for [{self.failed_feature}]')
                        self.error_report_for_external_callers = f'{ps} failed {test_name}.'  # For plausibility metrics calculations and output
                        return False
            else:
                if not self.pass_LF_legibility(ps.left(), logging):
                    return False
                if not self.pass_LF_legibility(ps.right(), logging):
                    return False
        return True

    def selection_test(self, probe):
        for f in sorted(probe.features):
            key, feature_set = self.format_selection_feature(f)
            if key and not self.selection_violation_test[key](probe, feature_set):
                self.failed_feature = str(feature_set)
                return True  # test failed

    # This will be removed once we have a universal standard
    def format_selection_feature(self, f):
        # Replace * with empty set (no features required, e.g. !COMP:*)
        if len(f) == 7 and f[6] == '*':
            return f[:5], set()

        # Selection features which do not have standard type:value format
        if ':' not in f and f[0] in self.selection_violation_test.keys():
            return f[0], f[1:]

        # Selection features with the standard type:value format
        if f[:5] in self.selection_violation_test.keys():
            return f[:5], set(f[6:].split(','))
        else:
            return None, None

    def final_tail_check(self, goal):
        if goal.complex():
            if not goal.left().copied and not self.final_tail_check(goal.left()):
                return False
            if not goal.right().copied and not self.final_tail_check(goal.right()):
                return False
        if goal.zero_level() and goal.get_tail_sets() and not goal.tail_test():
            log(f'\n\t\tPost-syntactic tail test for \'{goal.illustrate()}\' failed. @@')
            return False
        return True

    def LF_legibility_test_detached(self, ps):
        def detached(ps):
            ps.mother_ = None
            return ps
        self.active_test_battery = self.LF_legibility_tests
        return self.pass_LF_legibility(detached(ps.copy()), False)

