from local_file_system import LocalFileSystem
from language_guesser import LanguageGuesser
from support import is_comment
from speaker_model import SpeakerModel


def run_study(args):
    sentence = args.get('sentence', '')
    local_file_system = LocalFileSystem()
    local_file_system.initialize(args)
    local_file_system.configure_logging()

    speaker_model = {}
    language_guesser = LanguageGuesser(local_file_system.external_sources["lexicon_file_name"])
    for language in language_guesser.languages:
        speaker_model[language] = SpeakerModel(local_file_system, language)
        speaker_model[language].initialize()

    if not sentence:
        sentences_to_parse = [(sentence, group, part_of_conversation, grammatical)
                              for (sentence, group, part_of_conversation, grammatical)
                              in local_file_system.read_test_corpus()]
    else:
        sentences_to_parse = [([word.strip() for word in sentence.split()], '1', False, True)]

    sentence_number = 1
    for sentence, experimental_group, part_of_conversation, grammatical in sentences_to_parse:
        if not is_comment(sentence):
            language = language_guesser.guess_language(sentence)
            local_file_system.print_sentence_to_console(sentence_number, sentence, language)
            speaker_model[language].parse_sentence(sentence_number, sentence)
            local_file_system.save_output(speaker_model[language],
                                          sentence_number,
                                          sentence,
                                          experimental_group,
                                          part_of_conversation,
                                          grammatical)
            if not part_of_conversation:
                speaker_model[language].narrow_semantics.global_cognition.end_conversation()
            sentence_number = sentence_number + 1
        else:
            local_file_system.write_comment_line(sentence)

    # Finish processing
    if local_file_system.settings['datatake_full']:
        local_file_system.save_surface_vocabulary(speaker_model["LANG:EN"].lexicon.surface_lexicon)
    local_file_system.close_all_output_files()
    local_file_system.report_errors_to_console()
