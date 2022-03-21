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
        for node in [node for node in ps.top()]:
            f = self.get_floater(node)
            if f:
                self.drop_floater(f)
                if f.is_right():
                    break
        return ps.top()

    def get_floater(self, ps):
        if self.detect_floater(ps.left_const):
            H = ps.left_const.head()
            if not H.tail_test():
                log(ps.left_const.illustrate() + ' failed ' + illu(H.get_tail_sets()) + '. ')
                return ps.left_const
            if ps.left_const.container():
                J = ps.left_const.container()
                if (J.EPP() and 'FIN' in J.features) or ('-SPEC:*' in J.features and ps.left_const == next((const for const in J.edge()), None)):
                    return ps.left_const

        if self.detect_floater(ps.right_const):
            H = ps.right_const.head()
            if not H.tail_test():
                log(ps.right_const.illustrate() + ' failed ' + illu(H.get_tail_sets()) + '. ')
                if 'ADV' not in H.features and H.top().contains_feature('FIN'):
                    self.adjunct_constructor.externalize_structure(H)
                    if not ps.right_const.head().tail_test():
                        return ps.right_const
                elif 'ADV' in H.features and not ps.right_const.adjunct:
                    self.adjunct_constructor.externalize_structure(H)
                    # No need to drop, hence externalization is sufficient

    def detect_floater(self, ps):
        return ps and \
               ps.is_complex() and \
               not ps.find_me_elsewhere and \
               ps.head().get_tail_sets() and \
               'adjoinable' in ps.head().features and \
               '-adjoinable' not in ps.head().features and \
               '-float' not in ps.head().features and \
               not self.controlling_parser_process.narrow_semantics.operator_variable_module.scan_criterial_features(ps)

    def drop_floater(self, original_floater):
        def termination_condition(node, floater, local_tense_edge):
            return node == floater or node.find_me_elsewhere or \
                   (node.is_complex() and 'FORCE' in node.left_const.features and node.head() != local_tense_edge.head()) or \
                   (node.sister() and node.sister().is_primitive() and 'φ' in node.sister().features)

        log(f'Reconstructing {original_floater}...')
        if original_floater.is_left():
            starting_point_head = original_floater.container()
        else:
            starting_point_head = None
        test_item = original_floater.copy()
        local_tense_edge = self.local_tense_edge(original_floater)
        # ------------------------------------ minimal search ------------------------------------#
        for node in local_tense_edge:
            if termination_condition(node, original_floater, local_tense_edge):
                break
            self.merge_floater(node, test_item)
            self.adjunct_constructor.externalize_structure(test_item)
            if self.validate_position(test_item, starting_point_head):
                test_item.remove()
                dropped_floater = self.copy_and_insert_floater(node, original_floater)
                self.controlling_parser_process.narrow_semantics.pragmatic_pathway.unexpected_order_occurred(dropped_floater, starting_point_head)
                return
            test_item.remove()
        # ---------------------------------------------------------------------------------------#

    def copy_and_insert_floater(self, node, original_floater):
        if not original_floater.adjunct:
            self.adjunct_constructor.externalize_structure(original_floater)
        dropped_floater = original_floater.copy_from_memory_buffer(self.babtize())
        self.merge_floater(node, dropped_floater)
        self.controlling_parser_process.consume_resources("Move Adjunct")
        self.controlling_parser_process.consume_resources("Move Phrase", f'{dropped_floater.illustrate()}')
        return dropped_floater

    def merge_floater(self, node, dropped_floater):
        if self.is_right_adjunct(dropped_floater):
            node.merge_1(dropped_floater, 'right')
        else:
            node.merge_1(dropped_floater, 'left')

    def validate_position(self, test_item, starting_point_head):
        return self.conditions_for_right_adjuncts(test_item) or \
                self.conditions_for_left_adjuncts(test_item, starting_point_head)

    def is_right_adjunct(self, test_item):
        return {'ADV', 'P'} & test_item.head().features

    def conditions_for_right_adjuncts(self, test_item):
        return test_item.head().tail_test() and self.is_right_adjunct(test_item)

    def conditions_for_left_adjuncts(self, test_item, starting_point_head):
        if test_item.head().tail_test():
            if 'GEN' in test_item.head().features and 'φ' not in test_item.container().features:
                return True
            if not test_item.container():
                return True
            if test_item.container() == starting_point_head:
                return False
            if '-SPEC:*' in test_item.container().features:
                return False
            if 'φ' in test_item.head().features and not self.controlling_parser_process.LF.projection_principle(test_item.head(), 'weak'):
                return False
            if not test_item.container().selector():
                return True
            if '-ARG' not in test_item.container().selector().features:
                return True
            return True

    def local_tense_edge(self, ps):
        return next((node.mother for node in ps.working_memory_path() if {'T/fin', 'FORCE'} & node.features), ps.top())

    def babtize(self):
        self.name_provider_index += 1
        return str(self.name_provider_index)