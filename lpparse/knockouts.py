from support import log

def knockout_filter(funct):
    def knockout(self, ps, w):
        if 'knockouts' in self.cpp.local_file_system.settings:
            if 'filter' in self.cpp.local_file_system.settings['knockouts']:
                log(f'Filtering blocked...')
                return [ps.geometrical_minimal_search(), w]
        return funct(self, ps, w)
    return knockout

def knockout_lexical_ranking(funct):
    def knockout(self, site):
        if 'knockouts' in self.cpp.local_file_system.settings:
            if 'lexical_ranking' in self.cpp.local_file_system.settings['knockouts']:
                log(f'Lexical ranking blocked...')
                return False
        return funct(self, site)
    return knockout

def knockout_extra_ranking(funct):
    def knockout(self, site):
        if 'knockouts' in self.cpp.local_file_system.settings:
            if 'extra_ranking' in self.cpp.local_file_system.settings['knockouts']:
                log(f'Semantic ranking blocked...')
                return False
        return funct(self, site)
    return knockout

def knockout_late_closure(funct):
    def knockout(self, weighted_list):
        if 'knockouts' in self.cpp.local_file_system.settings:
            if 'late_closure' in self.cpp.local_file_system.settings['knockouts']:
                log(f'Late closure blocked...')
                return [(site, -j) for j, (site, w) in enumerate(weighted_list, start=1)]
        return funct(self, weighted_list)
    return knockout