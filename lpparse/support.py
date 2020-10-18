# This file contains ad hoc support functions
import logging
import time
import datetime
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

def show(self, start=True, label_only=False):

    s = f'{self.get_cats_string()} = ' if start else ''

    if self.identity != '':
        id_str = ':'+self.identity
    else:
        id_str = ''

    if self.features and 'null' in self.features:
        return s + '__' + id_str
    elif self.is_primitive():
        if not self.get_phonological_string():
            return s + '?'
        else:
            return s + self.get_cats_string()
    elif label_only:
        if self.adjunct:
            return f'{s}{self.get_cats_string()}' + id_str
        else:
            return f'{s}{self.get_cats_string()}' + id_str
    else:
        if self.right_const.adjunct:
            left = show(self.left_const, start=False)
            right = show(self.right_const, start=False, label_only=True)
        else:
            left = show(self.left_const, start=False, label_only=True)
            right = show(self.right_const, start=False)

        return f'{s}[{left} {right}]' + id_str

def show_all_vectors(h):
    if not h.is_primitive():
        return show_all_vectors(h.left_const) + show_all_vectors(h.right_const)
    return f'{h}: {h.feature_vector()};  '

# This function returns the type of pro-element depending on the valuation of (uD, up) probe
# PRO = control pro
# pro/x = antecedent requiring pro
# pro = little-pro
def get_pro_type(self):
    if 'PHI:NUM:_' in self.features and 'PHI:PER:_' in self.features and 'PHI:DET:_' in self.features:
        return '\N{GREEK CAPITAL LETTER PHI}'
    if 'PHI:NUM:_' not in self.features and 'PHI:PER:_' not in self.features and 'PHI:DET:_' in self.features:
        return '\N{GREEK SMALL LETTER PHI}/x'
    return '\N{GREEK SMALL LETTER PHI}'

def show_primitive_constituents(self):
    def sorted_by_relevance(set):
        first_class = {feature for feature in set if feature[:2] == 'PF' or feature[:2] == 'LF'}
        second_class = {feature for feature in set if feature in major_category}
        third_class = {feature for feature in set if feature in {'VAL', '-VAL', 'ARG', '-ARG', 'ASP', 'INF'}}
        fourth_class = {feature for feature in set if feature[:3] == 'PHI'}
        fifth_class = {feature for feature in set if feature[:3] == 'SEM'}
        sixth_class = {feature for feature in set if feature[:4] == 'TAIL'}
        residuum = set - first_class - second_class - third_class - fourth_class - fifth_class - sixth_class
        return sorted(first_class) + \
               sorted(second_class) + \
               sorted(third_class) + \
               sorted(fourth_class) + \
               sorted(fifth_class) + \
               sorted(sixth_class) + \
               sorted(residuum)

    reply = ''
    if not self.is_primitive():
        reply += show_primitive_constituents(self.left_const)
        reply += show_primitive_constituents(self.right_const)
    else:
        reply += f'{self.get_phonological_string():<10} {sorted_by_relevance(self.features)}\n'
    return reply


def report_LF_problem(ps_):
    log('\t\t\tLF-interface condition(s) violated')
    log(show_primitive_constituents(ps_))
    log(show_all_vectors(ps_))
    log('\n\t\tTrying to find other solutions...')


def report_tail_head_problem(ps_):
    log('\t\t\tFinal tail-head check failed.')
    log(show_primitive_constituents(ps_))
    log(show_all_vectors(ps_))
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
    log(f'\t\tSpellout {show(ps)}')

def illu(set):
    feats = []
    for f in set:
        if isinstance(f, frozenset):
            feats += list(f)
        else:
            feats.append(f)
    return ''.join([f'[{g}] ' for g in sorted(feats)])


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

def initialize_console(file_names):
    print('Parsing process initialized.')
    print(datetime.datetime.now())
    print(f'Loading test sentences from {file_names["test_corpus_file_name"]}.')
    print(f'Logs will be written to {file_names["log_file_name"]}.')
    print(f'Lexicon will be read from {file_names["lexicon_file_name"]}.')
    print(f'UG morphemes will be read from {file_names["ug_morphemes"]}')
    print(f'Redundancy will be read from {file_names["redundancy_rules"]}')

def is_comment(sentence):
    return sentence[0] == '&'