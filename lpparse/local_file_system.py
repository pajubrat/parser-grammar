import itertools
import sys

from datetime import datetime
from support import *
import logging
from support import feature_explanations
from tkinter import filedialog

def explanation(feature):
    for key in feature_explanations.keys():
        if key in feature:
            return feature_explanations[key]
    return ''

class LocalFileSystem:
    def __init__(self):
        self.test_corpus = None
        self.study_folder = None
        self.external_sources = {}
        self.results_file = None
        self.simple_log_file = None
        self.errors = None
        self.numeration_output = None
        self.resources_file = None
        self.visualizer = None
        self.settings = {}
        self.dev_log_file = None
        self.logger_handle = None
        self.app_settings = {}
        self.instruction_to_ignore_from_test_corpus = False
        self.encoding = 'utf8'
        self.initialize_dev_logging()

    def initialize_output_files(self, settings):
        self.dev_log_file.write('Initializing output files for writing...')
        self.configure_logging(settings)
        self.initialize_results_file(settings)
        self.initialize_resources_file(settings)
        self.initialize_error_file(settings)
        self.initialize_simple_log_file(settings)
        if settings.retrieve('use_numeration', False):
            self.initialize_numeration_output(settings)
        self.dev_log_file.write('Done.\n')

    def initialize_simple_log_file(self, settings):
        self.simple_log_file = open(settings.external_sources['simple_log_file'], 'w', -1, encoding=self.encoding)

    def initialize_error_file(self, settings):
        self.errors = open(settings.external_sources['error_report_name'], 'w', -1, encoding=self.encoding)
        self.stamp(self.errors, settings)

    def initialize_numeration_output(self, settings):
        self.numeration_output = open(settings.external_sources['numeration_output'], 'w', -1, encoding=self.encoding)
        self.numeration_output.write(f'# Corpus generated from the numeration in {self.external_sources["numeration"]}\n')

    def initialize_dev_logging(self):
        self.dev_log_file = open('dev_log.txt', 'w', -1, 'utf-8')
        self.dev_log_file.write(f'Devlogging started at {datetime.datetime.now()}.\n')

    def process_numeration(self, settings):
        self.dev_log_file.write(f'Processing numeration from {settings.external_sources["numeration"]} into {settings.external_sources["numeration_output"]}...')
        self.dev_log_file.write('\nNumerations')
        for line in open(settings.external_sources["numeration"], encoding=self.encoding):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            numeration = [x.strip() for x in line.split(',')]
            self.dev_log_file.write(f'\n{numeration}')
            permutations = list(itertools.permutations(numeration))
            for p in permutations:
                if not p[0].startswith('#'):
                    self.numeration_output.write('\n\t')
                    for w in p:
                        if not w.startswith('#'):
                            self.numeration_output.write(' ')
                        self.numeration_output.write(f'{w}')
        self.dev_log_file.write('\n')
        self.numeration_output.close()
        self.dev_log_file.write(f'were used to generate a corpus {self.external_sources["numeration_output"]}.\n')
        self.dev_log_file.write(f'^ This corpus will be used in the processing.\n')

    def initialize_results_file(self, settings):
        self.dev_log_file.write('Initializing results file...')
        self.results_file = open(settings.external_sources['results_file_name'], "w", -1, encoding=self.encoding)
        self.stamp(self.results_file, settings)

    def initialize_resources_file(self, settings):
        self.dev_log_file.write('Initializing resources file...')
        self.resources_file = open(settings.external_sources["resources_file_name"], "w", -1, encoding=self.encoding)

    def add_columns_to_resources_file(self, resources, experimental_groups):
        self.dev_log_file.write('Add columns to the resources file...')
        self.resources_file.write("Number,Sentence,Study_ID,")
        if experimental_groups:
            for index, group in enumerate(experimental_groups):
                self.resources_file.write(f"Group {index},")
        else:
            self.resources_file.write('Group,')
        for key in resources:
            self.resources_file.write(f'{key},')
        self.resources_file.write("Execution time (ms)\t\n")

    def save_app_settings(self, settings):
        """Save the app settings for the next session before closing the application"""
        # settings.app_settings['open_with'] = settings.folders['study'] / 'config_study.lpg'     # store the location of current dataset
        try:
            with open('$app_settings.txt', 'w', encoding=self.encoding) as output_file:
                output_file.write(f'file_study_configuration={self.settings["file_study_configuration"]}')
                output_file.write(f'file_study_folder={self.settings["file_study_folder"]}')
                for key, value in settings.app_settings.items():
                    output_file.write(f'{key}={value}\n')
        except IOError:
            pass

    def read_app_settings(self, arg_lst):
        """Loads application settings which provides the default behavior"""
        app_settings_dict = {}
        try:
            app_settings_file = open('$app_settings.txt', encoding=self.encoding)
            readlines = app_settings_file.readlines()
            for line in readlines:
                if '=' in line:
                    key, value = line.split('=')
                    key = key.strip()
                    value = value.strip()
                    app_settings_dict[key] = value
        except IOError:
            print(f'Could not find the application settings file $app_settings.txt.')
            print(f'Make sure this file exists in the root directory.')
            sys.exit()

        for arg in arg_lst:
            if arg.endswith('.lpg'):
                app_settings_dict['open_with'] = arg
        return app_settings_dict

    def load_settings(self, settings):
        if 'full_name' not in settings.data:
            name = settings.retrieve('file_study_configuration', '')
            folder = settings.retrieve('file_study_folder', '')
            settings.data['full_name'] = folder + '/' + name
        try:
            config_file = open(settings.retrieve('full_name'), encoding=self.encoding)
            for line in config_file:
                line = line.strip().replace('\t', '')
                if line and not line.startswith('#'):
                    key, value = line.split('=')
                    key = key.strip()
                    value = value.strip()
                    if key in settings.data and key != 'file_study_configuration' and key != 'file_study_folder':
                        settings.data[key] += '; ' + value      #   New values are added
                    else:
                        settings.data[key] = value
        except IOError:
            print(f'The application settings ($app_settings.txt) points to\n '
                  f'the study configuration file {settings.retrieve("full_name")},\n'
                  f'but the file does not seem to exist.')
            sys.exit()
        config_file.close()

    def create_new_from_corpus_file(self, settings):
        corpus_filename = filedialog.askopenfilename(title='Create new study from corpus file', defaultextension='.txt', initialdir='./language data working directory')
        settings.create_settings_for_file_system(corpus_filename)

    def save_study(self, settings):
        filename = filedialog.asksaveasfilename(title='Save study', defaultextension='.txt', initialdir='.')
        if filename:
            try:
                with open(filename, 'w', encoding=self.encoding) as f:
                    for key in settings.data.keys():
                        value = settings.retrieve(key, '')
                        f.write(f'{str(key)} = {str(value)}\n')
            except IOError:
                print(f'Saving the study was unsuccessful.')
                sys.exit()

    def read_test_corpus(self, settings):
        experimental_group = []
        parse_list = []
        if settings.retrieve('use_numeration', False):
            k = open(settings.external_sources['numeration_output'], encoding=self.encoding)
            input_file = settings.external_sources["numeration_output"]
        else:
            input_file = settings.data['file_study_folder'] + '/' + settings.data['file_test_corpus']
        self.dev_log_file.write(f'Reading test corpus file {input_file}...')
        index = 1
        try:
            for line in open(input_file, encoding=self.encoding):
                part_of_conversation = False
                line = line.strip()
                if line.startswith('=STOP=') or line.startswith('=END='):
                    break
                if line.startswith('=START=') or line.startswith('=BEGIN='):
                    parse_list = []
                    continue
                if not line or line.startswith('#'):
                    continue
                if line.startswith('%'):
                    parse_list = []
                    line = line.lstrip('%')
                    line = line.strip()
                    line = self.clear_line_end(line)
                    line, grammatical = self.gold_standard_grammaticality(line)
                    parse_list.append((index, [word.strip() for word in line.split()], experimental_group, part_of_conversation, grammatical))
                    break
                if line.endswith(';'):
                    part_of_conversation = True
                    line = self.clear_line_end(line)
                if line.endswith('.'):
                    part_of_conversation = False
                    line = self.clear_line_end(line)
                elif line.startswith('=>'):
                    experimental_group = self.read_experimental_group(line)
                    continue
                line, grammatical = self.gold_standard_grammaticality(line)
                if line.startswith('&') or line.startswith("\'"):
                    parse_list.append((None, [word.strip() for word in line.split()], experimental_group, part_of_conversation, grammatical))
                else:
                    parse_list.append((index, [word.strip() for word in line.split()], experimental_group, part_of_conversation, grammatical))
                    index += 1
            self.dev_log_file.write(f'Found {len(parse_list)} sentences. Done.\n')
            return parse_list
        except IOError:
            print(f'The corpus file "{input_file}" seems to be missing.\n'
                  f'Make sure that the file exists and that the name is correct.')
            sys.exit()

    def gold_standard_grammaticality(self, line):
        if line.startswith('*'):
            line = line.lstrip('*')
            return line, False
        else:
            return line, True

    def clear_line_end(self, line):
        if line.endswith(';'):
            line = line.rstrip(';')
        elif line.endswith('.'):
            line = line.rstrip('.')
        return line

    def read_experimental_group(self, line):
        line = line.strip().replace(' ', '').replace('=>', '')
        return line.split('.')

    def stamp(self, file_handle, settings):
        file_handle.write(self.stamp_string(settings))

    def stamp_string(self, settings):
        stri = ''
        stri += f'@  Simulation parameters: {settings.data}\n'
        stri += f'@  Time: {datetime.datetime.now()}\n'
        stri += f'@  Test sentences: {settings.external_sources["test_corpus_file_name"]}\n'
        stri += f'@  Logs: {settings.external_sources["log_file_name"]}\n\n\n'
        return stri

    def save_output(self, speaker_model, count, sentence, experimental_group, grammatical):
        self.results_file.write(f'#{count}. {speaker_model.results}')
        self.save_resources(speaker_model, count, " ".join(sentence), experimental_group)
        self.save_errors(speaker_model, count, sentence, grammatical)
        self.save_simple_log(speaker_model)

    def save_simple_log(self, speaker_model):
        for step in speaker_model.results.recorded_steps:
            self.simple_log_file.write(f'{step[0]}. {step[1]} ({step[2]})\n')

    def save_errors(self, speaker_model, count, sentence, grammatical):
        if len(speaker_model.results.syntax_semantics) > 0 and not grammatical or len(speaker_model.results.syntax_semantics) == 0 and grammatical:
            r = f"\n{str(count)}. {' '.join(sentence)}"
            self.errors.write(r)

    def save_resources(self, parser, count, sentence, experimental_group):
        if count == 1:
            self.add_columns_to_resources_file(parser.results.resources, experimental_group)
        self.resources_file.write(str(count) + ',')
        self.resources_file.write(f'{sentence},')
        self.resources_file.write(f'{self.settings.get("study_id", "0")},')
        self.resources_file.write(','.join(experimental_group))
        self.resources_file.write(',')
        if len(parser.results.syntax_semantics) > 0:
            for key in parser.results.resources:
                self.resources_file.write(f'{parser.results.resources[key]["n"]},')
        self.resources_file.write('\n')

    def write_comment_line(self, sentence_lst):
        if sentence_lst[0].startswith("'"):
            prefix = '\t'
        else:
            prefix = ''
        self.results_file.write(prefix + ' '.join(map(str, sentence_lst)) + '\n\n')

    def close_all_output_files(self):
        self.dev_log_file.write('Closing all output files...')
        self.results_file.close()
        self.resources_file.close()
        self.logger_handle.close()
        self.errors.close()
        self.dev_log_file.write('Done.\n')

    def configure_logging(self, settings):
        handler = logging.FileHandler(settings.external_sources["log_file_name"], 'w', 'utf-8')
        handler.terminator = ''
        logging.basicConfig(level=logging.INFO, handlers=[handler], format='%(message)s')
        self.logger_handle = handler
        if not settings.retrieve('general_parameter_logging', True):
            disable_all_logging()
        log(self.stamp_string(settings))

    def read_lexicons_into_dictionary(self, settings):
        lexicon_dict = {}

        # Examine all lexical files and the lexical redundancy file
        for lexicon_file in [file.strip() for file in settings.retrieve('file_lexicons', '').split(';')] + \
                            [file.strip() for file in settings.retrieve('file_redundancy_rules', '').split(';')]:
            lexicon_dict[lexicon_file] = {}

            # Example all lines in each file
            lexical_entries = open(settings.folders['lexicon'] / lexicon_file, encoding='utf8').readlines()

            # Break every line into (key, features) and then examine all features
            for lex, features in [e.strip().split('::') for e in lexical_entries if '::' in e]:

                lex = lex.strip()
                features = features.strip()
                features = features.replace('\t', ' ')
                lexicon_dict[lexicon_file][lex] = {}
                # Examine each feature
                feature_list = []
                for feature in features.strip().split(' '):
                    feature = feature.strip()
                    if feature:
                        feature_list.append(feature)
                        lexicon_dict[lexicon_file][lex][feature] = explanation(feature)
        return lexicon_dict
