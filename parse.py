
#################################################################################
# Linear phase parser
# Brattico, P. (2019). Computational implementation of a linear phase parser. Framework and technical documentation.
# See documentation in the \Documentation folder
# Version 6.x
################################################################################

# Imports
import datetime
from linear_phase_parser import LinearPhaseParser
from support import disable_all_logging, set_logging, log
import logging
import time
from pathlib import Path
from LanguageGuesser import LanguageGuesser
from context import Context

# Name of the corpus file
# CHANGE TO MATCH THE STUDY
# Name of the data directory
data_folder = Path("language data working directory/study-6-book/")
# Name of the corpus file
test_corpus_name = "book_corpus.txt"

# file name for the test corpus
# Created automatically from the corpus file -- do not change
test_set_name = data_folder / "book_corpus.txt"

# log file (name plus path)
# Created automatically from the corpus file -- do not change
log_name = test_corpus_name[:-4] + '_log.txt'
log_file_name = data_folder / log_name

# results file (name plus path)
# Created automatically from the corpus file -- do not change
results_name = test_corpus_name[:-4] + '_results_txt'
results_file_name = data_folder / results_name

# Name of the lexicon file
# Created automatically from the corpus file -- do not change
lexicon_file_name = data_folder / 'lexicon.txt'

# Name of the file containing universal morphemes
# Created automatically from the corpus file -- do not change
ug_morphemes = data_folder / 'ug_morphemes.txt'

# Name of the file containing lexical redundancy rules
# Created automatically from the corpus file -- do not change
redundancy_rules = data_folder / 'redundancy_rules.txt'

# Grammaticality judgment levels
grammaticality_judgement = ['', '?', '?', '??', '??', '?*', '?*', '##']

# List of sentences to be parsed
parse_list = []

# Current time and date used to stamp the output files
t = time.time()

# Set this tag if you want to disable all logging functions
# disable_all_logging()

# Start logging
set_logging(True)

# Output to console before parsing begins
print('Parsing process initialized.')
print(datetime.datetime.now())
print('Loading test sentences from file \"' + str(test_set_name) + '\".')
print(f'Logs will be written to file {log_file_name}.')
print(f'Lexicon will be read from file {lexicon_file_name}.')
print(f'UG morphemes will be read from {ug_morphemes}')
print(f'Redundancy rules from {redundancy_rules}')

# Read the corpus file
#   Ignore empty lines and comments
#   % - This is the only sentence to be parsed
#   + - This tags the clause to be parsed
#   Otherwise, all sentences are parsed
plus_sentences = []
for line in open(test_set_name):
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
logging.basicConfig(level=logging.INFO, filename=log_file_name, filemode='w', format='%(message)s')

# Print parameters to console
print()

# Create the output file
results_file = open(results_file_name, "w")
results_file.write(str(datetime.datetime.now())+'\n')
results_file.write(f'Test sentences from file \"{test_set_name}\".\n')
results_file.write(f'Logs into file \"{log_file_name}.\n')
results_file.write(f'Lexicon from file \"{lexicon_file_name}\".\n')

# Prepare
# Sets the index of the sentence in the corpus from which parsing will begin. This makes it possible to parse
# individual segments of larger corpora.
start = 0
count = start

# Number of sentences parsed, to be printed to output
count = 0
not_parsed = []

# Parsing loop (for all sentences in the corpus)
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
        P.number_of_Merge = 0
        P.number_of_head_Move = 0
        P.number_of_phrasal_Move = 0
        P.number_of_floating_Move = 0
        P.number_of_Transfer = 0
        P.number_of_Agree = 0
        P.number_of_solutions_tried = 0
        P.number_of_inflectional_features_processed = 0
        P.discourse_plausibility = 0
        P.number_of_items_consumed = 0
        P.score = 0

        # This has to do with the numbering of copies (traces) in the output
        P.name_provider_index = 0

        # Report the language of the input, assumed in the parse
        log(f'Language appears to be {lang}')

        # Parse the sentence
        # The results will be stored in the parser object P
        P.parse(sentence)

        # Print the sentence to the log file
        set_logging(True)
        s = ''
        for word in sentence:
            s = s + word + ' '

        # If no results were found, the sentence is ungrammatical
        if len(P.result_list) == 0:
            results_file.write('\t' + str(count) + '. * ' + s + '\n\n')
        else:
            # Marginality estimations are printed here
            if 0 >= P.score >= -6:
                judgment = grammaticality_judgement[int(round(abs(P.score), 0))]
            else:
                judgment = '##'
            results_file.write('\t' + str(count) + '. ' + judgment + s + '\n')

            # Print the result into the results file
            parse = P.result_list[0]
            results_file.write(f'\t\t{parse}\n')
            results_file.write(f'\t\tSolutions({P.number_of_solutions_tried}), '
                               f'Merge({P.number_of_Merge}), '
                               f'Move(head)({P.number_of_head_Move}), '
                               f'Move(phrasal)({P.number_of_phrasal_Move}), '
                               f'Transfer({P.number_of_Transfer}), '
                               f'Inflection({P.number_of_inflectional_features_processed}), '
                               f'Consumed({P.number_of_items_consumed})\n')
            results_file.write('\n')
    else:
        results_file.write(' '.join(map(str, sentence))+'\n\n')

# Print the computation time to console
print(f'took: {time.time() - t}s.')