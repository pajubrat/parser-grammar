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
        # ------------------ upward sequence --------------------------------------------------#
        current_node = phrase_structure.bottom()
        while not (current_node.root() and not self.detect_complex_head(current_node)):
            targeted_head = self.detect_complex_head(current_node)
            if targeted_head:
                log(f'Reconstruct {targeted_head.right_const} from {targeted_head}...')
                intervention_feature_set = self.determine_intervention_features(targeted_head)
                current_node = self.create_head_chain(targeted_head, self.get_affix_out(targeted_head), intervention_feature_set)
                log(f'={phrase_structure.top()}...')
            else:
                current_node = current_node.mother
        # -------------------------------------------------------------------------------------#
        return phrase_structure.top()

    def detect_complex_head(self, node):
        if node.complex_head():
            return node
        if node.is_complex() and node.left_const.complex_head():
            return node.left_const

    def create_head_chain(self, complex_head, affix, intervention_feature_set):
        if self.no_structure_for_reconstruction(complex_head):
            complex_head.merge_1(affix, 'right')
            return affix
        else:
            phrase_structure = complex_head.sister()
            # --------------- minimal search -------------------------------------------------#
            for node in phrase_structure:
                if self.causes_intervention(node, intervention_feature_set, phrase_structure):
                    log(f'{node.sister()} causes intervention with {intervention_feature_set}...')
                    self.last_resort(phrase_structure, affix)
                    return affix
                node.merge_1(affix, 'left')
                if self.reconstruction_is_successful(affix):
                    self.brain_model.consume_resources("Move Head")
                    return affix

                affix.remove()
            # --------------------------------------------------------------------------------#
            node.merge_1(affix, 'right')
            if self.reconstruction_is_successful(affix):
                self.brain_model.consume_resources("Move Head")
                return affix

            self.last_resort(phrase_structure, affix)
            return affix

    def reconstruction_is_successful(self, affix):
        if not self.head_is_selected(affix):    # Default behavior
            return False
        if not self.extra_condition(affix):     # One edge case
            return False
        return True

    def extra_condition(self, affix):
        if self.head_is_EPP_selected_by_C_fin(affix):
            if affix.local_edge():
                # Exception 1. Finnish third person forms (ultimate reason unknown)
                if 'pro' in affix.local_edge().features and 'PHI:PER:3' in affix.local_edge().features:
                    return False
                return True
            else:
                # Exception 2. The the structure is [Affix, X], Affix finite EPP head and with X primitive head
                if affix.sister() and affix.sister().terminal_node():
                    return True
                else:
                    return False
        return True

    def get_affix_out(self, node):
        if node.complex_head():
            affix = node.right_const
            node.right_const = None     # Head reconstruction is not copying
            return affix
        else:
            return node

    def determine_intervention_features(self, head):
        if head.has_op_feature() and self.brain_model.narrow_semantics.is_concept(head):
            return {'φ'} | set(self.brain_model.narrow_semantics.operator_variable_module.operator_interpretation.keys())
        return {'!COMP:*'}

    def last_resort(self, phrase_structure, affix):
        log(f'Reconstruction of {affix} failed, use last resort...{phrase_structure}')
        phrase_structure.merge_1(affix, 'left')
        self.brain_model.consume_resources("Move Head")

    @staticmethod
    def no_structure_for_reconstruction(complex_head):
        if not complex_head.sister() or complex_head.is_right():
            return True

    @staticmethod
    def head_is_selected(affix):
        def selects(h, selectee):
            if h.has_affix():
                selector = h.bottom_affix()
            else:
                selector = h
            return selectee.features & selector.licensed_complements()
        return affix.selector() and selects(affix.selector(), affix)

    @staticmethod
    def head_is_EPP_selected_by_C_fin(affix):
        return 'C/fin' in affix.selector().features and affix.EPP()

    @staticmethod
    def causes_intervention(node, feature_set, phrase_structure):
        if node != phrase_structure.minimal_search()[0] and feature_set & node.sister().features:
            return True