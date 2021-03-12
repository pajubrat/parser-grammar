import pandas as pd
from matplotlib import pyplot as plt
import seaborn as sns
from datetime import datetime

STUDY_DIRECTORY = './language data working directory/study-4c-LHM/'

class Diagnostics:
    def __init__(self):
        self.data = pd.DataFrame()
        self.log_file = None

    def run_resource_diagnostics(self):
        self.start_logging()
        self.prepare_data()
        self.data_integrity_test()
        self.report_experiment_1()

    def start_logging(self):
        self.log_file = open(STUDY_DIRECTORY + 'diagnostics_log.txt', 'w')
        self.log_file.write(f'\nRunnning diagnostics {datetime.now()}')

    def prepare_data(self):
        self.read_data()
        self.add_data_items()
        self.remove_ungrammatical_sentences()

    def add_data_items(self):
        self.data['Sentence length'] = [len(sentence)-1 for sentence in self.data['Sentence']]

    def data_integrity_test(self):
        self.log_file.write('\nFinal data characteristics:')
        self.log_file.write(f'\nShape: {self.data.shape}.')
        self.log_file.write(f'\nColumns: {self.data.columns}.')
        self.log_file.write(f'\nStudy numbers: {set(self.data["Study_ID"])}\n')
        self.log_file.write(str(self.data))

    def read_data(self):
        files_to_read = \
            [
            ".\language data working directory\study-4c-LHM\LHM_corpus_resources.txt"
            ]
        self.log_file.write('\nReading experimental data from files.\nFiles to be read:')
        for i, file in enumerate(files_to_read):
            self.log_file.write('\n' + str(i) + '. ' + file)
        self.csv_into_data(files_to_read)
        self.log_file.write('\nDone.')

    def csv_into_data(self, files_to_read):
        self.log_file.write(f'\nReading data from {len(files_to_read)} files...')
        data_temp = []
        for file_number, filename in enumerate(files_to_read, start=1):
            data_temp.append(self.format_data(pd.read_csv(filename, dtype={'Sentence': str, 'Study_ID': int, 'Group 0': int, 'Group 1': int}, sep=',', comment='@', encoding="utf-8")))
        self.data = pd.concat(data_temp)
        self.log_file.write(f'Data shape is {self.data.shape} (Rows x Columns)...')
        self.log_file.write(f'\nColumns: {self.data.columns}')
        self.log_file.write(f'\nNumber of sentences in the test corpus: {len(self.data.index)}')

    def format_data(self, data):
        data = data.fillna(0)
        for col in data:
            if col != 'Sentence':
                data[col] = data[col].astype(int)
        data.name = 'Resource Consumption per Construction Type'
        data.columns.name = 'Resource'
        return data

    def remove_ungrammatical_sentences(self):
        self.log_file.write(f'\nRemoving ungrammatical sentences and sentences whose processing has failed...')
        self.data = self.data[(self.data['Group 1'] == 0) & (self.data['Total Time'] > 0)]
        self.log_file.write(f'New data shape is{self.data.shape}...Done')

    def log_experiment_title(self, experiment):
        self.log_file.write('\n\n--------------------------------------------------------------------------------------')
        self.log_file.write(f'\nAnalysis of experiment {experiment}')

    # Experiment 1
    def report_experiment_1(self):
        self.log_experiment_title('Performance properties of LHM constructions')
        data_exp1 = self.data[self.data['Group 0'] > 0] # Ignore the artificial a-b-c-d examples
        self.log_file.write(f'\nSelected studies {set(data_exp1["Study_ID"])}.')

        self.log_file.write('\n\nAll groups combined:\n' + str(round(data_exp1.mean(),1)))
        self.log_file.write('\n\nGroup 1:\n' + str(round(data_exp1[data_exp1['Group 0'] == 1].mean(),1)))
        self.log_file.write('\n\nGroup 2:\n' + str(round(data_exp1[data_exp1['Group 0'] == 2].mean(), 1)))
        self.log_file.write('\n\nGroup 3:\n' + str(round(data_exp1[data_exp1['Group 0'] == 3].mean(), 1)))
        self.log_file.write('\n\nGroup 4:\n' + str(round(data_exp1[data_exp1['Group 0'] == 4].mean(), 1)))
        self.log_file.write('\n\nGroup 5:\n' + str(round(data_exp1[data_exp1['Group 0'] == 5].mean(), 1)))
        self.log_file.write('\n\nGroup 6:\n' + str(round(data_exp1[data_exp1['Group 0'] == 6].mean(), 1)))

        # Results Figure 1
        self.log_file.write('\n\nCreating Results Figure 1...')
        fig, (ax1) = plt.subplots(1, 1, figsize=(5, 5))
        sns.set_theme(style="whitegrid")
        h = sns.barplot(data=data_exp1,
                        x='Group 0',
                        y='Mean time per word',
                        ci=None,
                        palette='Greys', ax=ax1)
        ax1.set(ylim=(0, 1500), ylabel='Mean predicted cognitive time per word (ms)', xlabel='Construction type')
        fig.savefig(STUDY_DIRECTORY + 'Result Figure 4')
        plt.close()
        self.log_file.write('Done.')

        # Figure 1 results in numbers
        d2 = data_exp1.melt(id_vars='Study_ID', value_vars=['Mean time per word', 'Merge', 'Garden Paths'])
        self.log_file.write('\n' + str(d2.groupby(['Study_ID', 'Resource']).max().round(decimals=1)))

        # Sentences ordered by the number of garden paths
        self.log_file.write('\n\nSentences with most garden paths, with a parser that uses both lexical anticipation and locality preference:\n')
        df = data_exp1.sort_values(by='Garden Paths', ascending=False)
        self.log_file.write(str(df[['Sentence', 'Garden Paths']].head(42)))