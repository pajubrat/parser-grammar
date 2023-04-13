from pathlib import Path
from visualizer import Visualizer
from datetime import datetime
from support import *
from phrase_structure import PhraseStructure
import logging

class LocalFileSystem:
    def __init__(self):
        self.folder = {}
        self.test_corpus = None
        self.study_folder = None
        self.external_sources = {}
        self.grammaticality_judgments_file = None
        self.results_file = None
        self.semantics_file = None
        self.resources_file = None
        self.visualizer = None
        self.settings = {}
        self.timings_file = None
        self.resource_sequence_file = None
        self.simple_log_file = None
        self.simple_results_file = None
        self.control_file = None
        self.dev_log_file = None
        self.logger_handle = None
        self.instruction_to_ignore_from_test_corpus = False
        self.encoding = 'utf8'
        self.default_study_parameters = {'author': 'Unknown author',
                                         'year': 'Unknown year',
                                         'date': 'Unknown date',
                                         'study_id': '1',
                                         'only_first_solution': 'False',
                                         'logging': 'True',
                                         'study_folder': 'language data working directory/',
                                         'lexicon_folder': 'language data working directory/lexicons/',
                                         'test_corpus_file': 'default_corpus.txt',
                                         'test_corpus_folder': 'language data working directory/',
                                         'ignore_ungrammatical_sentences': 'False',
                                         'console_output': 'Full',
                                         'datatake_full': 'False',
                                         'datatake_images': 'False',
                                         'image_parameter_stop_after_each_image': 'False',
                                         'image_parameter_show_words': 'True',
                                         'image_parameter_nolabels': 'False',
                                         'image_parameter_spellout': 'False',
                                         'image_parameter_case': 'False',
                                         'image_parameter_show_sentences': 'False',
                                         'image_parameter_show_glosses': 'True',
                                         'extra_ranking': 'True',
                                         'filter': 'True',
                                         'lexical_anticipation': 'True',
                                         'closure': 'Bottom-up',
                                         'working_memory': 'True',
                                         'positive_spec_selection': '100',
                                         'negative_spec_selection': '-100',
                                         'break_head_comp_relations': '-100',
                                         'negative_tail_test': '-100',
                                         'positive_head_comp_selection': '100',
                                         'negative_head_comp_selection': '-100',
                                         'negative_semantics_match': '-100',
                                         'lf_legibility_condition': '-100',
                                         'negative_adverbial_test': '-100',
                                         'positive_adverbial_test': '100'
                                         }

    def check_output(self):
        grammatical = True
        number_of_errors = 0
        errors = open(self.external_sources['error_report_name'], 'w', -1, encoding=self.encoding)
        errors.write('Prediction errors were detected in the following sentences:\n')
        errors.write('(Determined solely on the basis of the grammatical/ungrammatical labels in the dataset file.)\n\n')
        for line in open(self.external_sources["grammaticality_judgments_file_name"], "r", -1, encoding=self.encoding):
            if line:
                if 'Grammatical' in line or 'grammatical' in line:
                    grammatical = True
                if 'Ungrammatical' in line or 'ungrammatical' in line:
                    grammatical = False
                if line.strip()[:1].isdigit():
                    if (' *' in line and grammatical) or (' *' not in line and not grammatical):
                        errors.write(f'{line}')
                        print(f'Error: {line}')
                        number_of_errors += 1
        errors.close()
        print(f'\nFound {number_of_errors} errors.')

    def initialize(self, args):
        self.initialize_dev_logging()
        self.read_study_config_file(args)
        self.read_input_arguments_into_settings(args)
        self.verify_and_check_mandatory_values()
        self.set_folders()
        self.set_external_resources()
        self.initialize_output_files()

    def initialize_output_files(self):
        self.dev_log_file.write('Initializing output files for writing...')
        self.initialize_grammaticality_judgments_file()
        self.initialize_results_file()
        if self.settings['datatake_images']:
            self.initialize_image_folder()
            self.settings['datatake_images'] = True
            self.visualizer = Visualizer(self.settings)
            self.visualizer.initialize(self.settings)
        if self.settings['datatake_full']:
            self.initialize_simple_results_file()
            self.initialize_resources_file()
            self.initialize_simple_log_file()
            self.initialize_semantics_file()
            self.initialize_control_file()
        self.dev_log_file.write('Done.\n')

    def initialize_dev_logging(self):
        self.dev_log_file  = open('dev_log.txt', 'w', -1, 'utf-8')
        self.dev_log_file.write(f'Devlogging started at {datetime.datetime.now()}.\n')

    def initialize_control_file(self):
        self.dev_log_file.write('Initializing control file...')
        self.control_file = open(self.external_sources['control_file_name'], 'w', -1, encoding=self.encoding)
        self.stamp(self.control_file)

    def verify_and_check_mandatory_values(self):
        self.dev_log_file.write('Checking and validating settings...')
        self.settings['study_folder'] = self.settings.get('study_folder','')
        self.settings['test_corpus_folder'] = self.settings.get('test_corpus_folder','')
        self.settings['test_corpus_file'] = self.settings.get('test_corpus_file', 'default_corpus.txt')
        self.settings['lexicon_folder'] = self.settings.get('lexicon_folder', 'lexicons')
        self.settings['console_output'] = self.settings.get('console_output', 'Full')
        self.dev_log_file.write('Done.\n')
        self.dev_log_file.write(f'Settings: {self.settings}.\n')

    def set_external_resources(self):
        self.dev_log_file.write('Setting external sources: ')
        self.external_sources = {"test_corpus_file_name": self.folder['test_corpus'] / self.settings['test_corpus_file'],
                                 "log_file_name": self.folder['study'] / (self.settings['test_corpus_file'][:-4] + '_log.txt'),
                                 "simple_log_file_name": self.folder['study'] / (self.settings['test_corpus_file'][:-4] + '_simple_log.txt'),
                                 "results_file_name": self.folder['study'] / (self.settings['test_corpus_file'][:-4] + '_results.txt'),
                                 "grammaticality_judgments_file_name": self.folder['study'] / (self.settings['test_corpus_file'][:-4] + '_grammaticality_judgments.txt'),
                                 "resources_file_name": self.folder['study'] / (self.settings['test_corpus_file'][:-4] + '_resources.txt'),
                                 "simple_results_file_name": self.folder['study'] / (self.settings['test_corpus_file'][:-4] + '_simple_results.txt'),
                                 "surface_vocabulary_file_name": self.folder['study'] / (self.settings['test_corpus_file'][:-4] + '_saved_vocabulary.txt'),
                                 "lexicon_file_name": self.folder['lexicon'] / 'lexicon.txt',
                                 "ug_morphemes": self.folder['lexicon'] / 'ug_morphemes.txt',
                                 "redundancy_rules": self.folder['lexicon'] / 'redundancy_rules.txt',
                                 "semantics_file_name": self.folder['study'] / (self.settings['test_corpus_file'][:-4] + '_semantics.txt'),
                                 "control_file_name": self.folder['study'] / (self.settings['test_corpus_file'][:-4] + '_control.txt'),
                                 "error_report_name": self.folder['study'] / (self.settings['test_corpus_file'][:-4] + '_error_reports.txt')
                                 }
        self.dev_log_file.write(f'{self.external_sources}.\n')

    def set_folders(self):
        self.dev_log_file.write(f'Setting folders for input and output files: ')
        self.folder['study'] = Path(self.settings.get('study_folder','language data working directory'))
        self.folder['test_corpus'] = Path(self.settings.get('test_corpus_folder','language data working directory'))
        self.folder['lexicon'] = Path(self.settings.get('lexicon_folder', 'language data working directory/lexicons'))
        self.folder['images'] = Path(self.folder['study'] / "phrase structure images")
        self.dev_log_file.write(f'{self.folder}.\n')

    def read_input_arguments_into_settings(self, args):
        self.dev_log_file.write('Reading input parameters from the user...')
        for key in args:
            self.settings[key] = args[key]
            self.dev_log_file.write(f'{key}: {args[key]}, ')
        self.dev_log_file.write('Done.\n')

    def read_root_config_file_into_settings(self):
        self.dev_log_file.write(f'Reading root configuration file...')
        try:
            with open('config.txt', 'r') as config_file:
                for line in config_file:
                    line = line.strip()
                    line = line.replace('\t', '')
                    line = line.replace('  ', '')
                    if len(line.split(':')) == 2 and not line.startswith('#'):
                        key, value = line.split(':')
                        self.settings[key] = value
                        self.dev_log_file.write(f'{key}:{value}, ')
                config_file.close()
                self.dev_log_file.write(f'Done.\n')
        except IOError:
            self.dev_log_file.write('No file found.\n')

    def read_study_config_file(self, args):
        self.dev_log_file.write('Reading study configuration file...')
        try:
            with open(args.get('study_folder', '') + 'config_study.txt', encoding=self.encoding) as config_file:
                # Read file into dict
                for line in config_file:
                    line = line.strip().replace('\t', '')
                    if line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        if ',' in value:
                            value = value.split(',')
                        else:
                            if key == 'show_features':
                                value = [value]
                            else:
                                value = value
                        self.settings[key] = value
                        self.dev_log_file.write(f'\n{key}={value}, ')
            config_file.close()
            # Safeguards
            if not self.settings['show_features'] or self.settings['show_features'] == '':
                self.settings['show_features'] = []
            self.dev_log_file.write('Done.\n')
        except IOError:
            for key in self.default_study_parameters:
                self.settings[key] = self.default_study_parameters[key]
            self.dev_log_file.write('Configuration file does not exist, using default values. Done.\n')

        for key in self.settings:
            if isinstance(self.settings[key], str):
                if self.settings[key].lower() in {'true', 'yes'}:
                    self.settings[key] = True
                elif self.settings[key].lower() in {'false', 'no'}:
                    self.settings[key] = False
                elif self.settings[key].lstrip('-').isdigit():
                    self.settings[key] = int(self.settings[key])

    def initialize_simple_log_file(self):
        self.dev_log_file.write('Initializing simple log file...')
        self.simple_log_file = open(self.external_sources['simple_log_file_name'], 'w', -1, encoding=self.encoding)
        self.stamp(self.simple_log_file)

    def print_sentence_to_console(self, sentence_number, sentence, language):
        print(f'\n{sentence_number}. {sentence} ({language[-2:]}) ', end='')

    def initialize_results_file(self):
        self.dev_log_file.write('Initializing results file...')
        self.results_file = open(self.external_sources['results_file_name'], "w", -1, encoding=self.encoding)
        self.stamp(self.results_file)

    def initialize_semantics_file(self):
        self.dev_log_file.write('Initializing semantics file...')
        self.semantics_file = open(self.external_sources['semantics_file_name'], "w", -1, encoding=self.encoding)
        self.stamp(self.semantics_file)

    def initialize_simple_results_file(self):
        self.dev_log_file.write('Initializing simple results file...')
        self.simple_results_file = open(self.external_sources['simple_results_file_name'], "w", -1, encoding=self.encoding)
        self.stamp(self.simple_results_file)

    def initialize_grammaticality_judgments_file(self):
        self.dev_log_file.write('Initializing grammaticality judgments file...')
        self.grammaticality_judgments_file = open(self.external_sources["grammaticality_judgments_file_name"], "w", -1, encoding=self.encoding)
        self.stamp(self.grammaticality_judgments_file)

    def initialize_resources_file(self):
        self.dev_log_file.write('Initializing resources file...')
        self.resources_file = open(self.external_sources["resources_file_name"], "w", -1, encoding=self.encoding)

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

    def initialize_image_folder(self):
        try:
            self.folder['images'].mkdir()
        except FileExistsError as exc:
            pass

    def format_resource_output(self, consumed_resources):
        s = ''
        i = 0
        for key in consumed_resources:
            s += f'{key}:{consumed_resources[key]["n"]}, '
            i += len(key)
            if i > 50:
                s += '\n\t'
                i = 0
        return s

    def formatted_semantics_output(self, semantic_interpretation_dict, parser):
        output_str = ''
        tabs_str = '\t'
        for key in semantic_interpretation_dict:
            if semantic_interpretation_dict[key]:
                if key == 'Assignments':
                    output_str += tabs_str + key + ': ' + str(self.illustrated(semantic_interpretation_dict[key], parser)) + '\n'
                else:
                    output_str += tabs_str + key + ': ' + str(semantic_interpretation_dict[key]) + '\n'
        return output_str

    def illustrated(self, assignments_list, parser):
        output_str = ''
        i = 0
        for assignment in assignments_list:
            if i > 2:
                output_str += '\n\t (...)'
                break
            if assignment['weight'] > 0:
                i += 1
                output_str += '\n\t'
                for key, value in assignment.items():
                    if key != 'weight':
                        output_str += parser.narrow_semantics.quantifiers_numerals_denotations_module.inventory[key]['Reference'] + ' ~ ' + value + ', '
                    else:
                        output_str += 'Weight ' + str(value)
        return output_str

    def generate_input_sentence_string(self, sentence):
        input_sentence_string = ''
        for word in sentence:
            input_sentence_string += word + ' '
        return input_sentence_string

    def read_test_corpus(self):
        self.dev_log_file.write(f'Reading test corpus file {self.external_sources["test_corpus_file_name"]}...')
        experimental_group = []
        parse_list = []
        plus_sentences = []
        for line in open(self.external_sources["test_corpus_file_name"], encoding=self.encoding):
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
                line = self.clear_line_end(line)
                parse_list.append(([word.strip() for word in line.split()], experimental_group, part_of_conversation))
                break
            if line.endswith(';'):
                part_of_conversation = True
                line = self.clear_line_end(line)
            if line.endswith('.'):
                part_of_conversation = False
                line = self.clear_line_end(line)
            if line.startswith('+'):
                line = self.clear_line_end(line)
                plus_sentences.append(([word.strip() for word in line.lstrip('+').split()], experimental_group, part_of_conversation))
            elif line.startswith('=>'):             # Respond to experimental grouping symbol
                experimental_group = self.read_experimental_group(line)
                continue
            parse_list.append(([word.strip() for word in line.split()], experimental_group, part_of_conversation))
        if plus_sentences:
            return plus_sentences
        self.dev_log_file.write(f'Found {len(parse_list)} sentences. Done.\n')
        return parse_list

    def clear_line_end(self, line):
        if line.endswith(';'):
            line = line.rstrip(';')
        elif line.endswith('.'):
            line = line.rstrip('.')
        return line

    def read_experimental_group(self, line):
        line = line.strip().replace(' ', '').replace('=>', '')
        return line.split('.')

    def stamp(self, file_handle):
        file_handle.write('@  '+str(self.settings) + '\n')
        file_handle.write('@  '+str(datetime.datetime.now()) + '\n')
        file_handle.write('@  '+f'Test sentences {self.external_sources["test_corpus_file_name"]}.\n')
        file_handle.write('@  '+f'Logs {self.external_sources["log_file_name"]}.\n')
        file_handle.write('@  '+f'Lexicon {self.external_sources["lexicon_file_name"]}.\n')
        file_handle.write('@  '+f'Redundancy rules {self.external_sources["redundancy_rules"]}.\n')
        file_handle.write('@  '+f'Universal morphemes {self.external_sources["ug_morphemes"]}.\n')
        file_handle.write('@ \n')

    def save_output(self, parser, count, sentence, experimental_group, part_of_conversation):
        self.dev_log_file.write('Saving output into output files...')
        self.save_grammaticality_judgment(parser, count, sentence)
        self.save_results(parser, count, sentence, part_of_conversation)
        if self.settings['datatake_full']:
            self.save_control_data(parser, count, sentence)
            self.save_resources(parser, count, self.generate_input_sentence_string(sentence), experimental_group)
        self.print_result_to_console(parser, sentence)
        if self.settings['datatake_images']:
            self.save_image(parser, sentence, count)
        self.dev_log_file.write('Done.\n')

    def save_grammaticality_judgment(self, P, count, sentence):
        sentence_string = self.generate_input_sentence_string(sentence)
        self.grammaticality_judgments_file.write('\n\t\t'+str(count) + '. ' + self.judgment_marker(P) + sentence_string + '\n')

    def judgment_marker(self, parser):
        if len(parser.result_list) == 0:
            return '*'
        if self.settings['calculate_assignments']:
            if not {assignment['weight'] for assignment in parser.result_list[0][1]['Assignments'] if assignment['weight'] > 0}:
                return '?'
        return ' '

    def save_resources(self, parser, count, sentence, experimental_group):
        if count == 1:
            self.add_columns_to_resources_file(parser.resources, experimental_group)
        self.resources_file.write(str(count) + ',')
        self.resources_file.write(f'{sentence},')
        self.resources_file.write(f'{self.settings.get("study_id", "0")},')
        self.resources_file.write(','.join(experimental_group))
        self.resources_file.write(',')
        if len(parser.result_list) > 0:
            for key in parser.resources:
                self.resources_file.write(f'{parser.resources[key]["n"]},')
            self.resources_file.write(f'{parser.execution_time_results[0]}')
        self.resources_file.write('\n')

    def save_control_data(self, parser, count, sentence):
        sentence_string = self.generate_input_sentence_string(sentence)
        self.control_file.write(str(count) + '. ' + self.judgment_marker(parser) + sentence_string + '\n')
        if len(parser.result_list) > 0:
            self.control_file.write('\t')
            p, sem = parser.result_list[0]
            if 'Recovery' in sem:
                for i, item in enumerate(sem['Recovery']):
                    self.control_file.write(item)
                    if i < len(sem['Recovery']) - 1:
                        self.control_file.write(', ')
                self.control_file.write('\n')
        self.control_file.write('\n')

    def save_results(self, parser, count, sentence, part_of_conversation):
        sentence_string = self.generate_input_sentence_string(sentence)
        if len(parser.result_list) == 0:
            self.results_file.write(str(count) + '. *' + sentence_string + '\n\n')
            if self.settings['datatake_full']:
                self.simple_results_file.write(str(count) + '. *' + sentence_string + '\n\n')
                self.semantics_file.write(str(count) + '. *' + sentence_string + '\n\n')
        else:
            self.results_file.write(str(count) + '. ' + self.judgment_marker(parser) + sentence_string + '\n\n')
            if self.settings['datatake_full']:
                self.simple_results_file.write(str(count) + '. ' + self.judgment_marker(parser) + sentence_string + '\n\n')
                self.semantics_file.write(str(count) + '. ' + self.judgment_marker(parser) + sentence_string + '\n\n')
            number_of_solutions = len(parser.result_list)
            parse_number = 1
            for parse, semantic_interpretation in parser.result_list:
                if number_of_solutions == 1:
                    self.results_file.write('\t' + f'{parse}\n')
                    if self.settings['datatake_full']:
                        self.simple_results_file.write('\t' + f'{parse}\n')
                        self.semantics_file.write('\t' + f'{parse}\n')
                else:
                    self.results_file.write('\t' + chr(96 + parse_number) + f'. {parse}\n')
                    if self.settings['datatake_full']:
                        self.simple_results_file.write('\t' + chr(96 + parse_number) + f'. {parse}\n')
                        self.semantics_file.write('\t' + chr(96 + parse_number) + f'. {parse}\n')
                if parse_number == 1:
                    self.results_file.write('\n\tSemantics:\n' + str(self.formatted_semantics_output(semantic_interpretation, parser)))
                    self.results_file.write(f'\n\tDiscourse inventory: {self.format_semantic_interpretation_simple(parser)}\n')
                    self.results_file.write('\tResources:\n\t' + self.format_resource_output(parser.resources) + '\n')
                    if self.settings['datatake_full']:
                        self.semantics_file.write('\n\tSemantics:\n' + str(self.formatted_semantics_output(semantic_interpretation, parser)))
                        self.semantics_file.write(f'\n\tDiscourse inventory: {self.format_semantic_interpretation(parser)}\n')
                parse_number = parse_number + 1
                if part_of_conversation:
                    self.results_file.write('\tConversation continues:\n')
                self.results_file.write('\n')
                if self.settings['datatake_full']:
                    self.simple_results_file.write('\n')
                    self.semantics_file.write('\n')

    def format_semantic_interpretation_simple(self, P):
        output_str = '\n'
        if len(P.narrow_semantics.all_inventories()) > 0:
            for semantic_object, data_dict in self.create_inventory_sorting(P.narrow_semantics.all_inventories().items()):
                if data_dict['Semantic space'] == 'GLOBAL':
                    if 'Reference' in data_dict and '§Thing' in data_dict['Semantic type']:
                        output_str += '\tObject ' + semantic_object
                        if 'Semantic space' in data_dict:
                            output_str += ' in ' + data_dict['Semantic space'] + ': '
                        if 'Reference' in data_dict:
                            output_str += data_dict['Reference'] + '\n'
            return output_str

    def format_semantic_interpretation(self, P):
        def format_lst(constituent_lst):
            out_s = ''
            for c in constituent_lst:
                out_s += f'{c.illustrate()}' + ','
            return out_s[:-1]

        output_str = '\n'
        if len(P.narrow_semantics.all_inventories()) > 0:
            for semantic_object, data_dict in self.create_inventory_sorting(P.narrow_semantics.all_inventories().items()):
                output_str += '\t\tObject ' + semantic_object
                if 'Semantic type' in data_dict:
                    output_str += ' ' + str(sorted(data_dict['Semantic type']))
                if 'Semantic space' in data_dict:
                    output_str += ' in ' + data_dict['Semantic space']
                output_str += '\n'
                for item, value in sorted(data_dict.items()):
                    if isinstance(value, list) and isinstance(value[0], PhraseStructure):
                        output_str += '\t\t\t' + item + ': ' + format_lst(value) + '\n'
                    else:
                        if isinstance(value, set):
                            output_str += '\t\t\t' + item + ': ' + f'{sorted(value)}' + '\n'
                        else:
                            output_str += '\t\t\t' + item + ': ' + f'{value}' + '\n'
            return output_str

    def create_inventory_sorting(list, to_be_sorted_dict):
        lst = [(semantic_object, data_dict) for semantic_object, data_dict in to_be_sorted_dict]
        lst_GLOBAL = [(semantic_object, data_dict) for semantic_object, data_dict in lst if data_dict['Semantic space'] == 'GLOBAL']
        lst_QND = [(semantic_object, data_dict) for semantic_object, data_dict in lst if data_dict['Semantic space'] == 'QND']
        lst_OP = [(semantic_object, data_dict) for semantic_object, data_dict in lst if data_dict['Semantic space'] == 'OP']
        lst_PE = [(semantic_object, data_dict) for semantic_object, data_dict in lst if data_dict['Semantic space'] == 'PRE']
        return lst_QND + lst_PE + lst_OP + lst_GLOBAL

    def save_image(self, P, sentence, count):
        self.dev_log_file.write('Creating images for solutions...')
        self.visualizer.input_sentence_string = self.generate_input_sentence_string(sentence)
        if self.visualizer.image_output:
            parse_number = 1
            for parse, semantic_interpretation in P.result_list:
                if len(P.result_list) > 1:
                    file_name = str(count) + chr(96 + parse_number) + '.png'
                else:
                    file_name = str(count) + '.png'
                self.visualizer.file_identifier = self.folder['images'] / file_name
                self.visualizer.draw(parse.top())
                parse_number = parse_number + 1
            if self.settings['image_parameter_spellout']:
                parse_number = 1
                for spellout in P.spellout_result_list:
                    file_name = 'Raw image of (' + str(count) + chr(96 + parse_number) + ')_spellout.png'
                    self.visualizer.file_identifier = self.folder['images'] / file_name
                    self.visualizer.draw(spellout)
                    parse_number = parse_number + 1
        self.dev_log_file.write('Done.\n')

    def write_comment_line(self, sentence_lst):
        sentence_string = ' '.join(map(str, sentence_lst))
        if sentence_lst[0].startswith("&"):
            self.grammaticality_judgments_file.write('\n')
        if sentence_lst[0].startswith("'"):
            prefix = '\t'
        else:
            prefix = ''
        self.grammaticality_judgments_file.write(prefix + sentence_string)
        self.grammaticality_judgments_file.write('\n')
        self.results_file.write(prefix + ' '.join(map(str, sentence_lst)) + '\n\n')

    def save_surface_vocabulary(self, surface_vocabulary):
        surface_vocabulary_file = open(self.external_sources["surface_vocabulary_file_name"], "w", -1, "utf-8")
        for key in surface_vocabulary:
            for lexical_item in surface_vocabulary[key]:
                value =str(lexical_item.features)
                string = f'{key:<15} {value:<10}' + '\n'
                surface_vocabulary_file.write(string)
        surface_vocabulary_file.close()

    def close_all_output_files(self):
        self.dev_log_file.write('Closing all output files...')
        self.results_file.close()
        self.grammaticality_judgments_file.close()

        if self.settings['datatake_full']:
            self.resources_file.close()
            self.control_file.close()
        self.logger_handle.close()
        self.dev_log_file.write('Done.\n')

    def print_result_to_console(self, parser, sentence):
        input_sentence_string = self.generate_input_sentence_string(sentence)
        if len(parser.result_list) > 0:
            print('\n\n\t' + self.judgment_marker(parser) + input_sentence_string + '\n')
            number_of_solutions = len(parser.result_list)
            parse_number = 1
            for parse, semantic_interpretation in parser.result_list:
                if number_of_solutions == 1:
                    print('\t' + f'{parse}')
                else:
                    print('\t' + chr(96 + parse_number) + f'. {parse}')
                if self.settings['console_output'] == 'Full':
                    print('\n\tSemantics:\n' + str(self.formatted_semantics_output(semantic_interpretation, parser)))
                    print(f'\tDiscourse inventory: {self.format_semantic_interpretation_simple(parser)}')
                    if parse_number == 1:
                        print('\n\t' + self.format_resource_output(parser.resources) + f'\n\tExecution time = {parser.execution_time_results[parse_number - 1]}ms.\n')
                parse_number = parse_number + 1

    def configure_logging(self):
        handler = logging.FileHandler(self.external_sources["log_file_name"], 'w', 'utf-8')
        handler.terminator = ''
        logging.basicConfig(level=logging.INFO, handlers=[handler], format='%(message)s')
        self.logger_handle = handler
        if 'logging' in self.settings and not self.settings['logging']:
            disable_all_logging()