from support import log

class Results():
    def __init__(self, speaker_model):
        self.syntax_semantics = None          # List of syntax, semantics tuples
        self.recorded_steps = None            # Contains all derivational steps
        self.step_number = None                # Step number of recorded step
        self.semantic_interpretation = {}
        self.resources = {}
        self.execution_time_results = []       # Execution time
        self.start_time = 0
        self.first_solution_found = False                       # Registers when the first solution if found
        self.number_of_ambiguities = 0
        self.speaker_model = speaker_model
        self.sentence = None

    def initialize(self, lst):
        self.sentence = lst
        self.syntax_semantics = []
        self.recorded_steps = []
        self.step_number = 1
        self.resources = {}
        self.execution_time_results = []
        self.first_solution_found = False                       # Registers when the first solution if found
        self.number_of_ambiguities = 0
        self.semantic_interpretation = {'Thematic roles': [],
                                        'Agreement': [],
                                        'Predicates': [],
                                        'Aspect': [],
                                        'DIS-features': [],
                                        'Operator bindings': [],
                                        'Semantic space': '',
                                        'Speaker attitude': [],
                                        'Assignments': [],
                                        'Information structure': []
                                        }
        self.resources = {"Total Time": {'ms': 0, 'n': 1},
                          "Garden Paths": {'ms': 1458, 'n': 0},
                          "Sensory Processing": {'ms': 46, 'n': 0},
                          "Lexical Retrieval": {'ms': 9, 'n': 0},
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

    def accumulate_resource_n(self, resource):
        self.resources[resource]['n'] += 1

    def calculate_total_time(self, sentence):
        for key in self.resources.keys():
            if key != 'Total Time' and key != 'Mean time per word':
                self.resources['Total Time']['ms'] += self.resources[key]['ms'] * self.resources[key]['n']
        self.resources['Mean time per word']['ms'] = self.resources['Total Time']['ms'] / len(sentence)

    def update_resources(self, res_dict, sentence):
        self.resources.update(res_dict)
        self.calculate_total_time(sentence)

    def record_derivational_step(self, ps, information):
        self.recorded_steps.append((self.step_number, ps.copy(), information))
        self.step_number += 1

    def recorded_step(self, index):
        return self.recorded_steps[index][0], self.recorded_steps[index][1], self.recorded_steps[index][2]

    def store_solution(self, ps):
        self.syntax_semantics.append((ps, self.semantic_interpretation))

    def store_semantic_interpretation(self, key, value):
        # If the value is string, it is added to the list
        if isinstance(value, str):
            if key not in self.semantic_interpretation:
                self.semantic_interpretation[key] = [value]
            else:
                self.semantic_interpretation[key].append(value)

        # If the value is list, the two lists are concatenated
        if isinstance(value, list):
            if key not in self.semantic_interpretation:
                self.semantic_interpretation[key] = value
            else:
                self.semantic_interpretation[key] += value

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

    def consume_resources(self, key, target):
        if not self.first_solution_found:
            self.accumulate_resource_n(key)
        if key == 'Sensory Processing':
            log(f'\n\t\t{key} of /#{target}/')
        elif key != 'Agree' and key != 'Last Resort Extraposition' and key != 'Lexical Retrieval':
            log(f'\n\t\t{key}({target.illustrate()}) => {target.top()} ')

    def log_success(self, ps):
        log('\n\t\tAccepted.\n')
        print('X', end='', flush=True)
        log(f'\n\n\t\tLexical features:\n{self.show_primitive_constituents(ps)}')
        if not self.first_solution_found:
            log(f'{self}')
            log('\n\t\tOntology:')
            log(f'\t\t{self.format_ontology_all(self.speaker_model)}\n')
            log('\t\t-------------------------------------------------------------------------------------------------------------------------------------------------------------------\n')
        log('\n\tChecking if the sentence is ambiguous...\n')
        self.first_solution_found = True

    def report_failure(self, ps):
        log('\n\t\tSOLUTION WAS REJECTED. \n\n')
        log('\t\tMemory dump:\n')
        log(f'{self.show_primitive_constituents(ps)}')

    def show_primitive_constituents(self, ps):
        def sorted_by_relevance(set):
            id = {feature for feature in set if feature[0] == '#'}
            A = {feature for feature in set if feature in ['√', 'n', 'N', 'Neg', 'Neg/fin', 'P', 'D', 'Qn', 'Num', 'φ', 'Top', 'C', 'a', 'A', 'v', 'V', 'Pass', 'VA/inf', 'T', 'Fin', 'Agr',
              'A/inf', 'MA/inf', 'ESSA/inf', 'E/inf', 'TUA/inf', 'KSE/inf', 'Inf', 'FORCE', 'EXPL', 'Adv', '0', 'a', 'b', 'c', 'd', 'x', 'y', 'z', 'X', 'Y', 'Z']}
            B = {feature for feature in set if feature[:2] == 'PF' or feature[:2] == 'LF'}
            C = {feature for feature in set if feature == '!SELF:d' or
                 feature == '!SELF:p' or
                 feature == 'p' or
                 feature == 'd' or
                 feature.startswith('!EF:') or
                 feature.startswith('-EF') or
                 feature.startswith('EF') or
                 feature.startswith('δPF')}
            D = {feature for feature in set if feature in {'ARG', '-ARG', 'ASP', 'Inf', 'Fin'}}
            E = {feature for feature in set if feature.startswith('TAIL')}
            F = {feature for feature in set if
                 feature[:4] == 'PHI:' or feature[:5] == 'iPHI:' or feature[:4] == 'PHI/' or feature[:5] == 'dPHI:'}
            G = {feature for feature in set if feature[:3] == 'SEM'}
            H = {feature for feature in set if
                 feature[:4] == 'COMP' or feature[:5] == '-COMP' or feature[:5] == '!COMP'}
            J = {feature for feature in set if
                 feature[:4] == 'SPEC' or feature[:5] == '-SPEC' or feature[:5] == '!SPEC'}
            residuum = set - A - B - C - D - E - F - G - H - J
            return sorted(A) + sorted(B) + sorted(C) + sorted(D) + sorted(E) + sorted(F) + sorted(G) + sorted(
                H) + sorted(J) + sorted(id) + sorted(residuum)

        def show_feature_list(lst):
            str = ''
            for feature in lst:
                str += f'[{feature}]'
            return str

        reply = ''
        if not ps.primitive():
            reply += self.show_primitive_constituents(ps.left())
            reply += self.show_primitive_constituents(ps.right())
        else:
            for head in ps.get_affix_list():
                if head.find_me_elsewhere:
                    break
                reply += f'\t\t{head.get_phonological_string():<10} {show_feature_list(sorted_by_relevance(head.features))}\n'
        return reply

    def format_ontology_all(self, speaker_model):
        output_str = '\n'
        if len(speaker_model.narrow_semantics.all_inventories()) > 0:
            for semantic_object, data_dict in self.create_inventory_sorting(speaker_model.narrow_semantics.all_inventories().items()):
                output_str += '\t\tObject ' + semantic_object
                if 'Semantic type' in data_dict:
                    output_str += ' ' + str(sorted(data_dict['Semantic type']))
                if 'Semantic space' in data_dict:
                    output_str += ' in ' + data_dict['Semantic space']
                output_str += '\n'
                for item, value in sorted(data_dict.items()):
                    if isinstance(value, set):
                        output_str += '\t\t\t' + item + ': ' + f'{sorted(value)}' + '\n'
                    else:
                        output_str += '\t\t\t' + item + ': ' + f'{value}' + '\n'
        return output_str

    def create_inventory_sorting(list, to_be_sorted_dict):
        lst = [(semantic_object, data_dict) for semantic_object, data_dict in to_be_sorted_dict]
        lst_GLOBAL = [(semantic_object, data_dict) for semantic_object, data_dict in lst if
                      data_dict['Semantic space'] == 'GLOBAL']
        lst_QND = [(semantic_object, data_dict) for semantic_object, data_dict in lst if
                   data_dict['Semantic space'] == 'QND']
        lst_OP = [(semantic_object, data_dict) for semantic_object, data_dict in lst if
                  data_dict['Semantic space'] == 'OP']
        lst_PE = [(semantic_object, data_dict) for semantic_object, data_dict in lst if
                  data_dict['Semantic space'] == 'PRE']
        return lst_QND + lst_PE + lst_OP + lst_GLOBAL

    def __str__(self):
        stri = f'\t{self.sentence}\n'
        if len(self.syntax_semantics) > 0:
            number_of_solutions = len(self.syntax_semantics)
            parse_number = 1
            for parse, semantic_interpretation in self.syntax_semantics:
                if number_of_solutions == 1:
                    stri += f'\n\t{parse}\n'
                else:
                    stri += f'\t{chr(96 + parse_number)}. {parse}\n'
                stri += f'\n\tSemantics:\n\n{self.formatted_semantics_output()}'
                parse_number = parse_number + 1
            stri += f'\n\tResources:\n\n{self.format_resource_output(self.resources)} \n'
            stri += f'\n\tOntology:\n{self.format_semantic_interpretation_simple()} \n'
        return stri

    def formatted_semantics_output(self):
        output_str = ''
        for key in self.semantic_interpretation:
            output_str += '\t\t' + key + ': ' + str(self.semantic_interpretation[key]) + '\n'
        return output_str

    def format_resource_output(self, consumed_resources):
        s = '\t\t'
        for i, key in enumerate(consumed_resources, start=1):
            s += f'{key}:{consumed_resources[key]["ms"]*consumed_resources[key]["n"]}ms({consumed_resources[key]["n"]}), '
            if i > 0 and i % 3 == 0:
                s += '\n\t\t'
        return s

    def format_semantic_interpretation_simple(self):
        output_str = '\n'
        if len(self.speaker_model.narrow_semantics.all_inventories()) > 0:
            for semantic_object, data_dict in self.create_inventory_sorting(self.speaker_model.narrow_semantics.all_inventories().items()):
                if data_dict['Semantic space'] == 'GLOBAL':
                    if 'Reference' in data_dict and '§Thing' in data_dict['Semantic type']:
                        output_str += '\t\tObject ' + semantic_object
                        if 'Semantic space' in data_dict:
                            output_str += ' in ' + data_dict['Semantic space'] + ': '
                        if 'Reference' in data_dict:
                            output_str += data_dict['Reference'] + '\n'
            return output_str