from support import log

def knockout_working_memory(funct):
    def knockout(self, ps):
        # If working memory is explicitly set to 'True', we implement it; otherwise we don't implement
        if 'working_memory' in self.speaker_model.settings.get():
            if self.speaker_model.settings.get()['working_memory']:
                return funct(self, ps)
        log(f'Working memory system is off-line...')
        return [N for N in self.geometrical_minimal_search(ps)], [] # Return all nodes inside working memory
    return knockout

def knockout_filter(funct):
    def knockout(self, list_of_sites, w):
        if 'filter' in self.speaker_model.settings.get():
            if not self.speaker_model.settings.get()['filter']:
                log(f'Filtering blocked...')
                return list_of_sites
        return funct(self, list_of_sites, w)
    return knockout

def knockout_lexical_ranking(funct):
    def knockout(self, site):
        if 'lexical_anticipation' in self.speaker_model.settings.get():
            if not self.speaker_model.settings.get()['lexical_anticipation']:
                log(f'Lexical anticipation blocked...')
                return False
        return funct(self, site)
    return knockout

def knockout_extra_ranking(funct):
    def knockout(self, site):
        if 'extra_ranking' in self.speaker_model.settings.get():
            if not self.speaker_model.settings.get()['extra_ranking']:
                log(f'Semantic ranking blocked...')
                return False
        return funct(self, site)
    return knockout

def knockout_baseline_weighting(funct):
    def knockout(self, weighted_list):
        if 'closure' in self.speaker_model.settings.get():
            return funct(self, weighted_list, method=self.speaker_model.settings.get()['closure'])
        else:
            return funct(self, weighted_list, method='')
    return knockout