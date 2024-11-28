from support import set_logging, log
from operator import itemgetter
from phrase_structure import PhraseStructure
import random


class PlausibilityMetrics:
    def __init__(self, speaker_model):
        self.speaker_model = speaker_model
        self.baseline_weights = []
        self.plausibility_conditions = \
            {'spec_selection':                  {'condition': self.spec_selection,
                                                 'weight': self.speaker_model.settings.retrieve('spec_selection', 100),
                                                 'log': 'SPEC selection'},
             'comp_selection':                  {'condition': self.comp_selection,
                                                 'weight': self.speaker_model.settings.retrieve('comp_selection', 100),
                                                 'log': 'COMP selection'},
             'negative_semantics_match':        {'condition': self.negative_semantic_match,
                                                 'weight': self.speaker_model.settings.retrieve('negative_semantics_match', 100),
                                                 'log': 'Semantic mismatch'},
             'lf_legibility_condition':         {'condition': self.lf_legibility_condition,
                                                 'weight': self.speaker_model.settings.retrieve('lf_legibility_condition', 100),
                                                 'log': '-LF-legibility for left branch'}
             }

        self.left_branch_filter_test_battery = [('Selection test', self.speaker_model.LF.selection_test),
                                                ('Semantic Complement test', PhraseStructure.semantic_selection),
                                                ('Probe_Goal test', PhraseStructure.probe_goal_test),
                                                ('Head Integrity test', PhraseStructure.unrecognized_label)]

    def initialize(self):
        self.baseline_weights = []

    def filter_and_rank(self, X, w):
        if X.bottom().w_internal():
            return [X.bottom()]
        return self.rank(self.filter(X.collect_into_sWM(geometrical=True, self=True)), w)

    def filter(self, X_right_edge):
        return [N for N in X_right_edge if N.zero_level() or self.left_branch_filter(N)]

    def rank(self, site_list, W):
        if self.speaker_model.settings.retrieve('dev_logging', False):
            self.speaker_model.settings.application.dev_logging(f'\nRanking {site_list[0].top()} + {W}')

        weighted_list = []
        for X, new_weight in self.create_baseline_weighting([(site, 0) for site in site_list]):
            for key in self.plausibility_conditions:
                if self.plausibility_conditions[key]['condition'](X, W):
                    new_weight += self.plausibility_conditions[key]['weight']
                else:
                    new_weight -= self.plausibility_conditions[key]['weight']
            weighted_list.append((X, new_weight))

        set_logging(True)
        merge_sites = [(site, priority) for site, priority in sorted(weighted_list, key=itemgetter(1))][::-1]
        log(f'\n\tRanking:\n')
        for i, X in enumerate(merge_sites, start=1):
            log(f'\n\t\t{i}.{X[0]} + {W} ({X[1]})')
        log('\n')
        return [X[0] for X in merge_sites]

    @staticmethod
    def spec_selection(X, W):
        return X.spec_selection(W)

    @staticmethod
    def comp_selection(X, W):
        return X.comp_selection(W)

    def negative_semantic_match(self, site, word):
        if site.zero_level():
            m = site.bottom_affix()
            if not m.core.semantic_match(word):
                return True

    def lf_legibility_condition(self, X, W):
        if not X.zero_level():
            return self.speaker_model.LF.pass_LF_legibility(X.copy().transfer())

    def create_baseline_weighting(self, weighted_site_list, method=''):
        if method == 'Z':
            new_weighted_site_list = [(site, j) for j, (site, w) in enumerate(weighted_site_list, start=1)]
            new_weighted_site_list[0] = (new_weighted_site_list[0][0], len(weighted_site_list))
            new_weighted_site_list[-1] = (new_weighted_site_list[-1][0], len(weighted_site_list)+1)
            new_weighted_site_list = [(site, weight-1) for site, weight in new_weighted_site_list]
            return new_weighted_site_list
        if method == 'Random':
            site_w = list(range(len(weighted_site_list)))
            random.shuffle(site_w)
            return [(site, site_w[i]) for i, (site, w) in enumerate(weighted_site_list, start=0)]
        if method == 'Top-down':
            return [(site, -j) for j, (site, w) in enumerate(weighted_site_list, start=1)]
        if method == 'Bottom-up':
            return [(site, j) for j, (site, w) in enumerate(weighted_site_list, start=1)]
        if method == 'Sling':
            lst = [(site, -j) for j, (site, w) in enumerate(weighted_site_list, start=1)]    # Top-down
            lst[-1] = (lst[-1][0], 1)                                                        # Promote the bottom node
            return lst
        else:
            return [(site, j) for j, (site, w) in enumerate(weighted_site_list, start=1)]

    def left_branch_filter(self, X):
        set_logging(False)
        self.speaker_model.LF.active_test_battery = self.left_branch_filter_test_battery
        return self.speaker_model.LF.pass_LF_legibility(X.copy().transfer(), logging=False)

    @staticmethod
    def word_breaking_filter(X, w):
        if X.complex() and X.M():
            return X.M().L().internal and X.L().internal
