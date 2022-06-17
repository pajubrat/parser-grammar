from support import log

class A_reconstruction:
    def __init__(self, controlling_parser_process):
        self.brain_model = controlling_parser_process

    def reconstruct(self, spec):
        log(f'{spec}, {spec.container()}')
        if spec == spec.container().licensed_phrasal_specifier() or self.VP_fronting_in_Finnish(spec):

            # Special case: [DP H] => [__ [H DP]]
            if spec.sister().is_primitive():
                spec.sister().merge_1(spec.copy_from_memory_buffer(self.brain_model.babtize()), 'right')
                return

            if spec.sister().find_me_elsewhere:
                return

            # -----------------minimal search---------------------------------------------------------------------------#
            for node in [node for node in spec.sister()][1:]:
                if self.target_location_for_A_reconstruction(node):
                    node.merge_1(spec.copy_from_memory_buffer(self.brain_model.babtize()), 'left')
                    self.brain_model.consume_resources('A-Move Phrase')
                    self.brain_model.consume_resources('Move Phrase')
                    break
                if self.intervention(node):
                    break
            # -----------------------------------------------------------------------------------------------------------#

    def intervention(self, node):
        return node.left_const and 'φ' in node.left_const.features

    def VP_fronting_in_Finnish(self, spec):
        return spec == next((spec for spec in spec.container().edge_specifiers() if {'A/inf', 'VA/inf'} & spec.head().features), None)

    def target_location_for_A_reconstruction(self, node):
        return (node.left_const and node.left_const.is_primitive() and node.sister().is_primitive()) or node.is_primitive()