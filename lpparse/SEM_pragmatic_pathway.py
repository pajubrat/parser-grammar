from support import log

class Discourse:
    def __init__(self, narrow_semantics):
        self.narrow_semantics = narrow_semantics
        self.interpretation_failed = False
        self.attitudes = {'FORCE:WH': 'Interrogative'}
        self.attention_gradient = []
        self.index_counter = 0
        self.records_of_attentional_processing = {}  # Traces of attentional allocation

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
            X.features.discard(feature)
            self.records_of_attentional_processing.pop(idx)

    def is_discourse_feature(self, feature):
        return feature[:4] == 'DIS:'

    def get_discourse_features(self, features):
        return {f for f in features if f[:4] == 'DIS:'}

    def get_inventory_index(self, ps):
        return next((f.split(':')[1] for f in ps.features if f[:4] == '*IDX'), None)

    def refresh_inventory(self, ps):
        if not ps.copied:
            idx = self.get_inventory_index(ps)
            if idx:
                self.records_of_attentional_processing[idx]['Name'] = f'{ps.H().max().illustrate()}'
                self.records_of_attentional_processing[idx]['Constituent'] = ps.H()

    def interpret_discourse_features(self, ps):
        self.refresh_inventory(ps)
        result = ''
        d_features = self.get_discourse_features(ps.features)
        if d_features:
            log('\n\t\t\tInterpreting ')
            for f in sorted(d_features):
                log(f'[{f}] at {ps.illustrate()}...')
                result += self.interpret_discourse_feature(f, ps)

    def interpret_discourse_feature(self, f, ps):
        return f'{f}, {ps.illustrate()}'

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
            if X.L().H().get_idx_tuple('QND'):
                arguments.add(X.L().H())
            if X.R().H().get_idx_tuple('QND'):
                arguments.add(X.R().H())
            if X.R().adjunct:
                arguments = arguments | self.collect_arguments(X.R())
                arguments = arguments | self.collect_arguments(X.L())
            else:
                arguments = arguments | self.collect_arguments(X.R())
        return arguments

    def out_of_proposition_scope(self, X, scope):
        if X.L.zero_level():
            if X.L.finite():
                if X.L.finite_tense():
                    if X != scope:
                        return True
        if X.R.zero_level():
            if X.R.finite():
                if X != scope:
                    return True

    def locate_proposition(self, X):
        return next((node for node in X if node.complex() and node.L.finite_tense()), None)

    def get_force_features(self, X):
        return {f for f in X.H().features if f[:5] == 'FORCE'}

    def compute_speaker_attitude(self, X):
        if self.get_force_features(X.H()):
            for count, force_feature in enumerate(self.get_force_features(X.H())):
                if force_feature in self.attitudes:
                    return self.attitudes[force_feature]
        else:
            return 'Declarative'

    def unexpected_order_occurred(self, X, starting_point_head):
        if self.narrow_semantics.speaker_model.results.first_solution_found or not self.get_inventory_index(X.H()):
            return

        idx = self.get_inventory_index(X.H())
        if starting_point_head in {const for const in X.H().path() if const.zero_level()}:
            direction = 'High'
        else:
            direction = 'Low'
        self.records_of_attentional_processing[idx]['Marked gradient'] = direction

    def allocate_attention(self, head):
        if head.referential() or head.preposition():
            idx = self.consume_index()
            head.features.add('*IDX:'+str(idx))
            self.records_of_attentional_processing[str(idx)] = {'Constituent': head.max(), 'Order': idx, 'Name': f'{head}'}