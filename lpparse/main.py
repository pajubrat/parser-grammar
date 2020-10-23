import sys
from local_file_system import LocalFileSystem
from log_functions import *
from language_guesser import LanguageGuesser
from support import is_comment
from linear_phase_parser import LinearPhaseParser

def run_study():

    # Prepare file systems and logging
    local_file_system = LocalFileSystem()
    local_file_system.initialize(set(sys.argv))
    configure_logging(local_file_system)

    # Prepare parsers for all languages together with their language-specific lexicons
    parser_for = {}
    lang_guesser = LanguageGuesser(local_file_system.external_sources["lexicon_file_name"])
    for language in lang_guesser.languages:
        parser_for[language] = LinearPhaseParser(local_file_system, language)
        parser_for[language].initialize()

    # Analyze all sentences from the test corpus
    sentence_number = 1
    for sentence in local_file_system.read_test_corpus():
        if not is_comment(sentence):
            language = lang_guesser.guess_language(sentence)
            parser_for[language].parse(sentence_number, sentence)
            local_file_system.save_output(parser_for[language], sentence_number, sentence)
            sentence_number = sentence_number + 1
        else:
            local_file_system.write_comment_line(sentence)

    # Finish processing
    local_file_system.save_surface_vocabulary(parser_for["LANG:EN"].lexicon.surface_vocabulary)
    local_file_system.close_all_output_files()