from support import *

def log_sentence(count, sentence, lang):
    log('\n\n\========================================================================')
    log('# ' + str(count))
    log(str(sentence))
    log(f'Language {lang}')

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