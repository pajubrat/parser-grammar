from support import log

class Discourse:
    def __init__(self, narrow_semantics):
        self.narrow_semantics = narrow_semantics
        self.interpretation_failed = False
        self.attitudes = {'FORCE:WH': 'Interrogative'}
        self.attention_gradient = []
        self.index_counter = 0
        self.records_of_attentional_processing = {}  # Traces of attentional allocation
        self.discourse_interpretation = {'FAM': 'Familiarity assumption',
                                         'POL': 'Affirmation bias',
                                         'DE/EM': 'De-emphasis, politeness'}

    def initialize(self):
        self.attention_gradient = []
        self.interpretation_failed = False
        self.index_counter = 0
        self.records_of_attentional_processing = {}

    def consume_index(self):
        self.index_counter += 1
        return self.index_counter

    def forget_object(self, X):
        print('.', end='', flush=True)
        if X and self.get_inventory_index(X):
            idx = self.get_inventory_index(X)
            feature = '*IDX:'+str(idx)
            X.core.remove_features({feature})
            self.records_of_attentional_processing.pop(idx)

    def is_discourse_feature(self, feature):
        return feature[:4] == 'DIS:'

    def get_discourse_features(self, X):
        fset = set()
        for s in [f.split(':')[1].split(',') for f in X.core.features() if f.startswith('DIS:')]:
            fset.update(s)
        return fset

    def get_inventory_index(self, ps):
        return next((f.split(':')[1] for f in ps.core.features() if f[:4] == '*IDX'), None)

    def refresh_inventory(self, ps):
        if not ps.copied:
            idx = self.get_inventory_index(ps)
            if idx:
                self.records_of_attentional_processing[idx]['Name'] = f'{ps.head().max().illustrate()}'
                self.records_of_attentional_processing[idx]['Constituent'] = ps.head()

    def interpret_discourse_features(self, X):
        results = []
        for f in self.get_discourse_features(X):
            log(f'\n\tInterpreting {f} at {X.illustrate()}.')
            results.append(self.interpret_discourse_feature(f, X))
        return results

    def interpret_discourse_feature(self, f, X):
        return f'{self.discourse_interpretation[f]}({f})'

    def calculate_information_structure(self, ps):
        log('\n\t\tCalculating information structure...')
        return self.create_topic_gradient(self.collect_arguments(ps))

    def calculate_speaker_attitude(self, ps):
        return self.compute_speaker_attitude(ps)

    def create_topic_gradient(self, constituents_in_information_structure):
        marked_topic_lst = []
        topic_lst = []
        marked_focus_lst = []
        topic_gradient = {key: val for key, val in sorted(self.records_of_attentional_processing.items(), key=lambda ele: ele[0])}
        for key in topic_gradient:
            if topic_gradient[key]['Constituent'] in constituents_in_information_structure:
                if 'Marked gradient' in topic_gradient[key]:
                    if topic_gradient[key]['Marked gradient'] == 'High':
                        marked_topic_lst.append(topic_gradient[key]['Name'])
                    elif topic_gradient[key]['Marked gradient'] == 'Low':
                        marked_focus_lst.append(topic_gradient[key]['Name'])
                else:
                    topic_lst.append(topic_gradient[key]['Name'])
        return {'Marked topics': marked_topic_lst, 'Neutral gradient': topic_lst, 'Marked focus': marked_focus_lst}

    def collect_arguments(self, X):
        arguments = set()
        if X.complex():
            if X.L().head().get_idx_tuple('QND'):
                arguments.add(X.L().head())
            if X.R().head().get_idx_tuple('QND'):
                arguments.add(X.R().head())
            if X.R().adjunct:
                arguments = arguments | self.collect_arguments(X.R())
                arguments = arguments | self.collect_arguments(X.L())
            else:
                arguments = arguments | self.collect_arguments(X.R())
        return arguments

    def out_of_proposition_scope(self, X, scope):
        if X.L().zero_level():
            if X.L().property('finite'):
                if X.L().property('finite_tense'):
                    if X != scope:
                        return True
        if X.R().zero_level():
            if X.R().property('finite'):
                if X != scope:
                    return True

    def locate_proposition(self, X):
        return next((node for node in X if node.complex() and node.L().core.property('finite_tense')), None)

    def get_force_features(self, X):
        return {f for f in X.head().core.features() if f[:5] == 'FORCE'}

    def compute_speaker_attitude(self, X):
        if self.get_force_features(X.head()):
            for count, force_feature in enumerate(self.get_force_features(X.head())):
                if force_feature in self.attitudes:
                    return self.attitudes[force_feature]
        else:
            return 'Declarative'

    def unexpected_order_occurred(self, X, starting_point_head):
        if self.narrow_semantics.speaker_model.results.first_solution_found or not self.get_inventory_index(X.head()):
            return

        idx = self.get_inventory_index(X.head())
        if starting_point_head in {const for const in X.head().path() if const.zero_level()}:
            direction = 'High'
        else:
            direction = 'Low'
        self.records_of_attentional_processing[idx]['Marked gradient'] = direction

    def allocate_attention(self, head):
        if head.core('referential') or head.core('preposition'):
            idx = self.consume_index()
            head.core.add_features({'*IDX:' + str(idx)})
            self.records_of_attentional_processing[str(idx)] = {'Constituent': head.max(), 'Order': idx, 'Name': f'{head}'}