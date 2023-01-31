from local_file_system import LocalFileSystem
from language_guesser import LanguageGuesser
from support import is_comment
from linear_phase_parser import LinearPhaseParser


def run_study(args):
    sentence = args.get('sentence', '')

    local_file_system = LocalFileSystem()
    local_file_system.initialize(args)
    local_file_system.configure_logging()

    parser_for = {}
    lang_guesser = LanguageGuesser(local_file_system.external_sources["lexicon_file_name"])
    for language in lang_guesser.languages:
        parser_for[language] = LinearPhaseParser(local_file_system, language)
        parser_for[language].initialize()

    if not sentence:
        sentences_to_parse = [(sentence, group, part_of_conversation)
                              for (sentence, group, part_of_conversation)
                              in local_file_system.read_test_corpus()]
    else:
        sentences_to_parse = [([word.strip() for word in sentence.split()], '1', False)]

    sentence_number = 1
    for sentence, experimental_group, part_of_conversation in sentences_to_parse:
        if not is_comment(sentence):
            language = lang_guesser.guess_language(sentence)
            local_file_system.print_sentence_to_console(sentence_number, sentence, language)
            parser_for[language].parse_sentence(sentence_number, sentence)
            local_file_system.save_output(parser_for[language],
                                          sentence_number,
                                          sentence,
                                          experimental_group,
                                          part_of_conversation)
            if not part_of_conversation:
                parser_for[language].narrow_semantics.global_cognition.end_conversation()
            sentence_number = sentence_number + 1
        else:
            local_file_system.write_comment_line(sentence)

    # Finish processing
    if local_file_system.settings['datatake_full']:
        local_file_system.save_surface_vocabulary(parser_for["LANG:EN"].lexicon.surface_vocabulary)
    local_file_system.close_all_output_files()