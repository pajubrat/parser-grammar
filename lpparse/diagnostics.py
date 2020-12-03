import pandas as pd
from numpy import median
from matplotlib import pyplot as plt
import seaborn as sns

class Diagnostics:
    def __init__(self):
        self.data_from_experiment = {}          # Dict of dicts {'Experiment': {'Substudy': DataFrame, 'Substudy': DataFrame..., 'all': DataFrame}}

    def run_resource_diagnostics(self):
        # Experiment 1
        # self.read_data(experiment='1')
        # self.remove_ungrammatical_sentences(experiment='1')
        # self.add_combined_metrics(experiment='1')
        # self.data_preparation(experiment='1')
        # self.combine_all_into_one(experiment='1')
        # self.report_experiment_1(['Mean time per word', 'Merge', 'Garden Paths'])
        # self.save_problem_sentences(experiment='1', group='1')

        # Experiment 1b (random closure algorithm)
        # self.read_data(experiment='1b')
        # self.remove_ungrammatical_sentences(experiment='1b')
        # self.add_combined_metrics(experiment='1b')
        # self.report_experiment_1b(['Mean time per word', 'Merge', 'Garden Paths'])

        # Experiment 2a
        # self.read_data(experiment='2a')
        # self.remove_ungrammatical_sentences(experiment='2a')
        # self.data_preparation(experiment='2a')
        # self.combine_all_into_one(experiment='2a')
        # self.report_experiment_2a(['Mean time per word', 'Merge', 'Garden Paths'])

        # Experiment 2b
        # self.read_data(experiment='2b')
        # self.remove_ungrammatical_sentences(experiment='2b')
        # self.data_preparation(experiment='2b')
        # self.combine_all_into_one(experiment='2b')
        # self.report_experiment_2b(['Mean time per word', 'Merge', 'Garden Paths'])

        # Experiment 2c
        # self.read_data(experiment='2c')
        # self.remove_ungrammatical_sentences(experiment='2c')
        # self.combine_all_into_one(experiment='2c')
        # self.report_experiment_2c(['Mean time per word', 'Merge', 'Garden Paths'])

        # Experiment 2d
        self.read_data(experiment='2d')
        self.remove_ungrammatical_sentences(experiment='2d')
        self.combine_all_into_one(experiment='2d')
        self.report_experiment_2d(['Mean time per word', 'Merge', 'Garden Paths'])

    def report_experiment_1(self, resources):
        # Produce data
        d2 = self.data_from_experiment['1']['all'].melt(id_vars='Study_ID', value_vars=resources)
        print(d2.groupby(['Study_ID', 'Resource']).mean().round(decimals=1))
        # Produce Figure 1
        plt.ylim(0, 30000)
        sns.set_theme(style="whitegrid")
        g = sns.barplot(data=self.data_from_experiment['1']['all'],
                        x='Lexical anticipation',
                        y='Mean time per word',
                        hue='Bottom-up closure',
                        ci=None,
                        capsize=.2)
        fig = g.get_figure()
        fig.savefig('Figure 1')
        plt.show()

    def report_experiment_1b(self, resources):
        print(self.data_from_experiment['1b']['1'])
        d2 = self.data_from_experiment['1b']['1'].melt(id_vars='Study_ID', value_vars=resources)
        print(d2.groupby(['Study_ID', 'Resource']).mean().round(decimals=1))

    def report_experiment_2a(self, resources):
        print(self.data_from_experiment['2a'])
        g = sns.barplot(data=self.data_from_experiment['2a']['all'],
                        x='Lexical anticipation Spec',
                        ci=None,
                        y='Garden Paths')
        plt.show()
        d2 = self.data_from_experiment['2a']['all'].melt(id_vars='Study_ID', value_vars=resources)
        print(d2.groupby(['Study_ID', 'Resource']).mean().round(decimals=2))

        g = sns.barplot(data=self.data_from_experiment['2a']['all'])

    def report_experiment_2b(self, resources):
        print(f"Mean time per word with lexical anticipation: {self.data_from_experiment['2b']['all']['Mean time per word'].loc[self.data_from_experiment['2b']['all']['Lexical anticipation'] == 1].mean()}")
        print(f"Mean time per word in the optimal condition: {self.data_from_experiment['2b']['1'].mean()}.")
        g = sns.barplot(data=self.data_from_experiment['2b']['all'], x='Study_ID', y='Mean time per word')
        plt.show()

    def report_experiment_2c(self, resources):
        plt.ylim(750, 950)
        g = sns.barplot(data=self.data_from_experiment['2c']['all'], x='Study_ID', y='Mean time per word')
        plt.show()

    def report_experiment_2d(self, resources):
        g = sns.barplot(data=self.data_from_experiment['2d']['all'], x='Study_ID', y='Mean time per word')
        plt.show()


    def save_problem_sentences(self, experiment, group):
        df2 = self.data_from_experiment[experiment][group].sort_values(by=['Garden Paths', 'Mean time per word'], ascending=False)
        df2[['Number', 'Sentence', 'Garden Paths', 'Mean time per word']].to_csv('./language data working directory/study-6-linear-phase-theory/Experiment '+experiment+'a/problem_sentences.txt')

    def combine_all_into_one(self, experiment='1'):
        self.data_from_experiment[experiment]['all'] = pd.concat(self.data_from_experiment[experiment])

    def read_data(self, experiment='1'):
        files_to_read = []
        if experiment=='1':
            files_to_read = \
                [
                ".\language data working directory\study-6-linear-phase-theory/Experiment 1a/01-1-1\linear_phase_theory_corpus_resources.txt",
                ".\language data working directory\study-6-linear-phase-theory/Experiment 1a/02-1-0\linear_phase_theory_corpus_resources.txt",
                ".\language data working directory\study-6-linear-phase-theory/Experiment 1a/03-0-1\linear_phase_theory_corpus_resources.txt",
                ".\language data working directory\study-6-linear-phase-theory/Experiment 1a/04-0-0\linear_phase_theory_corpus_resources.txt"
                ]
        if experiment=='1b':
            files_to_read = \
                [
                ".\language data working directory\study-6-linear-phase-theory/Experiment 1a/05-0-R\linear_phase_theory_corpus_resources.txt"
                ]
        if experiment=='2a':
            files_to_read = \
                [
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
                ".\language data working directory\study-6-linear-phase-theory/Experiment 2a/216-spec(0)-comp(0)-adj(0)-case(0)/linear_phase_theory_corpus_resources.txt"
                ]
        if experiment=='2b':
            files_to_read = \
                [
                    ".\language data working directory\study-6-linear-phase-theory/Experiment 2b/31-Bottom-up/linear_phase_theory_corpus_resources.txt",
                    ".\language data working directory\study-6-linear-phase-theory/Experiment 2b/32-Z/linear_phase_theory_corpus_resources.txt",
                    ".\language data working directory\study-6-linear-phase-theory/Experiment 2b/33-Sling/linear_phase_theory_corpus_resources.txt",
                    ".\language data working directory\study-6-linear-phase-theory/Experiment 2b/34-Random/linear_phase_theory_corpus_resources.txt",
                    ".\language data working directory\study-6-linear-phase-theory/Experiment 2b/35-Top-down/linear_phase_theory_corpus_resources.txt",
                    ".\language data working directory\study-6-linear-phase-theory/Experiment 2b/36-Bottom-up-no-lexical-anticipation/linear_phase_theory_corpus_resources.txt",
                    ".\language data working directory\study-6-linear-phase-theory/Experiment 2b/37-Z-no-lexical-anticipation/linear_phase_theory_corpus_resources.txt",
                    ".\language data working directory\study-6-linear-phase-theory/Experiment 2b/38-Sling-no-lexical-anticipation/linear_phase_theory_corpus_resources.txt",
                    ".\language data working directory\study-6-linear-phase-theory/Experiment 2b/39-Random-no-lexical-anticipation/linear_phase_theory_corpus_resources.txt",
                    ".\language data working directory\study-6-linear-phase-theory/Experiment 2b/310-Top-down-no-lexical-anticipation/linear_phase_theory_corpus_resources.txt"
                ]
        if experiment=='2c':
            files_to_read = \
                [
                    ".\language data working directory\study-6-linear-phase-theory/Experiment 2c/41-filter-on/linear_phase_theory_corpus_resources.txt",
                    ".\language data working directory\study-6-linear-phase-theory/Experiment 2c/42-filter-off/linear_phase_theory_corpus_resources.txt"
                ]

        if experiment=='2d':
            files_to_read = \
                [
                    ".\language data working directory\study-6-linear-phase-theory/Experiment 2d/51-BU(1)-LA(0)-F(0)/linear_phase_theory_corpus_resources.txt",
                    ".\language data working directory\study-6-linear-phase-theory/Experiment 2d/52-BU(0)-LA(1)-F(0)/linear_phase_theory_corpus_resources.txt",
                    ".\language data working directory\study-6-linear-phase-theory/Experiment 2d/53-BU(0)-LA(0)-F(1)/linear_phase_theory_corpus_resources.txt",
                    ".\language data working directory\study-6-linear-phase-theory/Experiment 2d/54-BU(0)-LA(0)-F(0)/linear_phase_theory_corpus_resources.txt"
                ]

        self.csv_into_data(files_to_read, experiment)

    def csv_into_data(self, files_to_read, experiment='1'):
        self.data_from_experiment[experiment] = {}
        for i, filename in enumerate(files_to_read, start=1):
            new_data = pd.read_csv(filename, dtype={'Sentence': str, 'Study_ID': int, 'Group 0': int, 'Group 1': int, 'Group 2': int, 'Group 3': int}, sep=',', comment='@', encoding="utf-8")
            new_data = new_data.fillna(0)
            for col in new_data:
                if col != 'Sentence':
                    new_data[col] = new_data[col].astype(int)
            new_data.name = 'Resource Consumption per Construction Type'
            new_data.columns.name = 'Resource'
            self.data_from_experiment[experiment][str(i)] = new_data

    def remove_ungrammatical_sentences(self, experiment='1'):
        for key in self.data_from_experiment[experiment]:
            self.data_from_experiment[experiment][key] = self.data_from_experiment[experiment][key][(self.data_from_experiment[experiment][key]['Group 3'] == 0) & (self.data_from_experiment[experiment][key]['Total Time'] > 0)]

    def add_combined_metrics(self, experiment='1'):
        for key in self.data_from_experiment[experiment]:
            self.data_from_experiment[experiment][key]['Relative load'] = self.data_from_experiment[experiment][key]['Asymmetric Merge'] / self.data_from_experiment[experiment][key]['Sentence'].str.len()
            self.data_from_experiment[experiment][key]['Move'] = self.data_from_experiment[experiment][key]['Move Phrase'] + self.data_from_experiment[experiment][key]['Move Head']

    def data_preparation(self, experiment='1'):
        if experiment=='1':
            for key in self.data_from_experiment[experiment]:
                if key in {'1', '2'}:
                    self.data_from_experiment[experiment][key]['Lexical anticipation'] = 1
                else:
                    self.data_from_experiment[experiment][key]['Lexical anticipation'] = 0
                if key in {'1', '3'}:
                    self.data_from_experiment[experiment][key]['Bottom-up closure'] = 1
                else:
                    self.data_from_experiment[experiment][key]['Bottom-up closure'] = 0
        if experiment=='2a':
            for key in self.data_from_experiment[experiment]:
                if key in {'1', '3', '5', '6', '9', '11', '13', '15'}:
                    self.data_from_experiment[experiment][key]['Lexical anticipation Case'] = 1
                else:
                    self.data_from_experiment[experiment][key]['Lexical anticipation Case'] = 0
                if key in {'1', '2', '5', '6', '9', '10', '13', '14'}:
                    self.data_from_experiment[experiment][key]['Lexical anticipation Adj'] = 1
                else:
                    self.data_from_experiment[experiment][key]['Lexical anticipation Adj'] = 0
                if key in {'1', '2', '3', '4', '9', '10', '11', '12'}:
                    self.data_from_experiment[experiment][key]['Lexical anticipation Comp'] = 1
                else:
                    self.data_from_experiment[experiment][key]['Lexical anticipation Comp'] = 0
                if key in {'1', '2', '3', '4', '5', '6', '7', '8'}:
                    self.data_from_experiment[experiment][key]['Lexical anticipation Spec'] = 1
                else:
                    self.data_from_experiment[experiment][key]['Lexical anticipation Spec'] = 0
        if experiment=='2b':
            for key in self.data_from_experiment[experiment]:
                if key in {'1', '2', '3', '4', '5'}:
                    self.data_from_experiment[experiment][key]['Lexical anticipation'] = 1
                else:
                    self.data_from_experiment[experiment][key]['Lexical anticipation'] = 0

