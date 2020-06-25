from support import set_logging, log, get_number_of_operations, reset_number_of_operations, log_result, illu
from LexicalInterface import LexicalInterface
from adjunct_constructor import AdjunctConstructor
import phrase_structure


class FloaterMovement():
    def __init__(self, controlling_parser_process):
        self.controlling_parser_process = controlling_parser_process
        self.name_provider_index = 0
        self.memory_buffer = []

        # Access to the lexicon
        self.lexical_access = LexicalInterface(self.controlling_parser_process)
        self.lexical_access.load_lexicon(self.controlling_parser_process)
        self.adjunct_constructor = AdjunctConstructor(self.controlling_parser_process)

    # Definition for floater reconstruction
    def reconstruct(self, ps):

        # Condition 1. Primitive heads are not reconstructed
        if ps.is_primitive():
            return ps

        # Move downward from top
        _ps_iterator = ps.top()

        while _ps_iterator:

            # Detect a floater
            floater = self.detect_floater(_ps_iterator)
            if floater:
                log(f'\t\t\t\t\tDropping {floater}')
                # Drop the floater
                self.drop_floater(floater, ps)
            _ps_iterator = _ps_iterator.walk_downstream()

        return ps.top()  # Return top, because it is possible that an adjunct expands the structure

    # Definition for floater that requires reconstruction
    def detect_floater(self, _ps_iterator):

        # Definition for a potential floater
        # Presupposition: Current target node is not primitive (=[X Y])
        # Condition 1: X is complex (heads cannot be floaters)
        # Condition 2: X has not been copied somewhere
        # Condition 3: X has a tail set
        # Condition 4: X has not been prevented from floating around
        # Condition 5: X has no criterial feature
        if _ps_iterator.is_complex() and \
                _ps_iterator.left_const.is_complex() and \
                not _ps_iterator.left_const.find_me_elsewhere and \
                _ps_iterator.left_const.head().get_tail_sets() and \
                'adjoinable' in _ps_iterator.left_const.head().features and \
                '-adjoinable' not in _ps_iterator.left_const.head().features and \
                not _ps_iterator.scan_criterial_features():

            floater = _ps_iterator.left_const

            # Definition for floater that requires reconstruction
            # Condition 1. External tail-head test fails
            if not floater.head().external_tail_head_test():
                log('\t\t\t\t\t' + floater.illustrate() + ' failed to tail ' + illu(floater.head().get_tail_sets()))
                return floater

            # Condition 2. The phrase is at EPP SPEC position of a finite clause
            elif floater.mother and floater.mother.head().EPP() and floater.mother.is_finite():
                log('\t\t\t\t\t' + floater.illustrate() + ' is in an EPP SPEC position.')
                return floater

            # Condition 3. The phrase sits in a wrong SPEC position
            elif floater.mother and '-SPEC:*' in floater.mother.head().features:
                if floater == floater.mother.head().local_edge():
                    return floater

        # Special condition: constituent at the right
        # [XP YP], XP not potential adjunct, but Y fails tail test,
        # Y not -FLOAT
        # They are marked for floating and turned into adjuncts, but ADVs on the right are only turned to adjuncts
        # for reasons I do not understand
        if _ps_iterator.is_complex() and \
                _ps_iterator.right_const.head().get_tail_sets() and \
                'adjoinable' in _ps_iterator.right_const.head().features:
            floater = _ps_iterator.right_const.head()

            # Condition 1. External tail test fails
            if not floater.external_tail_head_test():
                log('\t\t\t\t\t' + floater.illustrate() + ' at the right failed to tail ' + illu(floater.head().get_tail_sets()))

                # Condition 2a. DP and PP are transformed into adjuncts and marked for reconstruction
                if 'ADV' not in floater.labels() and floater.top().contains_feature('CAT:FIN'):
                    self.adjunct_constructor.create_adjunct(floater)
                    return floater.mother

                # Condition 2b. If the right branch is ADV, it is transformed into an adjunct, but not reconstructed.
                # (This must be wrong.)
                else:
                    if 'ADV' in floater.labels() and not _ps_iterator.right_const.adjunct:
                        self.adjunct_constructor.create_adjunct(floater)

    # Definition for floater reconstruction (dropping)
    def drop_floater(self, floater, ps):

        # Starting point is stored so we don't implement reconstruction inside the same projection (leads into regress)
        starting_point_head = floater.container_head()

        # We need to locate the appropriate starting point, XP in [fin XP]
        ps_iterator_ = self.locate_minimal_tense_edge(floater.mother)

        # This is the element we are going to fit into the structure
        floater_copy = floater.copy()

        # This downward loop searches a position for the floater
        while ps_iterator_ and not ps_iterator_ == floater and not ps_iterator_.find_me_elsewhere:

            # Create hypothetical structure for testing
            if 'ADV' in floater_copy.labels():
                ps_iterator_.merge(floater_copy, 'right')
            else:
                ps_iterator_.merge(floater_copy, 'left')

            # If a suitable position is found, dropping will be executed
            # Condition 1: tail test succeeds,
            # Condition 2: we are not reconstructing inside the same projection (does not apply to right-adjoined)
            # Condition 3: dropped non-ADV will become the only SPEC
            if self.is_drop_position(ps_iterator_, floater_copy, starting_point_head):
                if not floater.adjunct:
                    self.adjunct_constructor.create_adjunct(floater)

                # We have found a position and create the actual copy that will be in the new position
                dropped_floater = floater.copy_from_memory_buffer(self.babtize())

                # Adverbs and PPs are adjoined to the right
                if 'ADV' in floater_copy.labels() or 'P' in floater_copy.labels():
                    ps_iterator_.merge(dropped_floater, 'right')

                # Everything else is adjoined to the left
                else:
                    ps_iterator_.merge(dropped_floater, 'left')

                # Keep record of the computations consumed
                self.controlling_parser_process.number_of_phrasal_Move += 1

                floater_copy.remove()
                log(f'\t\t\t\t\t = {ps}')
                return
            else:
                floater_copy.remove()

            ps_iterator_ = ps_iterator_.walk_downstream()

    # Definition for a legitimate target position for floater reconstruction
    def is_drop_position(self, ps_iterator_, floater_copy, starting_point_head):

        # Condition 1. The position must satisfy the external tail head test
        if floater_copy.head().external_tail_head_test():

            # Condition 2. Condition for merging to the right: must be AdvP or PP
            # (Lax conditions)
            if 'ADV' in floater_copy.labels() or 'P' in floater_copy.labels():
                return True

            # Condition 3. Condition for merging to the left
            else:

                # Don't go inside where you started
                if floater_copy.container_head() != starting_point_head:
                    # Don't fill in more than one SPEC position
                    # (This should be revised because the function count specifiers is used only here)
                    if ps_iterator_.head().count_specifiers() < 2:
                        return True
                    else:
                        return False
                else:
                    return False
        else:
            return False

    # Definition for minimal tense edge
    def locate_minimal_tense_edge(self, ps):

        ps_iterator_ = ps
        node = ps

        # Go upwards to the upper edge of the finite construction
        # = highest node with label FIN but selected by non-fin head (e.g. V-FIN)
        while ps_iterator_:
            node = ps_iterator_
            # Condition 1. Must be inside FIN
            # Condition 2. The sister cannot be FIN (e.gg V-FIN)
            if ps_iterator_.sister() \
                    and 'FIN' in ps_iterator_.labels() \
                    and 'FIN' not in ps_iterator_.sister().labels():
                break
            ps_iterator_ = ps_iterator_.walk_upstream()

        # In [X FinP], we return FinP iff FinP is not an adjunct
        if node and node.right_const and not node.right_const.adjunct:
            return node.right_const
        else:
            # If FinP is adjunct, then we return [X FinP]
            return node

    # Provide unique names when chains are formed
    # Used only for printing output
    def babtize(self):
        self.name_provider_index += 1
        return str(self.name_provider_index)

    # get_specifiers() wrapper that implements the modular interface to the PhraseStructure class
    # Must be sorted out
    def get_specifiers(self, h):
        specs = h.edge()
        return [spec for spec in specs if not spec.is_primitive()]