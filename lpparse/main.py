import sys
from local_file_system import LocalFileSystem
from language_guesser import LanguageGuesser
from support import is_comment
from linear_phase_parser import LinearPhaseParser

def run_study(**args):

    print(args)
    folder = args.get('folder', '')
    file = args.get('file', '')
    test_corpus_folder = args.get('test_corpus_folder', '')
    sentence = args.get('sentence', '')

    # Prepare file systems and logging
    local_file_system = LocalFileSystem()
    local_file_system.initialize(folder, file, test_corpus_folder)
    local_file_system.configure_logging()

    # Prepare parsers for all languages together with their language-specific lexicons
    parser_for = {}
    lang_guesser = LanguageGuesser(local_file_system.external_sources["lexicon_file_name"])
    for language in lang_guesser.languages:
        parser_for[language] = LinearPhaseParser(local_file_system, language)
        parser_for[language].initialize()

    # Analyze all sentences from the test corpus (either input sentence or sentences from file)
    if not sentence:
        sentences_to_parse = [(s, e) for (s, e) in local_file_system.read_test_corpus()]
    else:
        sentences_to_parse = [(sentence, '1')]

    sentence_number = 1
    for sentence, experimental_group in sentences_to_parse:
        if not is_comment(sentence):
            language = lang_guesser.guess_language(sentence)
            local_file_system.print_sentence_to_console(sentence_number, sentence)
            parser_for[language].parse(sentence_number, sentence)
            local_file_system.save_output(parser_for[language], sentence_number, sentence, experimental_group)
            sentence_number = sentence_number + 1
        else:
            local_file_system.parse_and_analyze_comment(sentence)
            local_file_system.write_comment_line(sentence)

    # Finish processing
    local_file_system.save_surface_vocabulary(parser_for["LANG:EN"].lexicon.surface_vocabulary)
    local_file_system.close_all_output_files()