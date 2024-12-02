from support import log
from phrase_structure import PhraseStructure
import time


class Results:

    global_start_time = 0
    global_steps = 0

    def __init__(self, speaker_model):
        self.syntax_semantics = None          # List of syntax, semantics tuples
        self.recorded_steps = None            # Contains all derivational steps
        self.step_number = None               # Step number of recorded step
        self.output_fields = {}
        self.resources = {}
        self.execution_time_results = []       # Execution time
        self.first_solution_found = False      # Registers when the first solution if found
        self.number_of_ambiguities = 0
        self.speaker_model = speaker_model
        self.sentence = None

    def reset_output_fields(self):
        self.output_fields = {'Thematic roles': [],
                              'Indexing by Agree': [],
                              'Predicates': [],
                              'Aspect': [],
                              'DIS-features': [],
                              'Operator bindings': [],
                              'Semantic space': '',
                              'Speaker attitude': [],
                              'Assignments': [],
                              'Number of assignments': [],
                              'Information structure': []
                              }

    def initialize(self, lst):
        self.sentence = lst
        self.syntax_semantics = []
        self.recorded_steps = []
        self.step_number = 1
        self.resources = {}
        self.execution_time_results = []
        self.first_solution_found = False                       # Registers when the first solution if found
        self.number_of_ambiguities = 0
        self.reset_output_fields()
        self.resources = {"Total Time": {'ms': 0, 'n': 1},
                          "Garden Paths": {'ms': 1458, 'n': 0},
                          "Sensory Processing": {'ms': 75, 'n': 0},
                          "Reconstruction": {'ms': 0, 'n': 0},
                          "Lexical Retrieval": {'ms': 50, 'n': 0},
                          "Merge": {'ms': 7, 'n': 0},
                          "Head Chain": {'ms': 7, 'n': 0},
                          "Phrasal Chain": {'ms': 7, 'n': 0},
                          "Feature Inheritance": {'ms': 7, 'n': 0},
                          "Agree": {'ms': 7, 'n': 0},
                          "Feature": {'ms': 7, 'n': 0},
                          "Left Scrambling": {'ms': 7, 'n': 0},
                          "Right Scrambling": {'ms': 7, 'n': 0},
                          "Extraposition": {'ms': 7, 'n': 0},
                          "Last Resort Extraposition": {'ms': 7, 'n': 0},
                          "Mean time per word": {'ms': 0, 'n': 1}
                          }

    @classmethod
    def accumulate_global_steps(cls):
        cls.global_steps += 1

    def report_results_to_console(self):
        errors = open(self.speaker_model.settings.external_sources['errors'], 'r')
        print(f'\n')
        error_lines = [line for line in errors.readlines() if line.strip() and not line.startswith('@')]
        for line in error_lines:
            print(line)
        print(f'= {len(error_lines)}  errors (in {Results.global_steps} steps, {round(time.time() - Results.global_start_time, 2)} seconds). ')
        Results.reset_global_variables()
        errors.close()

    @classmethod
    def reset_global_variables(cls):
        cls.global_steps = 0
        cls.global_start_time = 0

    def calculate_total_time(self, sentence):
        for key in self.resources.keys():
            if key != 'Total Time' and key != 'Mean time per word':
                self.resources['Total Time']['ms'] += self.resources[key]['ms'] * self.resources[key]['n']
        self.resources['Mean time per word']['ms'] = round(self.resources['Total Time']['ms'] / len(sentence), 1)

    def update_resources(self, res_dict, sentence):
        self.resources.update(res_dict)
        self.calculate_total_time(sentence)

    def record_derivational_step(self, ps, information):
        self.recorded_steps.append((self.step_number, ps.copy(), information))
        self.step_number += 1

    def get_results_by_title(self, title):
        return [item[1] for item in self.recorded_steps if item[2] == title]

    def recorded_step(self, index):
        return self.recorded_steps[index][0], self.recorded_steps[index][1], self.recorded_steps[index][2]

    def store_solution(self, X, data_item):
        self.syntax_semantics.append((X, self.output_fields, data_item))

    def get_output_field(self, key):
        """Returns item [key] from the output field of the first result where it is found"""
        for tup in self.syntax_semantics:
            if tup[1].get(key, False):
                return tup[1][key]

    def retrieve_output_field(self, key):
        return self.output_fields.get(key, None)

    def store_output_field(self, key, value):
        """
        Converts the output of semantic interpretation into the correct format
        """
        if isinstance(value, str):
            if key not in self.output_fields:
                self.output_fields[key] = [value]
            else:
                self.output_fields[key].append(value)

        if isinstance(value, dict):
            self.output_fields[key] = [f'{k}: {value[k]}' for k in value.keys()]

        if isinstance(value, list):
            if key not in self.output_fields:
                self.output_fields[key] = value
            else:
                self.output_fields[key] += value

    def retrieve_syntax(self, solution):
        return solution[0]

    def retrieve_semantics(self, solution):
        return solution[1]

    def retrieve_resource(self, resource):
        return str(self.resources[resource]['n']) + ' x ' + str(self.resources[resource]['ms']) + ' = ' + str(self.resources[resource]['ms'] * self.resources[resource]['n']) + ' ms'

    def semantic_attributes(self, solution):
        return solution[1].keys()

    def interpretation(self, solution, semantic_attribute):
        return solution[1][semantic_attribute]

    def consume_resources(self, key, target, X=None, Y=None, comment=''):
        if not self.first_solution_found:
            self.resources[key]['n'] += 1
        if key == 'Sensory Processing':
            log(f'\n\t\t{key} of /#{target}/')
        elif key == 'Merge':
            log(u'\n\u0370' + f'\t{key}({target}, {X})')
        elif key == 'Reconstruction':
            log(f'\n\t\t{comment} = {target}')
        elif key != 'Agree' and key != 'Lexical Retrieval' and 'Extraposition' not in key:
            log(f'\n\t\t{key}({target.illustrate()}) => {target.path()}\n\n')
            if comment:
                log(f'({comment})')

    def log_success(self, ps):
        log(u'\n\n\u03F4''\t𝗔𝗰𝗰𝗲𝗽𝘁𝗲𝗱.\n')
        print('X', end='', flush=True)
        log(f'\n\n\t\tLexical features:\n{self.show_primitive_constituents(ps)}')
        if not self.first_solution_found:
            log('\n\tComplete ontology:')
            log(f'\t\t{self.format_ontology_all(self.speaker_model)}\n')
            log('\t\t-------------------------------------------------------------------------------------------------------------------------------------------------------------------\n')
        log('\n\tChecking if the sentence is ambiguous...\n')
        self.first_solution_found = True

    def report_failure(self, ps):
        log(f'\n\nX\tREJECTED.\n\n')
        log('\tMemory dump:\n\n')
        log(f'{self.show_primitive_constituents(ps)}')

    def show_primitive_constituents(self, X):
        reply = ''
        if not X.zero_level():
            reply += self.show_primitive_constituents(X.L())
            reply += self.show_primitive_constituents(X.R())
        else:
            for head in X.affixes():
                if head.copied:
                    break
                reply += f'\t\t{head.get_phonological_string():<11}{head.core}\n'
        return reply

    def format_ontology_all(self, speaker_model):
        output_str = '\n'
        for inventory in speaker_model.narrow_semantics.all_inventories():
            for semantic_object, data_dict in inventory.items():
                output_str += '\t\tObject ' + semantic_object
                if 'Semantic type' in data_dict:
                    output_str += ' ' + str(sorted(data_dict['Semantic type']))
                if 'Semantic space' in data_dict:
                    output_str += ' in ' + data_dict['Semantic space']
                output_str += '\n'
                # Show attributes
                for item, value in sorted(data_dict.items()):
                    if isinstance(value, set):
                        output_str += '\t\t\t' + item + ': ' + f'{", ".join(value)}' + '\n'
                    elif isinstance(value, list) and len(value) > 0 and isinstance(value[0], PhraseStructure):
                        output_str += '\t\t\t' + item + ': '+ ' + '.join([x.label() for x in value]) + '\n'
                    else:
                        output_str += '\t\t\t' + item + ': ' + f'{value}' + '\n'
        return output_str

    def create_inventory_sorting(list, to_be_sorted_dict):
        lst = [(semantic_object, data_dict) for semantic_object, data_dict in to_be_sorted_dict]
        lst_GLOBAL = [(semantic_object, data_dict) for semantic_object, data_dict in lst if
                      data_dict['Semantic space'] == 'GLOBAL']
        lst_QND = [(semantic_object, data_dict) for semantic_object, data_dict in lst if
                   data_dict['Semantic space'] == 'QND']
        lst_PRE = [(semantic_object, data_dict) for semantic_object, data_dict in lst if
                  data_dict['Semantic space'] == 'PRE']
        return lst_QND + lst_PRE + lst_GLOBAL

    def __str__(self):
        stri = '\n'
        if len(self.syntax_semantics) > 0:
            number_of_solutions = len(self.syntax_semantics)
            parse_number = 1
            for parse, output_fields, data_item in self.syntax_semantics:
                if number_of_solutions == 1:
                    stri += f'\n\t{parse}\n'
                else:
                    stri += f'\n\t{chr(96 + parse_number)}. {parse}\n'
                stri += f'\n\tDescriptive output:\n\n{self.formatted_semantics_output(output_fields)}'
                stri += f'\tPrediction errors:\n\n{self.prediction_errors(data_item, output_fields)}\n'
                parse_number = parse_number + 1
            stri += f'\n\tResources:\n\n{self.format_resource_output(self.resources)} \n'
            stri += f'\n\tGlobal ontology:\n{self.format_semantic_interpretation_simple()}'
        return stri

    def prediction_errors(self, data_item, output_fields):
        stri = ''
        for key in data_item.keys():
            if key in output_fields:
                if data_item[key] != ','.join(output_fields[key]):
                    stri += '\t\t' + data_item[key] + ' / ' + ','.join(output_fields[key]) + f' ({key})'
        if stri:
            return stri
        return '\t\tNone'

    def formatted_semantics_output(self, output_fields):
        stri = ''
        for i, key in enumerate(output_fields):
            if output_fields[key]:
                values = output_fields[key]
                if ';' in values[0]:
                    values = values[0].split(';')
                stri += f'\t\t{i}.' + key + ':\n\n\t\t\t'
                stri += '\n\t\t\t'.join(str(value).strip() for value in values)
                stri += '\n\n'
        stri += '\n'
        return stri

    def format_resource_output(self, consumed_resources):
        s = '\t\t'
        for i, key in enumerate(consumed_resources, start=1):
            s += f'{key}:{consumed_resources[key]["ms"]*consumed_resources[key]["n"]}ms({consumed_resources[key]["n"]}), '
            if i > 0 and i % 3 == 0:
                s += '\n\t\t'
        return s

    def format_semantic_interpretation_simple(self):
        stri = '\n'
        for semantic_object, data_dict in self.speaker_model.narrow_semantics.global_cognition.inventory.items():
            stri += '\t\tObject ' + semantic_object
            if 'Semantic space' in data_dict:
                stri += ' in ' + data_dict['Semantic space'] + ': '
            if data_dict.get('Number', None):
                stri += 'Spatiotemporal '
            if 'Reference' in data_dict:
                stri += data_dict['Reference']
            if 'Concept' in data_dict:
                stri += ' ' + data_dict['Concept']
            if 'Composition' in data_dict:
                stri += ' \'' + '.'.join(x.label() for x in data_dict['Composition']) + '\''
            stri += '\n'
        return stri
