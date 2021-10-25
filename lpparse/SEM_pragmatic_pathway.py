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
        return {feature for feature in features if feature[:4] == 'DIS:'}

    def get_inventory_index(self, ps):
        lst = [f.split(':')[1] for f in ps.features if f[:4] == '*IDX']
        if lst:
            return lst[0]
        else:
            return None

    def refresh_inventory(self, ps):
        idx = self.get_inventory_index(ps)
        if not ps.find_me_elsewhere and idx:
            self.records_of_attentional_processing[idx]['Name'] = f'{ps.head().max().illustrate()}'
            self.records_of_attentional_processing[idx]['Constituent'] = ps.head()


    #
    # todo knocked out currently
    #
    def interpret_discourse_features(self, ps, semantic_interpretation):
        log('\n\t\t\tCalculating pragmatic discourse features ')
        d_features = self.get_discourse_features(ps.features)
        results = []
        for f in sorted(d_features):
            log(f'[{f}], ')
            result = self.interpret_discourse_feature(f, ps)
            if not result:
                # self.interpretation_failed = True
                return []
            results.append(result)
        semantic_interpretation['D-features'] =  results
        self.refresh_inventory(ps)
        log('Done. ')

    def interpret_discourse_feature(self, f, ps):
        log(f'at {ps.illustrate()}: ')
        idx, space = self.narrow_semantics.get_referential_index_tuples(ps, 'QND')
        if not idx:
            log(f'{ps.illustrate()} not wired semantically (operation knocked out). ')
            return None
        if not self.narrow_semantics.query['QND']['Get'](idx):
            log(f'I have no idea what {ps.illustrate()} refers to. ')
            return None
        if 'Bound by' not in self.narrow_semantics.query['QND']['Get'](idx):
            log(f'{ps.max().illustrate()} not bound by propositional scope operator. ')
            # return None

        # Here we need to add the mechanism for excluding relative clauses i.e. only interpret them inside
        # full proposition

        log(f'Interpreted successfully with semantic object [{idx}].')
        return f'{ps.max().illustrate()}', f, idx

    def calculate_information_structure(self, root_node, semantic_interpretation):
        if 'FIN' in root_node.head().features:
            log('\n\t\tCalculating information structure...')
            semantic_interpretation['Information structure'] = self.create_topic_gradient(self.arguments_of_proposition(root_node))
            self.compute_speaker_attitude(root_node)
            log('Done. ')

    def create_topic_gradient(self, constituents_in_information_structure):

        marked_topic_lst = []
        topic_lst = []
        marked_focus_lst = []

        topic_gradient = {key: val for key, val in sorted(self.records_of_attentional_processing.items(), key = lambda ele: ele[0])}

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
            if self.is_relevant_for_information_structure(ps.left_const):
                arguments.add(ps.left_const.head())
            if self.is_relevant_for_information_structure(ps.right_const):
                arguments.add(ps.right_const.head())
            if ps.right_const.adjunct:
                arguments = arguments | self.collect_arguments(ps.right_const, scope)
                arguments = arguments | self.collect_arguments(ps.left_const, scope)
            else:
                arguments = arguments | self.collect_arguments(ps.right_const, scope)
        return arguments

    def is_relevant_for_information_structure(self, ps):
        return self.narrow_semantics.get_referential_index_tuples(ps, 'QND')

    def out_of_proposition_scope(self, ps, scope):
        if ps.left_const.is_primitive():
            if ps.left_const.finite():
                if {'C', 'T/fin', 'FORCE'} & ps.left_const.features:
                    if ps != scope:
                        return True
        if ps.right_const.is_primitive():
            if ps.right_const.finite():
                if ps != scope:
                    return True

    def locate_proposition(self, ps):
        for node in ps:
            if node.is_complex() and node.left_const.finite():
                return node

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
        feature_vector_set = set(ps.head().feature_vector())
        if starting_point_head in feature_vector_set:
            direction = 'High'
            log(f'Topicalization...')
        else:
            direction = 'Low'
            log(f'Focussing...')
        self.records_of_attentional_processing[idx]['Marked gradient'] = direction

    def allocate_attention(self, head):
        if self.included_in_attention_mechanism(head):  # This is arbitrary and only limits the scope of the current theory
            idx = self.consume_index()
            head.features.add('*IDX:'+str(idx))
            self.records_of_attentional_processing[str(idx)] = {'Order':idx, 'Name': f'{head}'}

    def included_in_attention_mechanism(self, head):
        return {'D', 'φ', 'P'} & head.features
