from support import log

def knockout_working_memory(funct):
    def knockout(self, ps):
        # If working memory is explicitly set to 'True', we implement it; otherwise we don't implement
        if 'working_memory' in self.brain_model.local_file_system.settings:
            if self.brain_model.local_file_system.settings['working_memory']:
                return funct(self, ps)
        log(f'Working memory system is off-line...')
        return [N for N in ps.geometrical_minimal_search()], [] # Return all nodes inside working memory
    return knockout

def knockout_filter(funct):
    def knockout(self, list_of_sites, w):
        if 'filter' in self.brain_model.local_file_system.settings:
            if not self.brain_model.local_file_system.settings['filter']:
                log(f'Filtering blocked...')
                return list_of_sites
        return funct(self, list_of_sites, w)
    return knockout

def knockout_lexical_ranking(funct):
    def knockout(self, site):
        if 'lexical_anticipation' in self.brain_model.local_file_system.settings:
            if not self.brain_model.local_file_system.settings['lexical_anticipation']:
                log(f'Lexical anticipation blocked...')
                return False
        return funct(self, site)
    return knockout

def knockout_extra_ranking(funct):
    def knockout(self, site):
        if 'extra_ranking' in self.brain_model.local_file_system.settings:
            if not self.brain_model.local_file_system.settings['extra_ranking']:
                log(f'Semantic ranking blocked...')
                return False
        return funct(self, site)
    return knockout

def knockout_baseline_weighting(funct):
    def knockout(self, weighted_list):
        if 'closure' in self.brain_model.local_file_system.settings:
            return funct(self, weighted_list, method=self.brain_model.local_file_system.settings['closure'])
        else:
            return funct(self, weighted_list, method='')
    return knockout