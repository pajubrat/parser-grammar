import datetime
from linear_phase_parser import LinearPhaseParser

def format_resource_output(consumed_resources):
    s = ''
    i = 0
    for key in consumed_resources:
        s += f'{key}:{consumed_resources[key]}, '
        i += 1
        if i == 7:
            s += '\n\t'
            i = 0
    return s

def formatted_output(enumerated_object, delimiter):
    output_str = ''
    enumerated_object = sorted(enumerated_object)
    for item in enumerated_object:
        output_str = output_str + '\t' + item + delimiter

    return output_str

def generate_input_sentence_string(sentence):
    input_sentence_string = ''
    for word in sentence:
        input_sentence_string += word + ' '
    return input_sentence_string

def read_test_corpus(file_names):
    parse_list = []
    plus_sentences = []
    for line in open(file_names["test_corpus_file_name"]):
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

def initialize_results_file(file_name):
    results_file = open(file_name, "w", -1, "utf-8")
    results_file.write(str(datetime.datetime.now()) + '\n')
    results_file.write(f'Test sentences from file \"{file_name}\".\n')
    results_file.write(f'Logs into file \"{file_name}.\n')
    results_file.write(f'Lexicon from file \"{file_name}\".\n')
    return results_file

def initialize_grammaticality_judgments_file(file_name):
    grammaticality_judgments_file = open(file_name, "w", -1, "utf-8")
    grammaticality_judgments_file.write(str(datetime.datetime.now()) + '\n')
    grammaticality_judgments_file.write(f'Test sentences from file \"{file_name}\".\n')
    grammaticality_judgments_file.write(f'Logs into file \"{file_name}.\n')
    grammaticality_judgments_file.write(f'Lexicon from file \"{file_name}\".\n')
    return grammaticality_judgments_file

def initialize_resources_file(external_source):
    resources_file = open(external_source["resources_file_name"], "w", -1, "utf-8")
    P = LinearPhaseParser(external_source)
    P.initialize()
    resources_file.write("Sentence\t")
    for key in P.resources:
        resources_file.write(f'{key}\t')
    resources_file.write("Execution time (ms)\t\n\n")
    return resources_file

def initialize_image_folder(path):
    try:
        path.mkdir()
    except FileExistsError as exc:
        pass

def write_results(P, results_file, grammaticality_file, resources_file, count, sentence):
    input_sentence_string = generate_input_sentence_string(sentence)
    print('\n')
    if len(P.result_list) == 0:
        grammaticality_file.write(str(count) + '. *' + input_sentence_string + '\n')
        results_file.write(str(count) + '. *' + input_sentence_string + '\n')
        print((str(count) + '. *' + input_sentence_string))
        resources_file.write(str(count)+'\n')
    else:
        grammaticality_file.write(str(count) + '.  ' + input_sentence_string + '\n')
        results_file.write(str(count) + '. ' + P.grammaticality_judgment() + input_sentence_string + '\n\n')
        print(str(count) + '. ' + P.grammaticality_judgment() + input_sentence_string + '\n')
        number_of_solutions = len(P.result_list)
        parse_number = 1
        for parse, semantic_interpretation in P.result_list:
            if number_of_solutions == 1:
                results_file.write('\t' + f'{parse}\n')
                print('\t' + f'{parse}')
            else:
                results_file.write('\t' + chr(96 + parse_number) + f'. {parse}\n')
                print('\t' + chr(96 + parse_number) + f'. {parse}')
            results_file.write('\n\tLF_Recovery: ' + str(formatted_output(semantic_interpretation, '\n')))
            print('\n\tLF_Recovery: ' + str(formatted_output(semantic_interpretation, ' ')))
            if parse_number == 1:
                results_file.write('\n\t' + format_resource_output(P.resources) + f'Execution time = {P.execution_time_results[parse_number - 1]}ms\n')
                print('\n\t' + format_resource_output(P.resources) + f'Execution time = {P.execution_time_results[parse_number - 1]}ms')
            if parse_number == 1:
                resources_file.write(f'{count}\t')
                for key in P.resources:
                    resources_file.write(f'{P.resources[key]}\t')
                resources_file.write(f'{P.execution_time_results[parse_number - 1]}\n')
                resources_file.write('\n')
            parse_number = parse_number + 1
            results_file.write('\n')

def write_images(P, Graphic_output, sentence, data_folder):
    Graphic_output.input_sentence_string = generate_input_sentence_string(sentence)
    if Graphic_output.image_output:
        parse_number = 1
        count = 1
        for parse, semantic_interpretation in P.result_list:
            file_name = 'Raw image of (' + str(count) + chr(96 + parse_number) + ').png'
            Graphic_output.file_identifier = data_folder / 'phrase_structure_images' / file_name
            Graphic_output.draw(parse)
            parse_number = parse_number + 1
            count = count + 1

        if Graphic_output.spellout:
            parse_number = 1
            count = 1
            for spellout in P.spellout_result_list:
                file_name = 'Raw image of (' + str(count) + chr(96 + parse_number) + ')_spellout.png'
                Graphic_output.file_identifier = data_folder / 'phrase_structure_images' / file_name
                Graphic_output.draw(spellout)
                parse_number = parse_number + 1
                count = count + 1

def write_info_line(results_file, grammaticality_judgments_file, sentence):
    results_file.write(' '.join(map(str, sentence)) + ' -------------------------------------------------------\n\n')
    grammaticality_judgments_file.write('\n')
    grammaticality_judgments_file.write(' '.join(map(str, sentence)))
    grammaticality_judgments_file.write('\n')

def save_surface_vocabulary(file_name, surface_vocabulary):
    results_file = open(file_name, "w", -1, "utf-8")

    for key in surface_vocabulary:
        for lexical_item in surface_vocabulary[key]:
            value =str(lexical_item.features)
            string = f'{key:<15} {value:<10}' + '\n'
            results_file.write(string)

    results_file.close()