from support import set_logging, log
from operator import itemgetter
import random
from knockouts import knockout_filter, \
    knockout_extra_ranking, \
    knockout_lexical_ranking, \
    knockout_baseline_weighting, \
    knockout_working_memory

class PlausibilityMetrics:
    def __init__(self, controlling_parsing_process):
        self.brain_model = controlling_parsing_process
        self.weighted_site_list = []
        self.word = None
        self.plausibility_conditions = {}
        self.word_specs = None
        self.not_word_specs = None
        self.rare_word_specs = None
        self.word_tail_set = None

    # Main entry point
    def filter_and_rank(self, ps, w):
        nodes_not_in_active_working_memory = []

        # Input integrity test
        if not ps or not w:
            return []

        # Word internal components are always sank into the bottom word, no need to filter or rank
        elif self.word_internal(ps, w) and self.dispersion_filter_active():
            solutions = [(ps.bottom(), True)]
        else:
            nodes_in_active_working_memory, nodes_not_in_active_working_memory = self.in_active_working_memory(ps)
            log(f'\n\t\tFiltering and ranking merge sites...')
            nodes_available = self.filter(nodes_in_active_working_memory, w)
            merge_sites = self.rank_merge_right_(nodes_available, w)
            all_merge_sites = merge_sites + nodes_not_in_active_working_memory
            solutions = self.evaluate_transfer(all_merge_sites)

        log(f'Done.\n\t\tRanking results:')
        for i, (site, transfer) in enumerate(solutions, start=1):
            if nodes_not_in_active_working_memory and site == nodes_not_in_active_working_memory[0]:
                log('\n\t\t\t\t--------------------------------Working memory boundary-------------------------------------------------')
            if transfer:
                log(f'\n\t\t({i}) [{site}↓+ ' + str(w) + ']')
            else:
                log(f'\n\t\t({i}) [{site} + ' + str(w) + ']')

        return solutions

    def evaluate_transfer(self, all_merge_sites):
        solutions = []
        for site in all_merge_sites:
            if site.is_complex():
                solutions.append((site, True))
            else:
                if site.complex_head():
                    if {'φ', 'D', 'P', 'A', 'D/rel'} & site.features:
                        solutions.append((site, True))
                        solutions.append((site, False))
                    else:
                        solutions.append((site, False))
                        solutions.append((site, True))
                else:
                    solutions.append((site, True))

        return solutions

    def dispersion_filter_active(self):
        if 'dispersion_filter' not in self.brain_model.local_file_system.settings:
            return True
        else:
            return self.brain_model.local_file_system.settings['dispersion_filter']

    @knockout_lexical_ranking
    def positive_spec_selection(self, site):
        return (site.is_complex() or 'D' in site.features) and self.word_specs & site.head().features

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
                    return True

    @knockout_lexical_ranking
    def negative_head_comp_selection(self, site):
        if site.is_primitive():
            m = site.bottom_affix()
            if self.word.features & m.convert_features_for_parsing(m.complements_not_licensed()):
                log(f'{self.word.features & m.convert_features_for_parsing(m.complements_not_licensed())}')
                return True

    @knockout_lexical_ranking
    def negative_semantic_match(self, site):
        if site.is_primitive():
            m = site.bottom_affix()
            if not self.brain_model.LF.semantic_match(m, self.word):
                return True

    @knockout_extra_ranking
    def lf_legibility_condition(self, site):
        if not site.is_primitive():
            set_logging(False)
            dropped, output_from_interfaces = self.brain_model.transfer_to_LF(site.copy())
            if not self.brain_model.LF_legibility_test(dropped):
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
                                                 'weight': self.brain_model.local_file_system.settings.get('positive_spec_selection', 100),
                                                 'log': '+Spec selection'},
             'negative_spec_selection':         {'condition': self.negative_spec_selection,
                                                 'weight': self.brain_model.local_file_system.settings.get('negative_spec_selection', -100),
                                                 'log': '-Spec selection'},
             'break_head_comp_relations':       {'condition': self.break_head_comp_relations,
                                                 'weight': self.brain_model.local_file_system.settings.get('break_head_comp_relations', -100),
                                                 'log': 'Head-complement word breaking condition'},
             'negative_tail_test':              {'condition': self.negative_tail_test,
                                                 'weight': self.brain_model.local_file_system.settings.get('negative_tail_test', -100),
                                                 'log': '-Tail'},
             'positive_head_comp_selection':    {'condition': self.positive_head_comp_selection,
                                                 'weight': self.brain_model.local_file_system.settings.get('positive_head_comp_selection', 100),
                                                 'log': '+Comp selection'},
             'negative_head_comp_selection':    {'condition': self.negative_head_comp_selection,
                                                 'weight': self.brain_model.local_file_system.settings.get('negative_head_comp_selection', -100),
                                                 'log': '-Comp selection'},
             'negative_semantics_match':        {'condition': self.negative_semantic_match,
                                                 'weight': self.brain_model.local_file_system.settings.get('negative_semantics_match', -100),
                                                 'log': 'Semantic mismatch'},
             'lf_legibility_condition':         {'condition': self.lf_legibility_condition,
                                                 'weight': self.brain_model.local_file_system.settings.get('lf_legibility_condition', -100),
                                                 'log': '-LF-legibility for left branch'},
             'negative_adverbial_test':         {'condition': self.negative_adverbial_test,
                                                 'weight': self.brain_model.local_file_system.settings.get('negative_adverbial_test', -100),
                                                 'log': '-Adverbial condition'},
             'positive_adverbial_test':         {'condition': self.positive_adverbial_test,
                                                 'weight': self.brain_model.local_file_system.settings.get('positive_adverbial_test', 100),
                                                 'log': '+Adverbial condition'}
             }

    def rank_merge_right_(self, site_list, word):
        self.word = word
        self.word_specs = word.convert_features_for_parsing(word.licensed_specifiers())
        self.not_word_specs =  word.convert_features_for_parsing(word.specifiers_not_licensed())
        self.rare_word_specs = word.convert_features_for_parsing(word.rare_specs())
        self.word_tail_set = word.get_tail_sets()
        log('Ranking...')

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
                    self.brain_model.consume_resources('Rank solution')
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
            log(f'Random baseline ranking {site_w}...')
            return [(site, site_w[i]) for i, (site, w) in enumerate(weighted_site_list, start=0)]
        if method == 'Top-down':
            log(f'Top-down baseline ranking...')
            return [(site, -j) for j, (site, w) in enumerate(weighted_site_list, start=1)]
        if method == 'Bottom-up':
            log(f'Bottom-up baseline ranking...')
            return [(site, j) for j, (site, w) in enumerate(weighted_site_list, start=1)]
        if method == 'Sling':
            lst = [(site, -j) for j, (site, w) in enumerate(weighted_site_list, start=1)]    # Top-down
            lst[-1] = (lst[-1][0], 1)                                                        # Promote the bottom node
            log(f'Sling baseline ranking {lst}...')
            return lst
        else:
            log(f'Closure principle not defined, using default bottom-up baseline ranking...')
            return [(site, j) for j, (site, w) in enumerate(weighted_site_list, start=1)]

    @knockout_filter
    def filter(self, list_of_sites_in_active_working_memory, w):
        set_logging(True)
        log('Filtering...')
        adjunction_sites = []
        #--------------------geometrical minimal search------------------------------
        for N in list_of_sites_in_active_working_memory:
            if self.does_not_accept_any_complementizers(N):
                log(f'Reject {N} + {w} because {N} does not accept complementizers...')
                self.brain_model.consume_resources('Filter solution')
                continue
            if N.is_complex() and self.left_branch_filter(N):
                log(f'Reject {N} + {w} due to bad left branch...')
                self.brain_model.consume_resources('Filter solution')
                continue
            if self.word_breaking_filter(N, w):
                log(f'Reject {N} + {w} because it breaks words...')
                self.brain_model.consume_resources('Filter solution')
                continue
            if self.impossible_sequence(N, w):
                 log(f'Reject {N} + {w} because the sequence is impossible...')
                 self.brain_model.consume_resources('Filter solution')
                 continue
            adjunction_sites.append(N)
        #-------------------------------------------------------------------------------
        log('Done. ')
        return adjunction_sites

    def word_internal(self, ps, w):
        if ps.bottom().bottom_affix().internal:
            log(f'\n\t\tOne solution due to sinking.')
            self.brain_model.consume_resources('Filter solution', 'sink')
            return True

    @knockout_working_memory
    def in_active_working_memory(self, ps):
        all_nodes_available = [N for N in self.geometrical_minimal_search(ps)]
        nodes_not_in_active_working_memory = []
        new_nodes_available = all_nodes_available.copy()
        for N in all_nodes_available:
            if not N.active_in_syntactic_working_memory:
                new_nodes_available.remove(N)
                nodes_not_in_active_working_memory.insert(0, N) # Outside list is stack
        return [node for node in new_nodes_available], [node for node in nodes_not_in_active_working_memory]

    def geometrical_minimal_search(self, ps):
        search_list = [ps]
        while ps.is_complex() and ps.right_const:
            search_list.append(ps.right_const)
            ps = ps.right_const
        return search_list

    def impossible_sequence(self, N, w):
        if N.is_primitive() and 'T/fin' in N.head().features and 'T/fin' in w.features:
            return True

    def left_branch_filter(self, N):
        set_logging(False)
        dropped, output_from_interfaces = self.brain_model.transfer_to_LF(N.copy())
        lf = self.brain_model.LF.LF_legibility_test(dropped)
        set_logging(True)
        if self.left_branch_rejection(lf, dropped):
            return True

    def left_branch_rejection(self, lf_test, dropped):
        def report(boolean):
            if boolean:
                return 'Passed'
            else:
                return 'Failed'

        set_logging(True)
        test_failed = not (lf_test.probe_goal_test_result and
                lf_test.head_integrity_test_result and
                lf_test.selection_test_result and
                lf_test.wrong_complement_test_result and
                lf_test.semantic_test_result)
        if test_failed:
            log(f'Left branch {dropped} failed because ' + ','.join(self.brain_model.LF.test_problem_report) + '. ')
        return test_failed

    def does_not_accept_any_complementizers(self, N):
        if N.is_primitive() and '-COMP:*' in N.features:
            return True

    def word_breaking_filter(self, N, w):
        if self.is_word_internal(N):
            if not w.is_adjoinable():  # Adjoinable phrases cannot be tested because they might become adjuncts later
                set_logging(True)

    def is_word_internal(self, XP):
        if XP.mother and XP.sister() and XP.sister().is_primitive() and XP.sister().internal:
            return True
        else:
            return False