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
        A = {feature for feature in set if feature in major_category}
        B = {feature for feature in set if feature[:2] == 'PF' or feature[:2] == 'LF'}
        C = {feature for feature in set if feature == '!SELF:d' or
             feature == '!SELF:p' or
             feature == 'p' or
             feature == 'd' or
             feature.startswith('!EF:') or
             feature.startswith('-EF') or
             feature.startswith('EF') or
             feature.startswith('δPF')}
        D = {feature for feature in set if feature in {'ARG', '-ARG', 'ASP', 'Inf', 'Fin'}}
        E = {feature for feature in set if feature.startswith('TAIL')}
        F = {feature for feature in set if feature[:4] == 'PHI:' or feature[:5] == 'iPHI:' or feature[:4] == 'PHI/' or feature[:5] == 'dPHI:'}
        G = {feature for feature in set if feature[:3] == 'SEM'}
        H = {feature for feature in set if feature[:4] == 'COMP' or feature[:5] == '-COMP' or feature[:5] == '!COMP'}
        J = {feature for feature in set if feature[:4] == 'SPEC' or feature[:5] == '-SPEC' or feature[:5] == '!SPEC'}
        residuum = set - A - B - C - D - E - F - G - H - J
        return sorted(A) + sorted(B) + sorted(C) + sorted(D) + sorted(E) + sorted(F) + sorted(G) + sorted(H) + sorted(J) + sorted(id) + sorted(residuum)

    reply = ''
    if not self.primitive():
        reply += show_primitive_constituents(self.left)
        reply += show_primitive_constituents(self.right)
    else:
        for head in self.get_affix_list():
            if head.find_me_elsewhere:
                break
            reply += f'\t\t{head.get_phonological_string():<10} {show_feature_list(sorted_by_relevance(head.features))}\n'
    return reply
def show_feature_list(lst):
    str = ''
    for feature in lst:
        str += f'[{feature}]'
    return str

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

def secure_copy(ps):
    if ps:
        return ps.copy()
    return None

def is_comment(sentence):
    return sentence[0] == '&' or sentence[0].startswith("'")

def log_solution(brain_model, ps, solution_found):
    if not solution_found:
        log(f'\n\tSemantic interpretation:\n{brain_model.local_file_system.formatted_semantics_output(brain_model.narrow_semantics.semantic_interpretation, brain_model)}')
    ps.tidy_names(1)
    log(f'\n\n\t\tLexical features:\n{show_primitive_constituents(ps)}')
    if not solution_found:
        log('\n\t\tSemantic bookkeeping:')
        log(f'\t\t{brain_model.local_file_system.format_semantic_interpretation(brain_model)}\n')
        log('\t\t-------------------------------------------------------------------------------------------------------------------------------------------------------------------\n')
    log('\n\tChecking if the sentence is ambiguous...\n')

def report_success(brain_model, ps):
    log('\n\t\tAccepted.++\n')
    print('X', end='', flush=True)
    if brain_model.local_file_system.settings['datatake_full']:
        brain_model.local_file_system.simple_log_file.write(f'\n\t{ps} <= accepted')
    if len(brain_model.narrow_semantics.semantic_interpretation['Assignments']) == 0:
        log('\t\tSentence was judged uninterpretable due to lack of legitimate assignments.\n')
    if not brain_model.first_solution_found:
        log(f'\t\tSolution accepted at {brain_model.resources["Total Time"]["n"]}ms stimulus onset.\n')
        brain_model.resources['Mean time per word']['n'] = int(brain_model.resources['Total Time']['n'] / count_words(brain_model.sentence))
    if brain_model.only_first_solution:
        brain_model.exit = True
    brain_model.execution_time_results.append(int((process_time() - brain_model.start_time) * 1000))
    brain_model.result_list.append([ps, brain_model.narrow_semantics.semantic_interpretation])
    brain_model.spellout_result_list.append(ps)
    brain_model.first_solution_found = True
    log_solution(brain_model, ps, brain_model.first_solution_found)
    brain_model.first_solution_found = True

def count_words(sentence):
    sentence_ = []
    for word in sentence:
        word_ = word.split('=')
        sentence_ = sentence_ + word_
    return len(sentence_)

def report_failure(ps):
    log('\n\t\tSOLUTION WAS REJECTED. \n\n')
    log('\t\tMemory dump:\n')
    log(f'{show_primitive_constituents(ps)}')

def log_new_sentence(brain_model, count, lst):
    set_logging(True)
    log('\n------------------------------------------------------------------------------------------------')
    log(f'\n#{count}. {brain_model.local_file_system.generate_input_sentence_string(lst)}')
    log(f'\n{brain_model.sentence}')
    log(f'\n\n\t 1. {brain_model.sentence}\n')
    if brain_model.local_file_system.settings['datatake_full']:
        brain_model.local_file_system.simple_log_file.write(f'\n\n#{count}. {brain_model.local_file_system.generate_input_sentence_string(lst)} / {brain_model.sentence}\n')
