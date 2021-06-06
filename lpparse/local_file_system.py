from pathlib import Path
from time import process_time
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
        self.resources_file = None
        self.visualizer = None
        self.settings = {}
        self.timings_file = None
        self.resource_sequence_file = None
        self.simple_log_file = None
        self.simple_results_file = None
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
                                         'datatake_resources': 'True',
                                         'datatake_resource_sequence': 'False',
                                         'datatake_timings': 'False',
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

    def initialize(self, args):
        """
        Initializes and configures the parser and the study
        """

        # Step 0. Initialize dev_logging
        self.initialize_dev_logging()

        # Step 1. Read the study configuration file
        self.read_study_config_file(args)

        # Step 2. Read input parameters into the settings dict and override Step 1 if there is overlap
        self.read_input_arguments_into_settings(args)

        # Step 3. Verify and check that mandatory values exist, if not, populate with default study
        self.verify_and_check_mandatory_values()

        # Step 4. Set up folder locations for various resources
        self.set_folders()

        # Step 5. Set up external resources (lexicons, test corpus, and others)
        self.set_external_resources()

        # Step 7. Initialize the output files
        self.initialize_output_files()

    def initialize_output_files(self):
        """
        Initializes various output files so that we can write into them runtime.
        """
        self.dev_log_file.write('Initializing output files for writing...')
        self.initialize_image_folder()
        self.initialize_grammaticality_judgments_file()
        self.initialize_results_file()
        self.initialize_simple_results_file()
        self.initialize_resources_file()
        self.initialize_timings_file()
        self.initialize_simple_log_file()
        self.initialize_resource_sequence_file()
        if self.settings['datatake_images']:
            self.settings['datatake_images'] = True
            self.visualizer = Visualizer()
            self.visualizer.initialize(self.settings)
        self.dev_log_file.write('Done.\n')

    def initialize_dev_logging(self):
        self.dev_log_file  = open('dev_log.txt', 'w', -1, 'utf-8')
        self.dev_log_file.write(f'Devlogging started at {datetime.datetime.now()}.\n')

    def verify_and_check_mandatory_values(self):
        """
        Set default values if no value is provided by configuration file or by user parameters.
        """
        self.dev_log_file.write('Checking and validating settings...')
        self.settings['study_folder'] = self.settings.get('study_folder','')
        self.settings['test_corpus_folder'] = self.settings.get('test_corpus_folder','')
        self.settings['test_corpus_file'] = self.settings.get('test_corpus_file', 'default_corpus.txt')
        self.settings['lexicon_folder'] = self.settings.get('lexicon_folder', 'lexicons')
        self.settings['console_output'] = self.settings.get('console_output', 'Full')
        self.dev_log_file.write('Done.\n')
        self.dev_log_file.write(f'Settings: {self.settings}.\n')

    def set_external_resources(self):
        """
        Sets parameters for various external sources, such as lexicons.
        """
        self.dev_log_file.write('Setting external sources: ')
        self.external_sources = {"test_corpus_file_name": self.folder['test_corpus'] / self.settings['test_corpus_file'],
                                 "log_file_name": self.folder['study'] / (self.settings['test_corpus_file'][:-4] + '_log.txt'),
                                 "simple_log_file_name": self.folder['study'] / (self.settings['test_corpus_file'][:-4] + '_simple_log.txt'),
                                 "results_file_name": self.folder['study'] / (self.settings['test_corpus_file'][:-4] + '_results.txt'),
                                 "grammaticality_judgments_file_name": self.folder['study'] / (self.settings['test_corpus_file'][:-4] + '_grammaticality_judgments.txt'),
                                 "resources_file_name": self.folder['study'] / (self.settings['test_corpus_file'][:-4] + '_resources.txt'),
                                 "simple_results_file_name": self.folder['study'] / (self.settings['test_corpus_file'][:-4] + '_simple_results.txt'),
                                 "timings_file_name": self.folder['study'] / (self.settings['test_corpus_file'][:-4] + '_timings.txt'),
                                 "resource_sequence_file": self.folder['study'] / (self.settings['test_corpus_file'][:-4] + '_resource_sequence.txt'),
                                 "surface_vocabulary_file_name": self.folder['study'] / (self.settings['test_corpus_file'][:-4] + '_saved_vocabulary.txt'),
                                 "lexicon_file_name": self.folder['lexicon'] / 'lexicon.txt',
                                 "ug_morphemes": self.folder['lexicon'] / 'ug_morphemes.txt',
                                 "redundancy_rules": self.folder['lexicon'] / 'redundancy_rules.txt'
                                 }
        self.dev_log_file.write(f'{self.external_sources}.\n')

    def set_folders(self):
        """
        Sets folders for various input and output files
        """
        self.dev_log_file.write(f'Setting folders for input and output files: ')
        self.folder['study'] = Path(self.settings.get('study_folder','language data working directory'))
        self.folder['test_corpus'] = Path(self.settings.get('test_corpus_folder','language data working directory'))
        self.folder['lexicon'] = Path(self.settings.get('lexicon_folder', 'language data working directory/lexicons'))
        self.folder['images'] = Path(self.folder['study'] / "phrase structure images")
        self.dev_log_file.write(f'{self.folder}.\n')

    def read_input_arguments_into_settings(self, args):
        """
        Using input arguments as settings, overriding previous values.
        """
        self.dev_log_file.write('Reading input parameters from the user...')
        for key in args:
            self.settings[key] = args[key]
            self.dev_log_file.write(f'{key}: {args[key]}, ')
        self.dev_log_file.write('Done.\n')

    def read_root_config_file_into_settings(self):
        """
        Populates the settings dict with values obtained from the "config.txt" file. These settings can be
        overridden by arguments in the function call, so the "config.txt" file also functions as a storage of
        default values. If the file does not exist, then nothing is done.
        """
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
        """
        Reads study configuration file which provides other input parameters.
        """
        self.dev_log_file.write('Reading study configuration file...')
        try:
            with open(args.get('study_folder', '') + 'config_study.txt', encoding=self.encoding) as config_file:
                # Read file into dict
                for line in config_file:
                    line = line.strip().replace('\t', '')
                    if line and not line.startswith('#'):
                        key, value = line.split(':', 1)
                        value = value.strip()
                        if ',' in value:
                            value = value.split(',')

                        self.settings[key] = value
                        self.dev_log_file.write(f'{key}: {value}, ')
            config_file.close()
            self.dev_log_file.write('Done.\n')
        except IOError:
            # Use default values if the study configuration file does not exist
            for key in self.default_study_parameters:
                self.settings[key] = self.default_study_parameters[key]
            self.dev_log_file.write('Configuration file does not exist, using default values. Done.\n')

        # Coverts boolean strings to booleans and integer strings to integers
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

    def initialize_resource_sequence_file(self):
        self.dev_log_file.write('Initializing resource sequence file...')
        self.resource_sequence_file = open(self.external_sources['resource_sequence_file'], 'w', -1, encoding=self.encoding)
        self.stamp(self.resource_sequence_file)

    def print_sentence_to_console(self, sentence_number, sentence):
        print(f'\n{sentence_number}. {sentence}', end='')

    def initialize_timings_file(self):
        self.dev_log_file.write('Initializing timings file...')
        self.timings_file = open(self.external_sources['timings_file_name'], 'w', -1, encoding=self.encoding)
        self.stamp(self.timings_file)

    def initialize_results_file(self):
        self.dev_log_file.write('Initializing results file...')
        self.results_file = open(self.external_sources['results_file_name'], "w", -1, encoding=self.encoding)
        self.stamp(self.results_file)

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
        self.stamp(self.resources_file)

    def add_columns_to_resources_file(self, resources, experimental_group):
        self.dev_log_file.write('Add columns to the resources file...')
        self.resources_file.write("Number,Sentence,Study_ID,")                                                              # Initial columns
        for index, group in enumerate(experimental_group):                                                                  # Experimental groups
            self.resources_file.write(f"Group {index},")
        for key in resources:                                                                                               # Resources
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
            if i > 60:
                s += '\n\t'
                i = 0
        return s

    def formatted_semantics_output(self, semantic_interpretation_dict, tabs=1):
        output_str = ''
        tabs_str = '\t'*tabs
        for key in semantic_interpretation_dict:
            if isinstance(semantic_interpretation_dict[key], set) or isinstance(semantic_interpretation_dict[key], list):
                output_str += tabs_str + key + ': ' + str(sorted(semantic_interpretation_dict[key])) + '\n'
            else:
                output_str += tabs_str + key + ': ' + str(semantic_interpretation_dict[key]) + '\n'
        return output_str

    def generate_input_sentence_string(self, sentence):
        input_sentence_string = ''
        for word in sentence:
            input_sentence_string += word + ' '
        return input_sentence_string

    def read_test_corpus(self):
        """
        Reads a test corpus file into a list [parse_list] of sentences, where each sentence is a list of words.
        """
        self.dev_log_file.write(f'Reading test corpus file {self.external_sources["test_corpus_file_name"]}...')
        experimental_group = []
        parse_list = []
        plus_sentences = []
        for line in open(self.external_sources["test_corpus_file_name"], encoding=self.encoding):
            if line.startswith('=STOP='):
                break
            if line.startswith('=START='):
                parse_list = []
                continue
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if line.startswith('%'):
                parse_list = []
                line = line.lstrip('%')
                parse_list.append(([word.strip() for word in line.split()], experimental_group))
                break
            if line.startswith('+'):
                plus_sentences.append(([word.strip() for word in line.lstrip('+').split()], experimental_group))
            elif line.startswith('=>'):
                experimental_group = self.read_experimental_group(line)
                continue
            parse_list.append(([word.strip() for word in line.split()], experimental_group))
        if plus_sentences:
            return plus_sentences
        self.dev_log_file.write(f'Found {len(parse_list)} sentences. Done.\n')
        return parse_list

    def read_experimental_group(self, line):
        line = line.strip().replace(' ', '').replace('=>', '')
        return line.split('.')

    def stamp(self, file_handle):
        file_handle.write('@  '+str(self.settings) + '\n')
        file_handle.write('@  '+str(datetime.datetime.now()) + '\n')
        file_handle.write('@  '+f'Test sentences from {self.external_sources["test_corpus_file_name"]}.\n')
        file_handle.write('@  '+f'Logs into {self.external_sources["log_file_name"]}.\n')
        file_handle.write('@  '+f'Lexicon from {self.external_sources["lexicon_file_name"]}.\n')
        file_handle.write('@  '+f'Redundancy rules from {self.external_sources["redundancy_rules"]}.\n')
        file_handle.write('@  '+f'Universal morphemes from {self.external_sources["ug_morphemes"]}.\n')
        file_handle.write('@ \n')
        file_handle.write('@ \n')

    def save_output(self, parser, count, sentence, experimental_group):
        self.dev_log_file.write('Saving output into output files...')
        self.save_grammaticality_judgment(parser, count, sentence)
        self.save_result(parser, count, sentence)
        if self.settings['datatake_resources']:
            self.save_resources(parser, count, self.generate_input_sentence_string(sentence), experimental_group)
        if self.settings['datatake_timings']:
            self.save_timings(parser, count, sentence)
        self.print_result_to_console(parser, count, sentence)
        if self.settings['datatake_images']:
            self.save_image(parser, sentence, count)
        self.dev_log_file.write('Done.\n')

    def save_timings(self, parser, count, sentence):
        self.timings_file.write(f'{count}, {self.generate_input_sentence_string(sentence)}, ')
        sum = 0
        for word, time in parser.time_from_stimulus_onset_for_word:
            self.timings_file.write(f'{word},{time},  ')
            sum = sum + time
        self.timings_file.write(f'= {sum}ms.\n')

    def save_grammaticality_judgment(self, P, count, sentence):
        sentence_string = self.generate_input_sentence_string(sentence)
        if len(P.result_list) == 0:
            self.grammaticality_judgments_file.write(str(count) + '. *' + sentence_string + '\n')
        else:
            self.grammaticality_judgments_file.write(str(count) + '.  ' + sentence_string + '\n')

    def save_resources(self, parser, count, sentence, experimental_group):
        # If this is the first sentence, we add the column line
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

    def save_result(self, P, count, sentence):
        sentence_string = self.generate_input_sentence_string(sentence)
        if len(P.result_list) == 0:
            self.results_file.write(str(count) + '. *' + sentence_string + '\n\n')
            self.simple_results_file.write(str(count) + '. *' + sentence_string + '\n\n')
        else:
            self.results_file.write(str(count) + '. ' + P.grammaticality_judgment() + sentence_string + '\n\n')
            self.simple_results_file.write(str(count) + '. ' + P.grammaticality_judgment() + sentence_string + '\n\n')
            number_of_solutions = len(P.result_list)
            parse_number = 1
            for parse, semantic_interpretation in P.result_list:
                if number_of_solutions == 1:
                    self.results_file.write('\t' + f'{parse}\n')
                    self.simple_results_file.write('\t' + f'{parse}\n')
                else:
                    self.results_file.write('\t' + chr(96 + parse_number) + f'. {parse}\n')
                    self.simple_results_file.write('\t' + chr(96 + parse_number) + f'. {parse}\n')
                if parse_number == 1:
                    self.results_file.write('\n\tSemantics:\n' + str(self.formatted_semantics_output(semantic_interpretation)))
                    self.results_file.write('\n\tResources:\n\t' + self.format_resource_output(P.resources) + '\n')
                    self.results_file.write(f'\n\tDiscourse inventory: {self.format_semantic_interpretation(P)}\n')
                parse_number = parse_number + 1
                self.results_file.write('\n')
                self.simple_results_file.write('\n')

    def format_semantic_interpretation(self, P):
        def format_lst(constituent_lst):
            out_s = ''
            for c in constituent_lst:
                out_s += f'{c.illustrate()}' + ','
            return out_s[:-1]

        output_str = '\n'
        if len(P.narrow_semantics.all_inventories()) > 0:
            for semantic_object, data_dict in sorted(P.narrow_semantics.all_inventories().items()):
                output_str += '\t\tObject ' + semantic_object
                if 'Semantic type' in data_dict:
                    output_str += ' ' + str(sorted(data_dict['Semantic type']))
                if 'Semantic space' in data_dict:
                    output_str += ' in ' + data_dict['Semantic space']
                output_str += '\n'
                for item, value in data_dict.items():
                    if isinstance(value, list) and isinstance(value[0], PhraseStructure):
                        output_str += '\t\t\t' + item + ': ' + format_lst(value) + '\n'
                    else:
                        if isinstance(value, set):
                            output_str += '\t\t\t' + item + ': ' + f'{sorted(value)}' + '\n'
                        else:
                            output_str += '\t\t\t' + item + ': ' + f'{value}' + '\n'
            return output_str

    def save_image(self, P, sentence, count):
        """
        Saves images for each solution
        """
        self.dev_log_file.write('Creating images for solutions...')
        self.visualizer.input_sentence_string = self.generate_input_sentence_string(sentence)
        if self.visualizer.image_output:
            parse_number = 1
            for parse, semantic_interpretation in P.result_list:
                file_name = 'Raw image of (' + str(count) + chr(96 + parse_number) + ').png'
                self.visualizer.file_identifier = self.folder['images'] / file_name
                self.visualizer.draw(parse)
                parse_number = parse_number + 1
            if self.visualizer.spellout:
                parse_number = 1
                for spellout in P.spellout_result_list:
                    file_name = 'Raw image of (' + str(count) + chr(96 + parse_number) + ')_spellout.png'
                    self.visualizer.file_identifier = self.folder['images'] / file_name
                    self.visualizer.draw(spellout)
                    parse_number =  parse_number + 1
        self.dev_log_file.write('Done.\n')

    def write_comment_line(self, sentence):

        if sentence[0].startswith("'"):
            s = '\t'
        else:
            s = ''
        self.grammaticality_judgments_file.write(s + ' '.join(map(str, sentence)))
        self.grammaticality_judgments_file.write('\n\n')
        self.results_file.write(s + ' '.join(map(str, sentence)) + '\n\n')

    def save_surface_vocabulary(self, surface_vocabulary):
        surface_vocabulary_file = open(self.external_sources["surface_vocabulary_file_name"], "w", -1, "utf-8")
        for key in surface_vocabulary:
            for lexical_item in surface_vocabulary[key]:
                value =str(lexical_item.features)
                string = f'{key:<15} {value:<10}' + '\n'
                surface_vocabulary_file.write(string)
        surface_vocabulary_file.close()

    def parse_and_analyze_comment(self, sentence):
        if self.settings['ignore_ungrammatical_sentences']:
            if 'ungram' in self.generate_input_sentence_string(sentence).lower():
                self.instruction_to_ignore_from_test_corpus = True
            elif 'gram' in self.generate_input_sentence_string(sentence).lower():
                self.instruction_to_ignore_from_test_corpus = False

    def close_all_output_files(self):
        self.dev_log_file.write('Closing all output files...')
        self.results_file.close()
        self.grammaticality_judgments_file.close()
        self.resources_file.close()
        self.timings_file.close()
        self.resource_sequence_file.close()
        self.logger_handle.close()
        self.dev_log_file.write('Done.\n')

    def print_result_to_console(self, parser, count, sentence):
        input_sentence_string = self.generate_input_sentence_string(sentence)
        if len(parser.result_list) > 0:
            print('\n\n\t' + parser.grammaticality_judgment() + input_sentence_string + '\n')
            number_of_solutions = len(parser.result_list)
            parse_number = 1
            for parse, semantic_interpretation in parser.result_list:
                if number_of_solutions == 1:
                    print('\t' + f'{parse}')
                else:
                    print('\t' + chr(96 + parse_number) + f'. {parse}')
                if self.settings['console_output'] == 'Full':
                    print('\n\tSemantics:\n' + str(self.formatted_semantics_output(semantic_interpretation)))
                    if parse_number == 1:
                        print('\n\t' + self.format_resource_output(parser.resources) + f'\n\tExecution time = {parser.execution_time_results[parse_number - 1]}ms.\n')
                parse_number = parse_number + 1
        else:
            print(f'({parser.resources["Garden Paths"]["n"]}gp/{parser.resources["Merge"]["n"]}m/{process_time()-parser.start_time}s)')

    def log_results(self, parser, ps_):
        ps_.tidy_names(1)
        log_result(ps_)
        log('\n\n')
        log('\t\tLexical features:\n')
        log(show_primitive_constituents(ps_))
        if not parser.first_solution_found:
            log('\n\t\tSemantic bookkeeping:')
            log(f'\t\t{self.format_semantic_interpretation(parser)}\n')
            log('\t\t-------------------------------------------------------------------------------------------------------------------------------------------------------------------\n')
        log('\n\tChecking if the sentence is ambiguous...\n')

    def configure_logging(self):
        handler = logging.FileHandler(self.external_sources["log_file_name"], 'w', 'utf-8')
        handler.terminator = ''
        logging.basicConfig(level=logging.INFO, handlers=[handler], format='%(message)s')
        self.logger_handle = handler
        if 'logging' in self.settings and not self.settings['logging']:
            disable_all_logging()