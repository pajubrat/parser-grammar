from local_file_system import LocalFileSystem
from support import is_comment


def run_study():
    """Runs a full study as defined by the input files"""
    lfs = LocalFileSystem()
    speaker_models, sentences_to_parse, language_guesser = lfs.set_up_experiment()
    for index, sentence, experimental_group, part_of_conversation, grammatical in sentences_to_parse:
        if not is_comment(sentence):
            language = language_guesser.guess_language(sentence)
            lfs.print_sentence_to_console(index, sentence)
            speaker_models[language].parse_sentence(index, sentence)
            lfs.save_output(speaker_models[language],
                            index,
                            sentence,
                            experimental_group,
                            part_of_conversation,
                            grammatical)
            if not part_of_conversation:
                speaker_models[language].narrow_semantics.global_cognition.end_conversation()
        else:
            lfs.write_comment_line(sentence)

    if lfs.settings['datatake_full']:
        lfs.save_surface_vocabulary(speaker_models["LANG:EN"].lexicon.surface_lexicon)
    lfs.close_all_output_files()
    lfs.report_errors_to_console()
