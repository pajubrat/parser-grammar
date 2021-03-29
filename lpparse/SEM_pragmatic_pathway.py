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

    def is_discourse_feature(self, feature):
        return feature[:2] == 'D:'

    def get_discourse_features(self, features):
        return {feature for feature in features if feature[:2] == 'D:'}

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
        for f in d_features:
            result = self.interpret_discourse_feature(f, ps)
            if not result:
                self.interpretation_failed = True
                return
            semantic_interpretation['D-features'].append(result)

    def interpret_discourse_feature(self, f, ps):
        """
        Interprets a discourse feature [f] at [ps]. Checks that [ps] refers to something
        that is bound by a propositional operator and then performs interpretation. Currently
        the latter only checks that the proposition is saturated and not an unsaturated predicate.
        Notice that D-feature interpretation relies on semantic objects, not solely on
        syntactic structure.
        """
        log(f'[{f}] at {ps.max().illustrate()}: ')
        idx = self.narrow_semantics.get_semantic_wiring(ps)
        if not idx:
            log(f'{ps.max().illustrate()} not wired semantically. ')
            return None
        if idx not in self.narrow_semantics.discourse_inventory:
            log(f'I have no idea what {ps.max().illustrate()} refers to. ')
            return None
        if 'Bound by' not in self.narrow_semantics.discourse_inventory[idx]:
            log(f'{ps.max().illustrate()} not bound by propositional scope operator. ')
            return None
        binder_idx = self.narrow_semantics.get_semantic_wiring(self.narrow_semantics.discourse_inventory[idx]['Bound by'][0])
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
        if self.narrow_semantics.discourse_inventory[binder_idx]['Semantic type']:
            if '§Predicate' in self.narrow_semantics.discourse_inventory[binder_idx]['Semantic type']:
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
        for idx in self.narrow_semantics.discourse_inventory:
            if idx in main_arguments and not self.narrow_semantics.discourse_inventory[idx]['Operator']:
                topic_lst.append((self.narrow_semantics.discourse_inventory[idx]['Order gradient'], idx))
                self.narrow_semantics.update_semantics_for_attribute(idx, 'In information structure', True)

        # Order the arguments by their gradient (in the spellout structure ~ sensory input)
        topic_lst = sorted(topic_lst)

        # Analyze the gradients
        # Group the arguments into three lists: marked topics, default/neutral gradient, and marked focus
        # The algorithm works by moving elements from the original topic list into the marked lists.
        topic_lst_ = topic_lst.copy()
        for topic, idx in topic_lst:
            if 'Marked gradient' in self.narrow_semantics.discourse_inventory[idx]:
                if self.narrow_semantics.discourse_inventory[idx]['Marked gradient'] == 'High':
                    marked_topic_lst.append(idx)
                    topic_lst_.remove((self.narrow_semantics.discourse_inventory[idx]['Order gradient'], idx))
                if self.narrow_semantics.discourse_inventory[idx]['Marked gradient'] == 'Low':
                    marked_focus_lst.append(idx)
                    topic_lst_.remove((self.narrow_semantics.discourse_inventory[idx]['Order gradient'], idx))
        return {'Marked topics': marked_topic_lst, 'Neutral gradient': [topic[1] for topic in topic_lst_], 'Marked focus': marked_focus_lst}

    def arguments_of_proposition(self, ps):
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
            arguments.add(self.narrow_semantics.get_semantic_wiring(ps.left_const))
            arguments.add(self.narrow_semantics.get_semantic_wiring(ps.right_const))
            if ps.right_const.adjunct:
                arguments = arguments | self.collect_arguments(ps.right_const, scope)
                arguments = arguments | self.collect_arguments(ps.left_const, scope)
            else:
                arguments = arguments | self.collect_arguments(ps.right_const, scope)
        return arguments

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
        idx = self.narrow_semantics.get_semantic_wiring(ps)
        if idx:
            feature_vector_set = set(ps.head().feature_vector())        # Take reconstructed floaters feature vector
            if starting_point_head in feature_vector_set:               # If starting point is in the feature vector,
                direction = 'High'                                      # then reconstructed was rightward and the
                log(f'Topicalization...')                               # production movement was leftward
            else:
                direction = 'Low'                                       # Starting point was not in the feature vector,
                log(f'Focussing...')                                    # then reconstruction was leftward and the
                                                                        # production movement was rightward

            self.narrow_semantics.update_semantics_for_attribute(idx, 'Marked gradient', direction)

    def allocate_attention_resources(self, idx):
        self.narrow_semantics.discourse_inventory[idx]['Order gradient'] = int(idx)

