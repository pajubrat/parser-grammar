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

    def forget_object(self, ps):
        if ps and self.get_inventory_index(ps):
            idx = self.get_inventory_index(ps)
            feature = '*IDX:'+str(idx)
            ps.features.discard(feature)
            self.records_of_attentional_processing.pop(idx)

    def is_discourse_feature(self, feature):
        return feature[:4] == 'DIS:'

    def get_discourse_features(self, features):
        return {f for f in features if f[:4] == 'DIS:'}

    def get_inventory_index(self, ps):
        return next((f.split(':')[1] for f in ps.features if f[:4] == '*IDX'), None)

    def refresh_inventory(self, ps):
        if not ps.find_me_elsewhere:
            idx = self.get_inventory_index(ps)
            if idx:
                self.records_of_attentional_processing[idx]['Name'] = f'{ps.head().max().illustrate()}'
                self.records_of_attentional_processing[idx]['Constituent'] = ps.head()

    def interpret_discourse_features(self, ps, semantic_interpretation):
        self.refresh_inventory(ps)
        d_features = self.get_discourse_features(ps.features)
        if d_features:
            log('\n\t\t\tInterpreting ')
        for f in sorted(d_features):
            log(f'[{f}] at {ps.illustrate()}...')
            result = self.interpret_discourse_feature(f, ps)
            if not result:
                return []
            semantic_interpretation['DIS-features'].append(result)

    def interpret_discourse_feature(self, f, ps):
        return f, f'{ps.illustrate()}'

    def calculate_information_structure(self, root_node, semantic_interpretation):
        if root_node.finite():
            log('\n\t\tCalculating information structure...')
            semantic_interpretation['Information structure'] = self.create_topic_gradient(self.arguments_of_proposition(root_node))
            log(f'{semantic_interpretation["Information structure"]}')
            self.compute_speaker_attitude(root_node)

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

    def arguments_of_proposition(self, ps):
        scope = self.locate_proposition(ps)
        if not scope:
            return set()
        return self.collect_arguments(ps, scope)

    def collect_arguments(self, ps, scope):
        arguments = set()
        if ps.is_complex() and not self.out_of_proposition_scope(ps, scope):
            if self.is_relevant_for_information_structure(ps.left_const.head()):
                arguments.add(ps.left_const.head())
            if self.is_relevant_for_information_structure(ps.right_const.head()):
                arguments.add(ps.right_const.head())
            if ps.right_const.adjunct:
                arguments = arguments | self.collect_arguments(ps.right_const, scope)
                arguments = arguments | self.collect_arguments(ps.left_const, scope)
            else:
                arguments = arguments | self.collect_arguments(ps.right_const, scope)
        return arguments

    def is_relevant_for_information_structure(self, ps):
        if ps.finite_tense():
            return False
        return (None, None) != self.narrow_semantics.get_referential_index_tuples(ps, 'QND')

    def out_of_proposition_scope(self, ps, scope):
        if ps.left_const.is_primitive():
            if ps.left_const.finite():
                if ps.left_const.finite_tense():
                    if ps != scope:
                        return True
        if ps.right_const.is_primitive():
            if ps.right_const.finite():
                if ps != scope:
                    return True

    def locate_proposition(self, ps):
        return next((node for node in ps if node.is_complex() and node.left_const.finite_tense()), None)

    def get_force_features(self, ps):
        return {f for f in ps.head().features if f[:5] == 'FORCE'}

    def compute_speaker_attitude(self, ps):
        if self.get_force_features(ps.head()):
            for count, force_feature in enumerate(self.get_force_features(ps.head())):
                if force_feature in self.attitudes:
                    self.narrow_semantics.semantic_interpretation['Speaker attitude'].append(self.attitudes[force_feature])
        else:
            self.narrow_semantics.semantic_interpretation['Speaker attitude'] = ['Declarative']

    def unexpected_order_occurred(self, ps, starting_point_head):
        if self.narrow_semantics.brain_model.first_solution_found or not self.get_inventory_index(ps.head()):
            return

        idx = self.get_inventory_index(ps.head())
        if starting_point_head in {const for const in ps.head().working_memory_path() if const.is_primitive()}:
            direction = 'High'
            log(f'Topicalization...')
        else:
            direction = 'Low'
            log(f'Focussing...')
        self.records_of_attentional_processing[idx]['Marked gradient'] = direction

    def allocate_attention(self, head):
        if head.referential() or head.preposition():
            idx = self.consume_index()
            head.features.add('*IDX:'+str(idx))
            self.records_of_attentional_processing[str(idx)] = {'Order':idx, 'Name': f'{head}'}