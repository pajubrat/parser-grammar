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
        if ps.is_primitive():
            return ps

        # --------------------- minimal search ----------------------------------#
        phrase_structure = ps.top()
        for node in phrase_structure.minimal_search():
            floater = self.detect_floater(node)
            if floater:
                log(f'\t\t\t\t\tDropping {floater}')
                self.drop_floater(floater, ps)
        # ----------------------------------------------------------------------#
        return ps.top()  # Return top, because it is possible that an adjunct expands the structure

    def detect_floater(self, _ps_iterator):

        # Internal function
        # Definition for finiteness (trivial)
        def is_finite(h):
            head = h.head()
            return 'FIN' in head.features

        # Main function
        if self.detect_left_floater(_ps_iterator):
            floater = _ps_iterator.left_const
            if not floater.head().external_tail_head_test():
                log('\t\t\t\t\t' + floater.illustrate() + ' failed to tail ' + illu(floater.head().get_tail_sets()))
                return floater
            elif floater.mother and floater.mother.head().EPP() and is_finite(floater.mother):
                log('\t\t\t\t\t' + floater.illustrate() + ' is in an EPP SPEC position.')
                return floater
            elif floater.mother and '-SPEC:*' in floater.mother.head().features:
                if floater == floater.mother.head().local_edge():
                    return floater
        elif self.detect_right_floater(_ps_iterator):
            floater = _ps_iterator.right_const.head()
            if not floater.external_tail_head_test():
                log('\t\t\t\t\t' + floater.illustrate() + ' failed to tail ' + illu(floater.head().get_tail_sets()))
                if 'ADV' not in floater.features and floater.top().contains_feature('FIN'):
                    self.adjunct_constructor.create_adjunct(floater)
                    return floater.mother
                else:
                    if 'ADV' in floater.features and not _ps_iterator.right_const.adjunct:
                        self.adjunct_constructor.create_adjunct(floater)

    def detect_right_floater(self, _ps_iterator):
        if _ps_iterator.is_complex() and \
                _ps_iterator.right_const.head().get_tail_sets() and \
                'adjoinable' in _ps_iterator.right_const.head().features and \
                '-adjoinable' not in _ps_iterator.right_const.head().features:
            return True

    def detect_left_floater(self, _ps_iterator):
        if _ps_iterator.is_complex() and \
                _ps_iterator.left_const.is_complex() and \
                not _ps_iterator.left_const.find_me_elsewhere and \
                _ps_iterator.left_const.head().get_tail_sets() and \
                'adjoinable' in _ps_iterator.left_const.head().features and \
                '-adjoinable' not in _ps_iterator.left_const.head().features and \
                not _ps_iterator.scan_criterial_features():
            return True

    # Definition for floater reconstruction (dropping)
    def drop_floater(self, floater, ps):
        starting_point_head = floater.container_head()
        ps_iterator_ = self.locate_minimal_tense_edge(floater.mother)   # Starting point, XP in [fin XP]
        if not ps_iterator_:
            return
        floater_copy = floater.copy()

        # ------------------------------------ minimal search ------------------------------------#
        for node in ps_iterator_.minimal_search():
            if self.termination_condition(node, floater):
                break
            self.merge_floater(node, floater_copy)
            if self.is_drop_position(node, floater_copy, starting_point_head):
                if not floater.adjunct:
                    self.adjunct_constructor.create_adjunct(floater)
                dropped_floater = floater.copy_from_memory_buffer(self.babtize())
                self.merge_floater(node, dropped_floater)
                self.controlling_parser_process.number_of_phrasal_Move += 1
                floater_copy.remove()
                log(f'\t\t\t\t\t = {ps}')
                return
            floater_copy.remove()
        # ---------------------------------------------------------------------------------------#

    def merge_floater(self, node, floater_copy):
        if self.is_right_adjunct(floater_copy):
            node.merge_1(floater_copy, 'right')
        else:
            node.merge_1(floater_copy, 'left')

    def termination_condition(self, node, floater):
        if node == floater or node.find_me_elsewhere:
            return True

    def is_right_adjunct(self, node):
        if 'ADV' in node.head().features or 'P' in node.head().features:
            return True

    # Definition for a legitimate target position for floater reconstruction
    def is_drop_position(self, ps_iterator_, floater_copy, starting_point_head):
        if not floater_copy.head().external_tail_head_test():
            return False
        else:
            if self.is_right_adjunct(floater_copy):
                return True
            else:
                if floater_copy.container_head() != self.count_specifiers(starting_point_head and ps_iterator_.head()) < 2:
                    if floater_copy.container_head():
                        if '-SPEC:*' not in floater_copy.container_head().features:
                            if floater_copy.container_head().selector():
                                if '-ARG' not in floater_copy.container_head().selector().features:
                                    return True
                                else:
                                    return False
                            else:
                                return True
                        else:
                            return False  # The position is impossible due to -SPEC:*
                    else:
                        return True  # No container, no other conditions must be checked

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
                    and 'FIN' in ps_iterator_.features \
                    and 'FIN' not in ps_iterator_.sister().features:
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

    @staticmethod
    # Counts the number of (in situ non-adjunct) specifiers
    def count_specifiers(h):
        ps_ = h.mother
        count = 0
        # ---------------- while loop begins ----------------------#
        while ps_ and ps_.sister() and \
                (ps_.sister().is_left() and \
                not ps_.sister().is_primitive()) and \
                not ps_.sister().find_me_elsewhere and \
                not ps_.sister().externalized():
            count = count + 1
            ps_ = ps_.walk_upstream()
        # ---------------- while loop ends --------------------------#
        return count