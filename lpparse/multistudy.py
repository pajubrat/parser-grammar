import main

def run_multi(args):
    if '1' in args:
        # Experiment 1
        main.run_study('study-6-linear-phase-theory/Experiment 1a/01-1-1/',
                       'linear_phase_theory_corpus.txt',
                       'study-6-linear-phase-theory')
        main.run_study('study-6-linear-phase-theory/Experiment 1a/02-1-0/',
                       'linear_phase_theory_corpus.txt',
                       'study-6-linear-phase-theory')
        main.run_study('study-6-linear-phase-theory/Experiment 1a/03-0-1/',
                       'linear_phase_theory_corpus.txt',
                       'study-6-linear-phase-theory')
        main.run_study('study-6-linear-phase-theory/Experiment 1a/04-0-0/',
                       'linear_phase_theory_corpus.txt',
                       'study-6-linear-phase-theory')
        main.run_study('study-6-linear-phase-theory/Experiment 1a/05-0-R/',
                       'linear_phase_theory_corpus.txt',
                       'study-6-linear-phase-theory')

    if '2a' in args:
        # Experiment 2a
        main.run_study('study-6-linear-phase-theory/Experiment 2a/21-spec(1)-comp(1)-adj(1)-case(1)/',
                       'linear_phase_theory_corpus.txt',
                       'study-6-linear-phase-theory')
        main.run_study('study-6-linear-phase-theory/Experiment 2a/22-spec(1)-comp(1)-adj(1)-case(0)/',
                       'linear_phase_theory_corpus.txt',
                       'study-6-linear-phase-theory')
        main.run_study('study-6-linear-phase-theory/Experiment 2a/23-spec(1)-comp(1)-adj(0)-case(1)/',
                       'linear_phase_theory_corpus.txt',
                       'study-6-linear-phase-theory')
        main.run_study('study-6-linear-phase-theory/Experiment 2a/24-spec(1)-comp(1)-adj(0)-case(0)/',
                       'linear_phase_theory_corpus.txt',
                       'study-6-linear-phase-theory')
        main.run_study('study-6-linear-phase-theory/Experiment 2a/25-spec(1)-comp(0)-adj(1)-case(1)/',
                       'linear_phase_theory_corpus.txt',
                       'study-6-linear-phase-theory')
        main.run_study('study-6-linear-phase-theory/Experiment 2a/26-spec(1)-comp(0)-adj(1)-case(0)/',
                       'linear_phase_theory_corpus.txt',
                       'study-6-linear-phase-theory')
        main.run_study('study-6-linear-phase-theory/Experiment 2a/27-spec(1)-comp(0)-adj(0)-case(1)/',
                       'linear_phase_theory_corpus.txt',
                       'study-6-linear-phase-theory')
        main.run_study('study-6-linear-phase-theory/Experiment 2a/28-spec(1)-comp(0)-adj(0)-case(0)/',
                       'linear_phase_theory_corpus.txt',
                       'study-6-linear-phase-theory')
        main.run_study('study-6-linear-phase-theory/Experiment 2a/29-spec(0)-comp(1)-adj(1)-case(1)/',
                       'linear_phase_theory_corpus.txt',
                       'study-6-linear-phase-theory')
        main.run_study('study-6-linear-phase-theory/Experiment 2a/210-spec(0)-comp(1)-adj(1)-case(0)/',
                       'linear_phase_theory_corpus.txt',
                       'study-6-linear-phase-theory')
        main.run_study('study-6-linear-phase-theory/Experiment 2a/211-spec(0)-comp(1)-adj(0)-case(1)/',
                       'linear_phase_theory_corpus.txt',
                       'study-6-linear-phase-theory')
        main.run_study('study-6-linear-phase-theory/Experiment 2a/212-spec(0)-comp(1)-adj(0)-case(0)/',
                       'linear_phase_theory_corpus.txt',
                       'study-6-linear-phase-theory')
        main.run_study('study-6-linear-phase-theory/Experiment 2a/213-spec(0)-comp(0)-adj(1)-case(1)/',
                       'linear_phase_theory_corpus.txt',
                       'study-6-linear-phase-theory')
        main.run_study('study-6-linear-phase-theory/Experiment 2a/214-spec(0)-comp(0)-adj(1)-case(0)/',
                       'linear_phase_theory_corpus.txt',
                       'study-6-linear-phase-theory')
        main.run_study('study-6-linear-phase-theory/Experiment 2a/215-spec(0)-comp(0)-adj(0)-case(1)/',
                       'linear_phase_theory_corpus.txt',
                       'study-6-linear-phase-theory')
        main.run_study('study-6-linear-phase-theory/Experiment 2a/216-spec(0)-comp(0)-adj(0)-case(0)/',
                       'linear_phase_theory_corpus.txt',
                       'study-6-linear-phase-theory')

    if '2b' in args:
        main.run_study('study-6-linear-phase-theory/Experiment 2b/31-Bottom-up/',
                       'linear_phase_theory_corpus.txt',
                       'study-6-linear-phase-theory')
        main.run_study('study-6-linear-phase-theory/Experiment 2b/32-Z/',
                       'linear_phase_theory_corpus.txt',
                       'study-6-linear-phase-theory')
        main.run_study('study-6-linear-phase-theory/Experiment 2b/33-Sling/',
                       'linear_phase_theory_corpus.txt',
                       'study-6-linear-phase-theory')
        main.run_study('study-6-linear-phase-theory/Experiment 2b/36-Bottom-up-no-lexical-anticipation/',
                       'linear_phase_theory_corpus.txt',
                       'study-6-linear-phase-theory')
        main.run_study('study-6-linear-phase-theory/Experiment 2b/37-Z-no-lexical-anticipation/',
                       'linear_phase_theory_corpus.txt',
                       'study-6-linear-phase-theory')
        main.run_study('study-6-linear-phase-theory/Experiment 2b/38-Sling-no-lexical-anticipation/',
                       'linear_phase_theory_corpus.txt',
                       'study-6-linear-phase-theory')

    if '2c' in args:
        main.run_study('study-6-linear-phase-theory/Experiment 2c/41-filter-on/',
                       'linear_phase_theory_corpus.txt',
                       'study-6-linear-phase-theory')
        main.run_study('study-6-linear-phase-theory/Experiment 2c/42-filter-off/',
                       'linear_phase_theory_corpus.txt',
                       'study-6-linear-phase-theory')

    if '2d' in args:
        main.run_study('study-6-linear-phase-theory/Experiment 2d/51-BU(1)-LA(0)-F(0)/',
                       'linear_phase_theory_corpus.txt',
                       'study-6-linear-phase-theory')
        main.run_study('study-6-linear-phase-theory/Experiment 2d/52-BU(0)-LA(1)-F(0)/',
                       'linear_phase_theory_corpus.txt',
                       'study-6-linear-phase-theory')
        main.run_study('study-6-linear-phase-theory/Experiment 2d/53-BU(0)-LA(0)-F(1)/',
                       'linear_phase_theory_corpus.txt',
                       'study-6-linear-phase-theory')
        main.run_study('study-6-linear-phase-theory/Experiment 2d/54-BU(0)-LA(0)-F(0)/',
                       'linear_phase_theory_corpus.txt',
                       'study-6-linear-phase-theory')

    if '3' in args:
        main.run_study('study-6-linear-phase-theory/Experiment 3/55-Optimal parser/',
                       'linear_phase_theory_corpus.txt',
                       'study-6-linear-phase-theory')
        main.run_study('study-6-linear-phase-theory/Experiment 3/56-Performance/',
                       'performance_corpus.txt',
                       'study-6-linear-phase-theory/Experiment 3/56-Performance/')
        main.run_study('study-6-linear-phase-theory/Experiment 3/57-no_left_branch_principles/',
                       'performance_corpus.txt',
                       'study-6-linear-phase-theory/Experiment 3/57-no_left_branch_principles/')
        main.run_study('study-6-linear-phase-theory/Experiment 3/58-no_left_branch_principles_all/',
                       'linear_phase_theory_corpus.txt',
                       'study-6-linear-phase-theory')
        main.run_study('study-6-linear-phase-theory/Experiment 3/59-Performance with WM/',
                       'performance_corpus.txt',
                       'study-6-linear-phase-theory/Experiment 3/59-Performance with WM/')
        main.run_study('study-6-linear-phase-theory/Experiment 3/60-Optimal parser with WM/',
                       'linear_phase_theory_corpus.txt',
                       'study-6-linear-phase-theory')