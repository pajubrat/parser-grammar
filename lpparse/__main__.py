from application import Application
import main
import sys

if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == '-app':
            app = Application()
            app.mainloop()
            sys.exit()
    main.run_study()    # Run one study (as defined by input files)
