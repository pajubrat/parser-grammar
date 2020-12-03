from support import log
from random import randrange
import sys

def knockout_filter(funct):
    def knockout(self, ps, w):
        if 'filter' in self.controlling_parser_process.local_file_system.settings:
            if not self.controlling_parser_process.local_file_system.settings['filter']:
                log(f'Filtering blocked...')
                return [ps.geometrical_minimal_search(), w]
        return funct(self, ps, w)
    return knockout

def knockout_lexical_ranking(funct):
    def knockout(self, site):
        if 'lexical_anticipation' in self.controlling_parser_process.local_file_system.settings:
            if not self.controlling_parser_process.local_file_system.settings['lexical_anticipation']:
                log(f'Lexical anticipation blocked...')
                return False
        return funct(self, site)
    return knockout

def knockout_extra_ranking(funct):
    def knockout(self, site):
        if 'extra_ranking' in self.controlling_parser_process.local_file_system.settings:
            if not self.controlling_parser_process.local_file_system.settings['extra_ranking']:
                log(f'Semantic ranking blocked...')
                return False
        return funct(self, site)
    return knockout

def knockout_baseline_weighting(funct):
    def knockout(self, weighted_list):
        if 'closure' in self.controlling_parser_process.local_file_system.settings:
            return funct(self, weighted_list, method=self.controlling_parser_process.local_file_system.settings['closure'])
        else:
            return funct(self, weighted_list, method='')
    return knockout