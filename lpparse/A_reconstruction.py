class A_reconstruction:
    def __init__(self, controlling_parser_process):
        self.brain_model = controlling_parser_process

    def reconstruct(self, spec):
        if spec == spec.container().licensed_phrasal_specifier() or spec.candidate_for_VP_fronting():

            # Special case: [DP H] => [__ [H DP]]
            if spec.sister().is_primitive():
                spec.sister().merge_1(spec.copy_for_reconstruction(self.brain_model.babtize()), 'right')
                self.brain_model.consume_resources('A-Chain')
                return
            if spec.sister().find_me_elsewhere:
                return

            # -----------------minimal search---------------------------------------------------------------------------#
            for node in [node for node in spec.sister()][1:]:
                if node.has_vacant_phrasal_position():
                    node.merge_1(spec.copy_for_reconstruction(self.brain_model.babtize()), 'left')
                    self.brain_model.consume_resources('A-Chain')
                    break
                if node.is_complex() and node.left_const.referential():  #Intervention
                    break
            # -----------------------------------------------------------------------------------------------------------#
