from support import *
import logging

def configure_logging(local_file_system):
    handler = logging.FileHandler(local_file_system.external_sources["log_file_name"], 'w', 'utf-8')
    handler.terminator = ''
    logging.basicConfig(level=logging.INFO, handlers=[handler], format='%(message)s')
    local_file_system.logger_handle = handler
    if 'logging' in local_file_system.settings and not local_file_system.settings['logging']:
        disable_all_logging()  # Disable logging to speed up processing

def log_results(ps_, sentence):
    log('\n\t\t---------------------------------------------------------------------------------------------------------------------------------------------------------------------')
    ps_.tidy_names(1)
    log_result(ps_)
    log('\t\t-----------------------------------------------------------------------------------------------------------------------------------------------------------------------\n')
    log(show_primitive_constituents(ps_))
    log('\n\tChecking if the sentence is ambiguous...\n')