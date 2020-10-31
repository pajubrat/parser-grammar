import main
import test
import sys
from diagnostics import Diagnostics

if __name__ == '__main__':
    if len(sys.argv) == 1:
        main.run_study()
    if 'test' in sys.argv:
        test.run_all_tests()
    if 'diagnostics' in sys.argv or '-d' in sys.argv:
        diag = Diagnostics()
        diag.run_resource_diagnostics()