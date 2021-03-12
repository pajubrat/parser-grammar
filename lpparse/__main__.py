import main
import sys
import multistudy

if __name__ == '__main__':
    if len(sys.argv) == 1:
        main.run_study()
    if '-diagnostics' in sys.argv:
        from diagnostics import Diagnostics
        diag = Diagnostics()
        diag.run_resource_diagnostics()
    if '-diagnostics4' in sys.argv:
        from diagnostics4 import Diagnostics
        diag = Diagnostics()
        diag.run_resource_diagnostics()
    if '-multi' in sys.argv:
        multistudy.run_multi(sys.argv)

    # Here we assume that the user has presented a sentence as input
    main.run_study(sentence=sys.argv[1:])