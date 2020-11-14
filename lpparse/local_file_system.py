from pathlib import Path
from time import process_time
from log_functions import *
from visualizer import Visualizer

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
        self.logger_handle = None
        self.instruction_to_ignore_from_test_corpus = False

    def initialize(self, args, folder, file, test_corpus_folder):
        if folder and file:
            self.settings['study_folder'] = folder
            self.settings['test_corpus_file'] = file
            self.settings['test_corpus_folder'] = test_corpus_folder
        else:
            self.read_root_config_file()
        self.folder['data'] = Path("language data working directory")
        self.folder['study'] = self.folder['data'] / self.settings['study_folder']
        self.folder['test_corpus'] = self.folder['data'] / self.settings['test_corpus_folder']
        self.folder['images'] = Path(self.folder['study'] / "phrase structure images")
        self.external_sources = {"test_corpus_file_name": self.folder['test_corpus'] / self.settings['test_corpus_file'],
                                 "log_file_name": self.folder['study'] / (self.settings['test_corpus_file'][:-4] + '_log.txt'),
                                 "results_file_name": self.folder['study'] / (self.settings['test_corpus_file'][:-4] + '_results.txt'),
                                 "grammaticality_judgments_file_name": self.folder['study'] / (self.settings['test_corpus_file'][:-4] + '_grammaticality_judgments.txt'),
                                 "resources_file_name": self.folder['study'] / (self.settings['test_corpus_file'][:-4] + '_resources.txt'),
                                 "lexicon_file_name": self.folder['data'] / 'lexicon.txt',
                                 "ug_morphemes": self.folder['data'] / 'ug_morphemes.txt',
                                 "redundancy_rules": self.folder['data'] / 'redundancy_rules.txt',
                                 "timings_file_name": self.folder['study'] / (self.settings['test_corpus_file'][:-4] + '_timings.txt'),
                                 "resource_sequence_file": self.folder['study'] / (self.settings['test_corpus_file'][:-4] + '_resource_sequence.txt'),
                                 "surface_vocabulary_file_name": self.folder['study'] / (self.settings['test_corpus_file'][:-4] + '_saved_vocabulary.txt')
                                 }
        self.read_study_config_file()
        self.initialize_image_folder()
        self.initialize_grammaticality_judgments_file()
        self.initialize_results_file()
        self.initialize_resources_file()
        self.initialize_timings_file()
        self.initialize_resource_sequence_file()
        if '/images' in args or self.settings['datatake_images']:
            self.settings['datatake_images'] = True
            self.visualizer = Visualizer()
            self.visualizer.initialize(self.settings)

    def read_root_config_file(self):
        config_file = open('config.txt')
        for line in config_file:
            line = line.strip()
            line = line.replace('\t', '')
            line = line.replace('  ', '')
            key, value = line.split(':', 1)
            self.settings[key] = value
        config_file.close()
        if 'test_corpus_folder' not in self.settings:  # Default behavior for test corpus folder
            self.settings['test_corpus_folder'] = self.settings['study_folder']

    def read_study_config_file(self):
        config_file = open(self.folder['study'] / 'config_study.txt')

        # Read file into dict
        for line in config_file:
            line = line.strip().replace('\t', '').replace(' ', '')
            if line and not line.startswith('#'):
                key, value = line.split(':', 1)
                if ',' in value:
                    value = value.split(',')
                self.settings[key] = value

        # Coverts boolean strings to booleans and integer strings to integers
        for key in self.settings:
            if isinstance(self.settings[key], str):
                if self.settings[key].lower() in {'true', 'yes'}:
                    self.settings[key] = True
                elif self.settings[key].lower() in {'false', 'no'}:
                    self.settings[key] = False
                elif self.settings[key].lstrip('-').isdigit():
                    self.settings[key] = int(self.settings[key])

        for key in self.settings:
            print(f'{key}: {self.settings[key]}')
        config_file.close()

    def initialize_resource_sequence_file(self):
        self.resource_sequence_file = open(self.external_sources['resource_sequence_file'], 'w', -1, 'utf-8')
        self.stamp(self.resource_sequence_file)

    def print_sentence_to_console(self, sentence_number, sentence):
        print(f'\n{sentence_number}. {sentence}', end='')

    def initialize_timings_file(self):
        self.timings_file = open(self.external_sources['timings_file_name'], 'w', -1, 'utf-8')
        self.stamp(self.timings_file)

    def initialize_results_file(self):
        self.results_file = open(self.external_sources['results_file_name'], "w", -1, "utf-8")
        self.stamp(self.results_file)

    def initialize_grammaticality_judgments_file(self):
        self.grammaticality_judgments_file = open(self.external_sources["grammaticality_judgments_file_name"], "w", -1, "utf-8")
        self.stamp(self.grammaticality_judgments_file)

    def initialize_resources_file(self):
        self.resources_file = open(self.external_sources["resources_file_name"], "w", -1, "utf-8")
        self.stamp(self.resources_file)

    def add_columns_to_resources_file(self, resources, experimental_group):
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

    def formatted_output(self, enumerated_object, delimiter):
        output_str = ''
        enumerated_object = sorted(enumerated_object)
        for item in enumerated_object:
            output_str = output_str + ', ' + item + delimiter
        return output_str

    def generate_input_sentence_string(self, sentence):
        input_sentence_string = ''
        for word in sentence:
            input_sentence_string += word + ' '
        return input_sentence_string

    def read_test_corpus(self):
        experimental_group = []
        parse_list = []
        plus_sentences = []
        for line in open(self.external_sources["test_corpus_file_name"]):
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
        self.save_grammaticality_judgment(parser, count, sentence)
        self.save_result(parser, count, sentence)
        if self.settings['datatake_resources']:
            self.save_resources(parser, count, self.generate_input_sentence_string(sentence), experimental_group)
        if self.settings['datatake_timings']:
            self.save_timings(parser, count, sentence)
        self.print_result_to_console(parser, count, sentence)
        if self.settings['datatake_images']:
            self.save_image(parser, sentence, count)

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
            self.results_file.write(str(count) + '. *' + sentence_string)
        else:
            self.results_file.write(str(count) + '. ' + P.grammaticality_judgment() + sentence_string + '\n\n')
            number_of_solutions = len(P.result_list)
            parse_number = 1
            for parse, semantic_interpretation in P.result_list:
                if number_of_solutions == 1:
                    self.results_file.write('\t' + f'{parse}\n')
                else:
                    self.results_file.write('\t' + chr(96 + parse_number) + f'. {parse}\n')
                self.results_file.write('\n\tLF_Recovery: ' + str(self.formatted_output(semantic_interpretation, delimiter=' ')) +'\n')
                if parse_number == 1:
                    self.results_file.write('\n\t' + self.format_resource_output(P.resources) + f'Execution time = {P.execution_time_results[parse_number - 1]}ms\n')
                parse_number = parse_number + 1
                self.results_file.write('\n')

    def save_image(self, P, sentence, count):
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

    def write_comment_line(self, sentence):
        self.results_file.write(' '.join(map(str, sentence)) + ' -------------------------------------------------------\n\n')
        self.grammaticality_judgments_file.write('\n')
        self.grammaticality_judgments_file.write(' '.join(map(str, sentence)))
        self.grammaticality_judgments_file.write('\n')

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
        self.results_file.close()
        self.grammaticality_judgments_file.close()
        self.resources_file.close()
        self.timings_file.close()
        self.resource_sequence_file.close()
        self.logger_handle.close()

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
                print('\n\tLF_Recovery: ' + str(self.formatted_output(semantic_interpretation, '')))
                if parse_number == 1:
                    print('\n\t' + self.format_resource_output(parser.resources) + f'\n\tExecution time = {parser.execution_time_results[parse_number - 1]}ms.\n')
                parse_number = parse_number + 1
        else:
            print(f'({parser.resources["Garden Paths"]["n"]}gp/{parser.resources["Merge"]["n"]}m/{process_time()-parser.start_time}s)')