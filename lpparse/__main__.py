import main
import test
import sys

if __name__ == '__main__':
    if len(sys.argv) == 1:
        main.run_study()
    if 'test' in sys.argv:
        test.run_all_tests()