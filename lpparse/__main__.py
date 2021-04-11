from diagnostics0 import Diagnostics
#
# Available arguments
#
#   sentence
#   study_folder
#   test_corpus_folder
#   test_corpus_file
#   lexicon_folder

import main
import sys


if __name__ == '__main__':
    args = {}
    if 'diagnostics0' in sys.argv:
        d = Diagnostics()
        d.run_resource_diagnostics()
    else:
        for i, argument in enumerate(sys.argv):
            # Ignore the name of the program
            if i > 0:
                # An argument form is 'type=value'
                decomposed_argument_list = argument.split('=')
                # An argument without key identifier is interpreted as the input sentence
                if len(decomposed_argument_list) == 1:
                    args['sentence'] = decomposed_argument_list[0]
                else:
                    # Create the entry into the argument dictionary, args[type] = value
                    args[decomposed_argument_list[0]] = decomposed_argument_list[1]
        print(args)
        main.run_study(args)