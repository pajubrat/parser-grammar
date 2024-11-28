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
                ('Semantic Complement test', PhraseStructure.semantic_selection),
                ('Adjunct Interpretation test', PhraseStructure.interpretable_adjunct),
                ('EPP test', PhraseStructure.EPP_violation),
                ('Core integrity', PhraseStructure.core_integrity),
                ('External head merge test', PhraseStructure.complex_head_integrity),
                ('Projection Principle', PhraseStructure.projection_principle_failure)]
        return [test for test in all_legibility_tests if self.speaker_model.settings.retrieve(test[0], True)]

    def pass_LF_legibility(self, X, **kwargs):
        logging = kwargs.get('logging', True)
        self.logging = logging
        self.failed_feature = ''
        if not X.copied:
            if X.zero_level():
                for (test_name, test_failure) in self.active_test_battery:
                    if test_failure(X):
                        if self.speaker_model.settings.retrieve('dev_logging', False):
                            self.speaker_model.settings.application.dev_logging(f'\n\tFailed {test_name}, {X.top().illustrate()})')
                        if logging:
                            log(f'\n\t{X} ({X.max().illustrate()}) FAILED {test_name} ')
                            if self.failed_feature:
                                log(f'𝗳𝗼𝗿 [{self.failed_feature}]')
                        self.error_report_for_external_callers = f'{X} failed {test_name}.'
                        return False
            else:
                if not self.pass_LF_legibility(X.L(), logging=logging):
                    return False
                if not self.pass_LF_legibility(X.R(), logging=logging):
                    return False
        return True

    def selection_test(self, X):
        for key in X.core.selection_keys():
            if key in self.selection_violation_test.keys():
                if X.core.get_selection_features(key):
                    if not self.selection_violation_test[key](X, X.core.get_selection_features(key)):
                        if self.speaker_model.settings.retrieve('dev_logging', False):
                            self.speaker_model.settings.application.dev_logging(f'\n\t{X} failed {key} {X.core.get_selection_features(key)}. ')
                        if self.logging:
                            log(f'\t{X} 𝗳𝗮𝗶𝗹𝗲𝗱 {key}: {X.core.get_selection_features(key)} ')
                        return True     # Failed test

    def final_tail_check(self, X):
        if X.complex():
            if not X.L().copied and not self.final_tail_check(X.L()):
                return False
            if not X.R().copied and not self.final_tail_check(X.R()):
                return False
        if X.zero_level() and X.max() != X.top() and X.get_tail_sets() and not X.tail_test(weak_test=X.core('referential')):
            log(f'\n\t\t𝗣𝗼𝘀𝘁-𝘀𝘆𝗻𝘁𝗮𝗰𝘁𝗶𝗰 𝘁𝗮𝗶𝗹 𝘁𝗲𝘀𝘁 𝗳𝗼𝗿 \'{X.illustrate()}\' 𝗳𝗮𝗶𝗹𝗲𝗱.')
            return False
        return True

    def LF_legibility_test_detached(self, ps):
        def detached(ps):
            ps.mother_ = None
            return ps
        self.active_test_battery = self.LF_legibility_tests
        return self.pass_LF_legibility(detached(ps.copy()), logging=False)
