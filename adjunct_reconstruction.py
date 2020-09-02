from support import log, illu
from LexicalInterface import LexicalInterface
from adjunct_constructor import AdjunctConstructor


class FloaterMovement():
    def __init__(self, controlling_parser_process):
        self.controlling_parser_process = controlling_parser_process
        self.name_provider_index = 0
        self.memory_buffer = []
        self.lexical_access = LexicalInterface(self.controlling_parser_process)
        self.lexical_access.load_lexicon(self.controlling_parser_process)
        self.adjunct_constructor = AdjunctConstructor(self.controlling_parser_process)

    # Definition for floater reconstruction
    def reconstruct(self, ps):
        # ------------------------------------ minimal search ----------------------------------------#
        for node in ps.top().minimal_search():
            floater = self.detect_floater(node)
            if floater:
                log(f'\t\t\t\t\tDropping {floater}')
                self.drop_floater(floater, ps)
        # -------------------------------------------------------------------------------------------#
        return ps.top()  # Return top, because it is possible that an adjunct expands the structure

    def detect_floater(self, ps):
        if self.detect_left_floater(ps):
            floater = ps.left_const
            if not floater.head().external_tail_head_test():
                log('\t\t\t\t\t' + floater.illustrate() + ' failed to tail ' + illu(floater.head().get_tail_sets()))
                return floater
            if floater.mother and floater.mother.head().EPP() and 'FIN' in floater.mother.head().features:
                log('\t\t\t\t\t' + floater.illustrate() + ' is in an EPP SPEC position.')
                return floater
            if floater.mother and '-SPEC:*' in floater.mother.head().features and floater == floater.mother.head().local_edge():
                log('\t\t\t\t\t' + floater.illustrate() + ' is in an specifier position that cannot be projected.')
                return floater
        if self.detect_right_floater(ps):
            floater = ps.right_const.head()
            if not floater.external_tail_head_test():
                log('\t\t\t\t\t' + floater.illustrate() + ' failed to tail ' + illu(floater.head().get_tail_sets()))
                if 'ADV' not in floater.features and floater.top().contains_feature('FIN'):
                    self.adjunct_constructor.create_adjunct(floater)
                    return floater
                if 'ADV' in floater.features and not ps.right_const.adjunct:
                    self.adjunct_constructor.create_adjunct(floater)

    def detect_left_floater(self, ps):
        if ps.is_complex() and \
                ps.left_const.is_complex() and \
                not ps.left_const.find_me_elsewhere and \
                ps.left_const.head().get_tail_sets() and \
                'adjoinable' in ps.left_const.head().features and \
                '-adjoinable' not in ps.left_const.head().features and \
                not ps.scan_criterial_features():
            return True

    def detect_right_floater(self, ps):
        if ps.is_complex() and \
                ps.right_const.head().get_tail_sets() and \
                'adjoinable' in ps.right_const.head().features and \
                '-adjoinable' not in ps.right_const.head().features:
            return True

    # Definition for floater reconstruction (dropping)
    def drop_floater(self, floater, ps):
        starting_point_head = floater.container_head()
        floater_copy = floater.copy()
        # ------------------------------------ minimal search ------------------------------------#
        for node in self.local_tense_edge(floater.mother).minimal_search():
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
        return node == floater or node.find_me_elsewhere

    def is_right_adjunct(self, node):
        return 'ADV' in node.head().features or 'P' in node.head().features

    # Definition for a legitimate target position for floater reconstruction
    def is_drop_position(self, ps, floater_copy, starting_point_head):
        if self.conditions_for_right_adjuncts(floater_copy):
            return True
        if self.conditions_for_left_adjuncts(floater_copy, starting_point_head):
            return True

    def conditions_for_right_adjuncts(self, floater):
        if floater.head().external_tail_head_test():
            if self.is_right_adjunct(floater):
                return True

    # Definition for conditions for left adjuncts
    # Note. Interacts with specifier mechanisms
    def conditions_for_left_adjuncts(self, floater, starting_point_head):
        if floater.head().external_tail_head_test() and self.license_to_specifier_position(floater, starting_point_head):
            return True

    def license_to_specifier_position(self, floater, starting_point_head):
        if not floater.container_head():
            return True
        if floater.container_head() == starting_point_head:
            return False
        if '-SPEC:*' in floater.container_head().features:
            return False
        if not floater.container_head().selector():
            return True
        if '-ARG' not in floater.container_head().selector().features:
            return True

    # Definition for minimal tense edge
    def local_tense_edge(self, ps):
        node = ps.top()
        # --------------------------- upstream search ---------------------------------------- #
        for node in ps.upstream_search():
            if 'FIN' in node.head().features and node.sister() and node.sister().is_primitive() and 'FIN' not in node.sister().head().features:
                break
        # --------------------------------------------------------------------------------------#
        return node

    # Provide unique names when chains are formed
    def babtize(self):
        self.name_provider_index += 1
        return str(self.name_provider_index)