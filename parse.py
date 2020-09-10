#
# Linear phase parser
#
# Documentation:
# Brattico, P. (2019). Computational implementation of a linear phase parser. Framework and technical documentation (version 6.x)

# Block 1. Imports
import sys
from file_IO import *
from linear_phase_parser import LinearPhaseParser
from log_functions import *
import logging
from LanguageGuesser import LanguageGuesser
import visualizer
from pathlib import Path
from support import is_comment

#
#
# Block 2. Define input and output data files and names
#
#
data_folder = Path("language data working directory/study-6-linear-phase-theory")
common_working_directory = Path("language data working directory")
test_corpus = "linear_phase_theory_corpus.txt"
external_source = {"test_corpus_file_name": data_folder / test_corpus,
                   "log_file_name": data_folder / (test_corpus[:-4] + '_log.txt'),
                   "results_file_name": data_folder / (test_corpus[:-4] + '_results.txt'),
                   "grammaticality_judgments_file_name": data_folder / (test_corpus[:-4] + '_grammaticality_judgments.txt'),
                   "resources_file_name": data_folder / (test_corpus[:-4] + '_resources.txt'),
                   "lexicon_file_name": common_working_directory / 'lexicon.txt',
                   "ug_morphemes": common_working_directory / 'ug_morphemes.txt',
                   "redundancy_rules": common_working_directory / 'redundancy_rules.txt',
                   "surface_vocabulary_file_name": data_folder / (test_corpus[:-4] + '_saved_vocabulary.txt')}

#
#
# Block 3. Preparations
#
#
start = 0
count = 1
arguments = set(sys.argv)
t = time.time()
set_logging(True)
logging.basicConfig(level=logging.INFO, handlers=[logging.FileHandler(external_source["log_file_name"], 'w', 'utf-8')], format='%(message)s')
set_logging(True)

# Create the visualizer
Graphic_output = visualizer.Visualizer()
# Image parameters based on command line arguments
Graphic_output.initialize(arguments)
# Read sentences from the test corpus
parse_list = read_test_corpus(external_source)
# Create the image folder
initialize_image_folder(Path(data_folder / 'phrase_structure_images'))
# Initialize results file
results_file = initialize_results_file(external_source["results_file_name"])
# Initialize the grammaticality judgments file
grammaticality_judgments_file = initialize_grammaticality_judgments_file(external_source["grammaticality_judgments_file_name"])
# Initialize the resources output file
resources_file = initialize_resources_file(external_source)
# Initialize language guesser
lang_guesser = LanguageGuesser(external_source["lexicon_file_name"])
# Send information to console
initialize_console(external_source)


#
#
# Block 4. Parse
#
#
P = LinearPhaseParser(external_source)                                                  # Activate parser module
for sentence in parse_list[start:]:                                                     # Parse each sentence from list
    if is_comment(sentence):                                                            # Do not parse comments
        write_info_line(results_file, grammaticality_judgments_file, sentence)          # Write comments as such
    else:                                                                               # Parse sentence
        language = lang_guesser.guess(sentence)                                         # Guess language
        log_sentence(count, sentence, language)                                         # Log sentence
        P.parse(sentence, language)                                                     # Parse  sentence
        write_results(P, results_file, grammaticality_judgments_file, resources_file, count, sentence)  # Write results to file
        write_images(P, Graphic_output, sentence, data_folder)                          # Write images to file
        count = count + 1                                                               # Count sentences

# Block 5. Closing the operations
results_file.close()                                                                    # CLose file
grammaticality_judgments_file.close()                                                   # Close file
resources_file.close()
save_surface_vocabulary(external_source["surface_vocabulary_file_name"], P.lexicon.surface_vocabulary)