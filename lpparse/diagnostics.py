import pandas as pd
from numpy import median
from matplotlib import pyplot as plt
import seaborn as sns

class Diagnostics:
    def __init__(self):
        self.data_from_experiment = {}          # Dict of dicts {'Experiment': {'Substudy': DataFrame, 'Substudy': DataFrame..., 'all': DataFrame}}

    def run_resource_diagnostics(self):
        # Experiment 1
        #self.read_data(experiment='1')
        #self.remove_ungrammatical_sentences(experiment='1')
        #self.add_combined_metrics(experiment='1')
        #self.combine_all_into_one(experiment='1')
        #self.Report_Experiment_1(['Mean time per word', 'Merge', 'Garden Paths'])

        # Experiment 2
        #self.read_data(experiment='2')
        #self.remove_ungrammatical_sentences(experiment='2')
        #self.combine_all_into_one(experiment='2')
        #self.Experiment_2()

        # Experiment 3
        self.read_data(experiment='3')
        self.remove_ungrammatical_sentences(experiment='3')
        self.combine_all_into_one(experiment='3')
        self.Report_Experiment_3(['Mean time per word', 'Merge', 'Garden Paths'])
        self.save_problem_sentences(experiment='3')

    def Report_Experiment_3(self, resources):
        print(self.data_from_experiment['3'])
        plt.ylim(680, 750)
        g = sns.barplot(data=self.data_from_experiment['3']['all'], x='Study_ID', y='Mean time per word', ci=68, capsize=.2)
        plt.show()
        d2 = self.data_from_experiment['3']['all'].melt(id_vars='Study_ID', value_vars=resources)
        print(d2.groupby(['Study_ID', 'Resource']).mean().round(decimals=2))

    def Report_Experiment_1(self, resources):

        # Arrange data so that id_vars, value_vars behave like group variables
        print(self.data_from_experiment['1'])
        d2 = self.data_from_experiment['1']['all'].melt(id_vars='Study_ID', value_vars=resources)
        print(d2.groupby(['Study_ID', 'Resource']).mean().round(decimals=2))
        self.save_problem_sentences(experiment='3')

        sns.set_theme(style="whitegrid")
        plt.ylim(800, 15000)
        g = sns.barplot(data=self.data_from_experiment['1']['all'], x='Filter', y='Mean time per word', ci=68, capsize=.2)
        plt.show()
        plt.ylim(800, 15000)
        g = sns.barplot(data=self.data_from_experiment['1']['all'], x='Lexical ranking', y='Mean time per word', ci=68, capsize=.2)
        plt.show()
        plt.ylim(800, 15000)
        g = sns.barplot(data=self.data_from_experiment['1']['all'], x='Late closure', y='Mean time per word', ci=68, capsize=.2)
        plt.show()

    def Experiment_2(self):
        print(self.data_from_experiment['2']['all'])
        plt.ylim(800, 860)
        g = sns.barplot(data=self.data_from_experiment['2']['all'], x='Study_ID', y='Mean time per word', ci=68, capsize=.2)
        plt.show()

    def save_problem_sentences(self, experiment):
        df2 = self.data_from_experiment[experiment]['1'].sort_values(by=['Garden Paths', 'Mean time per word'], ascending=False)
        df2[['Number', 'Sentence', 'Garden Paths', 'Mean time per word']].to_csv('./language data working directory/study-6-linear-phase-theory/Experiment '+experiment+'/problem_sentences.txt')

    def combine_all_into_one(self, experiment='1'):
        self.data_from_experiment[experiment]['all'] = pd.concat(self.data_from_experiment[experiment])

    def read_data(self, experiment='1'):
        files_to_read = []
        if experiment=='1':
            files_to_read = \
                [
                ".\language data working directory\study-6-linear-phase-theory/Experiment 1/1-1-1-1\linear_phase_theory_corpus_resources.txt",
                ".\language data working directory\study-6-linear-phase-theory/Experiment 1/2-1-1-0\linear_phase_theory_corpus_resources.txt",
                ".\language data working directory\study-6-linear-phase-theory/Experiment 1/3-1-0-1\linear_phase_theory_corpus_resources.txt",
                ".\language data working directory\study-6-linear-phase-theory/Experiment 1/4-1-0-0\linear_phase_theory_corpus_resources.txt",
                ".\language data working directory\study-6-linear-phase-theory/Experiment 1/5-0-1-1\linear_phase_theory_corpus_resources.txt",
                ".\language data working directory\study-6-linear-phase-theory/Experiment 1/6-0-1-0\linear_phase_theory_corpus_resources.txt",
                ".\language data working directory\study-6-linear-phase-theory/Experiment 1/7-0-0-1\linear_phase_theory_corpus_resources.txt",
                ".\language data working directory\study-6-linear-phase-theory/Experiment 1/8-0-0-0\linear_phase_theory_corpus_resources.txt",
                ".\language data working directory\study-6-linear-phase-theory/Experiment 1/9-1-1-1-1\linear_phase_theory_corpus_resources.txt"
                ]
        if experiment=='2':
            files_to_read = \
                [
                ".\language data working directory\study-6-linear-phase-theory/Experiment 2/1-Bottom-up\linear_phase_theory_corpus_resources.txt",
                ".\language data working directory\study-6-linear-phase-theory/Experiment 2/2-Z\linear_phase_theory_corpus_resources.txt",
                ".\language data working directory\study-6-linear-phase-theory/Experiment 2/3-Random\linear_phase_theory_corpus_resources.txt",
                ".\language data working directory\study-6-linear-phase-theory/Experiment 2/4-Top-down\linear_phase_theory_corpus_resources.txt",
                ".\language data working directory\study-6-linear-phase-theory/Experiment 2/5-Sling\linear_phase_theory_corpus_resources.txt"
                ]
        if experiment=='3':
            files_to_read = \
                [
                ".\language data working directory\study-6-linear-phase-theory/Experiment 3/3-0 knockouts\linear_phase_theory_corpus_resources.txt",
                ".\language data working directory\study-6-linear-phase-theory/Experiment 3/3-1 knockouts\linear_phase_theory_corpus_resources.txt",
                ".\language data working directory\study-6-linear-phase-theory/Experiment 3/3-2 knockouts\linear_phase_theory_corpus_resources.txt",
                ".\language data working directory\study-6-linear-phase-theory/Experiment 3/3-3 knockouts\linear_phase_theory_corpus_resources.txt",
                ".\language data working directory\study-6-linear-phase-theory/Experiment 3/3-4 knockouts\linear_phase_theory_corpus_resources.txt",
                ".\language data working directory\study-6-linear-phase-theory/Experiment 3/3-5 knockouts\linear_phase_theory_corpus_resources.txt",
                ".\language data working directory\study-6-linear-phase-theory/Experiment 3/3-6 knockouts\linear_phase_theory_corpus_resources.txt",
                ".\language data working directory\study-6-linear-phase-theory/Experiment 3/3-7 knockouts\linear_phase_theory_corpus_resources.txt",
                ".\language data working directory\study-6-linear-phase-theory/Experiment 3/3-8 knockouts\linear_phase_theory_corpus_resources.txt",
                ".\language data working directory\study-6-linear-phase-theory/Experiment 3/3-9 knockouts\linear_phase_theory_corpus_resources.txt",
                ".\language data working directory\study-6-linear-phase-theory/Experiment 3/3-10 knockouts\linear_phase_theory_corpus_resources.txt",
                ".\language data working directory\study-6-linear-phase-theory/Experiment 3/3-11 opposite\linear_phase_theory_corpus_resources.txt"
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
            self.data_from_experiment[experiment][key] = self.data_from_experiment[experiment][key][self.data_from_experiment[experiment][key]['Group 3'] == 0]

    def add_combined_metrics(self, experiment='1'):
        for key in self.data_from_experiment[experiment]:
            self.data_from_experiment[experiment][key]['Relative load'] = self.data_from_experiment[experiment][key]['Asymmetric Merge'] / self.data_from_experiment[experiment][key]['Sentence'].str.len()
            self.data_from_experiment[experiment][key]['Move'] = self.data_from_experiment[experiment][key]['Move Phrase'] + self.data_from_experiment[experiment][key]['Move Head']
            if key in {'1', '2', '3', '4', '9'}:
                self.data_from_experiment['1'][key]['Filter'] = 1
            else:
                self.data_from_experiment['1'][key]['Filter'] = 0
            if key in {'1', '2', '5', '6', '9'}:
                self.data_from_experiment['1'][key]['Lexical ranking'] = 1
            else:
                self.data_from_experiment['1'][key]['Lexical ranking'] = 0
            if key in {'1', '3', '5', '7', '9'}:
                self.data_from_experiment['1'][key]['Late closure'] = 1
            else:
                self.data_from_experiment['1'][key]['Late closure'] = 0