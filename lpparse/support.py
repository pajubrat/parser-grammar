# This file contains ad hoc support functions
import logging
import time
import datetime
my_log = logging.getLogger(__name__)

major_category = {'N', 'Neg', 'Neg/fin', 'C', 'C/fin', 'P', 'D', 'φ', 'A', 'v', 'V', 'ADV', 'Q', 'NUM', 'T', 'TO/inf', 'VA/inf', 'A/inf', 'MA/A', 'FORCE'}

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
        id = {feature for feature in set if feature[0] == '#'}
        A = {feature for feature in set if feature[:2] == 'PF' or feature[:2] == 'LF'}
        B = {feature for feature in set if 'EF:' in feature or 'EDGE' in feature}
        C = {feature for feature in set if feature in major_category}
        D = {feature for feature in set if feature in {'ARG', '-ARG', 'ASP', 'INF', 'FIN'}}
        E = {feature for feature in set if feature[:3] == 'PHI'}
        F = {feature for feature in set if feature[:3] == 'SEM'}
        G = {feature for feature in set if feature[:4] == 'TAIL'}
        residuum = set - A - B - C - D - E - F - G
        return sorted(A) + \
               sorted(C) + \
               sorted(B) + \
               sorted(D) + \
               sorted(E) + \
               sorted(F) + \
               sorted(G) + \
               sorted(id) + \
               sorted(residuum)

    reply = ''
    if not self.is_primitive():
        reply += show_primitive_constituents(self.left_const)
        reply += show_primitive_constituents(self.right_const)
    else:
        reply += f'\t\t{self.get_phonological_string():<10} {sorted_by_relevance(self.features)}\n'
    return reply

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

def log_result(ps):
    log(f'\n\t\t{ps}')

def illu(set):
    feats = []
    for f in set:
        if isinstance(f, frozenset):
            feats += list(f)
        else:
            feats.append(f)
    return ''.join([f'[{g}]' for g in sorted(feats) if not g.startswith('$')])

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
    return sentence[0] == '&' or sentence[0].startswith("'")