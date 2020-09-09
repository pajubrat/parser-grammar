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

# Block 2. Define input and output data files and names
data_folder = Path("language data working directory/study-6-linear-phase-theory")
common_working_directory = Path("language data working directory")
test_corpus = "linear_phase_theory_corpus.txt"
external_source = {"test_corpus_file_name": data_folder / test_corpus,
              "log_file_name": data_folder / (test_corpus[:-4] + '_log.txt'),
              "results_file_name": data_folder / (test_corpus[:-4] + '_results.txt'),
              "grammaticality_judgments_file_name": data_folder / (test_corpus[:-4] + '_grammaticality_judgments.txt'),
              "lexicon_file_name": common_working_directory / 'lexicon.txt',
              "ug_morphemes": common_working_directory / 'ug_morphemes.txt',
              "redundancy_rules": common_working_directory / 'redundancy_rules.txt',
              "surface_vocabulary_file_name": data_folder / (test_corpus[:-4] + '_saved_vocabulary.txt')}


# Block 3. Preparations
start = 0
count = 1
set_logging(True)
logging.basicConfig(level=logging.INFO, handlers=[logging.FileHandler(external_source["log_file_name"], 'w', 'utf-8')], format='%(message)s')
arguments = set(sys.argv)
t = time.time()
set_logging(True)
Graphic_output = visualizer.Visualizer()
Graphic_output.initialize(arguments)
parse_list = read_test_corpus(external_source)
initialize_console(external_source)
initialize_image_folder(Path(data_folder / 'phrase_structure_images'))
results_file = initialize_results_file(external_source["results_file_name"])
grammaticality_judgments_file = initialize_grammaticality_judgments_file(external_source["grammaticality_judgments_file_name"])
lang_guesser = LanguageGuesser(external_source["lexicon_file_name"])
not_parsed = []

# Block 4. Parsing operations
P = LinearPhaseParser(external_source)
for sentence in parse_list[start:]:
    if is_comment(sentence):
        write_info_line(results_file, grammaticality_judgments_file, sentence)
    else:
        language = lang_guesser.guess(sentence)
        log_sentence(count, sentence, language)
        P.parse(sentence, language)
        write_results(P, results_file, grammaticality_judgments_file, count, sentence)
        write_images(P, Graphic_output, sentence, data_folder)
        count = count + 1

# Block 5. Closing the operations
results_file.close()
grammaticality_judgments_file.close()
save_surface_vocabulary(external_source["surface_vocabulary_file_name"], P.lexicon.surface_vocabulary)