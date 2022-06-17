from support import set_logging, log, get_number_of_operations, reset_number_of_operations, log_result, illu
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
        while current_node.mother or self.detect_complex_head(current_node):
            current_node = self.consider_head_reconstruction(current_node, self.detect_complex_head(current_node))
        return phrase_structure.top()

    def detect_complex_head(self, node):
        if node.complex_head():
            return node
        if node.is_complex() and node.left_const.complex_head():
            return node.left_const

    def consider_head_reconstruction(self, current_node, targeted_head):
        if targeted_head:
            log(f'Reconstruct {targeted_head.right_const} from {targeted_head}...')
            current_node = self.create_head_chain(targeted_head, self.determine_intervention_features(targeted_head), self.get_affix_out(targeted_head))
            log(f'={current_node.top()}...')
            return current_node
        return current_node.mother

    def create_head_chain(self, complex_head, intervention_feature_set, affix):
        if not complex_head.sister() or complex_head.is_right():
            complex_head.merge_1(affix, 'right')
            return affix

        # --------------- minimal search -------------------------------------------------#
        starting_pos_node = complex_head.sister()
        for node in starting_pos_node:
            if node != starting_pos_node and intervention_feature_set & node.sister().features:
                node = starting_pos_node    # Reset the search pointer after intervention
                break
            node.merge_1(affix, 'left')
            if self.reconstruction_is_successful(affix):
                self.brain_model.consume_resources("Move Head")
                return affix
            affix.remove()
        # --------------------------------------------------------------------------------#

        if not self.consider_right_merge(affix, node, starting_pos_node):
            starting_pos_node.merge_1(affix, 'left') # last resort
            self.brain_model.consume_resources("Move Head")

        return affix

    def reconstruction_is_successful(self, reconstructed_affix):
        return reconstructed_affix.features & reconstructed_affix.selector().bottom_affix().licensed_complements() and \
               not self.extra_condition_violation(reconstructed_affix)

    def consider_right_merge(self, affix, node, starting_pos_node):
        for const in [node, starting_pos_node]:
            if const.merge_1(affix, 'right') and self.reconstruction_is_successful(affix):
                self.brain_model.consume_resources("Move Head")
                return True
            affix.remove()

    def extra_condition_violation(self, affix):
        return 'C/fin' in affix.selector().features and affix.EF() and not affix.edge_specifiers()

    def get_affix_out(self, node):
        affix = node.right_const
        node.right_const = None
        return affix

    def determine_intervention_features(self, head):
        if self.brain_model.narrow_semantics.is_concept(head) and {feature for feature in head.features if feature[:2] == 'OP'}:
            return {'φ'} | set(self.brain_model.narrow_semantics.operator_variable_module.operator_interpretation.keys())
        return {'!COMP:*'}