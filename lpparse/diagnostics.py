import pandas as pd
from matplotlib import pyplot as plt
import seaborn as sns

class Diagnostics:
    def __init__(self):
        self.data = {}

    # 1 - all mechanisms
    # 2 - no baseline ordering
    # 3 - no ranking
    # 4 - no filter
    # 5 - no filter, no ranking
    def run_resource_diagnostics(self):
        files_to_read = [".\language data working directory\study-6-linear-phase-theory\Study-1\linear_phase_theory_corpus_resources.txt",
                         ".\language data working directory\study-6-linear-phase-theory\Study-2\linear_phase_theory_corpus_resources.txt",
                         ".\language data working directory\study-6-linear-phase-theory\Study-3\linear_phase_theory_corpus_resources.txt",
                         ".\language data working directory\study-6-linear-phase-theory\Study-4\linear_phase_theory_corpus_resources.txt",
                         ".\language data working directory\study-6-linear-phase-theory\Study-5\linear_phase_theory_corpus_resources.txt",
                         ]
        self.read_data(files_to_read)
        self.remove_ungrammatical_sentences()
        self.add_combined_metrics()
        self.combine_all_into_one()
        self.compare_studies(['Merge', 'Move', 'Garden Paths'])

    def compare_studies(self, resources):
        # Arrange data so that id_vars, value_vars behave like group variables
        d2 = self.data['all'].melt(id_vars='Study_ID', value_vars=resources)
        # Create summary table
        d3 = d2.groupby(['Study_ID', 'Resource']).mean()
        print(d3)
        # Create plot
        g = sns.barplot(data=d2, x='Resource', y='value', hue='Study_ID', ci=None, palette='Greys')
        g.set_yscale("log")
        plt.show()

    def combine_all_into_one(self):
        self.data['all'] = pd.concat(self.data)

    def read_data(self, files_to_read):
        for i, filename in enumerate(files_to_read, start=1):
            new_data = pd.read_csv(filename, dtype={'Sentence': str, 'Study_ID': int, 'Group 0': int, 'Group 1': int, 'Group 2': int, 'Group 3': int}, sep=',',
                                    comment='@', encoding="utf-8")
            new_data = new_data.fillna(0)
            for col in new_data:
                if col != 'Sentence':
                    new_data[col] = new_data[col].astype(int)
            new_data.name = 'Resource Consumption per Construction Type'
            new_data.columns.name = 'Resource'
            self.data[str(i)] = new_data

    def remove_ungrammatical_sentences(self):
        for key in self.data:
            self.data[key] = self.data[key][self.data[key]['Group 3'] == 0]

    def add_combined_metrics(self):
        for key in self.data:
            self.data[key]['Relative load'] = self.data[key]['Asymmetric Merge'] / self.data[key]['Sentence'].str.len()
            self.data[key]['Move'] = self.data[key]['Move Phrase'] + self.data[key]['Move Head']