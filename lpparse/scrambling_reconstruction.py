from lexical_interface import LexicalInterface
from adjunct_constructor import AdjunctConstructor
from support import log


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
        for node in local_tense_edge.minimal_search(lambda x: x == x, lambda x: self.sustain_condition(x, target, local_tense_edge)):
            self.merge_floater(node, virtual_test_item)
            if virtual_test_item.valid_reconstructed_adjunct(starting_point):
                virtual_test_item.remove()
                dropped_floater = self.copy_and_insert(node, target)
                if target in starting_point.edge() and dropped_floater.scan_feature('δPF'):
                    starting_point.features.add('δPF')
                    log(f'\n\t\t{starting_point}° checked EPP.')
                self.brain_model.narrow_semantics.pragmatic_pathway.unexpected_order_occurred(dropped_floater, starting_point)
                return
            virtual_test_item.remove()

    # Don't reconstruct inside the element itself; into moved phrase; inside another finite clause
    def sustain_condition(self, node, target, local_tense_edge):
        return not (node.mother == target or node.mother.find_me_elsewhere or (node.force() and node.container() != local_tense_edge.head()))

    def copy_and_insert(self, node, original_floater):
        if not original_floater.adjunct:
            self.adjunct_constructor.externalize_structure(original_floater)
        reconstructed_floater = original_floater.copy_for_chain(self.babtize())
        self.merge_floater(node, reconstructed_floater)
        self.brain_model.consume_resources("Scrambling Chain", reconstructed_floater)
        return reconstructed_floater

    def merge_floater(self, node, floater):
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

    def babtize(self):
        self.name_provider_index += 1
        return str(self.name_provider_index)