# This script generates the dataset for Study 19

roots = ['pino-', 'laula-', 'luke-', 'puna-']

inner_V_morphemes = ['TA#v', 'ile', 'UTU', 'AhtA', 'a#v']
inner_N_morphemes = ['O', 'Us', 'ntO', 'stO', 'e']
inner_A_morphemes = ['ise', 'mAise']

outer_V_morphemes = ['A/inf', 'impss', 'T/fin#prs#n', 'v']
outer_N_morphemes = ['mise', 'tAr', 'jA', 'ri', '[NOM´]']
outer_A_morphemes = ['inen', 'mAinen', 'llinen', 'mAtOn', 'mA´', 'vA']

inner_morphemes = inner_V_morphemes + inner_N_morphemes + inner_A_morphemes
outer_morphemes = outer_V_morphemes + outer_N_morphemes + outer_A_morphemes
all_morphemes = inner_morphemes + outer_morphemes

# The maximum number of internal suffixes
MAX_SUFFIXES = 3

# This will store the  generated words
items = []

def add_suffixes(length, w, count):

    # Stop generation when length has been reached
    if count > length:
        for suffix in outer_morphemes:

            # Create the final word
            final_word = w + '#' + suffix

            # Create the sentence (context plus target word)
            items.append(final_word)

        return

    # Add all morphemes, recursively
    for m in all_morphemes:
        add_suffixes(length, w + '#' + m, count + 1)


# Generate all words between lengths 1-4 (root stem + max 3 suffixes)
for total_suffixes in range(0, MAX_SUFFIXES):
    # Begin every word with a root
    for root in roots:
        add_suffixes(total_suffixes, root, 1)

# Store the results into file
print(f'\nGenerated {len(items)} items, storing them to file...')
output_file = open('GENERATED_CORPUS.txt', 'w', -1, 'utf-8')
output_file.write('# Generated corpus\n')
for item in items:
    output_file.write(f'\n\n{item}')
output_file.close()
