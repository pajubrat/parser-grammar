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
                                                 'log': '+Spec selection'},
             'comp_selection':                  {'condition': self.comp_selection,
                                                 'weight': self.speaker_model.settings.retrieve('comp_selection', 100),
                                                 'log': '+Comp selection'},
             'negative_semantics_match':        {'condition': self.negative_semantic_match,
                                                 'weight': self.speaker_model.settings.retrieve('negative_semantics_match', 100),
                                                 'log': 'Semantic mismatch'},
             'lf_legibility_condition':         {'condition': self.lf_legibility_condition,
                                                 'weight': self.speaker_model.settings.retrieve('lf_legibility_condition', 100),
                                                 'log': '-LF-legibility for left branch'}
             }

        self.left_branch_filter_test_battery = [('Selection test', self.speaker_model.LF.selection_test),
                                                ('Semantic Complement test', PhraseStructure.semantic_complement),
                                                ('Probe_Goal test', PhraseStructure.probe_goal_test),
                                                ('Head Integrity test', PhraseStructure.unrecognized_label)]

    def initialize(self):
        self.baseline_weights = []

    def filter_and_rank(self, X, w):
        if X.bottom().w_internal():
            return [X.bottom()]
        return self.rank(self.filter(X.geometrical_minimal_search(), w), w)

    def filter(self, right_edge, w):
        set_logging(False)
        return [N for N in right_edge if not (N.complex() and not self.left_branch_filter(N))]

    def rank(self, site_list, W):
        weighted_list = []
        for X, new_weight in self.create_baseline_weighting([(site, 0) for site in site_list]):
            for key in self.plausibility_conditions:
                if self.plausibility_conditions[key]['condition'](X, W):
                    new_weight = new_weight + self.plausibility_conditions[key]['weight']
                else:
                    new_weight = new_weight - self.plausibility_conditions[key]['weight']
            weighted_list.append((X, new_weight))

        set_logging(True)
        merge_sites = [(site, priority) for site, priority in sorted(weighted_list, key=itemgetter(1))][::-1]
        log(f'\n\tRanking:\n')
        for i, X in enumerate(merge_sites, start=1):
            log(f'\n\t\t{i}.{X[0]} + {W} ({X[1]})')
        log('\n')
        return [X[0] for X in merge_sites]

    @staticmethod
    def spec_selection(X, Y):
        return X.spec_selection(Y)

    @staticmethod
    def comp_selection(X, Y):
        return X.comp_selection(Y)

    def negative_semantic_match(self, site, word):
        if site.zero_level():
            m = site.bottom_affix()
            if not m.semantic_match(word):
                return True

    def lf_legibility_condition(self, site, word):
        if not site.zero_level():
            left_branch_copy = site.copy().transfer()
            if not self.speaker_model.LF.pass_LF_legibility(left_branch_copy, False):
                return True

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

    def left_branch_filter(self, N):
        left_branch = N.copy().transfer()
        self.speaker_model.LF.active_test_battery = self.left_branch_filter_test_battery
        return self.speaker_model.LF.pass_LF_legibility(left_branch, False)

    @staticmethod
    def word_breaking_filter(N, w):
        if N.complex() and N.M():
            return N.M().L().internal and N.L().internal
