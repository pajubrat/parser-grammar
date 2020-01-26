# This file contains ad hoc support functions
import logging
import time
my_log = logging.getLogger(__name__)

major_category = {'N', 'P', 'D', 'C/fin', 'T/fin', 'A', 'v', 'V', 'ADV', 'Q', 'NUM'}


class Logger:
    def __init__(self):
        self.logging = True
        self.use_buffer = False
        self.buffer = []
        self.colors = True
        self.operations = 0
        self.disabled = 0
        self.indent_level = 0


log_instance = Logger()


def show_results(ps_, result_list, semantic_interpretation):
    log('----------------------------------------------------------------------------------------------------------')
    log(f'                                              All tests passed                                           ')
    log('----------------------------------------------------------------------------------------------------------')
    ps_.tidy_names(1)
    print(chr(96 + len(result_list)) + '. ' + ps_.show())
    print(f'{ps_}')
    print(ps_.illustrate())
    print(str(semantic_interpretation))
    # print(str(number_of_Merges) + ', Moves: ' + str(number_of_Moves)
    #      + ', Solutions tried: ' + str(number_of_solutions_tried) + '\n')
    log_result(ps_)
    log('----------------------------------------------------------------------------------------------------------')
    log(ps_.show_primitive_constituents())
    log(ps_.show_all_vectors())
    log('\t\t\tChecking if the sentence is ambiguous...')


def report_LF_problem(ps_):
    log('\t\t\tLF-interface condition(s) violated')
    log(ps_.show_primitive_constituents())
    log(ps_.show_all_vectors())
    log('\n\t\tTrying to find other solutions...')


def report_tail_head_problem(ps_):
    log('\t\t\tFinal tail-head check failed.')
    log(ps_.show_primitive_constituents())
    log(ps_.show_all_vectors())
    log('\t\t\tLet\'s find another solution...\n.\n.\n.')


def log(text):
    if log_instance.logging and not log_instance.disabled:
        my_log.info(text)
        log_instance.operations += 1
        if log_instance.use_buffer:
            log_instance.buffer.append(text)


def disable_logging():
    log_instance.disabled += 1


def is_logging_enabled():
    if log_instance.disabled == 0:
        return True
    else:
        return False


def enable_logging():
    log_instance.disabled -= 1
    if log_instance.disabled < 0:
        log_instance.disabled = 0


def indent_log():
    log_instance.indent_level += 1


def unindent_log():
    log_instance.indent_level -= 1


def set_intent_level(level):
    log_instance.indent_level = level


def disable_all_logging():
    log_instance.disabled = True


def get_log_buffer():
    return log_instance.buffer


def clear_log_buffer():
    log_instance.buffer = []


def set_log_buffering(value):
    log_instance.use_buffer = value


def get_number_of_operations():
    return log_instance.operations


def reset_number_of_operations():
    log_instance.operations = 0


def set_logging(value):
    log_instance.logging = value


def is_logging():
    return log_instance.logging


def log_color(text, color_code):
    if log_instance.logging:
        if log_instance.colors:
            my_log.info(f'\033[1{color_code}m{text}\033[0m')
        else:
            my_log.info(text)


def log_bold(text):
    log_color(text, '')


def log_red(text):
    log_color(text, ';31')


def log_blue(text):
    log_color(text, ';34')


def log_cyan(text):
    log_color(text, ';36')


def log_result(ps):

    log('\t\tSolution:')
    log(f'\t\t{ps.illustrate()}')
    log(f'\t\tGrammar: {ps}')
    log(f'\t\tSpellout {ps.show()}')


def illu(set):
    feats = []
    for f in set:
        if isinstance(f, frozenset):
            feats += list(f)
        else:
            feats.append(f)
    return ''.join([f'[{g}]' for g in sorted(feats)])


def time_me(function):
    """ Print out the duration in ms it takes to run this function.
    You know, for debugging!
    :param function:
    :return:
    """

    def wrap(*arg, **kwargs):
        """

        :param arg:
        :param kwargs:
        :return:
        """
        start = time.time()
        r = function(*arg, **kwargs)
        end = time.time()
        print("%s (%0.3f ms) at %s" % (function.__name__, (end - start) * 1000, function.__module__))
        return r

    return wrap
