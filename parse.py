
#################################################################################
# Linear phase parser
# Documentation:
# Brattico, P. (2019). Computational implementation of a linear phase parser. Framework and technical documentation (version 5.x)
################################################################################
#
#
# Block 1. Imported modules
#
#
# Time and date information
import datetime
import time

# Imports the linear parser module
from linear_phase_parser import LinearPhaseParser

# Import  support functions
from support import disable_all_logging, set_logging, log, formatted_output

# Import logging
import logging

# Import mechanism to handle folder paths
from pathlib import Path

# Import language guesser
from LanguageGuesser import LanguageGuesser

# Import context
# Context is a data structure that maintains information concerning the context of the sentence, such a
# what language it is, what is the discourse, what lexicon file should be used, and so on. It defines a
# global data structure in the sense that the hearer must be aware of global contextual factors
from context import Context

# Visualizer
import visualizer
import pyglet

#
# Block 2. Define input and output data files and names
#
# Define the data directory
data_folder = Path("language data working directory/study-6-linear-phase-theory/")
# Define the corpus file
test_corpus_name = "linear_phase_theory_corpus.txt"

# Create a file name for the test corpus
# Created automatically from the corpus file above -- do not change
test_set_name = data_folder / test_corpus_name

# Create a file name for the log file
# Created automatically from the corpus file -- do not change
log_name = test_corpus_name[:-4] + '_log.txt'
log_file_name = data_folder / log_name

# Create a file name for the results file
# Created automatically from the corpus file -- do not change
results_name = test_corpus_name[:-4] + '_results.txt'
results_file_name = data_folder / results_name

# Create a file name for the lexicon file
# Created automatically from the corpus file -- do not change
lexicon_file_name = data_folder / 'lexicon.txt'

# Create a file name for universal morphemes
# Created automatically from the corpus file -- do not change
ug_morphemes = data_folder / 'ug_morphemes.txt'

# Create a file name for lexical redundancy rules
# Created automatically from the corpus file -- do not change
redundancy_rules = data_folder / 'redundancy_rules.txt'

# Create a file name for storing the surface vocabulary used in processing
# Created automatically from the corpus file -- do not change
saved_vocabulary_name = test_corpus_name[:-4] + '_saved_vocabulary.txt'
surface_vocabulary_file_name = data_folder / saved_vocabulary_name

#
# Block 3. Preparations
#
# Define grammaticality levels
grammaticality_judgement = ['', '?', '?', '??', '??', '?*', '?*', '##']

# List of sentences to be parsed
# Empty at first
parse_list = []

# Current time and date used to stamp the output files
t = time.time()

# Define logging
# Set this tag if you want to disable all logging functions
# disable_all_logging()
#
# Start logging
#
set_logging(True)

# Produce output to console before parsing begins
print('Parsing process initialized.')
print(datetime.datetime.now())
print('Loading test sentences from file \"' + str(test_set_name) + '\".')
print(f'Logs will be written to file {log_file_name}.')
print(f'Lexicon will be read from file {lexicon_file_name}.')
print(f'UG morphemes will be read from {ug_morphemes}')
print(f'Redundancy rules from {redundancy_rules}')

#Initialize the visualizer
Graphic_output = visualizer.Visualizer()
image_output = True # Set to False if you don't want to see phrase structure images


# Read the corpus file
# Special symbols:
#       #           Comment that is ignored
#       %           This is the only sentence to be parsed (i.e. select on target sentence for testing)
#       +           This tags the clause to be parsed
#       &           Not parsed but inserted into results file as such (i.e. comment)
#       =STOP=      Stop reading the file here

# This list is used if the + symbols is used in the input corpus file (see the definition above)
plus_sentences = []

# Reading begins here
for line in open(test_set_name):

    # Symbol =STOP= is used to stop reading the corpus file
    if line.startswith('=STOP='):
        break

    line = line.strip()

    # Ignore empty lines and comment lines
    if not line or line.startswith('#'):
        continue

    # If a line begins with %, it will the only item parsed
    if line.startswith('%'):
        parse_list = []
        line = line.lstrip('%')
        parse_list.append([word.strip() for word in line.split()])
        break

    # Select lines marked by + for parsing
    elif line.startswith('+'):
        plus_sentences.append([word.strip() for word in line.lstrip('+').split()])
    parse_list.append([word.strip() for word in line.split()])

if plus_sentences:
    parse_list = plus_sentences

# Prepare parsers for each language
# Languages are detected form the lexicon file used in the study
parsers = {}
lang_guesser = LanguageGuesser(lexicon_file_name)
for language in lang_guesser.languages:
    sentence_context = Context()
    sentence_context.lexicon_file = lexicon_file_name
    sentence_context.ug_morphemes_file = ug_morphemes
    sentence_context.redundancy_rules_file = redundancy_rules
    sentence_context.language = language
    parsers[language] = LinearPhaseParser(sentence_context)

# Set up logging functions and parameters
logging.basicConfig(level=logging.INFO, handlers=[logging.FileHandler(log_file_name, 'w', 'utf-8')], format='%(message)s')

# Create the output results file and insert time stamp and information concerning the input files
results_file = open(results_file_name, "w", -1, "utf-8")
results_file.write(str(datetime.datetime.now())+'\n')
results_file.write(f'Test sentences from file \"{test_set_name}\".\n')
results_file.write(f'Logs into file \"{log_file_name}.\n')
results_file.write(f'Lexicon from file \"{lexicon_file_name}\".\n')

# Sets the index of the sentence in the corpus from which parsing will begin.
# 0 = start from the beginning
# This makes it possible to parse individual segments of larger corpora.
start = 0
count = start

# Number of sentences parsed, to be printed to output
count = 0
not_parsed = []

#
# BLock 4. Parsing loop
#
# Parses all  sentences in the corpus
for sentence in parse_list[start:]:
    print('\n' + str(count) + ', ' + f'{sentence}')

    # Sentences beginning with & will be written to the log file as such
    if sentence[0] != '&':
        count = count + 1

        # Print information to the log
        set_logging(True)
        log('\n\n\========================================================================')
        log('# '+str(count))
        log(str(sentence))
        log(f'Using lexicon "{lexicon_file_name}".\n')
        set_logging(False)
        lang = lang_guesser.guess(sentence)

        # Initialize the parser for language lang
        P = parsers[lang]

        # Initialize resource metrics
        # These measure the number of computational operations consumed in processing of any given sentence
        # Computational operations
        P.number_of_Merge = 0
        P.number_of_head_Move = 0
        P.number_of_phrasal_Move = 0
        P.number_of_floating_Move = 0
        P.number_of_Transfer = 0
        P.number_of_Agree = 0

        # Number of item consumed from the input
        P.number_of_inflectional_features_processed = 0
        P.number_of_items_consumed = 0

        # Various output scores
        P.discourse_plausibility = 0        #   Finnish only (study 2)
        P.score = 0                         #   Grammaticality and marginality
        P.number_of_solutions_tried = 0     #   Number of garden paths before first solution

        # This has to do with the numbering of copies (traces) in the output
        P.name_provider_index = 0

        # Report the language of the input, assumed in the parse
        log(f'Language appears to be {lang}')

        #
        # Parse the sentence
        # Results will be stored in the parser object P itself (see below)
        #
        P.parse(sentence)
        #
        #
        #

        # Print the input sentence to the log file
        set_logging(True)
        s = ''
        for word in sentence:
            s = s + word + ' '

        # Definition for ungrammaticality
        # Sentence S is ungrammatical if and only if no results were found
        if len(P.result_list) == 0:
            results_file.write(str(count) + '. * ' + s + '\n\n')
        else:
            # Marginality estimations (if relevant) are printed here
            # grammaticality_judgment refers to the categories '', ?, ??, ?* provided above
            # Graded judgments are not always used
            if 0 >= P.score >= -6:
                judgment = grammaticality_judgement[int(round(abs(P.score), 0))]
            else:
                judgment = '##'
            results_file.write(str(count) + '. ' + judgment + s + '\n\n')

            # Print the results into the results file
            parse_id = 1
            number_of_solutions = len(P.result_list)

            # Loop through all solutions stored by the parser
            for parse, semantic_interpretation in P.result_list:

                # If there is only one solution, we preface it with its number
                if number_of_solutions == 1:
                    results_file.write('\t' + f'{parse}\n')

                # if there are several solutions, we separate them by using alphabetic letters a, b, c, ...
                else:
                    results_file.write('\t' + chr(96 + parse_id) + f'. {parse}\n')

                # Print additional information concerning the result
                results_file.write(f'\tGarden paths: {P.number_of_solutions_tried-1}\n')
                results_file.write('\tLF_Recovery: ' + str(formatted_output(semantic_interpretation, '\n')))
                parse_id = parse_id + 1
                results_file.write('\n')

                if image_output:
                    Graphic_output.file_identifier = 'image of (' + str(count) + chr(96 + parse_id) + ').png'
                    Graphic_output.draw(parse)

    else:
        results_file.write(' '.join(map(str, sentence))+' -------------------------------------------------------\n\n')

# Print the computation time to console
print(f'took: {time.time() - t}s.')

# Print the surface vocabulary used in the study to a file
P.lexicon.save_surface_vocabulary(surface_vocabulary_file_name)
