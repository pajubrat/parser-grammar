# This module will be used for unit tests

from plausibility_metrics import PlausibilityMetrics
from linear_phase_parser import LinearPhaseParser
from phrase_structure import PhraseStructure
from local_file_system import LocalFileSystem
import sys

# String to constituent conversion
def parse_features(s):
    se = set(s.strip().replace(' ', '').split(','))
    return se

def str_to_const(s, index):
    s.strip().replace(' ','')
    const = PhraseStructure()
    const_id = ''
    while index < len(s):
        if index < len(s) and s[index] == 0:
            index = index + 1
        else:
            if index < len(s) and s[index] == '[':
                const.left_const, index = str_to_const(s, index + 1)
                const.left_const.mother = const
            if index < len(s) and s[index] == ']':
                const.features = parse_features(const_id)
                return const, index + 1
        if index < len(s) and s[index] == '[':
            const.right_const, index = str_to_const(s, index + 1)
            const.right_const.mother = const
        if index < len(s) and s[index] == ']':
            const.features = parse_features(const_id)
            return const, index + 1
        if index < len(s):
            const_id = const_id + s[index]
        index = index + 1
    return const

# UNIT TESTS

# Class PlausibilityMetrics()
def test_plausibility_metrics():

    # create_baseline_weighting()
    # Environment
    loc = LocalFileSystem()
    loc.initialize(set(sys.argv))
    lin = LinearPhaseParser(loc)
    pla = PlausibilityMetrics(lin)

    # Tests
    test_suite = {'1': {'input': [(1, 0), (2, 0), (3, 0), (4, 0)], 'output': [(1, 3), (2, 1), (3, 2), (4, 4)]},
                  '2': {'input': [(1,0)], 'output': [(1, 1)]}}
    for test in test_suite:
        assert pla.create_baseline_weighting(test_suite[test]['input']) == test_suite[test]['output']

    # new_ranking_algorithm()
    test_suite = {'1': {'input': ([1, 2, 3], 'word'), 'output': 0}}
    for test in test_suite:
        assert pla.rank_merge_right_(test_suite[test]['input']) == test_suite[test]['output']

def run_all_tests():
    test_plausibility_metrics()

if __name__ == '__main__':
    run_all_tests()
