import pandas as pd
from matplotlib import pyplot as plt
import seaborn as sns
from datetime import datetime
import numpy as np
import sys

STUDY_DIRECTORY = './language data working directory/study-6-linear-phase-theory/'

class Diagnostics:
    def __init__(self):
        self.data = pd.DataFrame()
        self.log_file = None

    def run_resource_diagnostics(self):
        self.start_logging()
        self.prepare_data()
        self.data_integrity_test()
        self.report_experiment_1a()       #  Lexical anticipation and locality preference
        self.report_experiment_2a()       #  Variations of lexical anticipation
        self.report_experiment_2b()       #  Variations of locality preference
        self.report_experiment_2c()       #  Left branch filter
        self.report_experiment_3a()       #  Noncanonical constructions, relative clauses, working memory

    def start_logging(self):
        self.log_file = open(STUDY_DIRECTORY + 'diagnostics_log.txt', 'w')
        self.log_file.write(f'\nRunnning diagnostics {datetime.now()}')

    def prepare_data(self):
        self.read_data()
        self.remove_ungrammatical_sentences()
        self.add_groups()

    def data_integrity_test(self):
        self.log_file.write('\nFinal data characteristics:')
        self.log_file.write(f'\nShape: {self.data.shape}.')
        self.log_file.write(f'\nColumns: {self.data.columns}.')
        self.log_file.write(f'\nStudy numbers: {set(self.data["Study_ID"])}')

    def read_data(self):
        files_to_read = \
            [
            ".\language data working directory\study-6-linear-phase-theory/Experiment 1a/01-1-1\linear_phase_theory_corpus_resources.txt",
            ".\language data working directory\study-6-linear-phase-theory/Experiment 1a/02-1-0\linear_phase_theory_corpus_resources.txt",
            ".\language data working directory\study-6-linear-phase-theory/Experiment 1a/03-0-1\linear_phase_theory_corpus_resources.txt",
            ".\language data working directory\study-6-linear-phase-theory/Experiment 1a/04-0-0\linear_phase_theory_corpus_resources.txt",
            ".\language data working directory\study-6-linear-phase-theory/Experiment 1a/05-0-R\linear_phase_theory_corpus_resources.txt",
            ".\language data working directory\study-6-linear-phase-theory/Experiment 2a/21-spec(1)-comp(1)-adj(1)-case(1)/linear_phase_theory_corpus_resources.txt",
            ".\language data working directory\study-6-linear-phase-theory/Experiment 2a/22-spec(1)-comp(1)-adj(1)-case(0)/linear_phase_theory_corpus_resources.txt",
            ".\language data working directory\study-6-linear-phase-theory/Experiment 2a/23-spec(1)-comp(1)-adj(0)-case(1)/linear_phase_theory_corpus_resources.txt",
            ".\language data working directory\study-6-linear-phase-theory/Experiment 2a/24-spec(1)-comp(1)-adj(0)-case(0)/linear_phase_theory_corpus_resources.txt",
            ".\language data working directory\study-6-linear-phase-theory/Experiment 2a/25-spec(1)-comp(0)-adj(1)-case(1)/linear_phase_theory_corpus_resources.txt",
            ".\language data working directory\study-6-linear-phase-theory/Experiment 2a/26-spec(1)-comp(0)-adj(1)-case(0)/linear_phase_theory_corpus_resources.txt",
            ".\language data working directory\study-6-linear-phase-theory/Experiment 2a/27-spec(1)-comp(0)-adj(0)-case(1)/linear_phase_theory_corpus_resources.txt",
            ".\language data working directory\study-6-linear-phase-theory/Experiment 2a/28-spec(1)-comp(0)-adj(0)-case(0)/linear_phase_theory_corpus_resources.txt",
            ".\language data working directory\study-6-linear-phase-theory/Experiment 2a/29-spec(0)-comp(1)-adj(1)-case(1)/linear_phase_theory_corpus_resources.txt",
            ".\language data working directory\study-6-linear-phase-theory/Experiment 2a/210-spec(0)-comp(1)-adj(1)-case(0)/linear_phase_theory_corpus_resources.txt",
            ".\language data working directory\study-6-linear-phase-theory/Experiment 2a/211-spec(0)-comp(1)-adj(0)-case(1)/linear_phase_theory_corpus_resources.txt",
            ".\language data working directory\study-6-linear-phase-theory/Experiment 2a/212-spec(0)-comp(1)-adj(0)-case(0)/linear_phase_theory_corpus_resources.txt",
            ".\language data working directory\study-6-linear-phase-theory/Experiment 2a/213-spec(0)-comp(0)-adj(1)-case(1)/linear_phase_theory_corpus_resources.txt",
            ".\language data working directory\study-6-linear-phase-theory/Experiment 2a/214-spec(0)-comp(0)-adj(1)-case(0)/linear_phase_theory_corpus_resources.txt",
            ".\language data working directory\study-6-linear-phase-theory/Experiment 2a/215-spec(0)-comp(0)-adj(0)-case(1)/linear_phase_theory_corpus_resources.txt",
            ".\language data working directory\study-6-linear-phase-theory/Experiment 2a/216-spec(0)-comp(0)-adj(0)-case(0)/linear_phase_theory_corpus_resources.txt",
            ".\language data working directory\study-6-linear-phase-theory/Experiment 2b/31-Bottom-up/linear_phase_theory_corpus_resources.txt",
            ".\language data working directory\study-6-linear-phase-theory/Experiment 2b/32-Z/linear_phase_theory_corpus_resources.txt",
            ".\language data working directory\study-6-linear-phase-theory/Experiment 2b/33-Sling/linear_phase_theory_corpus_resources.txt",
            ".\language data working directory\study-6-linear-phase-theory/Experiment 2b/36-Bottom-up-no-lexical-anticipation/linear_phase_theory_corpus_resources.txt",
            ".\language data working directory\study-6-linear-phase-theory/Experiment 2b/37-Z-no-lexical-anticipation/linear_phase_theory_corpus_resources.txt",
            ".\language data working directory\study-6-linear-phase-theory/Experiment 2b/38-Sling-no-lexical-anticipation/linear_phase_theory_corpus_resources.txt",
            ".\language data working directory\study-6-linear-phase-theory/Experiment 2c/41-filter-on/linear_phase_theory_corpus_resources.txt",
            ".\language data working directory\study-6-linear-phase-theory/Experiment 2c/42-filter-off/linear_phase_theory_corpus_resources.txt",
            ".\language data working directory\study-6-linear-phase-theory/Experiment 3/55-Optimal parser/linear_phase_theory_corpus_resources.txt",
            ".\language data working directory\study-6-linear-phase-theory/Experiment 3/56-Performance/performance_corpus_resources.txt",
            ".\language data working directory\study-6-linear-phase-theory/Experiment 3/58-no_left_branch_principles_all/linear_phase_theory_corpus_resources.txt",
            ".\language data working directory\study-6-linear-phase-theory/Experiment 3/59-Performance with WM/performance_corpus_resources.txt",
            ".\language data working directory\study-6-linear-phase-theory/Experiment 3/60-Optimal parser with WM/linear_phase_theory_corpus_resources.txt"
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
            data_temp.append(self.format_data(pd.read_csv(filename, dtype={'Sentence': str, 'Study_ID': int, 'Group 0': int, 'Group 1': int, 'Group 2': int, 'Group 3': int}, sep=',', comment='@', encoding="utf-8")))
        self.data = pd.concat(data_temp)
        self.log_file.write(f'Data shape is {self.data.shape} (Rows x Columns)...')
        self.log_file.write(f'\nColumns: {self.data[self.data["Study_ID"]==1].columns}')
        self.log_file.write(f'\nOverall statistics:')
        self.log_file.write(f'\nNumber of sentences in the test corpus: {len(self.data[self.data["Study_ID"]==1].index)}')
        for group in range(1, 11):
            self.log_file.write(f'\n\tGroup {group}: {len(self.data[(self.data["Study_ID"]==1) & (self.data["Group 0"] == group)].index)}')
            self.log_file.write(f'\n\t\tGrammatical: {len(self.data[(self.data["Study_ID"]==1) & (self.data["Group 3"] == 0) & (self.data["Group 0"] == group)].index)}')
            self.log_file.write(f'\n\t\tUngrammatical: {len(self.data[(self.data["Study_ID"] == 1) & (self.data["Group 3"] == 1) & (self.data["Group 0"] == group)].index)}')

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
        self.data = self.data[(self.data['Group 3'] == 0) & (self.data['Total Time'] > 0)]
        self.log_file.write(f'New data shape is{self.data.shape}...Done')

    def add_groups(self):
        def lexical_anticipation(study):
            return 1 if study in {1, 2, 21, 22, 23, 24, 25, 26, 27, 28, 29, 210, 211, 212, 213, 214, 214, 31, 32, 33, 41, 42, 52} else 0
        def Locality_Preference(study):
            return 1 if study in {1, 3, 21, 22, 23, 24, 25, 26, 27, 28, 29, 210, 211, 212, 213, 214, 215, 216, 31, 36} else 0
        def Lexical_anticipation_Case(study):
            return 1 if study in {1, 2, 21, 23, 25, 27, 29, 211, 213, 215, 31, 32, 33, 41, 42, 52} else 0
        def Lexical_anticipation_Adj(study):
            return 1 if study in {1, 2, 21, 22, 25, 26, 29, 210, 213, 214, 31, 32, 33, 41, 42, 52} else 0
        def Lexical_anticipation_Comp(study):
            return 1 if study in {1, 2, 21, 22, 23, 24, 29, 210, 211, 212, 31, 32, 33, 41, 42, 52} else 0
        def Lexical_anticipation_Spec(study):
            return 1 if study in {1, 2, 21, 22, 23, 24, 25, 26, 27, 28, 31, 32, 33, 41, 42, 52} else 0

        self.log_file.write(f'\nAdding group variables...')
        self.data['Lexical Anticipation'] = [lexical_anticipation(study) for study in self.data['Study_ID']]
        self.data['Locality Preference'] = [Locality_Preference(study) for study in self.data['Study_ID']]
        self.data['Lexical Anticipation (Case)'] = [Lexical_anticipation_Case(study) for study in self.data['Study_ID']]
        self.data['Lexical Anticipation (Adj)'] = [Lexical_anticipation_Adj(study) for study in self.data['Study_ID']]
        self.data['Lexical Anticipation (Comp)'] = [Lexical_anticipation_Comp(study) for study in self.data['Study_ID']]
        self.data['Lexical Anticipation (Spec)'] = [Lexical_anticipation_Spec(study) for study in self.data['Study_ID']]
        self.log_file.write(f'Result is {self.data.shape}...')

    def log_experiment_title(self, experiment):
        self.log_file.write('\n\n--------------------------------------------------------------------------------------')
        self.log_file.write(f'\nAnalysis of experiment {experiment}')

    # Experiment 1a
    # Locality preference and lexical anticipation
    # Manuscript section 3.4
    def report_experiment_1a(self):
        self.log_experiment_title('1a Locality preference and lexical anticipation')
        data_exp1 = self.data[(self.data['Study_ID'] > 0) & (self.data['Study_ID'] < 5)]
        self.log_file.write(f'\nSelected studies {set(data_exp1["Study_ID"])}.')
        # Table 2
        # Mean number of garden paths, grammatical operations (Merge) and mean predicted
        # word processing time per sentence as a function of independent variables locality
        # preference and lexical anticipation.
        d2 = data_exp1.melt(id_vars='Study_ID', value_vars=['Mean time per word', 'Merge', 'Garden Paths'])
        self.log_file.write(f'\nTable 2:')
        print(d2)
        self.log_file.write('\n' + str(d2.groupby(['Study_ID', 'Resource']).mean().round(decimals=1)))
        # Results Figure 1
        # Mean predicted cognitive time per word (ms) in an incremental parser as a function
        # of the independent variables locality preference and lexical anticipation.
        self.log_file.write('\n\nCreating Results Figure 1...')
        data_exp1 = self.data[(self.data['Study_ID'] > 0) & (self.data['Study_ID'] < 5)]
        self.log_file.write(f'\nSelected studies {set(data_exp1["Study_ID"])}.')
        cat = {0: 'No', 1: 'Yes'}
        data_exp1['Anticipation'] = [cat[value] for value in data_exp1['Lexical Anticipation']]
        data_exp1['Locality'] = [cat[value] for value in data_exp1['Locality Preference']]
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5))
        sns.set_theme(style="whitegrid")
        h = sns.barplot(data=data_exp1,
                        x='Anticipation',
                        y='Mean time per word',
                        hue='Locality',
                        ci=None,
                        palette='Greys', ax=ax1)
        ax1.set(ylim=(0, 2000), ylabel='Mean predicted cognitive time per word (ms)')
        h = sns.barplot(data=data_exp1,
                        x='Anticipation',
                        y='Merge',
                        hue='Locality',
                        ci=None,
                        palette='Greys', ax=ax2)
        ax2.set(ylim=(0, 40), ylabel='Mean number of attachments')
        h = sns.barplot(data=data_exp1,
                        x='Anticipation',
                        y='Garden Paths',
                        hue='Locality',
                        ci=None,
                        palette='Greys', ax=ax3)
        ax3.set(ylim=(0, 10), ylabel='Mean number of garden paths')
        fig = h.get_figure()
        fig.savefig(STUDY_DIRECTORY + 'Result Figure 1')
        plt.close()
        self.log_file.write('Done.')

        # Figure 1 results in numbers
        d2 = data_exp1.melt(id_vars='Study_ID', value_vars=['Mean time per word', 'Merge', 'Garden Paths'])
        self.log_file.write('\n' + str(d2.groupby(['Study_ID', 'Resource']).max().round(decimals=1)))

        # Processing times over the whole study
        data_exp1 = self.data[(self.data['Study_ID'] > 0) & (self.data['Study_ID'] < 5)]
        self.log_file.write(f'\n\nMean predicted processing time over all experimental groups: {round(data_exp1["Mean time per word"].mean(),1)}')
        self.log_file.write(f'\nMean garden paths all experimental groups: {round(data_exp1["Garden Paths"].mean(), 1)}')

        # Figure 2
        # Processing time as a function of construction type
        self.log_file.write('\n\nCreating Result Figure 2...')
        cat = {1: 'Basic', 2: 'Adjuncts', 3: 'Wh-movement', 4: 'Case', 5: 'Agreement', 6: 'Pro-drop', 7:'Control', 8:'Word order', 9:'Head movement', 10:'Clitics'}
        data_exp1['Construction'] = [cat[value] for value in data_exp1['Group 0']]
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))
        h = sns.barplot(data=data_exp1, x='Construction', y = 'Mean time per word', ci=None, palette='Greys', ax = ax1)
        h = sns.barplot(data=data_exp1, x='Construction', y = 'Garden Paths', ci=None, palette='Greys', ax = ax2)
        ax1.set(ylim=(0, 1400), ylabel='Mean predicted cognitive time per word (ms)')
        ax2.set(ylim=(0, 10), ylabel='Garden paths')
        fig = h.get_figure()
        fig.savefig(STUDY_DIRECTORY + 'Result Figure 2')
        plt.close()
        self.log_file.write('Done.')

        # Figure 3
        # Processing time as a function of construction type with lexical anticipation and locality preference
        self.log_file.write('\n\nCreating Result Figure 3...')
        data_exp2 = data_exp1[(data_exp1['Lexical Anticipation']==1) & (data_exp1['Locality Preference']==1)]
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))
        h = sns.barplot(data=data_exp2, x='Construction', y = 'Mean time per word', ci=None, palette='Greys', ax = ax1)
        h = sns.barplot(data=data_exp2, x='Construction', y = 'Garden Paths', ci=None, palette='Greys', ax = ax2)
        ax1.set(ylim=(0, 1400), ylabel='Mean predicted cognitive time per word (ms)')
        ax2.set(ylim=(0, 10), ylabel='Garden paths')
        fig = h.get_figure()
        fig.savefig(STUDY_DIRECTORY + 'Result Figure 3')
        plt.close()
        self.log_file.write('Done.')

        # Sentences ordered by the number of garden paths
        self.log_file.write('\n\nSentences with most garden paths, with a parser that uses both lexical anticipation and locality preference:\n')
        df = data_exp2.sort_values(by='Garden Paths', ascending=False)
        self.log_file.write(str(df[['Sentence', 'Garden Paths']].head(42)))

        # Result Figure 3
        # Distribution of the mean predicted cognitive time per word, as measured for a
        # realistic parser with lexical anticipation and locality preference.
        data_exp1 = self.data[(self.data['Study_ID'] > 0) &
                              (self.data['Study_ID'] < 5)]
        self.log_file.write(f'\n\nVariation values for realistic parser (lexical anticipation and locality preference):')
        self.log_file.write(f'\n\nMean time per word: ')
        self.log_file.write(f'Min={data_exp1["Mean time per word"].min()}, '
                            f'Max={data_exp1["Mean time per word"].max()}, '
                            f'Mean={data_exp1["Mean time per word"].mean()}, '
                            f'Median={data_exp1["Mean time per word"].median()},'
                            f'Std={data_exp1["Mean time per word"].std()}')

    # Experiment 2a explores different lexical anticipation features (head-comp, head-spec, adjunct, case)
    # Manuscript section 4.2
    def report_experiment_2a(self):
        self.log_experiment_title('2a variations of lexical anticipation')
        data_exp1 = self.data[((self.data['Study_ID'] >= 21) &
                               (self.data['Study_ID'] <= 29)) |
                              ((self.data['Study_ID'] >= 210) &
                               (self.data['Study_ID'] <= 216))]
        self.log_file.write(f'\nSelected studies {set(data_exp1["Study_ID"])}.')
        cat = {0: 'No', 1: 'Yes'}
        data_exp1['Head-complement selection'] = [cat[value] for value in data_exp1['Lexical Anticipation (Comp)']]
        data_exp1['Case-based selection'] = [cat[value] for value in data_exp1['Lexical Anticipation (Case)']]
        data_exp1['Head-specifier selection'] = [cat[value] for value in data_exp1['Lexical Anticipation (Spec)']]
        data_exp1['Adjunct selection'] = [cat[value] for value in data_exp1['Lexical Anticipation (Adj)']]
        # Result Figure 4
        # Main effects of head-complement selection (top left), case matching (top right), specifier selection
        # (bottom left) and adjunct selection (bottom right) in an incremental parser that uses locality preference.
        self.log_file.write('\nCreating Results Figure 4...')
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(10, 8))
        yaxis = (650, 800)
        sns.set_theme(style="whitegrid")
        h = sns.barplot(data=data_exp1,
                        x='Head-complement selection',
                        y='Mean time per word',
                        ci=None,
                        palette='Greys', ax=ax1)
        ax1.set(ylim=yaxis, ylabel='Mean predicted cognitive time per word (ms)')
        g = sns.barplot(data=data_exp1,
                        x='Case-based selection',
                        y='Mean time per word',
                        ci=None,
                        palette='Greys', ax=ax2)
        ax2.set(ylim=yaxis, ylabel='Mean predicted cognitive time per word (ms)')
        j = sns.barplot(data=data_exp1,
                        x='Head-specifier selection',
                        y='Mean time per word',
                        ci=None,
                        palette='Greys', ax=ax3)
        ax3.set(ylim=yaxis, ylabel='Mean predicted cognitive time per word (ms)')
        i = sns.barplot(data=data_exp1,
                        x='Adjunct selection',
                        y='Mean time per word',
                        ci=None,
                        palette='Greys', ax=ax4)
        ax4.set(ylim=yaxis, ylabel='Mean predicted cognitive time per word (ms)')
        fig = i.get_figure()
        fig.savefig(STUDY_DIRECTORY + 'Result Figure 4')
        plt.close()
        self.log_file.write('Done.')
        d2 = data_exp1.melt(id_vars='Head-complement selection', value_vars=['Mean time per word', 'Merge', 'Garden Paths'])
        self.log_file.write(f'\nDetailed values:')
        self.log_file.write('\n' + str(d2.groupby(['Head-complement selection', 'Resource']).mean().round(decimals=1)))
        d2 = data_exp1.melt(id_vars='Case-based selection', value_vars=['Mean time per word', 'Merge', 'Garden Paths'])
        self.log_file.write('\n' + str(d2.groupby(['Case-based selection', 'Resource']).mean().round(decimals=1)))
        d2 = data_exp1.melt(id_vars='Head-specifier selection', value_vars=['Mean time per word', 'Merge', 'Garden Paths'])
        self.log_file.write('\n' + str(d2.groupby(['Head-specifier selection', 'Resource']).mean().round(decimals=1)))
        d2 = data_exp1.melt(id_vars='Adjunct selection', value_vars=['Mean time per word', 'Merge', 'Garden Paths'])
        self.log_file.write('\n' + str(d2.groupby(['Adjunct selection', 'Resource']).mean().round(decimals=1)))

    # Experiment 2b explores the three locality preference principles (bottom-up, Z, sling)
    def report_experiment_2b(self):
        self.log_experiment_title('2b three locality preference principles')
        data_exp1 = self.data[((self.data['Study_ID'] >= 31)&(self.data['Study_ID'] <= 33))|
                               (self.data['Study_ID'] >= 36)&(self.data['Study_ID'] <= 38)]
        self.log_file.write(f'\nSelected studies {set(data_exp1["Study_ID"])}.')
        cat = {31: 'Bottom-up', 32: 'Z', 33: 'Sling', 36: 'Bottom-up', 37: 'Z', 38: 'Sling'}
        data_exp1['Locality'] = [cat[value] for value in data_exp1['Study_ID']]
        self.log_file.write(f'\nSelected studies {sorted(set(data_exp1["Study_ID"]))}.')
        # Result Figure 5
        # Comparisons between the three locality mechanisms (from left to right):
        # bottom-up locality (31), Z-algorithm (32), sling (33), both with (left) and
        # without lexical anticipation (right). Notice that in order to show the minuscule
        # differences between the conditions, the scale of the y-axis was changed between
        # the two results plots.
        self.log_file.write('\nCreating Results Figure 5...')
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))
        sns.set_theme(style="whitegrid")
        sns.barplot(data=data_exp1[data_exp1['Lexical Anticipation'] == 1],
                        x='Locality',
                        y='Mean time per word',
                        ci=None,
                        palette='Greys', ax=ax1)
        ax1.set(ylim=(650, 800), xlabel='Locality mechanism')
        k = sns.barplot(data=data_exp1[data_exp1['Lexical Anticipation'] == 0],
                        x='Locality',
                        y='Mean time per word',
                        ci=None,
                        palette='Greys', ax=ax2)
        ax2.set(ylim=(650, 800), xlabel='Locality mechanism')
        fig = k.get_figure()
        fig.savefig(STUDY_DIRECTORY + 'Result Figure 5')
        plt.close()
        self.log_file.write('Done.')
        self.log_file.write('\nDetailed values:')
        d2 = data_exp1.melt(id_vars='Locality', value_vars=['Mean time per word', 'Merge', 'Garden Paths'])
        self.log_file.write('\n' + str(d2.groupby(['Locality', 'Resource']).mean().round(decimals=1)))

    # Experiment 2c explores the left branch filter (on and off, without lexical anticipation and locality preference)
    # Manuscript section 4.3
    def report_experiment_2c(self):
        self.log_experiment_title('2 left branch filter')
        data_exp1 = self.data[(self.data['Study_ID']==41) | (self.data['Study_ID']==42)]
        self.log_file.write(f'\nSelected studies {set(data_exp1["Study_ID"])}.')
        self.log_file.write(f'\nSelected studies {set(data_exp1["Study_ID"])}.')
        self.log_file.write(f'\nMean predicted cognitive time per word with left branch filter: {round(self.data[self.data["Study_ID"]==41]["Mean time per word"].mean(), 1)}')
        self.log_file.write(f'\nMean predicted cognitive time per word without left branch filter: {round(self.data[self.data["Study_ID"] == 42]["Mean time per word"].mean(), 1)}')

        # Figure 10
        # Processing time as a function of construction type with left branch filter on and off
        self.log_file.write('\n\nCreating Result Figure 10...')
        cat = {1: 'Basic', 2: 'Adjuncts', 3: 'Wh-movement', 4: 'Case', 5: 'Agreement', 6: 'Pro-drop', 7: 'Control',
               8: 'Word order', 9: 'Head movement', 10: 'Clitics'}
        data_exp1['Construction'] = [cat[value] for value in data_exp1['Group 0']]
        data_exp1['Left branch filter'] = ['Yes' if study_id == 41 else 'No' for study_id in data_exp1['Study_ID']]
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))
        h = sns.barplot(data=data_exp1, x='Construction', y = 'Mean time per word', hue = 'Left branch filter', ci=None, palette='Greys', ax = ax1)
        h = sns.barplot(data=data_exp1, x='Construction', y = 'Garden Paths', hue = 'Left branch filter', ci=None, palette='Greys', ax = ax2)
        ax1.set(ylim=(0, 3000), ylabel='Mean predicted cognitive time per word (ms)')
        ax2.set(ylim=(0, 25), ylabel='Garden paths')
        fig = h.get_figure()
        fig.savefig(STUDY_DIRECTORY + 'Result Figure 10')
        plt.close()
        self.log_file.write('Done.')

        self.log_experiment_title('3a Benchmark values for the optimal parser')
        self.log_file.write('\nBenchmark values for the optimal parser:')
        data_exp1 = self.data[self.data['Study_ID']==55]
        self.log_file.write(f'\nSelected studies {set(data_exp1["Study_ID"])}.')

        # Figure 11
        # Processing time as a function of construction type two optimal parsers
        self.log_file.write('\n\nCreating Result Figure 11...')
        data_exp1 = self.data[(self.data['Study_ID'] == 1) | (self.data['Study_ID']==55)]
        cat = {1: 'Basic', 2: 'Adjuncts', 3: 'Wh-movement', 4: 'Case', 5: 'Agreement', 6: 'Pro-drop', 7: 'Control',
               8: 'Word order', 9: 'Head movement', 10: 'Clitics'}
        data_exp1['Construction'] = [cat[value] for value in data_exp1['Group 0']]
        data_exp1['Left branch filter'] = ['Yes' if study_id == 55 else 'No' for study_id in data_exp1['Study_ID']]
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))
        h = sns.barplot(data=data_exp1, x='Construction', y='Mean time per word', hue='Left branch filter', ci=None,
                        palette='Greys', ax=ax1)
        h = sns.barplot(data=data_exp1, x='Construction', y='Garden Paths', hue='Left branch filter', ci=None,
                        palette='Greys', ax=ax2)
        ax1.set(ylim=(0, 1000), ylabel='Mean predicted cognitive time per word (ms)')
        ax2.set(ylim=(0, 5), ylabel='Garden paths')
        fig = h.get_figure()
        fig.savefig(STUDY_DIRECTORY + 'Result Figure 11')
        plt.close()
        self.log_file.write('Done.')

    # Experiment 3a
    # Manuscript section 5
    def report_experiment_3a(self):


        self.log_experiment_title('5.2 Garden paths by lexical selection')
        data_exp1 = self.data[self.data['Study_ID'] == 56]
        self.log_file.write(f'\nSelected studies {set(data_exp1["Study_ID"])}.')
        self.log_file.write('\n Mean time per word:')
        self.log_file.write('\nJohn knows the solution to the problem: ' + str(data_exp1[data_exp1['Sentence'] == 'John knows the solution to the problem ']['Mean time per word'].mean()))
        self.log_file.write('\nJohn knows the solution to the problem disappeared: ' + str(data_exp1[data_exp1['Sentence'] == 'John knows the solution to the problem disappeared ']['Mean time per word'].mean()))
        self.log_file.write('\n Garden Paths:')
        self.log_file.write('\nJohn knows the solution to the problem: ' + str(data_exp1[data_exp1['Sentence'] == 'John knows the solution to the problem ']['Garden Paths'].mean()))
        self.log_file.write('\nJohn knows the solution to the problem disappeared: ' + str(data_exp1[data_exp1['Sentence'] == 'John knows the solution to the problem disappeared ']['Garden Paths'].mean()))
        self.log_file.write('\n Merge:')
        self.log_file.write('\nJohn knows the solution to the problem: ' + str(data_exp1[data_exp1['Sentence'] == 'John knows the solution to the problem ']['Merge'].mean()))
        self.log_file.write('\nJohn knows the solution to the problem disappeared: ' + str(data_exp1[data_exp1['Sentence'] == 'John knows the solution to the problem disappeared ']['Merge'].mean()))
        self.log_file.write('\n\n Mean time per word:')
        self.log_file.write('\nJohn claims the solution to the problem disappeared: ' + str(data_exp1[data_exp1['Sentence'] == 'John claims the solution to the problem disappeared ']['Mean time per word'].mean()))
        self.log_file.write('\n Garden Paths:')
        self.log_file.write('\nJohn claims the solution to the problem disappeared: ' + str(data_exp1[data_exp1['Sentence'] == 'John claims the solution to the problem disappeared ']['Garden Paths'].mean()))
        self.log_file.write('\n Merge:')
        self.log_file.write('\nJohn claims the solution to the problem disappeared: ' + str(data_exp1[data_exp1['Sentence'] == 'John claims the solution to the problem disappeared ']['Merge'].mean()))

        # Experiment 5.3 Lexical ambiguity garden paths
        # Manuscript Section 5.3
        self.log_experiment_title('5.3 Lexical ambiguity')
        data_exp1 = self.data[self.data['Study_ID']==56]
        self.log_file.write(f'\nSelected studies {set(data_exp1["Study_ID"])}.')
        self.log_file.write('\n Mean time per word:')
        self.log_file.write('\nThe horse raced past the barn: '+str(data_exp1[data_exp1['Sentence'] == 'the horse raced past the barn ']['Mean time per word'].mean()))
        self.log_file.write('\nThe horse raced past the barn fell: ' + str(data_exp1[data_exp1['Sentence'] == 'the horse raced past the barn fell ']['Mean time per word'].mean()))
        self.log_file.write('\n Garden Paths:')
        self.log_file.write('\nThe horse raced past the barn: ' + str(data_exp1[data_exp1['Sentence'] == 'the horse raced past the barn ']['Garden Paths'].mean()))
        self.log_file.write('\nThe horse raced past the barn fell: ' + str(data_exp1[data_exp1['Sentence'] == 'the horse raced past the barn fell ']['Garden Paths'].mean()))
        self.log_file.write('\n Merge:')
        self.log_file.write('\nThe horse raced past the barn: ' + str(data_exp1[data_exp1['Sentence'] == 'the horse raced past the barn ']['Merge'].mean()))
        self.log_file.write('\nThe horse raced past the barn fell: ' + str(data_exp1[data_exp1['Sentence'] == 'the horse raced past the barn fell ']['Merge'].mean()))

        # Manuscript section 5.4
        self.log_experiment_title('5.4 Nested operator movement')
        data_exp1 = self.data[self.data['Study_ID'] == 56]
        self.log_file.write(f'\nSelected studies {set(data_exp1["Study_ID"])}.')
        self.log_file.write('\nMita kaupunkia kohti virtaamalla Seine saavuttaa meren, mean time per word: ')
        self.log_file.write('\n time: ' + str(data_exp1[data_exp1['Sentence'] == 'mita kaupunkia kohti virtaamalla Seine saavuttaa meren ']['Mean time per word'].mean()))
        self.log_file.write('\n Garden paths: ' + str(data_exp1[data_exp1['Sentence'] == 'mita kaupunkia kohti virtaamalla Seine saavuttaa meren ']['Garden Paths'].mean()))
        self.log_file.write('\n Merge: ' + str(data_exp1[data_exp1['Sentence'] == 'mita kaupunkia kohti virtaamalla Seine saavuttaa meren ']['Merge'].mean()))

        # Manuscript section 5.5
        self.log_experiment_title('5.5 Relative clauses and working memory')
        data_exp1 = self.data[self.data['Study_ID']==56]
        self.log_file.write(f'\nSelected studies {set(data_exp1["Study_ID"])}.')
        self.log_file.write(str(data_exp1.shape))
        self.log_file.write('\n\nSubject relative clauses/time per word: ' +
                            str(round(data_exp1.loc[(data_exp1['Group 0']==1) & (data_exp1['Group 1']==1)]['Mean time per word'].mean(), 1)))
        self.log_file.write('\nSubject relative clauses/Garden paths: ' +
                            str(round(data_exp1.loc[(data_exp1['Group 0']==1) & (data_exp1['Group 1']==1)]['Garden Paths'].mean(), 1)))
        self.log_file.write('\nSubject relative clauses/Merge: ' +
                            str(round(data_exp1.loc[(data_exp1['Group 0']==1) & (data_exp1['Group 1']==1)]['Merge'].mean(), 1)))
        self.log_file.write('\n\nObject relative clauses/time per word: ' +
                            str(round(data_exp1.loc[(data_exp1['Group 0']==1) & (data_exp1['Group 1']==2)]['Mean time per word'].mean(), 1)))
        self.log_file.write('\nObject relative clauses/Garden paths: ' +
                            str(round(data_exp1.loc[(data_exp1['Group 0']==1) & (data_exp1['Group 1']==2)]['Garden Paths'].mean(), 1)))
        self.log_file.write('\nObject relative clauses/Merge: ' +
                            str(round(data_exp1.loc[(data_exp1['Group 0']==1) & (data_exp1['Group 1']==2)]['Merge'].mean(), 1)))
        self.log_file.write('\n\nCenter-embedded relative clauses/time per word: ' +
                            str(round(data_exp1.loc[(data_exp1['Group 0']==1) & (data_exp1['Group 1']==3)]['Mean time per word'].mean(), 1)))
        self.log_file.write('\nCenter-embedded clauses/Garden paths: ' +
                            str(round(data_exp1.loc[(data_exp1['Group 0']==1) & (data_exp1['Group 1']==3)]['Garden Paths'].mean(), 1)))
        self.log_file.write('\nCenter-embedded clauses/Merge: ' +
                            str(round(data_exp1.loc[(data_exp1['Group 0']==1) & (data_exp1['Group 1']==3)]['Merge'].mean(), 1)))

        self.log_experiment_title('3c left-blind parser')
        self.log_file.write('\nBenchmark values for the parser without left branch filter and specifier selection:')
        data_exp1 = self.data[self.data['Study_ID']==58]
        self.log_file.write(f'\nSelected studies {set(data_exp1["Study_ID"])}.')
        self.log_file.write(f'\n{round(data_exp1.mean(),1)}')

        self.log_experiment_title('3d left-blind parser')
        data_exp1 = self.data[(self.data['Study_ID']==58) | (self.data['Study_ID']==55)]
        self.log_file.write(f'\nSelected studies {set(data_exp1["Study_ID"])}.')
        data_exp1['Left blindness'] = 'No'
        data_exp1.loc[data_exp1.Study_ID==58, 'Left blindness'] = 'Yes'
        self.log_file.write('\nDetailed valuess:')
        d2 = data_exp1.melt(id_vars='Left blindness', value_vars=['Mean time per word', 'Merge', 'Garden Paths'])
        self.log_file.write('\n' + str(d2.groupby(['Left blindness', 'Resource']).mean().round(decimals=1)))

        # Experiment 3d relative clauses and working memory
        # Manuscript section 5.5
        self.log_experiment_title('3d Relative clauses with working memory')
        data_exp1 = self.data[self.data['Study_ID'] == 59]
        self.log_file.write('\n\nSubject relative clauses/time per word: ' +
                            str(round(data_exp1.loc[(data_exp1['Group 0'] == 1) & (data_exp1['Group 1'] == 1)][
                                          'Mean time per word'].mean(), 1)))
        self.log_file.write('\nSubject relative clauses/Garden paths: ' +
                            str(round(data_exp1.loc[(data_exp1['Group 0'] == 1) & (data_exp1['Group 1'] == 1)][
                                          'Garden Paths'].mean(), 1)))
        self.log_file.write('\nSubject relative clauses/Merge: ' +
                            str(round(data_exp1.loc[(data_exp1['Group 0'] == 1) & (data_exp1['Group 1'] == 1)][
                                          'Merge'].mean(), 1)))
        self.log_file.write('\n\nObject relative clauses/time per word: ' +
                            str(round(data_exp1.loc[(data_exp1['Group 0'] == 1) & (data_exp1['Group 1'] == 2)][
                                          'Mean time per word'].mean(), 1)))
        self.log_file.write('\nObject relative clauses/Garden paths: ' +
                            str(round(data_exp1.loc[(data_exp1['Group 0'] == 1) & (data_exp1['Group 1'] == 2)][
                                          'Garden Paths'].mean(), 1)))
        self.log_file.write('\nObject relative clauses/Merge: ' +
                            str(round(data_exp1.loc[(data_exp1['Group 0'] == 1) & (data_exp1['Group 1'] == 2)][
                                          'Merge'].mean(), 1)))
        self.log_file.write('\n\nCenter-embedded relative clauses/time per word: ' +
                            str(round(data_exp1.loc[(data_exp1['Group 0'] == 1) & (data_exp1['Group 1'] == 3)][
                                          'Mean time per word'].mean(), 1)))
        self.log_file.write('\nCenter-embedded clauses/Garden paths: ' +
                            str(round(data_exp1.loc[(data_exp1['Group 0'] == 1) & (data_exp1['Group 1'] == 3)][
                                          'Garden Paths'].mean(), 1)))
        self.log_file.write('\nCenter-embedded clauses/Merge: ' +
                            str(round(data_exp1.loc[(data_exp1['Group 0'] == 1) & (data_exp1['Group 1'] == 3)][
                                          'Merge'].mean(), 1)))

        # Test increase of cognitive load as a function of the number of center-embedding
        # Result Figure 8
        data_exp1 = self.data[(self.data['Study_ID'] == 59) & (self.data['Group 0'] == 1) & (self.data['Group 1'] == 4)]
        data_exp1['Mean time per word'] = [value for value in data_exp1['Mean time per word']]
        self.log_file.write('\nCreating Results Figure 8...')
        plt.ylim(0, 100000)
        sns.set_theme(style="whitegrid")
        g = sns.barplot(data=data_exp1,
                        x='Group 2',
                        y='Mean time per word',
                        ci=None,
                        palette='Greys')
        g.set(xlabel='Number of center-embeddings', ylabel='Mean predicted cognitive time per word (ms)')
        fig = g.get_figure()
        fig.savefig(STUDY_DIRECTORY + 'Result Figure 8')
        plt.close()
        self.log_file.write('Done.')

        # Running the whole test corpus with WP
        # Result Figure 9
        self.log_experiment_title('3d Test corpus with working memory')
        data_exp1 = self.data[(self.data['Study_ID'] == 60) | (self.data['Study_ID']==55)]
        data_exp1['Working memory restraint'] = 'No'
        data_exp1.loc[data_exp1.Study_ID==60, 'Working memory restraint'] = 'Yes'
        self.log_file.write('\nCreating Results Figure 9...')
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5))
        sns.set_theme(style='whitegrid')
        h = sns.barplot(data=data_exp1,
                        x='Working memory restraint',
                        y='Mean time per word',
                        ci=None,
                        palette='Greys', ax=ax1)
        ax1.set(ylim=(650, 1000), xlabel='Working memory barrier', ylabel='Mean predicted cognitive time per word (ms)')
        fig = h.get_figure()
        sns.set_theme(style='whitegrid')
        h = sns.barplot(data=data_exp1,
                        x='Working memory restraint',
                        y='Merge',
                        ci=None,
                        palette='Greys', ax=ax2)
        ax2.set(ylim=(5, 10), xlabel='Working memory barrier', ylabel='Mean attachment operations')
        fig = h.get_figure()
        h = sns.barplot(data=data_exp1,
                        x='Working memory restraint',
                        y='Garden Paths',
                        ci=None,
                        palette='Greys', ax=ax3)
        ax3.set(ylim=(0, 2), xlabel='Working memory barrier', ylabel='Mean garden paths')
        fig.savefig(STUDY_DIRECTORY + 'Result Figure 9')
        plt.close()
        self.log_file.write('Done.')
        d2 = data_exp1.melt(id_vars='Group 2', value_vars=['Mean time per word', 'Merge', 'Garden Paths'])
        self.log_file.write('\n' + str(d2.groupby(['Group 2', 'Resource']).mean().round(decimals=1)))

        data_exp1 = self.data[self.data['Study_ID']==56]
        data_e = data_exp1[data_exp1['Sentence'] == 'that that John sleeps surprised Mary surprised John ']
        self.log_file.write('\nthat that -clause...')
        self.log_file.write('\nGarden paths:' + str(data_e['Garden Paths'].mean()))
        self.log_file.write('\nMerge:'+ str(data_e["Merge"].mean()))
        self.log_file.write('\nMean time per word:' + str(data_e["Mean time per word"].mean()))

        #
        # Appendix A
        # Performance properties of all parser models examined in the study
        self.log_file.write('\n\nProperties of all parser models:\n')
        data_exp1 = self.data
        pd.set_option('display.max_rows', 1000)
        d2 = data_exp1.melt(id_vars='Study_ID', value_vars=['Mean time per word', 'Merge', 'Garden Paths', 'Asymmetric Merge', 'Move Phrase'])
        self.log_file.write('\n' + str(d2.groupby(['Study_ID', 'Resource']).mean().round(decimals=2)))