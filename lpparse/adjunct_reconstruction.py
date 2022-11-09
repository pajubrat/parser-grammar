from support import log, illu, set_logging
from lexical_interface import LexicalInterface
from adjunct_constructor import AdjunctConstructor

class FloaterMovement():
    def __init__(self, controlling_parser_process):
        self.brain_model = controlling_parser_process
        self.name_provider_index = 0
        self.memory_buffer = []
        self.lexical_access = LexicalInterface(self.brain_model)
        self.lexical_access.load_lexicon(self.brain_model)
        self.adjunct_constructor = AdjunctConstructor(self.brain_model)

    def reconstruct(self, ps):
        for constituent in [daughter_const for node in ps.top() for daughter_const in [node.left_const, node.right_const] if self.trigger_reconstruction(daughter_const)]:
            self.reconstruct_floater(constituent)
            if constituent.is_right():
                break
        return ps.top()

    def trigger_reconstruction(self, target):
        return target and target.adjoinable_and_floatable() and not self.operator_in_scope_position(target) and not self.brain_model.LF.interpretable(target, 'adjunct')

    def operator_in_scope_position(self, ps):
        return self.brain_model.narrow_semantics.operator_variable_module.scan_criterial_features(ps) and ps.container() and ps.container().head().finite()

    def reconstruct_floater(self, target):
        # Exception: only non-adverbial and uninterpretable right adjuncts are reconstructed if they are inside finite construction
        if target.is_right():
            self.adjunct_constructor.externalize_structure(target.head())
            if target.head().adverbial() or not target.top().contains_finiteness() or self.brain_model.LF.interpretable(target, 'adjunct'):
                return  # No reconstruction

        starting_point = self.set_starting_point(target)
        virtual_test_item = target.copy()
        local_tense_edge = target.local_tense_edge()
        # ------------------------------------ minimal search ------------------------------------#
        for node in local_tense_edge:
            if self.termination_condition(node, target, local_tense_edge):
                break
            self.merge_floater(node, virtual_test_item)
            if self.brain_model.LF.validate_reconstructed_adjunct(virtual_test_item, starting_point):
                virtual_test_item.remove()
                dropped_floater = self.copy_and_insert(node, target)
                self.brain_model.narrow_semantics.pragmatic_pathway.unexpected_order_occurred(dropped_floater, starting_point)
                return
            virtual_test_item.remove()
        # ---------------------------------------------------------------------------------------#

    def set_starting_point(self, target):
        if target.is_left():
            return target.container()

    def termination_condition(self, node, floater, local_tense_edge):
        return node == floater or node.find_me_elsewhere or \
               (node.is_complex() and node.left_const.force() and node.head() != local_tense_edge.head()) or \
               (node.sister() and node.sister().is_primitive() and node.sister().referential())

    def copy_and_insert(self, node, original_floater):
        if not original_floater.adjunct:
            self.adjunct_constructor.externalize_structure(original_floater)
        reconstructed_floater = original_floater.copy_for_reconstruction(self.babtize())
        self.merge_floater(node, reconstructed_floater)
        self.brain_model.consume_resources("Adjunct Chain")
        return reconstructed_floater

    def merge_floater(self, node, dropped_floater):
        if dropped_floater.adverbial_adjunct():
            node.merge_1(dropped_floater, 'right')
        else:
            node.merge_1(dropped_floater, 'left')
        self.adjunct_constructor.externalize_structure(dropped_floater)

    def babtize(self):
        self.name_provider_index += 1
        return str(self.name_provider_index)