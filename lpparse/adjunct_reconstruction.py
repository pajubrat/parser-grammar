from support import log, illu, set_logging
from lexical_interface import LexicalInterface
from adjunct_constructor import AdjunctConstructor

class FloaterMovement():
    def __init__(self, controlling_parser_process):
        self.controlling_parser_process = controlling_parser_process
        self.name_provider_index = 0
        self.memory_buffer = []
        self.lexical_access = LexicalInterface(self.controlling_parser_process)
        self.lexical_access.load_lexicon(self.controlling_parser_process)
        self.adjunct_constructor = AdjunctConstructor(self.controlling_parser_process)

    def reconstruct(self, ps):
        for node in ps.top():
            self.drop_floater(self.get_floater_if_present(node))
        return ps.top()

    def get_floater_if_present(self, ps):
        if self.detect_left_floater(ps):
            floater = ps.left_const

            # Case (1): XP fails the tail test
            if not floater.head().tail_test():
                log(floater.illustrate() + ' failed to tail ' + illu(floater.head().get_tail_sets()) + '...')
                return floater.head().max()

            # Case (2): XP sits in an EPP position;
            if floater.mother and floater.mother.head().EPP() and 'FIN' in floater.mother.head().features:
                log(floater.illustrate() + ' is in an EPP SPEC position...')
                return floater.head().max()

            # Case (3): XP sits in a specifier position that does not exist
            if floater.mother and '-SPEC:*' in floater.mother.head().features and floater == next((const for const in floater.mother.head().edge()), None):
                log(floater.illustrate() + ' is in an specifier position that cannot be projected...')
                return floater.head().max()

        if self.detect_right_floater(ps):
            floater = ps.right_const.head()
            if not floater.tail_test():
                log(floater.illustrate() + ' failed to tail ' + illu(floater.head().get_tail_sets()) + '...')
                if 'ADV' not in floater.features and floater.top().contains_feature('FIN'):
                    self.adjunct_constructor.externalize_structure(floater)
                    return floater.head().max()
                if 'ADV' in floater.features and not ps.right_const.adjunct:
                    self.adjunct_constructor.externalize_structure(floater)

    def detect_left_floater(self, ps):
        return ps.is_complex() and \
                ps.left_const.is_complex() and \
                not ps.left_const.find_me_elsewhere and \
                ps.left_const.head().get_tail_sets() and \
                'adjoinable' in ps.left_const.head().features and \
                '-adjoinable' not in ps.left_const.head().features and \
                '-float' not in ps.left_const.head().features and \
                not self.controlling_parser_process.narrow_semantics.operator_variable_module.scan_criterial_features(ps.left_const)

    def detect_right_floater(self, ps):
        return ps.is_complex() and \
                ps.right_const.head().get_tail_sets() and \
                not ps.right_const.find_me_elsewhere and \
               'adjoinable' in ps.right_const.head().features and \
                '-adjoinable' not in ps.right_const.head().features and \
                '-float' not in ps.right_const.head().features

    def drop_floater(self, floater):
        if floater:
            log(f'Reconstructing {floater}...')
            if floater.is_left():
                starting_point_head = floater.container_head()
            else:
                starting_point_head = None
            floater_copy = floater.copy()
            local_tense_edge = self.local_tense_edge(floater)
            # ------------------------------------ minimal search ------------------------------------#
            for node in local_tense_edge:
                if self.termination_condition(node, floater, local_tense_edge):
                    break
                self.merge_floater(node, floater_copy) # Right adjuncts to right, left adjuncts to left
                self.adjunct_constructor.externalize_structure(floater_copy) # Externalize for testing
                if self.is_drop_position(floater_copy, starting_point_head):
                    if not floater.adjunct:
                        self.adjunct_constructor.externalize_structure(floater)
                    dropped_floater = floater.copy_from_memory_buffer(self.babtize())
                    self.merge_floater(node, dropped_floater)
                    self.controlling_parser_process.consume_resources("Move Adjunct")
                    self.controlling_parser_process.consume_resources("Move Phrase", f'{dropped_floater.illustrate()}')
                    self.controlling_parser_process.narrow_semantics.pragmatic_pathway.unexpected_order_occurred(dropped_floater, starting_point_head)
                    floater_copy.remove()
                    return
                floater_copy.remove()
            # ---------------------------------------------------------------------------------------#

    def merge_floater(self, node, floater_copy):
        if self.is_right_adjunct(floater_copy):
            node.merge_1(floater_copy, 'right')
        else:
            node.merge_1(floater_copy, 'left')

    def termination_condition(self, node, floater, local_tense_edge):
        if node == floater:
            return True

        if node.find_me_elsewhere:
            return True

        if node.is_complex() and 'FORCE' in node.left_const.features and node.head() != local_tense_edge.head():
            log(f'Intervention by finiteness at {node}...')
            return True

        if node.sister() and node.sister().is_primitive() and 'φ' in node.sister().features:
            log(f'Intervention by φ at {node}...')
            return True

    def is_right_adjunct(self, node):
        return 'ADV' in node.head().features or 'P' in node.head().features

    def is_drop_position(self, floater_copy, starting_point_head):
        return self.conditions_for_right_adjuncts(floater_copy) or \
                self.conditions_for_left_adjuncts(floater_copy, starting_point_head)

    def conditions_for_right_adjuncts(self, floater):
        return floater.head().tail_test() and self.is_right_adjunct(floater)

    def conditions_for_left_adjuncts(self, floater, starting_point_head):
        return floater.head().tail_test() and self.license_floater_position(floater, starting_point_head)

    def license_floater_position(self, floater, starting_point_head):
        if not floater.container_head():
            return True
        if floater.container_head() == starting_point_head:
            return False
        if '-SPEC:*' in floater.container_head().features:
            return False
        if 'φ' in floater.head().features and not self.controlling_parser_process.LF.projection_principle(floater.head(), 'weak'):
            return False
        if not floater.container_head().selector():
            return True
        if '-ARG' not in floater.container_head().selector().features:
            return True

    def local_tense_edge(self, ps):
        return next((node.mother for node in ps.working_memory_path() if {'T/fin', 'FORCE'} & node.features), ps.top())

    def babtize(self):
        self.name_provider_index += 1
        return str(self.name_provider_index)