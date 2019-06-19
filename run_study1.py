from parse import run_parse

run_parse(test_set_name='study1/Study1_seeds.txt',
          lexicon_file_name='lexicon.txt',
          ug_morphemes='ug_morphemes.txt',
          redundancy_rules='redundancy_rules.txt',
          start=0)