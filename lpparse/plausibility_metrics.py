from support import set_logging, log
from operator import itemgetter
import random
from knockouts import knockout_filter, \
    knockout_extra_ranking, \
    knockout_lexical_ranking, \
    knockout_baseline_weighting

class PlausibilityMetrics:
    def __init__(self, controlling_parsing_process):
        self.controlling_parser_process = controlling_parsing_process
        self.weighted_site_list = []
        self.word = None
        self.plausibility_conditions = {}
        self.word_specs = None
        self.not_word_specs = None
        self.rare_word_specs = None
        self.word_tail_set = None

    # Main entry point
    def filter_and_rank(self, ps, w):
        log(f'\n\t\tFiltering and ranking merge sites...')
        merge_sites = self.rank_merge_right_(self.filter(ps, w))
        log('Done.\n')
        log(f'\t\tResults: ')
        for i, site in enumerate(merge_sites, start=1):
            log(f'({i}) [{site} + {w}] ')
        return merge_sites

    @knockout_lexical_ranking
    def positive_spec_selection(self, site):
        return site.is_complex() and self.word_specs & site.head().features

    @knockout_lexical_ranking
    def negative_spec_selection(self, site):
        return site.is_complex() and self.not_word_specs & site.head().features

    @knockout_lexical_ranking
    def rare_spec_selection(self, site):
        return site.is_complex() and self.rare_word_specs & site.head().features

    @knockout_lexical_ranking
    def break_head_comp_relations(self, site):
        if not site.is_primitive() and site.mother and \
                site.mother.left_const and site.mother.left_const.is_primitive():
            if site.mother.left_const.licensed_complements() & site.features:
                if 'ADV' not in self.word.features:
                    return True

    @knockout_lexical_ranking
    def negative_tail_test(self, site):
        if site.is_primitive():
            if self.word_tail_set:
                test_word = self.word.copy()
                site.merge_1(test_word, 'right')
                if not test_word.internal_tail_head_test():
                    test_word.remove()
                    return True
                test_word.remove()

    @knockout_lexical_ranking
    def positive_head_comp_selection(self, site):
        if site.is_primitive():
            for m in site.get_affix_list():
                if self.word.features & m.convert_features_for_parsing(m.licensed_complements()):
                    if 'NOM' not in self.word.features:
                        return True

    @knockout_lexical_ranking
    def negative_head_comp_selection(self, site):
        if site.is_primitive():
            m = site.bottom_affix()
            if self.word.features & m.convert_features_for_parsing(m.complements_not_licensed()):
                return True

    @knockout_lexical_ranking
    def negative_semantic_match(self, site):
        if site.is_primitive():
            m = site.bottom_affix()
            if not self.controlling_parser_process.LF.semantic_match(m, self.word):
                return True

    @knockout_extra_ranking
    def lf_legibility_condition(self, site):
        if not site.is_primitive():
            set_logging(False)
            dropped = self.controlling_parser_process.transfer_to_LF(site.copy())
            if not self.controlling_parser_process.LF_legibility_test(dropped):
                set_logging(True)
                return True
            set_logging(True)

    @knockout_lexical_ranking
    def negative_adverbial_test(self, site):
        if 'ADV' in self.word.features and self.word_tail_set:
            w_copy = self.word.copy()
            site.merge_1(w_copy, 'right')
            # If external tail head test fails and the site itself does not match with the tail features,
            # the negative adverbial test is true
            if not w_copy.external_tail_head_test():
                if not self.sister_tail_head_test(site, w_copy):
                    w_copy.remove()
                    return True
            w_copy.remove()

    def sister_tail_head_test(self, site, w_copy):
        for tail_set in w_copy.get_tail_sets():
            if site.head().match_features(tail_set) == 'complete match':
                return True

    @knockout_lexical_ranking
    def positive_adverbial_test(self, site):
        if 'ADV' in self.word.features and self.word_tail_set and site.is_complex():
            w_copy = self.word.copy()
            site.merge_1(w_copy, 'right')
            if w_copy.external_tail_head_test() or self.sister_tail_head_test(site, w_copy):
                w_copy.remove()
                return True
            w_copy.remove()

    def initialize(self):
        self.weighted_site_list = []
        self.word = None
        self.word_specs = None
        self.not_word_specs = None
        self.rare_word_specs = None
        self.word_tail_set = None
        self.plausibility_conditions = \
            {'positive_spec_selection':         {'condition': self.positive_spec_selection,
                                                 'weight': self.controlling_parser_process.local_file_system.settings.get('positive_spec_selection', 100),
                                                 'log': 'Positive specifier selection'},
             'negative_spec_selection':         {'condition': self.negative_spec_selection,
                                                 'weight': self.controlling_parser_process.local_file_system.settings.get('negative_spec_selection', -100),
                                                 'log': 'Negative specifier selection'},
             'break_head_comp_relations':       {'condition': self.break_head_comp_relations,
                                                 'weight': self.controlling_parser_process.local_file_system.settings.get('break_head_comp_relations', -100),
                                                 'log': 'Head-complement word breaking condition'},
             'negative_tail_test':              {'condition': self.negative_tail_test,
                                                 'weight': self.controlling_parser_process.local_file_system.settings.get('negative_tail_test', -100),
                                                 'log': 'Negative tail test condition'},
             'positive_head_comp_selection':    {'condition': self.positive_head_comp_selection,
                                                 'weight': self.controlling_parser_process.local_file_system.settings.get('positive_head_comp_selection', 100),
                                                 'log': 'Positive head-complement selection'},
             'negative_head_comp_selection':    {'condition': self.negative_head_comp_selection,
                                                 'weight': self.controlling_parser_process.local_file_system.settings.get('negative_head_comp_selection', -100),
                                                 'log': 'Negative head-complement selection'},
             'negative_semantics_match':        {'condition': self.negative_semantic_match,
                                                 'weight': self.controlling_parser_process.local_file_system.settings.get('negative_semantics_match', -100),
                                                 'log': 'Semantic mismatch condition'},
             'lf_legibility_condition':         {'condition': self.lf_legibility_condition,
                                                 'weight': self.controlling_parser_process.local_file_system.settings.get('lf_legibility_condition', -100),
                                                 'log': 'Negative LF-legibility condition for left branch'},
             'negative_adverbial_test':         {'condition': self.negative_adverbial_test,
                                                 'weight': self.controlling_parser_process.local_file_system.settings.get('negative_adverbial_test', -100),
                                                 'log': 'Negative adverbial condition'},
             'positive_adverbial_test':         {'condition': self.positive_adverbial_test,
                                                 'weight': self.controlling_parser_process.local_file_system.settings.get('positive_adverbial_test', 100),
                                                 'log': 'Positive adverbial condition'}
             }

    def rank_merge_right_(self, sites_and_word_tuple):
        site_list, word = sites_and_word_tuple
        self.word = word
        self.word_specs = word.convert_features_for_parsing(word.licensed_specifiers())
        self.not_word_specs =  word.convert_features_for_parsing(word.specifiers_not_licensed())
        self.rare_word_specs = word.convert_features_for_parsing(word.rare_specs())
        self.word_tail_set = word.get_tail_sets()
        log('Ranking...')

        self.weighted_site_list = self.create_baseline_weighting([(site, 0) for site in site_list])
        calculated_weighted_site_list = []
        for site, weight in self.weighted_site_list:
            new_weight = weight
            for key in self.plausibility_conditions:
                if self.plausibility_conditions[key]['condition'](site):
                    log(self.plausibility_conditions[key]['log'] + f' for {site}...')
                    log('('+str(self.plausibility_conditions[key]['weight'])+') ')
                    self.controlling_parser_process.consume_resources('Rank solution')
                    new_weight = new_weight + self.plausibility_conditions[key]['weight']
            calculated_weighted_site_list.append((site, new_weight))
        sorted_and_calculated_merge_sites = sorted(calculated_weighted_site_list, key=itemgetter(1))
        merge_sites = [site for site, priority in sorted_and_calculated_merge_sites]
        merge_sites.reverse()
        return merge_sites

    @knockout_baseline_weighting
    def create_baseline_weighting(self, weighted_site_list, method=''):
        if method == 'Z':
            log(f'Using Z-baseline ranking...')
            new_weighted_site_list = [(site, j) for j, (site, w) in enumerate(weighted_site_list, start=1)]
            new_weighted_site_list[0] = (new_weighted_site_list[0][0], len(weighted_site_list))
            new_weighted_site_list[-1] = (new_weighted_site_list[-1][0], len(weighted_site_list)+1)
            new_weighted_site_list = [(site, weight-1) for site, weight in new_weighted_site_list]
            return new_weighted_site_list
        if method == 'Random':
            site_w = list(range(len(weighted_site_list)))
            random.shuffle(site_w)
            log(f'Using random baseline ranking {site_w}...')
            return [(site, site_w[i]) for i, (site, w) in enumerate(weighted_site_list, start=0)]
        if method == 'Top-down':
            log(f'Using top-down baseline ranking...')
            return [(site, -j) for j, (site, w) in enumerate(weighted_site_list, start=1)]
        if method == 'Bottom-up':
            log(f'Using bottom-up baseline ranking...')
            return [(site, j) for j, (site, w) in enumerate(weighted_site_list, start=1)]
        if method == 'Sling':
            lst = [(site, -j) for j, (site, w) in enumerate(weighted_site_list, start=1)]                                   # Top-down
            lst[-1] = (lst[-1][0], 1)                                                                                       # Promote the bottom node
            log(f'Using sling baseline ranking {lst}...')
            return lst
        else:
            log(f'Closure principle not defined, using default bottom-up baseline ranking...')
            return [(site, j) for j, (site, w) in enumerate(weighted_site_list, start=1)]

    @knockout_filter
    def filter(self, ps, w):
        set_logging(True)
        log('Filtering...')
        adjunction_sites = []
        if ps.bottom().bottom_affix().internal:
            log(f'Sink \"{w.get_phonological_string()}\" because it belongs to the same word...')
            self.controlling_parser_process.consume_resources('Filter solution', 'sink')
            log('Done. ')
            return [[ps.bottom()], w]
        #--------------------geometrical minimal search------------------------------
        for N in ps.geometrical_minimal_search():
            if self.does_not_accept_any_complementizers(N):
                log(f'Reject {N} + {w} because {N} does not accept complementizers...')
                self.controlling_parser_process.consume_resources('Filter solution')
                continue
            if N.is_complex() and self.bad_left_branch_test(N):
                log(f'Reject {N} + {w} due to bad left branch...')
                self.controlling_parser_process.consume_resources('Filter solution')
                continue
            if self.breaks_words(N, w):
                log(f'Reject {N} + {w} because it breaks words...')
                self.controlling_parser_process.consume_resources('Filter solution')
                continue
            adjunction_sites.append(N)
        #-------------------------------------------------------------------------------
        log('Done. ')
        return [adjunction_sites, w]

    def bad_left_branch_test(self, N):
        set_logging(False)
        dropped = self.controlling_parser_process.transfer_to_LF(N.copy())
        lf = self.controlling_parser_process.LF.test(dropped)
        set_logging(True)
        if self.left_branch_rejection(lf, dropped):
            return True

    def left_branch_rejection(self, lf_test, dropped):
        set_logging(True)
        test_failed = not (lf_test.probe_goal_test_result and
                lf_test.head_integrity_test_result and
                lf_test.selection_test_result and
                lf_test.wrong_complement_test_result)
        if test_failed:
            log(f'Left branch {dropped} failed (diagnostics: Probe-goal/{lf_test.probe_goal_test_result}, '
                f'Head integrity/{lf_test.head_integrity_test_result}, '
                f'Selection/{lf_test.selection_test_result}, '
                f'Wrong complement/{lf_test.wrong_complement_test_result})... ')
        return test_failed

    def does_not_accept_any_complementizers(self, N):
        if N.is_primitive() and '-COMP:*' in N.features:
            return True

    def breaks_words(self, N, w):
        if self.is_word_internal(N):
            if not w.is_adjoinable():  # Adjoinable phrases cannot be tested because they might become adjuncts later
                set_logging(True)

    # Checks if phrase structure XP cannot be broken off from H-XP because
    # H and X were part of the same word. It is used to prevent right merge to XP
    def is_word_internal(self, XP):
        if XP.mother and XP.sister() and XP.sister().is_primitive() and XP.sister().internal:
            return True
        else:
            return False