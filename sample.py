
import random

test_set_name = 'Experiment1_corpus_full.txt'
sample_file_name = test_set_name[:-4] + '_sample.txt'
sample_size = 200000
sample_list = []
count = 1

for line in open(test_set_name):
    if not line or line.startswith('#'):
        continue
    if line.startswith('&'):
        continue
    if line.startswith(' '):
        continue
    if line.startswith('\n'):
        continue
    sample_list.append((count, line))
    count = count + 1
    if count > sample_size:
        break

random.shuffle(sample_list)

sample_file = open(sample_file_name, "w")

count_2 = 1

for index, sentence in sample_list:
    sample_file.write('#' + str(count_2) + ' (in the original corpus, #' + str(index) + ')\n')
    sample_file.write(sentence + '\n')
    count_2 = count_2 + 1

