
class A_reconstruction:
    def __init__(self, controlling_parser_process):
        self.brain_model = controlling_parser_process

    def reconstruct(self, spec):
        if self.candidate_for_A_reconstruction(spec):
            # Special case: [DP H] => [__ [H DP]]
            if spec.sister().is_primitive():
                spec.sister().merge_1(spec.copy_from_memory_buffer(self.brain_model.babtize()), 'right')
                return

            #-----------------minimal search---------------------------------------------------------------------------#
            for node in [node for node in spec.sister()][1:]:
                if self.target_location_for_A_reconstruction(node) and not self.ad_hoc_genitive_filter(node, spec.copy()):
                    node.merge_1(spec.copy_from_memory_buffer(self.brain_model.babtize()), 'left')
                    self.brain_model.consume_resources('A-Move Phrase')
                    self.brain_model.consume_resources('Move Phrase')
                    break
                if self.intervention(node):
                    break
            #-----------------------------------------------------------------------------------------------------------#

    def intervention(self, node):
        return node.left_const and 'φ' in node.left_const.features

    def candidate_for_A_reconstruction(self, spec):
        return spec.is_complex() and \
               spec == spec.container_head().licensed_phrasal_specifier() and \
               'φ' in spec.head().features and \
               spec.sister() and \
               spec.is_left() and \
               not spec.is_primitive()

    def target_location_for_A_reconstruction(self, node):
        return (node.left_const and
                node.left_const.is_primitive() and
                node.sister().is_primitive()) or \
               node.is_primitive()

    def ad_hoc_genitive_filter(self, node, moved_constituent):
        if 'GEN' in moved_constituent.head().features:
            node.merge_1(moved_constituent, 'left')
            if not moved_constituent.external_tail_head_test():
                moved_constituent.remove()
                return True
            moved_constituent.remove()