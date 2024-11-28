from application import Application
import sys

if __name__ == '__main__':

    # Create the application, instance of the Application class

    app = Application(sys.argv)

    # Input parameter -app ruins the GUI interface

    if len(sys.argv) > 1:
        if sys.argv[1] == '-app':
            app.mainloop()
            sys.exit()

    # Without -app run one whole study as defined in various input configuration files

    app.run_study()    # Run one study (as defined by input files)
