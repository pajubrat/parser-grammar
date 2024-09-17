import itertools
import sys
from datetime import datetime
from support import *
from language_data import LanguageData
import logging
from tkinter import filedialog

class LocalFileSystem:
    def __init__(self, application):
        self.application = application
        self.root_settings = {}
        self.external_sources = {}
        self.encoding = 'utf-8'
        self.file_handle = {}
        self.output_files = ['simple log', 'results', 'resources', 'errors', 'descriptive', 'numeration output']

    def initialize_output_files(self):
        self.configure_logging()
        for output_file in self.output_files:
            self.open_output_file(output_file)

    def open_output_file(self, filename):
        self.file_handle[filename] = open(self.application.settings.external_sources[filename], 'w', 1, encoding=self.encoding)
        self.stamp(self.file_handle[filename])

    def save_app_settings(self):
        output_file = open('$app_settings.txt', 'w', encoding=self.encoding)
        output_file.write(f'file_study_configuration={self.application.settings["file_study_configuration"]}')
        output_file.write(f'file_study_folder={self.application.settings["file_study_folder"]}')
        for key, value in self.application.settings.app_settings.items():
            output_file.write(f'{key}={value}\n')

    def read_app_settings(self, argument_lst):
        try:
            for line in open('$app_settings.txt', encoding=self.encoding):
                if '=' in line:
                    key, value = line.split('=')
                    self.root_settings[key.strip()] = value.strip()
        except IOError:
            print(f'Could not find the application settings file $app_settings.txt.')
            print(f'Make sure this file exists in the root directory.')
            sys.exit()
        for arg in argument_lst:
            if arg.endswith('.lpg'):
                self.root_settings['open_with'] = arg

    def load_settings(self):
        settings = {}
        if 'full_name' not in self.root_settings:
            name = self.root_settings.get('file_study_configuration', '')
            folder = self.root_settings.get('file_study_folder', '')
            self.root_settings['full_name'] = folder + '/' + name
        try:
            for line in open(self.root_settings['full_name'], encoding=self.encoding):
                line = line.strip().replace('\t', '')
                if line and not line.startswith('#'):
                    key, value = line.split('=')
                    key = key.strip()
                    value = value.strip()
                    if key in self.root_settings and key != 'file_study_configuration' and key != 'file_study_folder':
                        settings[key] += '; ' + value      #   New values are added
                    else:
                        settings[key] = value
        except IOError:
            print(f'The application settings ($app_settings.txt) points to\n '
                  f'the study configuration file {self.application.settings.retrieve("full_name")},\n'
                  f'but the file does not seem to exist.')
            sys.exit()
        return settings

    def create_new_from_corpus_file(self):
        corpus_filename = filedialog.askopenfilename(title='Create new study from corpus file',
                                                     defaultextension='.txt',
                                                     initialdir='./language data working directory')
        self.application.settings.create_settings_for_file_system(corpus_filename)

    def save_study(self):
        filename = filedialog.asksaveasfilename(title='Save study',
                                                defaultextension='.txt',
                                                initialdir='.')
        if filename:
            try:
                with open(filename, 'w', encoding=self.encoding) as f:
                    for key in self.application.settings.data.keys():
                        value = self.application.settings.retrieve(key, '')
                        f.write(f'{str(key)} = {str(value)}\n')
            except IOError:
                print(f'Saving the study was unsuccessful.')
                sys.exit()

    def read_test_corpus(self):
        input_data = LanguageData()
        cont = True
        input_file = self.application.settings.data['file_study_folder'] + '/' + self.application.settings.data['file_test_corpus']
        if self.application.settings.retrieve('use_numeration', False):
            input_file = self.application.settings.external_sources["numeration output"]
        index = 0
        try:
            for line in open(input_file, encoding=self.encoding):
                part_of_conversation = False
                line = line.strip()
                if line.startswith('STOP') or line.startswith('END'):
                    break
                if not line or line.startswith('#') or line.startswith("\'") or line.startswith('&'):
                    continue
                if line.startswith('BEGIN'):
                    input_data.reset()
                    index = 0
                    continue
                if line.startswith('%'):
                    # We take only this line
                    index = 0
                    cont = False                #   This will break out of the loop once next sentence is detected
                    line = line.lstrip('%')
                    line = line.strip()
                    line = clear_line_end(line)
                    input_data.reset()          #   Empty the input data stored thus far; the new item is added below
                if line.endswith(';'):
                    part_of_conversation = True
                    line = clear_line_end(line)
                if line.endswith('.'):
                    part_of_conversation = False
                    line = clear_line_end(line)
                if line.startswith('¦->') and len(line.split(':')) == 2:
                    line = line.lstrip('¦->')
                    field, value = line.split(':')
                    input_data.update(index, {field.strip(): value.strip()})
                    continue
                index += 1
                if not cont and index > 1:
                    break
                input_data.add(self.create_data_from_line(line, index, part_of_conversation))
            return input_data
        except IOError:
            print(f'The corpus file "{input_file}" seems to be missing.\n'
                  f'Make sure that the file exists and that the name is correct.')
            sys.exit()

    def create_data_from_line(self, line, index, part_of_conversation):
        line, grammatical = gold_standard_grammaticality(line)
        return {'index': index,
                'expression': line.strip(),
                'word_list': [word.strip() for word in line.split()],
                'grammaticality': grammatical,
                'experimental_group': '1',
                'part_of_conversation': part_of_conversation}

    def read_experimental_group(self, line):
        line = line.strip().replace(' ', '').replace('=>', '')
        return line.split('.')

    def stamp(self, file_handle):
        file_handle.write(self.stamp_string())

    def stamp_string(self):
        stri = f'@  Simulation parameters: {self.application.settings.data}\n'
        stri += f'@  Time: {datetime.datetime.now()}\n'
        stri += f'@  Test sentences: {self.application.settings.external_sources["test_corpus_file_name"]}\n'
        stri += f'@  Logs: {self.application.settings.external_sources["log_file_name"]}\n\n\n'
        return stri

    def save_output(self, speaker_model, data_dict):
        self.file_handle['results'].write(f'#{data_dict["index"]}. {speaker_model.results}')
        self.save_resources(speaker_model, data_dict["index"], data_dict["expression"], data_dict["experimental_group"])
        self.save_errors(speaker_model, data_dict)
        self.save_simple_log(speaker_model)

    def close_all_output_files(self):
        for key, file_ in self.file_handle.items():
            file_.close()

    def save_simple_log(self, speaker_model):
        for step in speaker_model.results.recorded_steps:
            self.file_handle['simple log'].write(f'{step[0]}. {step[1]} ({step[2]})\n')

    def save_errors(self, speaker_model, data_item):
        if len(speaker_model.results.syntax_semantics) > 0 and not data_item["grammaticality"] or len(speaker_model.results.syntax_semantics) == 0 and data_item["grammaticality"]:
            r = f'\n{data_item["index"]}. {data_item["expression"]}'
            self.file_handle['errors'].write(r)
        for key in data_item.keys():
            if key in speaker_model.results.output_fields:
                if data_item[key] != ','.join(speaker_model.results.output_fields[key]):
                    r = f'\n{data_item["index"]}. {data_item["expression"]} ({key})\n\n\tPredicted:\t\t{data_item[key]}\n\tOutcome:\t\t{",".join(speaker_model.results.output_fields[key])}\n\n'
                    self.file_handle['descriptive'].write(r)

    def save_resources(self, speaker_model, count, sentence, experimental_group):
        if count == 1:
            self.add_columns_to_resources_file(speaker_model.results.resources, experimental_group)
        self.file_handle['resources'].write(f'{str(count)},{sentence},{",".join(experimental_group)},')
        if len(speaker_model.results.syntax_semantics) > 0:
            for key in speaker_model.results.resources:
                self.file_handle['resources'].write(f'{speaker_model.results.resources[key]["n"]},')
        self.file_handle['resources'].write('\n')

    def write_comment_line(self, sentence_lst):
        if sentence_lst[0].startswith("'"):
            prefix = '\t'
        else:
            prefix = ''
        self.file_handle['resources'].write(prefix + ' '.join(map(str, sentence_lst)) + '\n\n')

    def configure_logging(self):
        handler = logging.FileHandler(self.application.settings.external_sources["log_file_name"], 'w', 'utf-8')
        handler.terminator = ''
        logging.basicConfig(level=logging.INFO, handlers=[handler], format='%(message)s')
        self.logger_handle = handler
        if not self.application.settings.retrieve('general_parameter_logging', True):
            disable_all_logging()
        log(self.stamp_string())

    def add_columns_to_resources_file(self, resources, experimental_groups):
        self.file_handle['resources'].write("Number,Sentence,")
        if experimental_groups:
            for index, group in enumerate(experimental_groups):
                self.file_handle['resources'].write(f"Group {index},")
        else:
            self.file_handle['resources'].write('Group,')
        for key in resources:
            self.file_handle['resources'].write(f'{key},')
        self.file_handle['resources'].write("Execution time (ms)\t\n")

    def read_lexicons_into_dictionary(self):
        lexicon_dict = {}
        for lexicon_file in [file.strip() for file in self.application.settings.retrieve('file_lexicons', '').split(';')] + \
                            [file.strip() for file in self.application.settings.retrieve('file_redundancy_rules', '').split(';')]:
            lexicon_dict[lexicon_file] = {}
            lexical_entries = open(self.application.settings.folders['lexicon'] / lexicon_file, encoding='utf8').readlines()
            for lex, features in [e.strip().split('::') for e in lexical_entries if '::' in e]:
                lexicon_dict[lexicon_file][lex] = {}
        return lexicon_dict

    def process_numeration(self):
        for line in open(self.application.settings.external_sources["numeration"], encoding=self.encoding):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            numeration = [x.strip() for x in line.split(',')]
            permutations = list(itertools.permutations(numeration))
            for p in permutations:
                if not p[0].startswith('#'):
                    self.file_handle['numeration output'].write('\n\t')
                    for w in p:
                        if not w.startswith('#'):
                            self.file_handle['numeration output'].write(' ')
                        self.file_handle['numeration output'].write(f'{w}')
        self.file_handle['numeration output'].close()