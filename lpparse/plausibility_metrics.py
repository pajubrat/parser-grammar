from support import set_logging, log
from operator import itemgetter

class PlausibilityMetrics:
    def __init__(self, controlling_parsing_process):
        self.cpp = controlling_parsing_process

    def rank_solutions(self, ps, w):
        return self.rank_merge_right(self.filter(ps, w))

    def filter(self, ps, w):
        log('\n\t\t\tFiltering out impossible merge sites...')
        adjunction_sites = []
        if ps.bottom().bottom_affix().internal:
            log(f'Sink \"{w.get_phonological_string()}\" because it belongs to the same word...Done.\n')
            return [[ps.bottom()], w]
        #--------------------geometrical minimal search------------------------------
        for N in ps.geometrical_minimal_search():
            if self.does_not_accept_any_complementizers(N):
                log(f'Reject {N} + {w} because {N} does not accept complementizers...')
                continue
            if N.is_complex() and self.bad_left_branch_test(N):
                log(f'Reject {N} + {w} due to bad left branch...')
                continue
            if self.breaks_words(N, w):
                log(f'Reject {N} + {w} because it breaks words...')
                continue
            adjunction_sites.append(N)
        #-------------------------------------------------------------------------------
        log('Done.\n')
        return [adjunction_sites, w]

    # Definition for the ranking function
    def rank_merge_right(self, arg_list):
        site_list = arg_list[0]
        w = arg_list[1]
        if len(site_list) <= 1:
            return site_list
        log('\t\t\tRanking remaining sites...')
        word_specs = w.convert_features_for_parsing(w.licensed_specifiers())
        word_rare_specs = w.convert_features_for_parsing(w.rare_specs())
        word_not_specs = w.convert_features_for_parsing(w.specifiers_not_licensed())
        word_tail_set = w.get_tail_sets()
        word_pf = w.get_phonological_string()
        word_labels = w.features
        adjunction_sites = []
        avoid_set = set()

        # Loop through the possible merge sites
        for i, site in enumerate(site_list, start=1):
            # This determines how to order constituents with the same ranking
            # This method prioritizes lower sites (e.g., top node scores 0 bonus)
            priority_base = i
            priority = priority_base
            site_features = site.head().features

            # Case 2a. positive SPEC solutions
            # Check if there are SPEC-w solutions
            if word_specs & site_features:
                # The higher the number the higher the relative ranking will be
                # This is in part arbitrary and should be considered carefully when aiming for realism
                priority = priority + priority_base + 100 * len(word_specs & site_features)
                log(f'Prioritize {site.get_cats_string()} as SPEC,{word_pf}...')
                avoid_set.clear()

            # Case 2b. Negative Spec solutions
            # Check if there are negative SPEC conditions and avoid them
            if not site.is_primitive() and (word_not_specs & site_features):
                # The higher the number the higher the relative ranking will be
                # This is in part arbitrary and should be considered carefully when aiming for realism
                priority = priority + priority_base - 100 * len(word_not_specs & site_features)
                log(f'Avoid {site.head().get_cats_string()}P as SPEC, {word_pf}...')
                avoid_set.add(site)
            # Avoid all SPEC solutions if there is [-SPEC:*]
            if '*' in word_not_specs:
                # The higher the number the higher the relative ranking will be
                # This is in part arbitrary and should be considered carefully when aiming for realism
                priority = priority + priority_base - 100
                log(f'Avoid {site.head().get_cats_string()}P as SPEC for {word_pf} due to unselective SPEC feature...')
                avoid_set.add(site)
            # Avoid rare SPEC solutions
            if word_rare_specs & site_features:
                # The higher the number the higher the relative ranking will be
                # This is in part arbitrary and should be considered carefully when aiming for realism
                priority = priority + priority_base - 1000
                log(f'Avoid {site.head().get_cats_string()}P as SPEC for {word_pf} due to rare SPEC feature...')
                avoid_set.add(site)

            # Case 2c. Check if existing H-Comp-relations would be broken, if yes, avoid them
            # Antecedent condition: site is c-commanded locally (possible selected) by a head H
            if not site.is_primitive() and site.mother and \
                    site.mother.left_const and site.mother.left_const.is_primitive():
                # and if H selects for site
                if site.mother.left_const.licensed_complements() & site.features:
                    if 'ADV' not in w.features:  # Adverbs will not break selection because they will be adjuncts
                        # The higher the number the higher the relative ranking will be
                        # This is in part arbitrary and should be considered carefully when aiming for realism
                        priority = priority + priority_base - 100 * len(
                            site.mother.left_const.licensed_complements() & site.features)
                        log(f'Avoid [{site}, {w}] because the operation breaks up an existing selectional dependency...')
                        avoid_set.add(site)

            # Case 4. Prioritize/avoid Comp solutions
            # Check if site is primitive (takes a complement)
            if site.is_primitive():
                # Check if the solution violates tailing agreement and if yes, avoid
                # Check that the new constituent has tailing features
                if word_tail_set:
                    test_word = w.copy()
                    site.merge_1(test_word,'right')  # We must merge the constituent in order to see possible violations
                    if not test_word.internal_tail_head_test():
                        priority = priority + priority_base - 50
                        log(f'Avoid [{site.get_phonological_string()} {word_pf}] due to local agreement failure...')
                        avoid_set.add(site)
                    test_word.remove()
                # Evaluate Comp selection for all morphemes inside the site
                for m in site.get_affix_list():
                    # Check if H selects w and if yes, prioritize this solution
                    if w.features & m.convert_features_for_parsing(m.licensed_complements()):
                        priority = priority + priority_base + 100
                        log(f'Prioritize [{m.get_phonological_string()} {word_pf}] due to complement selection...')
                        avoid_set.clear()
                    # ... if f cannot be merged to the complement, avoid this solution
                    if w.features & m.convert_features_for_parsing(m.complements_not_licensed()):
                        priority = priority + priority_base - 100 * len(
                            w.features & m.convert_features_for_parsing(m.complements_not_licensed()))
                        log(f'Avoid [{m.get_phonological_string()} {word_pf}] due to complement selection...')
                        avoid_set.add(site)
                    if not LF.semantic_match(m, w):
                        priority = priority + priority_base - 100
                        log(f'Avoid [{site},{w}] solution due to semantic mismatch...')
                        avoid_set.add(site)

            # Case 5. LF-legibility violations
            if not site.is_primitive():
                # Transfer before checking
                set_logging(False)  # "Hypothetical reconstruction" is confusing in the logs
                dropped = self.cpp.transfer_to_LF(site.copy())
                set_logging(True)
                # If Transfer results in failures, avoid the solution
                if self.cpp.LF_legibility_test(dropped):
                    priority = priority + priority_base - 100
                    log(
                        f'Avoid {dropped.illustrate()} as left branch because it constitutes illicit structure...')
                    avoid_set.add(site)

            # Case 6. Word-breaking violations
            # Remove all solutions which would cause phonological words to break apart
            if site.is_primitive() and self.cpp.is_word_internal(site):
                if 'ADV' not in w.features:
                    priority = priority + priority_base - 100
                    log(f'Avoid {site} because it could break words...')
                    avoid_set.add(site)

            # Case 7. Adverbials select legitimate tail-head configurations
            if 'ADV' in word_labels and word_tail_set:
                # Make copies to test merge
                w_copy = w.copy()
                site.merge_1(w_copy, 'right')

                # Adverbial attachment is only tested inside finite tense
                if 'T/fin' in str(w_copy.feature_vector()):
                    if not w_copy.external_tail_head_test():
                        priority = priority + priority_base - 100
                        log(f'Avoid {site} due to tail-head failure...\n')
                        avoid_set.add(site)
                    else:
                        priority = priority + priority_base + 200
                        log(f'Considering {site} due to legitimate tail-head configuration...')
                        avoid_set.clear()
                w_copy.remove()

            # Case 8. Surface conditions
            adjunction_sites.append((priority, site))

            # Case 8. No positive solution found based on local information available
            if len(avoid_set) == len(adjunction_sites):
                # Search the largest adjoinable and LF-legible attachment site not containing T/fin
                size = 0
                max_site = None
                for priority, site_ in adjunction_sites:
                    if site_.is_adjoinable():
                        size_ = site_.size()
                        if size_ > size and not site_.contains_feature('T/fin'):
                            set_logging(False)
                            if self.cpp.LF_legibility_test(self.cpp.transfer_to_LF(site_.copy())):
                                max_site = site_
                                max_priority = priority
                                size = size_
                            set_logging(True)
                if max_site:
                    log(f'Prioritize {max_site} because all solutions were negative...')
                    adjunction_sites.remove((max_priority, max_site))
                    adjunction_sites.append((max_priority + 200, max_site))
            log('Done.\n')

            # Sort based on priority (highest is prioritized)
            adjunction_sites = sorted(adjunction_sites, key=itemgetter(0))
            adjunction_sites = [site for priority, site in adjunction_sites]
            adjunction_sites.reverse()  # Reverse so that highest will be first
            # Print the completed ranking to the logs
            log(f'\t\t\tResults: ')
            for i, site in enumerate(adjunction_sites, start=1):
                log(f'{i}. [{site}; {word_pf}] ')
            # Return the finished list of ranked adjunction sites
            log('.\n')
            return adjunction_sites

    def bad_left_branch_test(self, N):
        set_logging(False)
        dropped = self.cpp.transfer_to_LF(N.copy())
        lf = self.cpp.LF.test(dropped)
        set_logging(True)
        if self.left_branch_rejection(lf):
            return True

    def left_branch_rejection(self, lf_test):
        return not (lf_test.probe_goal_test_result and
                lf_test.head_integrity_test_result and
                lf_test.selection_test_result and
                lf_test.wrong_complement_test_result)

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


