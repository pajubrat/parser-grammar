from support import *
import logging

def configure_logging(local_file_system):
    logging.basicConfig(level=logging.INFO, handlers=[logging.FileHandler(local_file_system.external_sources["log_file_name"], 'w', 'utf-8')], format='%(message)s')

def log_sentence(count, sentence):
    log('\n\n\========================================================================')
    log('# ' + str(count))
    log(str(sentence))

def log_results(ps_, sentence):
    log('----------------------------------------------------------------------------------------------------------')
    log('                                              All tests passed                                           ')
    log('----------------------------------------------------------------------------------------------------------')
    ps_.tidy_names(1)
    log_result(ps_)
    log('----------------------------------------------------------------------------------------------------------')
    log(show_primitive_constituents(ps_))
    log(show_all_vectors(ps_))
    log('\t\t\tChecking if the sentence is ambiguous...')