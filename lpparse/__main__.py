from application import Application
import sys

if __name__ == '__main__':
    app = Application(sys.argv)
    if len(sys.argv) > 1:
        if sys.argv[1] == '-app':
            app.mainloop()
            sys.exit()
    app.run_study()    # Run one study (as defined by input files)
