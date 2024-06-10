# This file contains ad hoc support functions
import logging
import time
import datetime
from time import process_time

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

def legitimate_input_sentence(sentence):
    sentence = sentence.strip()
    return not sentence or not sentence.startswith('&') and not sentence.startswith('#') and not sentence.startswith("\'")

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


def comment(line):
    return line.startswith('#')

def gold_standard_grammaticality(line):
    if line.startswith('*'):
        return line.lstrip('*'), False
    return line, True

def clear_line_end(line):
    if line.endswith(';'):
        line = line.rstrip(';')
    elif line.endswith('.'):
        line = line.rstrip('.')
    return line

def extract_key_and_value(line):
    line = line.strip().replace('\t', '')
    if not comment(line) and '=' in line:
        key, value = line.split('=')
        key = key.strip()
        value = value.strip()
        return key, value
    return None, None


def log(text):
    if log_instance.logging and not log_instance.disabled:
        if text.startswith('\n'):
            text2 = '\n' + '\t'*log_instance.indent_level + text[1:]
        else:
            text2 = text
        my_log.info(text2)
        log_instance.operations += 1
        if log_instance.use_buffer:
            log_instance.buffer.append(text2)

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

def secure_copy(ps):
    if ps:
        return ps.copy()
    return None

def is_comment(sentence):
    return sentence[0] == '&' or sentence[0].startswith("'")

def log_new_sentence(brain_model, count, lst):
    set_logging(True)
    log('\n------------------------------------------------------------------------------------------------')
    log(f'\nSentence #{count}. {" ".join(lst)}')
    log(f'\n\n\tPhonological words: {brain_model.sentence}')