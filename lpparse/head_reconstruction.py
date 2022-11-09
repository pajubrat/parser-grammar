from support import log
from lexical_interface import LexicalInterface

class HeadMovement:
    def __init__(self, controlling_parser_process):
        self.brain_model = controlling_parser_process
        self.name_provider_index = 0
        self.memory_buffer = []
        self.lexical_access = LexicalInterface(self.brain_model)
        self.lexical_access.load_lexicon(self.brain_model)

    def reconstruct(self, phrase_structure):
        current_node = phrase_structure.bottom()
        while current_node.mother or self.get_head_needing_reconstruction(current_node):
            current_node = self.consider_head_reconstruction(current_node, self.get_head_needing_reconstruction(current_node))
        return phrase_structure.top()

    def get_head_needing_reconstruction(self, node):
        if not self.brain_model.LF.interpretable(node, 'head'):
            return node
        if node.is_complex() and not self.brain_model.LF.interpretable(node.left_const, 'head'):
            return node.left_const

    def consider_head_reconstruction(self, current_node, targeted_head):
        if targeted_head:
            current_node = self.create_head_chain(targeted_head, self.determine_intervention_features(targeted_head), self.get_affix_out(targeted_head))
            log(f'={current_node.top()}. ')
            return current_node
        return current_node.mother

    def create_head_chain(self, complex_head, intervention_feature_set, affix):
        if not complex_head.sister() or complex_head.is_right() or complex_head.geometrical_sister().adjunct:
            complex_head.merge_1(affix, 'right')
            return affix

        # --------------- minimal search -------------------------------------------------#
        starting_pos_node = complex_head.sister()
        for node in starting_pos_node:
            if node != starting_pos_node and intervention_feature_set & node.sister().features:
                node = starting_pos_node    # Reset the search pointer after intervention
                break
            node.merge_1(affix, 'left')
            if self.brain_model.LF.validate_reconstructed_head(affix):
                self.brain_model.consume_resources("Head Chain")
                return affix
            affix.remove()
        # --------------------------------------------------------------------------------#

        if not self.consider_right_merge(affix, node, starting_pos_node):
            starting_pos_node.merge_1(affix, 'left') # last resort
            self.brain_model.consume_resources("Head Chain")
        return affix

    def consider_right_merge(self, affix, node, starting_pos_node):
        for const in [node, starting_pos_node]:
            if const.merge_1(affix, 'right') and self.brain_model.LF.validate_reconstructed_head(affix):
                self.brain_model.consume_resources("Head Chain")
                return True
            affix.remove()

    def get_affix_out(self, node):
        affix = node.right_const
        node.right_const = None
        return affix

    def determine_intervention_features(self, head):
        if self.brain_model.narrow_semantics.is_concept(head) and {feature for feature in head.features if feature[:2] == 'OP'}:
            return {'φ'} | set(self.brain_model.narrow_semantics.operator_variable_module.operator_interpretation.keys())
        return {'!COMP:*'}