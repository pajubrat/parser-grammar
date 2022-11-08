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
        for constituent in [const for node in ps.top() for const in [node.left_const, node.right_const]]:
            if self.detect_potential_floater(constituent):
                if self.reconstruct_floater(self.get_floater(constituent)):
                    break
        return ps.top()

    def get_floater(self, target_phrase):
        if target_phrase.is_left():
            return self.get_left_floater_for_reconstruction(target_phrase)
        else:
            return self.get_right_floater_for_reconstruction(target_phrase)

    def get_left_floater_for_reconstruction(self, target_phrase):
        if self.floater_in_wrong_position(target_phrase) or target_phrase.in_EPP_position():
            return target_phrase

    def floater_in_wrong_position(self, target_phrase):
        if not target_phrase.head().tail_test():
            log(f'{target_phrase.illustrate()}({illu(target_phrase.head().get_tail_sets())}) needs reconstruction. ')
            return True

    def get_right_floater_for_reconstruction(self, target_phrase):
        if self.floater_in_wrong_position(target_phrase):
            if not target_phrase.head().adverbial() and target_phrase.top().contains_feature('Fin'):
                self.adjunct_constructor.externalize_structure(target_phrase.head())
                if self.floater_in_wrong_position(target_phrase):
                    return target_phrase
            elif target_phrase.head().adverbial():
                self.adjunct_constructor.externalize_structure(target_phrase.head())
                # No need to reconstruct, externalization is sufficient

    def detect_potential_floater(self, ps):
        return ps and ps.adjoinable_and_floatable() and self.do_not_float_operators_at_scope_position(ps)

    def do_not_float_operators_at_scope_position(self, ps):
        # If there are criterial features
        if self.controlling_parser_process.narrow_semantics.operator_variable_module.scan_criterial_features(ps):
            # If this phrase structure has scope position somewhere
            if ps.top().contains_feature('Fin'):
                # If the operator cannot see FIN, it means it is not in a scope position
                for node in ps.head().working_memory_path('FORCE'):
                    if node.finite():
                        return True
                # If the operator cannot see FIN upwards, it means that it is probably in a scope position
                return False
        return True

    def reconstruct_floater(self, target_phrase):
        def termination_condition(node, floater, local_tense_edge):
            return node == floater or node.find_me_elsewhere or \
                   (node.is_complex() and 'FORCE' in node.left_const.features and node.head() != local_tense_edge.head()) or \
                   (node.sister() and node.sister().is_primitive() and 'φ' in node.sister().features)

        if target_phrase:
            log(f'Reconstructing {target_phrase}...')
            if target_phrase.is_left():
                starting_point_head = target_phrase.container()
            else:
                starting_point_head = None
            test_item = target_phrase.copy()
            local_tense_edge = self.local_tense_edge(target_phrase)
            # ------------------------------------ minimal search ------------------------------------#
            for node in local_tense_edge:
                if termination_condition(node, target_phrase, local_tense_edge):
                    break
                self.merge_floater(node, test_item)
                self.adjunct_constructor.externalize_structure(test_item)
                if self.validate_position(test_item, starting_point_head):
                    test_item.remove()
                    dropped_floater = self.copy_and_insert_floater(node, target_phrase)
                    self.controlling_parser_process.narrow_semantics.pragmatic_pathway.unexpected_order_occurred(dropped_floater, starting_point_head)
                    return True
                test_item.remove()
            # ---------------------------------------------------------------------------------------#

    def copy_and_insert_floater(self, node, original_floater):
        if not original_floater.adjunct:
            self.adjunct_constructor.externalize_structure(original_floater)
        dropped_floater = original_floater.copy_from_memory_buffer(self.babtize())
        self.merge_floater(node, dropped_floater)
        self.controlling_parser_process.consume_resources("Adjunct Chain")
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
        return test_item.adverbial() or 'P' in test_item.head().features

    def conditions_for_right_adjuncts(self, test_item):
        return test_item.head().tail_test() and self.is_right_adjunct(test_item)

    def conditions_for_left_adjuncts(self, test_item, starting_point_head):
        if test_item.head().tail_test():
            if not test_item.container():
                return True
            if 'GEN' in test_item.head().features and 'φ' not in test_item.container().features:
                return True
            if test_item.container() == starting_point_head:
                return False
            if '-SPEC:*' in test_item.container().features:
                return False
            if 'φ' in test_item.head().features and self.controlling_parser_process.LF.projection_principle(test_item.head(), 'weak'):
                return False
            return True

    def local_tense_edge(self, ps):
        return next((node.mother for node in ps.working_memory_path('FORCE') if {'T/fin', 'FORCE'} & node.features), ps.top())

    def babtize(self):
        self.name_provider_index += 1
        return str(self.name_provider_index)