
#################################################################################
# Parser-grammar
# Based on Brattico, P. (2019). Computational implementation of a top-down grammar.
# See documentation in the \Documentation folder
# Version 2.1
# Programming: Pauli Brattico, with additional programming by Jukka Purma
################################################################################

# Imports
import datetime
from parser_module import Pcb_parser
from support import disable_all_logging, set_logging, log
import logging
import time
from LanguageGuesser import LanguageGuesser
from context import Context

# Name of the corpus file
test_set_name = 'Gold_standard_corpus.txt'

# Additional naming conventions
lexicon_file_name = 'lexicon.txt'
log_file_name = test_set_name[:-4] + '_log.txt'
results_file_name = test_set_name[:-4] + '_results.txt'
ug_morphemes = 'ug_morphemes.txt'
redundancy_rules = 'redundancy_rules.txt'
grammaticality_judgement = ['','?','?','??', '??', '?*', '?*', '##']
parse_list = []
t = time.time()

# Set this tag if you want to disable all logging functions
disable_all_logging()
# set_logging(True)


print('Parsing process initialized.')
print(datetime.datetime.now())
print('Loading test sentences from file \"' + test_set_name + '\".')
print(f'Logs will be written to file {log_file_name}.')
print(f'Lexicon will be read from file {lexicon_file_name}.')

# Reads the corpus file
plus_sentences = []
for line in open(test_set_name):
    line = line.strip()
    if not line or line.startswith('#'):
        continue
    if line.startswith('%'):
        parse_list = []
        line = line.lstrip('%')
        parse_list.append([word.strip() for word in line.split()])
        break
    # Ignore other sentences and parse only those starting with '+'
    elif line.startswith('+'):
        plus_sentences.append([word.strip() for word in line.lstrip('+').split()])
    parse_list.append([word.strip() for word in line.split()])

if plus_sentences:
    parse_list = plus_sentences

# Prepare parsers for each language found in lexicon
parsers = {}
lang_guesser = LanguageGuesser(lexicon_file_name)
for language in lang_guesser.languages:
    context = Context()
    context.lexicon_file_name = lexicon_file_name
    context.ug_morpheme_file = ug_morphemes
    context.redundancy_rule_file = redundancy_rules
    context.language = language
    parsers[language] = Pcb_parser(context)

logging.basicConfig(level=logging.INFO, filename=log_file_name, filemode='w', format='%(message)s')
# Parses all sentences in parse_list and shows the results
count = 0
not_parsed = []

print()
print('Loading test sentences from file \"' + test_set_name + '\".')
print(f'Logs will be written to file {log_file_name}.')
print('Lexicon will be read from file \"' + test_set_name[:-4] + '_lexicon.lex\".')

# Stamp the output file
results_file = open(results_file_name, "w")
results_file.write('Parser-Grammar v. 1.9\n')
results_file.write(str(datetime.datetime.now())+'\n')
results_file.write(f'Test sentences from file \"{test_set_name}\".\n')
results_file.write(f'Logs into file \"{log_file_name}.\n')
results_file.write(f'Lexicon from file \"{lexicon_file_name}\".\n')

# Starting index
# Sets the index of the sentence in the corpus from which parsing will begin. This makes it possible to parse
# individual segments of larger corpora.
start = 0
count = start

# Main parsing loop
for sentence in parse_list[start:]:
    print(str(count))

    if sentence[0] != '&':  # Sentences beginning with & will be written to the log file as such
        count = count + 1
        set_logging(True)
        log('\n\n\========================================================================')
        log('# '+str(count))
        log(str(sentence) + '\n\n')
        set_logging(False)
        lang = lang_guesser.guess(sentence)

        # Initialize the parser for a language
        P = parsers[lang]
        P.number_of_solutions_tried = 0
        P.number_of_Moves = 0
        P.number_of_Merges = 0
        P.score = 0
        P.name_provider_index = 0
        P.reconstruction.name_provider_index = 0
        log(f'Using lexicon "{lexicon_file_name}".')
        log(f'Language appears to be {lang}')

        # Parse the sentence
        P.parse(sentence)

        set_logging(True)
        s = ''
        for word in sentence:
            s = s + word + ' '

        # If no results were found, the sentence is ungrammatical
        if len(P.result_list) == 0:
            results_file.write(str(count) + '. * ' + s + '\n\n')

        # If results were found, the sentence is grammatical
        else:

            # Marginality estimations are printed here
            if 0 >= P.score >= -6:
                judgment = grammaticality_judgement[int(round(abs(P.score),0))]
            else:
                judgment = '##'
            results_file.write(str(count) + '. ' + judgment + ' ' + s + '\n\n')

            # Print the result into the results file
            parse = P.result_list[0]
            results_file.write(f'{parse}\n')
            results_file.write('\''+parse.gloss()+'.\'\n')
            results_file.write('Score: ' + str(P.score) + '  (')
            results_file.write('Failed: ' + str(P.number_of_solutions_tried - 1) + ', Merge:' +
                               str(P.number_of_Merges) + ', Move: ' + str(P.number_of_Moves) + ' = Ops: ' + str(P.number_of_Moves + P.number_of_Merges) + '; ')
            results_file.write('Discourse plausibility: -' + str(P.discourse_plausibility) + ')' + '\n\n')
    else:
        results_file.write('\n'+' '.join(map(str, sentence))+'\n')

print(f'took: {time.time() - t}s.')

