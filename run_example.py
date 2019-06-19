from parse import parse_test_set

parse_test_set(test_set_name='example/test_set.txt',
               lexicon_file_name='lexicon.txt',
               ug_morphemes='ug_morphemes.txt',
               redundancy_rules='redundancy_rules.txt',
               start=0)
