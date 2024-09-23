from support import log, set_logging
from phrase_structure import PhraseStructure

def for_lf_interface(features):
    return {f for f in features if f.startswith('!') or f.startswith('-') or f.startswith('+') or f == '&P'}

def self_selectional_feature(f):
    return ':' not in f and (f.startswith('!') or f.startswith('+') or f.startswith('-'))

class LF:
    def __init__(self, speaker_model):
        self.logging = True
        self.speaker_model = speaker_model
        self.failed_feature = ''
        self.LF_legibility_tests = self.determine_legilibity_tests()
        self.selection_violation_test = {'-SPEC': PhraseStructure.minus_SPEC,
                                         '+SPEC': PhraseStructure.plus_SPEC,
                                         '-COMP': PhraseStructure.minus_COMP,
                                         '+COMP': PhraseStructure.plus_COMP,
                                         '-SELF': PhraseStructure.minus_SELF,
                                         '+SELF': PhraseStructure.plus_SELF,
                                         '=SELF': PhraseStructure.conjunctive_minus_SELF}

        self.active_test_battery = self.LF_legibility_tests
        self.error_report_for_external_callers = ''

    def determine_legilibity_tests(self):
        all_legibility_tests = [('Selection test', self.selection_test),
                ('Head Integrity test', PhraseStructure.unrecognized_label),
                ('Feature Conflict test', PhraseStructure.feature_conflict),
                ('Probe-Goal test', PhraseStructure.probe_goal_test),
                ('Semantic Complement test', PhraseStructure.semantic_complement),
                ('Double Specifier Filter', PhraseStructure.double_spec_filter),
                ('Criterial Feature test', PhraseStructure.legitimate_criterial_feature),
                ('Adjunct Interpretation test', PhraseStructure.interpretable_adjunct),
                ('Phi Level test', PhraseStructure.phi_level_violation),
                ('External head merge test', PhraseStructure.complex_head_integrity),
                ('Projection Principle', PhraseStructure.projection_principle_failure)]
        return [test for test in all_legibility_tests if self.speaker_model.settings.retrieve(test[0], True)]

    def pass_LF_legibility(self, X, logging=True):
        self.logging = logging
        self.failed_feature = ''
        if not X.copied:
            if X.zero_level():
                for (test_name, test_failure) in self.active_test_battery:
                    if test_failure(X):
                        if logging:
                            log(f'\n\t\t{X} ({X.max().illustrate()}) failed {test_name} ')
                            if self.failed_feature:
                                log(f'for [{self.failed_feature}]')
                        self.error_report_for_external_callers = f'{X} failed {test_name}.'
                        return False
            else:
                if not self.pass_LF_legibility(X.left(), logging):
                    return False
                if not self.pass_LF_legibility(X.right(), logging):
                    return False
        return True

    def selection_test(self, X):
        for key in [f.split(':')[0] for f in X.features if 'COMP' in f or 'SPEC' in f or 'SELF' in f]:
            if key in self.selection_violation_test.keys():
                if not self.selection_violation_test[key](X, X.get_selection_features(key)):
                    if self.logging:
                        log(f'\t\t{X} failed {key}: {X.get_selection_features(key)} ')
                    return True     # Failed test

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
