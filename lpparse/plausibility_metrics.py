from support import set_logging, log
from operator import itemgetter
from phrase_structure import PhraseStructure
import random
from knockouts import knockout_filter, \
    knockout_extra_ranking, \
    knockout_lexical_ranking, \
    knockout_baseline_weighting
from feature_processing import convert_features_for_parsing


class PlausibilityMetrics:
    def __init__(self, speaker_model):
        self.speaker_model = speaker_model
        self.weighted_site_list = []
        self.word = None
        self.plausibility_conditions = \
            {'positive_spec_selection':         {'condition': self.positive_spec_selection,
                                                 'weight': self.speaker_model.settings.retrieve('positive_spec_selection', 100),
                                                 'log': '+Spec selection'},
             'negative_spec_selection':         {'condition': self.negative_spec_selection,
                                                 'weight': self.speaker_model.settings.retrieve('negative_spec_selection', -100),
                                                 'log': '-Spec selection'},
             'break_head_comp_relations':       {'condition': self.break_head_comp_relations,
                                                 'weight': self.speaker_model.settings.retrieve('break_head_comp_relations', -100),
                                                 'log': 'Head-complement word breaking condition'},
             'positive_head_comp_selection':    {'condition': self.positive_head_comp_selection,
                                                 'weight': self.speaker_model.settings.retrieve('positive_head_comp_selection', 100),
                                                 'log': '+Comp selection'},
             'negative_head_comp_selection':    {'condition': self.negative_head_comp_selection,
                                                 'weight': self.speaker_model.settings.retrieve('negative_head_comp_selection', -100),
                                                 'log': '-Comp selection'},
             'negative_semantics_match':        {'condition': self.negative_semantic_match,
                                                 'weight': self.speaker_model.settings.retrieve('negative_semantics_match', -100),
                                                 'log': 'Semantic mismatch'},
             'lf_legibility_condition':         {'condition': self.lf_legibility_condition,
                                                 'weight': self.speaker_model.settings.retrieve('lf_legibility_condition', -100),
                                                 'log': '-LF-legibility for left branch'},
             'negative_adverbial_test':         {'condition': self.negative_adverbial_test,
                                                 'weight': self.speaker_model.settings.retrieve('negative_adverbial_test', -100),
                                                 'log': '-Adverbial condition'},
             'positive_adverbial_test':         {'condition': self.positive_adverbial_test,
                                                 'weight': self.speaker_model.settings.retrieve('positive_adverbial_test', 100),
                                                 'log': '+Adverbial condition'}
             }

        self.not_word_specs = None
        self.word_tail_set = None
        self.address_label = 0
        self.left_branch_filter_test_battery = [('Selection test', self.speaker_model.LF.selection_test),
                                                ('Semantic Complement test', PhraseStructure.semantic_complement),
                                                ('Probe_Goal test', PhraseStructure.probe_goal_test),
                                                ('Head Integrity test', PhraseStructure.unrecognized_label)]

    def initialize(self):
        self.weighted_site_list = []
        self.word = None
        self.not_word_specs = None
        self.word_tail_set = None

    def filter_and_rank(self, X, w):
        set_logging(False)
        if not w:
            return []

        if 'inflectional' in w.features:
            return []

        # Input integrity test
        if not X or not w:
            return []

        elif X.word_internal() and self.dispersion_filter_active():
            merge_sites = X.bottom()
        else:
            log(f'\n\t\tFiltering and ranking merge sites...')
            nodes_available = self.filter(X.geometrical_minimal_search(), w)
            merge_sites = self.rank_merge_right_(nodes_available, w)

        set_logging(True)
        log(f'\n\tRanking:')
        for i, site in enumerate(merge_sites, start=1):
            log(f'\n\t\t{i}.{site} + {w}')
        return merge_sites

    def dispersion_filter_active(self):
        return True

    @knockout_lexical_ranking
    def positive_spec_selection(self, site):
        return (site.complex() or 'D' in site.features) and not self.not_word_specs & site.head().features

    @knockout_lexical_ranking
    def negative_spec_selection(self, site):
        return site.complex() and self.not_word_specs & site.head().features

    @knockout_lexical_ranking
    def break_head_comp_relations(self, site):
        if not site.zero_level() and site.mother_ and \
                site.mother_.left() and site.mother_.left().zero_level():
            if not site.mother_.left().get_selection_features('-COMP') & site.features:
                if not self.word.adverbial():
                    return True

    @knockout_lexical_ranking
    def positive_head_comp_selection(self, site):
        if site.zero_level():
            for m in site.get_affix_list():
                if not self.word.features & convert_features_for_parsing(m.get_selection_features('-COMP')):
                    return True

    @knockout_lexical_ranking
    def negative_head_comp_selection(self, site):
        if site.zero_level():
            m = site.bottom_affix()
            if self.word.features & convert_features_for_parsing(m.get_selection_features('-COMP')):
                log(f'{self.word.features & convert_features_for_parsing(m.get_selection_features("-COMP"))}')
                return True

    @knockout_lexical_ranking
    def negative_semantic_match(self, site):
        if site.zero_level():
            m = site.bottom_affix()
            if not m.semantic_match(self.word):
                return True

    @knockout_extra_ranking
    def lf_legibility_condition(self, site):
        if not site.zero_level():
            dropped = site.copy().transfer_to_LF()
            if not self.speaker_model.LF.pass_LF_legibility(dropped, False):
                return True

    @knockout_lexical_ranking
    def negative_adverbial_test(self, site):
        if self.word.adverbial() and self.word_tail_set:
            w_copy = self.word.copy()
            site.Merge_inside(w_copy, 'right')
            # If external tail head test fails and the site itself does not match with the tail features,
            # the negative adverbial test is true
            if not w_copy.tail_test():
                    w_copy.remove()
                    return True
            w_copy.remove()

    @knockout_lexical_ranking
    def positive_adverbial_test(self, site):
        if self.word.adverbial() and self.word_tail_set and site.complex():
            w_copy = self.word.copy()
            site.Merge_inside(w_copy, 'right')
            if w_copy.tail_test():
                w_copy.remove()
                return True
            w_copy.remove()

    def rank_merge_right_(self, site_list, word):
        self.word = word
        self.not_word_specs = convert_features_for_parsing(word.specifiers_not_licensed())
        self.word_tail_set = word.get_tail_sets()

        # Create baseline default weighting order (default order is decided by input parameters in study config file)
        self.weighted_site_list = self.create_baseline_weighting([(site, 0) for site in site_list])
        calculated_weighted_site_list = []

        # Apply all plausibility conditions (defined as as dict of functions) for each candidate site + word solution
        for site, weight in self.weighted_site_list:
            new_weight = weight
            for key in self.plausibility_conditions:
                if self.plausibility_conditions[key]['condition'](site):
                    log(self.plausibility_conditions[key]['log'] + f' for {site}...')
                    log('('+str(self.plausibility_conditions[key]['weight'])+') ')
                    new_weight = new_weight + self.plausibility_conditions[key]['weight']
            calculated_weighted_site_list.append((site, new_weight))

        sorted_and_calculated_merge_sites = sorted(calculated_weighted_site_list, key=itemgetter(1))
        merge_sites = [site for site, priority in sorted_and_calculated_merge_sites]
        merge_sites.reverse()
        return merge_sites

    @knockout_baseline_weighting
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

    @knockout_filter
    def filter(self, list_of_sites_in_active_working_memory, w):
        adjunction_sites = []
        for N in list_of_sites_in_active_working_memory:
            if N.complex() and self.left_branch_filter(N):
                log(f'Reject {N} + {w} due to bad left branch ({self.speaker_model.LF.error_report_for_external_callers})...')
                continue
            if self.word_breaking_filter(N, w) and not N.bottom():
                log(f'Reject {N} + {w} because it breaks words. ')
                continue
            if self.left_branch_filter(N):
                pass
            if N.impossible_sequence(w):
                 log(f'Reject {N} + {w} because the sequence is impossible. ')
                 continue
            adjunction_sites.append(N)
        return adjunction_sites

    def left_branch_filter(self, N):
        dropped = N.copy().transfer_to_LF()
        self.speaker_model.LF.active_test_battery = self.left_branch_filter_test_battery
        left_branch_passes_LF = self.speaker_model.LF.pass_LF_legibility(dropped, False)
        if not left_branch_passes_LF:
            log(f'in {dropped}. ')
        return not left_branch_passes_LF

    def word_breaking_filter(self, N, w):
        if N.is_word_internal():
            if not w.is_adjoinable():  # Adjoinable phrases cannot be tested because they might become adjuncts later
                return True
