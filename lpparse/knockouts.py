from support import log

def knockout_filter(funct):
    def knockout(self, ps, w):
        if 'knockouts' in self.cpp.local_file_system.settings:
            if 'filter' in self.cpp.local_file_system.settings['knockouts']:
                log(f'Filtering blocked...')
                return [ps.geometrical_minimal_search(), w]
        return funct(self, ps, w)
    return knockout

def knockout_rank_merge_right(funct):
    def knockout(self, sites_and_word_tuple):
        if 'knockouts' in self.cpp.local_file_system.settings:
            if 'ranking' in self.cpp.local_file_system.settings['knockouts']:
                log(f'Ranking blocked...')
                return sites_and_word_tuple[0]
        return funct(self, sites_and_word_tuple)
    return knockout

def knockout_head_complement_selection(funct):
    def knockout(self, site):
        if 'knockouts' in self.cpp.local_file_system.settings:
            if 'head_comp_selection' in self.cpp.local_file_system.settings['knockouts']:
                log(f'Head-complement selection blocked...')
                return False
        return funct(self, site)
    return knockout

def knockout_spec_head_selection(funct):
    def knockout(self, site):
        if 'knockouts' in self.cpp.local_file_system.settings:
            if 'spec_head_selection' in self.cpp.local_file_system.settings['knockouts']:
                log(f'Spec-head selection blocked...')
                return False
        return funct(self, site)
    return knockout

def knockout_semantic_ranking(funct):
    def knockout(self, site):
        if 'knockouts' in self.cpp.local_file_system.settings:
            if 'semantic_ranking' in self.cpp.local_file_system.settings['knockouts']:
                log(f'Semantic ranking blocked...')
                return False
        return funct(self, site)
    return knockout