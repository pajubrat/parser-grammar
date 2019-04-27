
#################################################################################
# This is the main script that should be run when testing the parser
# Version 1.01
################################################################################

# Imports

import datetime
from parser_module import Pcb_parser
from support import disable_all_logging, set_logging, log
import logging
import time
from LanguageGuesser import LanguageGuesser
from context import Context

parse_list = []
t = time.time()
# disable_all_logging()
set_logging(True)

test_set_name = 'intransitive_corpus.txt'
lexicon_file_name = test_set_name[:-4] + '_lexicon.txt'
log_file_name = test_set_name[:-4] + '_log.txt'
results_file_name = test_set_name[:-4] + '_results.txt'
ug_morphemes = 'ug_morphemes.txt'
redundancy_rules = 'redundancy_rules.txt'

print('Parsing process initialized.')
print(datetime.datetime.now())
print('Loading test sentences from file \"' + test_set_name + '\".')
print(f'Logs will be written to file {log_file_name}.')
print(f'Lexicon will be read from file {lexicon_file_name}.')

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

results_file = open(results_file_name, "w")
results_file.write('BC parser v. 0.9\n')
results_file.write(str(datetime.datetime.now())+'\n')
results_file.write(f'Test sentences from file \"{test_set_name}\".\n')
results_file.write(f'Logs into file \"{log_file_name}.\n')
results_file.write(f'Lexicon from file \"{lexicon_file_name}\".\n')

for sentence in parse_list:
    if sentence[0] != '&':
        count = count + 1
        set_logging(True)
        log('\n\n\========================================================================')
        log('# '+str(count))
        log(str(sentence) + '\n\n')
        print('\n' + str(count) + '. ' + str(sentence))
        print('----------------------------------------------------------------')
        set_logging(False)
        lang = lang_guesser.guess(sentence)
        P = parsers[lang]
        log(f'Using lexicon "{lexicon_file_name}".')
        log(f'Language appears to be {lang}')
        P.number_of_solutions_tried = 0
        P.number_of_Moves = 0
        P.number_of_Merges = 0
        P.parse(sentence)
        set_logging(True)
        if len(P.result_list) == 0:
            print('This sentence is ungrammatical.')
            results_file.write(str(count) + '\n')
            results_file.write(str(sentence) + '\n')
            results_file.write('*Ungrammatical.' + '\n')
        else:
            results_file.write(str(count) + '\n')
            results_file.write(str(sentence) + '\n')
            for parse in P.result_list:
                results_file.write(f'{parse}\n')
                results_file.write('\''+parse.gloss()+'.\'\n')
                results_file.write('Failed parses ' + str(P.number_of_solutions_tried - 1) + ', Merge operations:' +
                                   str(P.number_of_Merges) + ', Move operations: ' + str(P.number_of_Moves) + '\n')
    else:
        results_file.write('\n'+' '.join(map(str, sentence))+'\n')

print(f'took: {time.time() - t}s.')

