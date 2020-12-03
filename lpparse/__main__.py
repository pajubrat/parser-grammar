import main
import sys
import multistudy

if __name__ == '__main__':
    if len(sys.argv) == 1:
        main.run_study()
    if 'diagnostics' in sys.argv or '-d' in sys.argv:
        from diagnostics import Diagnostics
        diag = Diagnostics()
        diag.run_resource_diagnostics()
    if 'multi' in sys.argv:
        multistudy.run_multi(sys.argv)

