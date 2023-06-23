from lexical_interface import LexicalInterface
from adjunct_constructor import AdjunctConstructor
from support import log


# This class must be decomposed into independent left and right operations such that the latter contains extraposition
class ScramblingReconstruction():
    def __init__(self, controlling_parser_process):
        self.brain_model = controlling_parser_process
        self.name_provider_index = 0
        self.memory_buffer = []
        self.lexical_access = LexicalInterface(self.brain_model)
        self.lexical_access.load_lexicon(self.brain_model)
        self.adjunct_constructor = AdjunctConstructor(self.brain_model)

    def reconstruct(self, ps):
        for target in ps.symmetric_minimal_search(lambda x: x.trigger_adjunct_reconstruction(), lambda x: x.is_right()):
            self.reconstruct_scrambled_item(target)

    def reconstruct_scrambled_item(self, target):
        if target.is_right():
            self.adjunct_constructor.externalize_structure(target.head())
            if target.legible_adjunct() or target.head().adverbial() or not target.top().contains_finiteness():
                return

        starting_point = target.container()
        virtual_test_item = target.copy()
        local_tense_edge = target.local_tense_edge()

        node = starting_point
        for node in local_tense_edge.minimal_search(lambda x: True, lambda x: self.sustain_condition(x, target, local_tense_edge)):
            self.merge_floater(node, virtual_test_item)
            if self.test_adjunction_solution(node, target, virtual_test_item, starting_point, 'left'):
                break
        else:
            node.Merge(virtual_test_item, 'right')
            virtual_test_item.adjunct = False
            self.test_adjunction_solution(node, target, virtual_test_item, starting_point, 'right')

    def test_adjunction_solution(self, node, target, virtual_test_item, starting_point, direction):
        if virtual_test_item.valid_reconstructed_adjunct(starting_point):
            virtual_test_item.remove()
            dropped_floater = self.copy_and_insert(node, target, direction)
            if target in starting_point.edge() and starting_point.requires_SUBJECT():
                starting_point.scan_criterial_features(dropped_floater, 'ΔOP')
                starting_point.copy_criterial_features(dropped_floater)
            starting_point.features = self.brain_model.transfer.access_lexicon.apply_redundancy_rules(starting_point.features)
            self.brain_model.narrow_semantics.pragmatic_pathway.unexpected_order_occurred(dropped_floater, starting_point)
            return True
        virtual_test_item.remove()

    # Don't reconstruct:inside the element itself; into moved phrase; inside another finite clause
    def sustain_condition(self, node, target, local_tense_edge):
        return not (node.mother == target or
                    node.mother.find_me_elsewhere or
                    (node.force() and node.container() != local_tense_edge.head()) or
                    (node.primitive() and node.referential()))

    def copy_and_insert(self, node, original_floater, direction):
        if not original_floater.adjunct:
            self.adjunct_constructor.externalize_structure(original_floater)
        reconstructed_floater = original_floater.copy_for_chain(self.babtize())
        self.merge_floater(node, reconstructed_floater, direction)
        self.brain_model.consume_resources("Scrambling Chain", reconstructed_floater)
        return reconstructed_floater

    def merge_floater(self, node, floater, direction='left'):
        if direction == 'left':
            if node.is_right():
                if floater.adverbial_adjunct():
                    node.Merge(floater, 'right')
                else:
                    node.Merge(floater, 'left')
            else:
                if floater.adverbial_adjunct():
                    node.mother.Merge(floater, 'right')
                else:
                    node.mother.Merge(floater, 'left')
            self.adjunct_constructor.externalize_structure(floater)
        elif direction == 'right':
            node.Merge(floater, 'right')
            floater.adjunct = False

    def babtize(self):
        self.name_provider_index += 1
        return str(self.name_provider_index)