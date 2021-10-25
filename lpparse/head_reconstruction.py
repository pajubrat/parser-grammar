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
        # ------------------ minimal search ----------------------------------------------#
        for node in phrase_structure:
            if self.detect_complex_head(node):
                complex_head = self.detect_complex_head(node)
                log(f'Reconstruct {complex_head.right_const} from {complex_head}...')
                intervention_feature = self.determine_intervention_feature(complex_head)
                self.create_head_chain(complex_head, self.get_affix_out(complex_head), intervention_feature)
                log(f'={phrase_structure.top()}...')
        #------------------------------------------------------------------------------------#
        return phrase_structure.top()

    @staticmethod
    def detect_complex_head(h):
        if h.left_const and h.left_const.is_primitive() and h.left_const.has_affix():   # [X(Y) Z]
            return h.left_const
        if h.is_primitive() and h.has_affix():                                          # [Z X(Y)]
            return h

    def create_head_chain(self, complex_head, affix, intervention_feature):
        if self.no_structure_for_reconstruction(complex_head):
            self.reconstruct_to_sister(complex_head, affix)
        else:
            phrase_structure = complex_head.sister()
            node = None
            # --------------- minimal search -----------------------------------------------#
            for node in phrase_structure:
                if self.causes_intervention(node, intervention_feature, phrase_structure):
                    self.last_resort(phrase_structure, affix)
                    return
                node.merge_1(affix, 'left')
                if self.reconstruction_is_successful(affix):
                    self.brain_model.consume_resources("Move Head")
                    return
                affix.remove()
            # --------------------------------------------------------------------------------#

            Result, Expanded_node = self.try_manipulate_bottom_node(node, affix, intervention_feature)
            if Result:
                return
            else:
                affix.remove()
                if phrase_structure == node:
                    phrase_structure = Expanded_node

            self.last_resort(phrase_structure, affix)

    def try_manipulate_bottom_node(self, node, affix, intervention_feature):
        expanded_node = node
        # Case 1. If the bottom node is complex, we try to reconstruct it first
        if node.has_affix():
            log(f'Try reconstruct {node} first...')
            self.reconstruct(node)
            expanded_node = node.mother

        if 'D' in expanded_node.head().features:
            expanded_node.merge_1(affix, 'right')

        else:
            node = node.top().bottom()
            if intervention_feature not in node.features and intervention_feature not in node.sister().features:
                node.merge_1(affix, 'right')  # Solution #1 [Z(_) ...[X [Y Affix]]]
            else:
                node.merge_1(affix, 'left')   # Solution #2 [Z(_) ...[X [Affix Y]]]
        if self.reconstruction_is_successful(affix):
            self.brain_model.consume_resources("Move Head")
            return True, expanded_node
        return False, expanded_node

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

    def determine_intervention_feature(self, head):
        if head.has_op_feature() and self.brain_model.narrow_semantics.is_concept(head):
            return 'φ'
        return '!COMP:*'

    def last_resort(self, phrase_structure, affix):
        log(f'Reconstruction of {affix} failed, use last resort...{phrase_structure}')
        phrase_structure.merge_1(affix, 'left')
        self.brain_model.consume_resources("Move Head")

    def reconstruct_to_sister(self, complex_head, affix):
        complex_head.merge_1(affix, 'right')                    # If X(Y) => [X Y]
        self.brain_model.consume_resources("Move Head")
        if affix.has_affix():                                   # If Y(Z) => reconstruct Y(Z)
            self.reconstruct(affix)

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
    def causes_intervention(node, feature, phrase_structure):
        if node != phrase_structure.minimal_search()[0] and feature in node.sister().features:
            return True