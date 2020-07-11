
#################################################################################
# Linear phase parser
# Documentation:
# Brattico, P. (2019). Computational implementation of a linear phase parser. Framework and technical documentation (version 5.x)
################################################################################
# Block 1. Imported modules
import datetime
import time

# Command line argument parser
import sys

# Imports the linear parser module
from linear_phase_parser import LinearPhaseParser

# Import  support functions
from support import disable_all_logging, set_logging, log, formatted_output

# Import logging
import logging

# Import language guesser
from LanguageGuesser import LanguageGuesser

# Import context
# Context is a data structure that maintains information concerning the context of the sentence, such a
# what language it is, what is the discourse, what lexicon file should be used, and so on. It defines a
# global data structure in the sense that the hearer must be aware of global contextual factors
from context import Context

# Visualizer
import visualizer

# file systems
from pathlib import Path

# Block 2. Define input and output data files and names
data_folder = Path("language data working directory/study-6-linear-phase-theory")
test_corpus_name = "linear_phase_theory_corpus.txt"
test_set_name = data_folder / test_corpus_name
log_name = test_corpus_name[:-4] + '_log.txt'
log_file_name = data_folder / log_name
results_name = test_corpus_name[:-4] + '_results.txt'
results_file_name = data_folder / results_name
grammaticality_judgments_name = test_corpus_name[:-4] + '_grammaticality_judgments.txt'
grammaticality_judgments_file_name = data_folder / grammaticality_judgments_name
lexicon_file_name = data_folder / 'lexicon.txt'
ug_morphemes = data_folder / 'ug_morphemes.txt'
redundancy_rules = data_folder / 'redundancy_rules.txt'
saved_vocabulary_name = test_corpus_name[:-4] + '_saved_vocabulary.txt'
surface_vocabulary_file_name = data_folder / saved_vocabulary_name

# Block 3. Preparations
arguments = set(sys.argv)
if '/images' in arguments:
    Graphic_output = visualizer.Visualizer()
    Graphic_output.image_output = True
    Graphic_output.image_output = False
    Graphic_output.stop_after_each_image = False
    Graphic_output.show_words = False
    Graphic_output.nolabels = False
    Graphic_output.spellout = False
    Graphic_output.case = False
    Graphic_output.show_sentences = False
    if '/slow' in arguments:
        Graphic_output.stop_after_each_image = True
    if '/words' in arguments:
        Graphic_output.show_words = True
    if '/glosses' in arguments:
        Graphic_output.show_glosses = True
    if '/sentences' in arguments:
        Graphic_output.show_sentences = True
    if '/nolabels' in arguments:
        Graphic_output.nolabels = True
    if '/spellout' in arguments:
        Graphic_output.spellout = True
    if '/cases' in arguments:
        Graphic_output.show_cases = True

p = Path(data_folder / 'phrase_structure_images')
try:
    p.mkdir()
except FileExistsError as exc:
    pass

t = time.time()
set_logging(True)
print('Parsing process initialized.')
print(datetime.datetime.now())
print('Loading test sentences from file \"' + str(test_set_name) + '\".')
print(f'Logs will be written to file {log_file_name}.')
print(f'Lexicon will be read from file {lexicon_file_name}.')
print(f'UG morphemes will be read from {ug_morphemes}')
print(f'Redundancy rules from {redundancy_rules}')

grammaticality_judgement = ['', '?', '?', '??', '??', '?*', '?*', '##']
parse_list = []
plus_sentences = []
for line in open(test_set_name):
    if line.startswith('=STOP='):
        break
    line = line.strip()
    if not line or line.startswith('#'):
        continue
    if line.startswith('%'):
        parse_list = []
        line = line.lstrip('%')
        parse_list.append([word.strip() for word in line.split()])
        break
    elif line.startswith('+'):
        plus_sentences.append([word.strip() for word in line.lstrip('+').split()])
    parse_list.append([word.strip() for word in line.split()])
if plus_sentences:
    parse_list = plus_sentences

parsers = {}
lang_guesser = LanguageGuesser(lexicon_file_name)
for language in lang_guesser.languages:
    sentence_context = Context()
    sentence_context.lexicon_file = lexicon_file_name
    sentence_context.ug_morphemes_file = ug_morphemes
    sentence_context.redundancy_rules_file = redundancy_rules
    sentence_context.language = language
    sentence_context.data_folder = data_folder
    parsers[language] = LinearPhaseParser(sentence_context)

logging.basicConfig(level=logging.INFO, handlers=[logging.FileHandler(log_file_name, 'w', 'utf-8')], format='%(message)s')

results_file = open(results_file_name, "w", -1, "utf-8")
results_file.write(str(datetime.datetime.now())+'\n')
results_file.write(f'Test sentences from file \"{test_set_name}\".\n')
results_file.write(f'Logs into file \"{log_file_name}.\n')
results_file.write(f'Lexicon from file \"{lexicon_file_name}\".\n')
grammaticality_judgments_file = open(grammaticality_judgments_file_name, "w", -1, "utf-8")
grammaticality_judgments_file.write(str(datetime.datetime.now())+'\n')
grammaticality_judgments_file.write(f'Test sentences from file \"{test_set_name}\".\n')
grammaticality_judgments_file.write(f'Logs into file \"{log_file_name}.\n')
grammaticality_judgments_file.write(f'Lexicon from file \"{lexicon_file_name}\".\n')

start = 0
count = start
not_parsed = []

# BLock 4. Parsing loop
#-------------------------------------------------------------------------------------------------------
for sentence in parse_list[start:]:
    print('\n' + str(count) + '. ' + f'{sentence}')
    if sentence[0] != '&':
        count = count + 1
        set_logging(True)
        log('\n\n\========================================================================')
        log('# '+str(count))
        log(str(sentence))
        lang = lang_guesser.guess(sentence)
        log(f'Language {lang}')
        P = parsers[lang]
        P.number_of_Merge = 0
        P.number_of_head_Move = 0
        P.number_of_phrasal_Move = 0
        P.number_of_floating_Move = 0
        P.number_of_Transfer = 0
        P.number_of_Agree = 0
        P.number_of_inflectional_features_processed = 0
        P.number_of_items_consumed = 0
        P.discourse_plausibility = 0
        P.score = 0
        P.number_of_solutions_tried = 0
        P.name_provider_index = 0

        #
        P.parse(sentence)
        #

        input_sentence_string = ''
        for word in sentence:
            input_sentence_string = input_sentence_string + word + ' '

        if len(P.result_list) == 0:
            grammaticality_judgments_file.write(str(count) + '. *' + input_sentence_string + '\n')
            results_file.write(str(count) + '. * ' + input_sentence_string + '\n\n')
        else:
            grammaticality_judgments_file.write(str(count) + '.  ' + input_sentence_string + '\n')
            if 0 >= P.score >= -6:
                judgment = grammaticality_judgement[int(round(abs(P.score), 0))]
            else:
                judgment = '##'
            results_file.write(str(count) + '. ' + judgment + input_sentence_string + '\n\n')

            parse_number = 1
            number_of_solutions = len(P.result_list)
            for parse, semantic_interpretation in P.result_list:

                if number_of_solutions == 1:
                    results_file.write('\t' + f'{parse}\n')
                else:
                    results_file.write('\t' + chr(96 + parse_number) + f'. {parse}\n')
                results_file.write(f'\tGarden paths: {P.number_of_solutions_tried-1} (Merge:{P.number_of_Merge}, A-bar/A Move:{P.number_of_phrasal_Move}, Agree:{P.number_of_Agree})\n')
                results_file.write('\tLF_Recovery: ' + str(formatted_output(semantic_interpretation, '\n')))
                results_file.write('\n')
                if '/images' in arguments:
                    file_name = 'Raw image of (' + str(count) + chr(96 + parse_number) + ').png'
                    Graphic_output.file_identifier = data_folder / 'phrase_structure_images' / file_name
                    Graphic_output.input_sentence_string = input_sentence_string
                    Graphic_output.draw(parse)
                parse_number = parse_number + 1

            if '/images' in arguments and Graphic_output.spellout:
                parse_number = 1
                for spellout in P.spellout_result_list:
                    file_name = 'Raw image of (' + str(count) + chr(96 + parse_number) + ')_spellout.png'
                    Graphic_output.file_identifier = data_folder / 'phrase_structure_images' / file_name
                    Graphic_output.draw(spellout)
                    parse_number = parse_number + 1

    else:
        results_file.write(' '.join(map(str, sentence))+' -------------------------------------------------------\n\n')
        grammaticality_judgments_file.write('\n')
        grammaticality_judgments_file.write(' '.join(map(str, sentence)))
        grammaticality_judgments_file.write('\n')
#---------------------------------------------------------------------------------------------------------------#

print(f'took: {time.time() - t}s.')
P.lexicon.save_surface_vocabulary(surface_vocabulary_file_name)