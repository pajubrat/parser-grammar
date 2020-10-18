import datetime
from linear_phase_parser import LinearPhaseParser
from pathlib import Path
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

    def initialize(self, args):
        self.visualizer = Visualizer()
        self.visualizer.initialize(args)
        self.test_corpus = "linear_phase_theory_corpus.txt"
        self.study_folder = "study-6-linear-phase-theory"
        self.folder['data'] = Path("language data working directory")
        self.folder['study'] = self.folder['data'] / self.study_folder
        self.folder['images'] = Path(self.folder['study'] / "phrase structure images")
        self.external_sources = {"test_corpus_file_name": self.folder['study'] / self.test_corpus,
                           "log_file_name": self.folder['study'] / (self.test_corpus[:-4] + '_log.txt'),
                           "results_file_name": self.folder['study'] / (self.test_corpus[:-4] + '_results.txt'),
                           "grammaticality_judgments_file_name": self.folder['study'] / (self.test_corpus[:-4] + '_grammaticality_judgments.txt'),
                           "resources_file_name": self.folder['study'] / (self.test_corpus[:-4] + '_resources.txt'),
                           "lexicon_file_name": self.folder['data'] / 'lexicon.txt',
                           "ug_morphemes": self.folder['data'] / 'ug_morphemes.txt',
                           "redundancy_rules": self.folder['data'] / 'redundancy_rules.txt',
                           "surface_vocabulary_file_name": self.folder['study'] / (self.test_corpus[:-4] + '_saved_vocabulary.txt')}
        self.initialize_image_folder()
        self.initialize_grammaticality_judgments_file()
        self.initialize_results_file()
        self.initialize_resources_file()

    def initialize_results_file(self):
        self.results_file = open(self.external_sources['results_file_name'], "w", -1, "utf-8")
        self.stamp(self.results_file)

    def initialize_grammaticality_judgments_file(self):
        self.grammaticality_judgments_file = open(self.external_sources["grammaticality_judgments_file_name"], "w", -1, "utf-8")
        self.stamp(self.grammaticality_judgments_file)

    def initialize_resources_file(self):
        self.resources_file = open(self.external_sources["resources_file_name"], "w", -1, "utf-8")
        self.stamp(self.resources_file)

    def add_columns_to_resources_file(self, resources):
        self.resources_file.write("Sentence,")
        for key in resources:
            self.resources_file.write(f'{key},')
        self.resources_file.write("Execution time (ms)\t\n\n")

    def initialize_image_folder(self):
        try:
            self.folder['images'].mkdir()
        except FileExistsError as exc:
            pass

    def format_resource_output(self, consumed_resources):
        s = ''
        i = 0
        for key in consumed_resources:
            s += f'{key}:{consumed_resources[key]}, '
            i += 1
            if i == 7:
                s += '\n\t\t'
                i = 0
        return s

    def formatted_output(self, enumerated_object, delimiter):
        output_str = ''
        enumerated_object = sorted(enumerated_object)
        for item in enumerated_object:
            output_str = output_str + '\t' + item + delimiter
        return output_str

    def generate_input_sentence_string(self, sentence):
        input_sentence_string = ''
        for word in sentence:
            input_sentence_string += word + ' '
        return input_sentence_string

    def read_test_corpus(self):
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
                parse_list.append([word.strip() for word in line.split()])
                break
            elif line.startswith('+'):
                plus_sentences.append([word.strip() for word in line.lstrip('+').split()])
            parse_list.append([word.strip() for word in line.split()])
        if plus_sentences:
            return plus_sentences
        return parse_list

    def stamp(self, file_handle):
        file_handle.write(str(datetime.datetime.now()) + '\n')
        file_handle.write(f'Test sentences from {self.external_sources["test_corpus_file_name"]}.\n')
        file_handle.write(f'Logs into {self.external_sources["log_file_name"]}.\n')
        file_handle.write(f'Lexicon from {self.external_sources["lexicon_file_name"]}.\n')
        file_handle.write(f'Redundancy rules from {self.external_sources["redundancy_rules"]}.\n')
        file_handle.write(f'Universal morphemes from {self.external_sources["ug_morphemes"]}.\n')

    def save_output(self, parser, count, sentence):
        self.save_grammaticality_judgment(parser, count, sentence)
        self.save_result(parser, count, sentence)
        self.save_resources(parser, count)
        self.print_result_to_console(parser, count, sentence)
        self.save_image(parser, sentence, count)
        log_sentence(count, sentence)

    def save_grammaticality_judgment(self, P, count, sentence):
        sentence_string = self.generate_input_sentence_string(sentence)
        if len(P.result_list) == 0:
            self.grammaticality_judgments_file.write(str(count) + '. *' + sentence_string + '\n')
        else:
            self.grammaticality_judgments_file.write(str(count) + '.  ' + sentence_string + '\n')

    def save_resources(self, parser, count):
        if count == 1:
            self.add_columns_to_resources_file(parser.resources)
        if len(parser.result_list) == 0:
            self.resources_file.write(str(count) + '\n')
        else:
            self.resources_file.write(str(count) + ',')
            for key in parser.resources:
                self.resources_file.write(f'{parser.resources[key]},')
            self.resources_file.write(f'{parser.execution_time_results[0]}\n')

    def save_result(self, P, count, sentence):
        sentence_string = self.generate_input_sentence_string(sentence)
        if len(P.result_list) == 0:
            self.results_file.write(str(count) + '. *' + sentence_string + '\n')
        else:
            self.results_file.write(str(count) + '. ' + P.grammaticality_judgment() + sentence_string + '\n\n')
            number_of_solutions = len(P.result_list)
            parse_number = 1
            for parse, semantic_interpretation in P.result_list:
                if number_of_solutions == 1:
                    self.results_file.write('\t' + f'{parse}\n')
                else:
                    self.results_file.write('\t' + chr(96 + parse_number) + f'. {parse}\n')
                self.results_file.write('\n\tLF_Recovery: ' + str(self.formatted_output(semantic_interpretation, '\n')))
                if parse_number == 1:
                    self.results_file.write('\n\t\t' + self.format_resource_output(P.resources) + f'Execution time = {P.execution_time_results[parse_number - 1]}ms\n')
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

    def close_all_output_files(self):
        self.results_file.close()
        self.grammaticality_judgments_file.close()
        self.resources_file.close()

    def print_result_to_console(self, parser, count, sentence):
        input_sentence_string = self.generate_input_sentence_string(sentence)
        if len(parser.result_list) == 0:
            print('\n' + str(count) + '. *' + input_sentence_string)
        else:
            print('\n' + str(count) + '. ' + parser.grammaticality_judgment() + input_sentence_string + '\n')
            number_of_solutions = len(parser.result_list)
            parse_number = 1
            for parse, semantic_interpretation in parser.result_list:
                if number_of_solutions == 1:
                    print('\t' + f'{parse}')
                else:
                    print('\t' + chr(96 + parse_number) + f'. {parse}')
                print('\n\t\tLF_Recovery: ' + str(self.formatted_output(semantic_interpretation, ' ')))
                if parse_number == 1:
                    print('\n\t\t' + self.format_resource_output(
                        parser.resources) + f'Execution time = {parser.execution_time_results[parse_number - 1]}ms.\n')
                parse_number = parse_number + 1