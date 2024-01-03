import itertools
from pathlib import Path
from visualizer import Visualizer
from datetime import datetime
from support import *
from phrase_structure import PhraseStructure
import logging
from language_guesser import LanguageGuesser
from speaker_model import SpeakerModel
from support import feature_explanations


def explanation(feature):
    for key in feature_explanations.keys():
        if key in feature:
            return feature_explanations[key]
    return ''

class LocalFileSystem:
    def __init__(self):
        self.folder = {}
        self.test_corpus = None
        self.study_folder = None
        self.external_sources = {}
        self.grammaticality_judgments_file = None
        self.results_file = None
        self.errors = None
        self.numeration_output = None
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

    def set_up_experiment(self):
        self.initialize()
        self.configure_logging()
        lg = LanguageGuesser(self.settings['lexicons'], self.folder['lexicon'])
        speaker_model = {}
        for language in lg.languages:
            speaker_model[language] = SpeakerModel(self, language)
            speaker_model[language].initialize()
        sentences_to_parse = [(index, sentence, group, part_of_conversation, grammatical)
                              for (index, sentence, group, part_of_conversation, grammatical)
                              in self.read_test_corpus()]
        return speaker_model, sentences_to_parse, lg

    def initialize(self):
        self.initialize_dev_logging()
        self.read_study_config_file()
        self.verify_and_check_mandatory_values()
        self.set_folders()
        self.set_external_resources()
        if self.settings['use_numeration']:
            self.process_numeration()
            self.settings['check_output'] = False

    def initialize_output_files(self):
        self.dev_log_file.write('Initializing output files for writing...')
        self.initialize_grammaticality_judgments_file()
        self.initialize_results_file()
        self.initialize_resources_file()
        self.initialize_error_file()
        self.initialize_simple_log_file()
        if self.settings['use_numeration']:
            self.initialize_numeration_output()
        self.dev_log_file.write('Done.\n')

    def initialize_error_file(self):
        self.errors = open(self.external_sources['error_report_name'], 'w', -1, encoding=self.encoding)
        self.errors.write(f'Prediction errors:')

    def initialize_numeration_output(self):
        self.numeration_output = open(self.external_sources['numeration_output'], 'w', -1, encoding=self.encoding)
        self.numeration_output.write(f'# Corpus generated from the numeration in {self.external_sources["numeration"]}\n')

    def initialize_dev_logging(self):
        self.dev_log_file = open('dev_log.txt', 'w', -1, 'utf-8')
        self.dev_log_file.write(f'Devlogging started at {datetime.datetime.now()}.\n')

    def verify_and_check_mandatory_values(self):
        self.dev_log_file.write('Checking and validating settings...')
        self.settings['study_folder'] = self.settings.get('study_folder', '')
        self.settings['test_corpus_folder'] = self.settings.get('test_corpus_folder', '')
        self.settings['test_corpus_file'] = self.settings.get('test_corpus_file', 'default_corpus.txt')
        self.settings['lexicon_folder'] = self.settings.get('lexicon_folder', 'lexicons')
        self.settings['console_output'] = self.settings.get('console_output', 'Full')
        self.settings['Agree'] = self.settings.get('Agree', 'standard')
        self.settings['phase_heads'] = self.settings.get('phase_heads', {'C', 'v', 'FORCE'})
        self.settings['phase_heads_excluded'] = self.settings.get('phase_heads_excluded', set())
        self.settings['lexicons'] = self.settings.get('lexicons', {'lexicon.txt', 'ug_morphemes.txt'})
        self.dev_log_file.write('Done.\n')
        self.dev_log_file.write(f'Settings: {self.settings}.\n')

    def set_external_resources(self):
        self.dev_log_file.write('Setting external sources: ')
        self.external_sources = {"test_corpus_file_name": self.folder['test_corpus'] / self.settings['test_corpus'],
                                 "log_file_name": self.folder['study'] / (self.settings['test_corpus'][:-4] + '_log.txt'),
                                 "simple_log_file_name": self.folder['study'] / (self.settings['test_corpus'][:-4] + '_simple_log.txt'),
                                 "results_file_name": self.folder['study'] / (self.settings['test_corpus'][:-4] + '_results.txt'),
                                 "grammaticality_judgments_file_name": self.folder['study'] / (self.settings['test_corpus'][:-4] + '_grammaticality_judgments.txt'),
                                 "resources_file_name": self.folder['study'] / (self.settings['test_corpus'][:-4] + '_resources.txt'),
                                 "simple_results_file_name": self.folder['study'] / (self.settings['test_corpus'][:-4] + '_simple_results.txt'),
                                 "surface_vocabulary_file_name": self.folder['study'] / (self.settings['test_corpus'][:-4] + '_saved_vocabulary.txt'),
                                 "numeration": self.folder['study'] / self.settings['numeration'],
                                 "numeration_output": self.folder['study'] / (self.settings['test_corpus'][:-4] + '_N.txt'),
                                 "redundancy_rules": self.folder['lexicon'] / self.settings['redundancy_rules'],
                                 "semantics_file_name": self.folder['study'] / (self.settings['test_corpus_file'][:-4] + '_semantics.txt'),
                                 "control_file_name": self.folder['study'] / (self.settings['test_corpus_file'][:-4] + '_control.txt'),
                                 "error_report_name": self.folder['study'] / (self.settings['test_corpus'][:-4] + '_error_reports.txt')
                                 }

        self.dev_log_file.write(f'{self.external_sources}.\n')

    def set_folders(self):
        self.dev_log_file.write(f'Setting folders for input and output files: ')
        self.folder['study'] = Path(self.settings.get('study_folder', 'language data working directory'))
        self.folder['test_corpus'] = Path(self.settings.get('test_corpus_folder', 'language data working directory'))
        self.folder['lexicon'] = Path(self.settings.get('lexicon_folder', 'language data working directory/lexicons'))
        self.folder['images'] = Path(self.folder['study'] / "phrase structure images")
        self.dev_log_file.write(f'{self.folder}.\n')

    def initialize_simple_log_file(self):
        self.dev_log_file.write('Initializing simple log file...')
        self.simple_log_file = open(self.external_sources['simple_log_file_name'], 'w', -1, encoding=self.encoding)
        self.stamp(self.simple_log_file)

    def read_study_config_file(self):
        self.dev_log_file.write('Reading study configuration file...')
        try:
            with open('config_study.txt', encoding=self.encoding) as config_file:
                # Read file into dict
                for line in config_file:
                    line = line.strip().replace('\t', '')
                    if line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        if ';' in value:
                            value = set(value.split(';'))
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

        PhraseStructure.phase_heads = self.settings['phase_heads']
        PhraseStructure.phase_heads_exclude = self.settings['phase_heads_exclude']
        PhraseStructure.spellout_heads = self.settings['image_parameter_spellout_complex_heads']

    def process_numeration(self):
        self.dev_log_file.write(f'Processing numeration from {self.external_sources["numeration"]} into {self.external_sources["numeration_output"]}...')
        self.dev_log_file.write('\nNumerations')
        for line in open(self.external_sources["numeration"], encoding=self.encoding):
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

    def print_sentence_to_console(self, sentence_number, sentence):
        print(f'\n{sentence_number}. {sentence} ', end='')

    def initialize_results_file(self):
        self.dev_log_file.write('Initializing results file...')
        self.results_file = open(self.external_sources['results_file_name'], "w", -1, encoding=self.encoding)
        self.stamp(self.results_file)

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
        experimental_group = []
        parse_list = []
        if self.settings['use_numeration']:
            k = open(self.external_sources['numeration_output'], encoding=self.encoding)
            input_file = self.external_sources["numeration_output"]
        else:
            input_file = self.external_sources["test_corpus_file_name"]
        self.dev_log_file.write(f'Reading test corpus file {input_file}...')
        index = 1
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

    def stamp(self, file_handle):
        file_handle.write('@  '+str(self.settings) + '\n')
        file_handle.write('@  '+str(datetime.datetime.now()) + '\n')
        file_handle.write('@  '+f'Test sentences {self.external_sources["test_corpus_file_name"]}.\n')
        file_handle.write('@  '+f'Logs {self.external_sources["log_file_name"]}.\n')
        file_handle.write('@ \n')

    def save_output(self, speaker_model, count, sentence, experimental_group, part_of_conversation, grammatical):
        self.save_predicted_grammaticality_judgment(speaker_model, count, sentence)
        self.save_results(speaker_model, count, sentence, part_of_conversation)
        self.save_resources(speaker_model, count, self.generate_input_sentence_string(sentence), experimental_group)
        self.print_result_to_console(speaker_model, sentence)
        if len(speaker_model.result_list) > 0 and not grammatical or len(speaker_model.result_list) == 0 and grammatical:
            self.save_error(count, sentence)

    def save_predicted_grammaticality_judgment(self, P, count, sentence):
        self.grammaticality_judgments_file.write(f'\n#{str(count)}.\n{self.judgment_marker(P)}{self.generate_input_sentence_string(sentence)}\n')

    def save_error(self, count, sentence):
        r = f'\n{str(count)}. {self.generate_input_sentence_string(sentence)}'
        self.errors.write(r)

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

    def save_results(self, parser, count, sentence, part_of_conversation):
        sentence_string = self.generate_input_sentence_string(sentence)
        if len(parser.result_list) == 0:
            self.results_file.write(str(count) + '. *' + sentence_string + '\n\n')
        else:
            self.results_file.write(str(count) + '. ' + self.judgment_marker(parser) + sentence_string + '\n\n')
            number_of_solutions = len(parser.result_list)
            parse_number = 1
            for parse, semantic_interpretation in parser.result_list:
                if number_of_solutions == 1:
                    self.results_file.write('\t' + f'{parse}\n')
                else:
                    self.results_file.write('\t' + chr(96 + parse_number) + f'. {parse}\n')
                if parse_number == 1:
                    self.results_file.write('\n\tSemantics:\n' + str(self.formatted_semantics_output(semantic_interpretation, parser)))
                    self.results_file.write(f'\n\tDiscourse inventory: {self.format_semantic_interpretation_simple(parser)}\n')
                    self.results_file.write('\tResources:\n\t' + self.format_resource_output(parser.resources) + '\n')
                parse_number = parse_number + 1
                if part_of_conversation:
                    self.results_file.write('\tConversation continues:\n')
                self.results_file.write('\n')

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

    def close_all_output_files(self):
        self.dev_log_file.write('Closing all output files...')
        self.results_file.close()
        self.grammaticality_judgments_file.close()
        self.resources_file.close()
        self.logger_handle.close()
        self.errors.close()
        self.dev_log_file.write('Done.\n')

    def report_errors_to_console(self):
        self.errors = open(self.external_sources['error_report_name'], 'r')
        print(f'\n')
        contents = self.errors.read()
        print(contents)
        self.errors = open(self.external_sources['error_report_name'], 'r')
        error_N = len(self.errors.readlines()) - 1
        print(f'= {error_N}  errors.')
        self.errors.close()

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

    def read_lexicons_into_dictionary(self):
        lexicon_dict = {}

        # Examine all lexical files and the lexical redundancy file
        for lexicon_file in list(self.settings['lexicons']) + [self.settings['redundancy_rules']]:
            lexicon_dict[lexicon_file] = {}

            # Example all lines in each file
            lexical_entries = open(self.folder['lexicon'] / lexicon_file, encoding='utf8').readlines()

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
