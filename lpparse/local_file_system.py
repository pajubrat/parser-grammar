import itertools
import sys
from datetime import datetime
from support import *
import logging
from tkinter import filedialog

class LocalFileSystem:
    def __init__(self):
        self.external_sources = {}
        self.encoding = 'utf-8'
        self.file_handle = {}
        self.output_files = ['simple log', 'results', 'resources', 'errors', 'numeration output']

    def initialize_output_files(self, settings):
        self.configure_logging(settings)
        for output_file in self.output_files:
            self.open_output_file(output_file, settings)

    def open_output_file(self, filename, settings):
        self.file_handle[filename] = open(settings.external_sources[filename], 'w', 1, encoding=self.encoding)
        self.stamp(self.file_handle[filename], settings)

    def save_app_settings(self, settings):
        output_file = open('$app_settings.txt', 'w', encoding=self.encoding)
        output_file.write(f'file_study_configuration={settings["file_study_configuration"]}')
        output_file.write(f'file_study_folder={settings["file_study_folder"]}')
        for key, value in settings.app_settings.items():
            output_file.write(f'{key}={value}\n')

    def read_app_settings(self, argument_lst):
        app_settings_dict = {}
        try:
            for line in open('$app_settings.txt', encoding=self.encoding):
                if '=' in line:
                    key, value = line.split('=')
                    app_settings_dict[key.strip()] = value.strip()
        except IOError:
            print(f'Could not find the application settings file $app_settings.txt.')
            print(f'Make sure this file exists in the root directory.')
            sys.exit()

        for arg in argument_lst:
            if arg.endswith('.lpg'):
                app_settings_dict['open_with'] = arg

        return app_settings_dict

    def load_settings(self, settings):
        if 'full_name' not in settings.data:
            name = settings.retrieve('file_study_configuration', '')
            folder = settings.retrieve('file_study_folder', '')
            settings.data['full_name'] = folder + '/' + name
        try:
            for line in open(settings.retrieve('full_name'), encoding=self.encoding):
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

    def create_new_from_corpus_file(self, settings):
        corpus_filename = filedialog.askopenfilename(title='Create new study from corpus file',
                                                     defaultextension='.txt',
                                                     initialdir='./language data working directory')
        settings.create_settings_for_file_system(corpus_filename)

    def save_study(self, settings):
        filename = filedialog.asksaveasfilename(title='Save study',
                                                defaultextension='.txt',
                                                initialdir='.')
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
        input_file = settings.data['file_study_folder'] + '/' + settings.data['file_test_corpus']
        if settings.retrieve('use_numeration', False):
            input_file = settings.external_sources["numeration output"]
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
                    line = clear_line_end(line)
                    line, grammatical = gold_standard_grammaticality(line)
                    parse_list.append((index, [word.strip() for word in line.split()], experimental_group, part_of_conversation, grammatical))
                    break
                if line.endswith(';'):
                    part_of_conversation = True
                    line = clear_line_end(line)
                if line.endswith('.'):
                    part_of_conversation = False
                    line = clear_line_end(line)
                elif line.startswith('=>'):
                    experimental_group = self.read_experimental_group(line)
                    continue
                line, grammatical = gold_standard_grammaticality(line)
                if line.startswith('&') or line.startswith("\'"):
                    parse_list.append((None, [word.strip() for word in line.split()], experimental_group, part_of_conversation, grammatical))
                else:
                    parse_list.append((index, [word.strip() for word in line.split()], experimental_group, part_of_conversation, grammatical))
                    index += 1
            return parse_list
        except IOError:
            print(f'The corpus file "{input_file}" seems to be missing.\n'
                  f'Make sure that the file exists and that the name is correct.')
            sys.exit()

    def read_experimental_group(self, line):
        line = line.strip().replace(' ', '').replace('=>', '')
        return line.split('.')

    def stamp(self, file_handle, settings):
        file_handle.write(self.stamp_string(settings))

    def stamp_string(self, settings):
        stri = f'@  Simulation parameters: {settings.data}\n'
        stri += f'@  Time: {datetime.datetime.now()}\n'
        stri += f'@  Test sentences: {settings.external_sources["test_corpus_file_name"]}\n'
        stri += f'@  Logs: {settings.external_sources["log_file_name"]}\n\n\n'
        return stri

    def save_output(self, speaker_model, count, sentence, experimental_group, grammatical):
        self.file_handle['results'].write(f'#{count}. {speaker_model.results}')
        self.save_resources(speaker_model, count, " ".join(sentence), experimental_group)
        self.save_errors(speaker_model, count, sentence, grammatical)
        self.save_simple_log(speaker_model)

    def close_all_output_files(self):
        for key, file_ in self.file_handle.items():
            file_.close()

    def save_simple_log(self, speaker_model):
        for step in speaker_model.results.recorded_steps:
            self.file_handle['simple log'].write(f'{step[0]}. {step[1]} ({step[2]})\n')

    def save_errors(self, speaker_model, count, sentence, grammatical):
        if len(speaker_model.results.syntax_semantics) > 0 and not grammatical or len(speaker_model.results.syntax_semantics) == 0 and grammatical:
            r = f"\n{str(count)}. {' '.join(sentence)}"
            self.file_handle['errors'].write(r)

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
        for lexicon_file in [file.strip() for file in settings.retrieve('file_lexicons', '').split(';')] + \
                            [file.strip() for file in settings.retrieve('file_redundancy_rules', '').split(';')]:
            lexicon_dict[lexicon_file] = {}
            lexical_entries = open(settings.folders['lexicon'] / lexicon_file, encoding='utf8').readlines()
            for lex, features in [e.strip().split('::') for e in lexical_entries if '::' in e]:
                lexicon_dict[lexicon_file][lex] = {}
        return lexicon_dict

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

    def process_numeration(self, settings):
        for line in open(settings.external_sources["numeration"], encoding=self.encoding):
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