from support import log

class NarrowSemantics:
    """
    Narrow semantics is responsible for creating semantic interpretation for isolated sentences. The result of
    narrow semantic interpretation will be combined with broad semantic interpretation that takes context
    into account.
    """
    def __init__(self, controlling_parsing_process):
        self.semantic_bookkeeping = {}
        self.index_counter = None
        self.controlling_parsing_process = controlling_parsing_process
        self.speaker_attitudes = []
        self.information_structure_active = True
        self.main_arguments = {}
        self.topic_focus_structure = ()
        self.attitudes = {'FORCE:OP:WH': 'Interrogative'}   # These descriptions are only used in outputting results

    def initialize(self):
        self.index_counter = 1
        self.semantic_bookkeeping = {}

    def wire_semantics(self, ps):
        """
        Wires constituents in [ps] recursively with objects inside the semantic space and adds them to semantic bookkeeping.
        Creates an IDX feature for the constituent and creates the corresponding object into the semantic space
        (semantic bookkeeping). This version is still unable to create co-reference dependencies. Semantic bookkeeping
        holds a ranked gradient which records the prominence of the item in the input structure.

        Travels on the right edge and wires all referential heads that have not been wired already.
        Right adjuncts are visited separately, after which the right edge travel continues
        """
        if self.controlling_parsing_process.first_solution_found:
            return
        if ps.is_complex():
            if ps.right_const.adjunct:
                self.wire_semantics(ps.right_const) # Visit and wired the externalized right adjuncts
                self.wire_semantics(ps.left_const)  # Continue from the right edge of the main structure
            if not self.get_semantic_wiring(ps) and ps.head().referential():
                self.create_wiring(ps)
                self.add_to_semantic_bookkeeping(ps)
                self.index_counter += 1             # This will be identifier for the next object
            self.wire_semantics(ps.right_const)

    def create_wiring(self, ps):
        """
        Wires constituent ps (its head) with an object inside the semantic space. THis module will later
        include the binding theory.
        """
        log(f'Wiring semantics for {ps}')
        idx_feature = 'IDX:' + str(self.index_counter)
        log(f'({idx_feature})...')
        ps.head().features.add(idx_feature)

    def add_to_semantic_bookkeeping(self, ps):
        """
        Adds the element to semantic space (semantic bookkeeping)
        """
        # Ranked gradient that will go into information structure module
        self.semantic_bookkeeping[str(self.index_counter)] = {'Const': f'{ps}', 'Order gradient': self.index_counter}
        if ps.scan_criterial_features():
            self.semantic_bookkeeping[str(self.index_counter)]['Operator'] = True
        else:
            self.semantic_bookkeeping[str(self.index_counter)]['Operator'] = False

    def get_semantic_wiring(self, ps):
        """
        Returns IDX-features which point to objects in the semantic space
        """
        return {f[4:] for f in ps.head().features if f[:3] == 'IDX'}

    def get_force_features(self, ps):
        """
        Returns force features.
        """
        return {f for f in ps.head().features if f[:5] == 'FORCE'}

    def update_semantics_for_marked_gradient(self, floater, starting_point_head):
        """
        Allows communication between adjunct reconstruction and semantic bookkeeping.

        When constituent is reconstructed by adjunct reconstruction, semantic bookkeeping is updated to
        record the operation, which will be then used by information structure module
        """
        idx_set = self.get_semantic_wiring(floater)
        if idx_set:
            feature_vector_set = set(floater.head().feature_vector())   # Take reconstructed floaters feature vector
            if starting_point_head in feature_vector_set:               # If starting point is in the feature vector,
                direction = 'Topicalization'                            # then reconstructed was rightward and the
                log(f'Topicalization...')                               # production movement was leftward
            else:
                direction = 'Focussing'                                 # Starting point was not in the feature vector,
                log(f'Focussing...')                                    # then reconstruction was leftward and the
                                                                        # production movement was rightward

            value = list(idx_set)[0]                                    # normally we only have one IDX, this is just
                                                                        # precaution
            self.update_semantics_for_attribute(value, 'Marked gradient', direction)

    def update_semantics_for_attribute(self, sem_object, attribute, value):
        """
        Updates attribute:value for semantic object [sem_object]
        """

        if self.semantic_bookkeeping[sem_object]:
            self.semantic_bookkeeping[sem_object][attribute] = value

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
            self.speaker_attitudes = []
            return
        if self.get_force_features(ps.head()):
            # If specific force features exists, then they are used for interpretation
            for count, force_feature in enumerate(self.get_force_features(ps.head())):
                if force_feature in self.attitudes:
                    self.speaker_attitudes = [self.attitudes[force_feature]]
                    self.information_structure_active = False
                    log('Attitude determined by the Force feature...')
        else:
            # Default value is 'declarative' (judgment)
            self.speaker_attitudes = ['Declarative']
            self.information_structure_active = True
            log('Declarative finite clause...')

    def compute_information_structure(self, ps):
        self.main_arguments = self.arguments_of_proposition(ps)
        self.topic_focus_structure = self.create_topic_gradient(self.main_arguments)

    def create_topic_gradient(self, main_arguments):
        """
        Creates a topic gradient tuple with three items: marked topic list, neutral gradient, and marked focus list
        """
        marked_topic_lst = []
        topic_lst = []
        marked_focus_lst = []

        # Restrict the vision of this module to main arguments and their gradients
        for idx in self.semantic_bookkeeping:
            if idx in main_arguments and not self.semantic_bookkeeping[idx]['Operator']:
                topic_lst.append((self.semantic_bookkeeping[idx]['Order gradient'], idx))

        # Order the arguments by their gradient (in the spellout structure ~ sensory input)
        topic_lst = sorted(topic_lst)

        # Analyze the gradients
        # Group the arguments into three lists: marked topics, default/neutral gradient, and marked focus
        # The algorithm works by moving elements from the original topic list into the marked lists.
        topic_lst_ = topic_lst.copy()
        for topic, idx in topic_lst:
            if 'Marked gradient' in self.semantic_bookkeeping[idx]:
                if self.semantic_bookkeeping[idx]['Marked gradient'] == 'Topicalization':
                    marked_topic_lst.append(idx)
                    topic_lst_.remove((self.semantic_bookkeeping[idx]['Order gradient'], idx))
                if self.semantic_bookkeeping[idx]['Marked gradient'] == 'Focussing':
                    marked_focus_lst.append(idx)
                    topic_lst_.remove((self.semantic_bookkeeping[idx]['Order gradient'], idx))
        #
        return marked_topic_lst, [topic[1] for topic in topic_lst_], marked_focus_lst

    def operator_argument(self, arg):
        if self.semantic_bookkeeping[arg]:
            if self.semantic_bookkeeping[arg]['Operator']:
                return True

    def arguments_of_proposition(self, ps):
        scope = self.locate_proposition(ps)
        if not scope:
            return set()
        return self.collect_arguments(ps, scope)

    def collect_arguments(self, ps, scope):
        arguments = set()
        if ps.is_complex() and not self.out_of_proposition_scope(ps, scope):
            arguments = arguments | self.get_semantic_wiring(ps.left_const)
            if ps.right_const.adjunct:
                arguments = arguments | self.collect_arguments(ps.right_const, scope)
                arguments = arguments | self.collect_arguments(ps.left_const, scope)
            else:
                arguments = arguments | self.collect_arguments(ps.right_const, scope)
        return arguments

    def out_of_proposition_scope(self, ps, scope):
        if ps.left_const.is_primitive():
            if ps.left_const.finite():
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

