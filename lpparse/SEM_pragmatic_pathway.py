from support import log

class Discourse:
    """
    This class defines the pragmatic pathway and interprets D-features (discourse features) which express notions that
    this module understands.
    """
    def __init__(self, narrow_semantics):
        self.narrow_semantics = narrow_semantics            # This provides access to semantic bookkeeping
        self.interpretation_failed = False
        self.attitudes = {'FORCE:OP:WH': 'Interrogative'}   # These descriptions are only used in outputting results
        self.attention_gradient = []

    def initialize(self):
        self.attention_gradient = []
        self.interpretation_failed = False

    def is_discourse_feature(self, feature):
        return feature[:4] == 'DIS:'

    def get_discourse_features(self, features):
        return {feature for feature in features if feature[:4] == 'DIS:'}

    def reconstruct_discourse(self, ps, semantic_interpretation):
        """
        Interprets all D-features from [ps]
        """
        if 'C' in ps.features or 'C/fin' in ps.features:
            return
        d_features = self.get_discourse_features(ps.features)
        if not d_features:
            return
        log('\n\t\tInterpreting D-features: ')
        for f in sorted(d_features):
            result = self.interpret_discourse_feature(f, ps)
            if not result:
                self.interpretation_failed = True
                return
            semantic_interpretation['D-features'] = result

    def interpret_discourse_feature(self, f, ps):
        """
        Interprets a discourse feature [f] at [ps]. Checks that [ps] refers to something
        that is bound by a propositional operator and then performs interpretation. Currently
        the latter only checks that the proposition is saturated and not an unsaturated predicate.
        Notice that D-feature interpretation relies on semantic objects, not solely on
        syntactic structure.
        """
        #
        return 'Not functional'
        #
        # There is a problem below because semantic space was divided between two modules but here it is still
        # assumed that they are all in the global cognition.
        #

        log(f'[{f}] at {ps.max().illustrate()}: ')
        idx = self.narrow_semantics.get_referential_index_tuples(ps, 'QND')
        if not idx:
            log(f'{ps.max().illustrate()} not wired semantically. ')
            return None
        if not self.narrow_semantics.query['QND']['Get'](idx):
            log(f'I have no idea what {ps.max().illustrate()} refers to. ')
            return None
        if 'Bound by' not in self.narrow_semantics.query['QND']['Get'](idx):
            log(f'{ps.max().illustrate()} not bound by propositional scope operator. ')
            return None
        binder_idx = self.narrow_semantics.get_referential_index_tuples(self.narrow_semantics.global_cognition.inventory[idx]['Bound by'][0], 'QND')
        if not binder_idx:
            log('The relevant proposition not available in SEM. ')
            return None
        if not self.interpret_D_feature_inside_proposition(binder_idx, ps, f):
            log(f'Interpretation failed.')
            return None
        log(f'Interpreted successfully with semantic object [{idx}].')
        return f'{ps.max().illustrate()}', f, idx       # This information will be marked to SEM

    def interpret_D_feature_inside_proposition(self, binder_idx, ps, f):
        """
        Interprets a discourse feature (D-feature, [f]) inside a proposition [binder_idx].
        Currently this only checks that the proposition is not a predicate, which makes the
        interpretation impossible.
        """
        if self.narrow_semantics.inventory[binder_idx]['Semantic type']:
            if '§Predicate' in self.narrow_semantics.inventory[binder_idx]['Semantic type']:
               log(f'Attempting to interpret discourse feature [{f}] at {ps.max().illustrate()} in connection with predicate.')
               return False
        return True

    def compute_information_structure(self, ps):
        main_arguments = self.arguments_of_proposition(ps)
        self.narrow_semantics.semantic_interpretation['Information structure'] = self.create_topic_gradient(main_arguments)

    def create_topic_gradient(self, main_arguments):
        """
        Creates a topic gradient tuple with three items: marked topic list, neutral gradient, and marked focus list.
        Referential operator expressions are ignored.
        """
        marked_topic_lst = []
        topic_lst = []
        marked_focus_lst = []

        # Restrict the vision of this module to main arguments and their gradients, while ignoring operator expressions
        for idx_tuple in self.attention_gradient:
            if idx_tuple in main_arguments and not self.narrow_semantics.is_operator(idx_tuple):
                topic_lst.append(idx_tuple)
                idx, space = idx_tuple
                self.narrow_semantics.update_semantics_for_attribute(idx, space, 'In information structure', True)

        # Order the arguments by their gradient (in the spellout structure ~ sensory input)
        topic_lst = sorted(topic_lst)

        # Analyze the gradients
        # Group the arguments into three lists: marked topics, default/neutral gradient, and marked focus
        # The algorithm works by moving elements from the original topic list into the marked lists.
        topic_lst_ = topic_lst.copy()
        for idx_tpl in topic_lst:
            idx, space = idx_tpl
            semantic_object = self.narrow_semantics.query[space]['Get'](idx)
            if 'Marked gradient' in semantic_object:
                if semantic_object['Marked gradient'] == 'High':
                    marked_topic_lst.append((idx, space))
                    topic_lst_.remove(idx_tpl)
                if semantic_object['Marked gradient'] == 'Low':
                    marked_focus_lst.append(idx_tpl)
                    topic_lst_.remove(idx_tpl)
        return {'Marked topics': marked_topic_lst, 'Neutral gradient': topic_lst_, 'Marked focus': marked_focus_lst}

    def arguments_of_proposition(self, ps):
        """
        Returns a set containing the index tuples (idx, space) of the main arguments of a proposition
        """
        scope = self.locate_proposition(ps)
        if not scope:
            return set()
        return self.collect_arguments(ps, scope)

    def collect_arguments(self, ps, scope):
        """
        Collects the semantic arguments (referential indexes) from [ps] which should express a proposition.
        Presupposes that referential indexes have been provided by wire_semantics function. Does not explore
        left branches or go outside of current proposition as defined by feature [FIN] 'finiteness'
        """
        arguments = set()
        if ps.is_complex() and not self.out_of_proposition_scope(ps, scope):
            if self.is_relevant_for_information_structure(ps.left_const):
                arguments.add(self.narrow_semantics.get_referential_index_tuples(ps.left_const.head(), 'QND'))
            if self.is_relevant_for_information_structure(ps.right_const):
                arguments.add(self.narrow_semantics.get_referential_index_tuples(ps.right_const.head(), 'QND'))
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
        """
        Returns force features.
        """
        return {f for f in ps.head().features if f[:5] == 'FORCE'}

    def compute_speaker_attitude(self, ps):
        """
        Speaker attitude is a relation between the speaker and the finite head of [ps]. It is grammaticalized into
        [FORCE] features.

        If the head is not finite, no propositional attitudes can be computed by narrow semantics (only by context).
        If the head is finite, then propositional attitudes are collected into a list by using force features.
        The default interpretation is declarative (Frege's judgment)
        """
        if not ps.head().finite():
            log('Not relevant for this expression types...')
            self.narrow_semantics.semantic_interpretation['Speaker attitude'] = []
            return

        # If specific force features exists, then they are used for interpretation
        if self.get_force_features(ps.head()):
            for count, force_feature in enumerate(self.get_force_features(ps.head())):
                if force_feature in self.attitudes:
                    self.narrow_semantics.semantic_interpretation['Speaker attitude'].append(self.attitudes[force_feature])
        else:
            # Default value is 'declarative' (judgment)
            self.narrow_semantics.semantic_interpretation['Speaker attitude'] = ['Declarative']

    def notify_adjunct_reconstruction_occurred(self, ps, starting_point_head):
        """
        Allows communication between adjunct reconstruction and semantic bookkeeping.

        When constituent is reconstructed by adjunct reconstruction, semantic bookkeeping is updated to
        record the operation, which will be then used by the information structure module
        """

        # We compute pragmatic information only for the first solution, because
        # 1) I don't know what it means to compute information structure for secondary solutions;
        # 2) the algorithm does not work because in order for implement secondary IS computations, we need
        # to cleanup all semantic information recursively which is not implemented.
        if self.narrow_semantics.controlling_parsing_process.first_solution_found:
            return

        idx, space = self.narrow_semantics.get_referential_index_tuples(ps, 'QND')
        feature_vector_set = set(ps.head().feature_vector())        # Take reconstructed floaters feature vector
        if starting_point_head in feature_vector_set:               # If starting point is in the feature vector,
            direction = 'High'                                      # then reconstructed was rightward and the
            log(f'Topicalization...')                               # production movement was leftward
        else:
            direction = 'Low'                                       # Starting point was not in the feature vector,
            log(f'Focussing...')                                    # then reconstruction was leftward and the
                                                                    # production movement was rightward

        self.narrow_semantics.update_semantics_for_attribute(idx, space, 'Marked gradient', direction)

    def allocate_attention_resources(self, idx_tuple):
        self.attention_gradient.append(idx_tuple)