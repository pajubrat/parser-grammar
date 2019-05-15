
#################################################################################
# Scrambler
################################################################################

# Imports
import itertools

scramble_file_list = ['Experiment1_seeds']

print('Scrambling...')

for input_file_name in scramble_file_list:
    scramble_list = []
    for line in open(input_file_name + '.txt'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        scramble_list.append([word.strip() for word in line.split()])

    output_file_name = input_file_name[:-6] + '_corpus.txt'
    results_file = open(output_file_name, "w")
    counter = 1

    for sentence in scramble_list:
        if sentence[0] != '&':
            for permutation in itertools.permutations(sentence, len(sentence)):

                # Create sentence without prosodic focus
                results_file.write('#' + str(counter) + '\n')
                for word in permutation:
                    results_file.write(word + ' ')
                results_file.write('\n')
                counter = counter + 1

                # Create alternative sentence with prosodic focus
                results_file.write('#' + str(counter) + '\n')
                first = True
                for word in permutation:
                    if first:
                        word = word + '#foc'
                        first = False
                    results_file.write(word + ' ')
                results_file.write('\n')
                counter = counter + 1
        else:
            s = ''
            for word in sentence:
                s = s + word + ' '
            results_file.write('\n& --------------------------------------------------------\n' + s +
                               '\n& --------------------------------------------------------\n\n')