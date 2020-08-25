from support import set_logging, log, get_number_of_operations, reset_number_of_operations, log_result, illu
from LexicalInterface import LexicalInterface
import phrase_structure


class HeadMovement:
    def __init__(self, controlling_parser_process):
        self.controlling_parser_process = controlling_parser_process
        self.name_provider_index = 0
        self.memory_buffer = []

        # Access to the lexicon
        self.lexical_access = LexicalInterface(self.controlling_parser_process)
        self.lexical_access.load_lexicon(self.controlling_parser_process)

    # Higher-level function for head movement reconstruction
    def reconstruct(self, phrase_structure):

        # Alternative 1. Open a complex head into independent left branch
        if phrase_structure.is_complex_head():
            if 'D' in phrase_structure.features or 'P' in phrase_structure.features or 'A' in phrase_structure.features:
                if self.reconstruct_head_movement(phrase_structure.copy()).LF_legibility_test().all_pass():
                    new = self.reconstruct_head_movement(phrase_structure)
                    set_logging(True)
                    log(f'\t\t\t\t\t{phrase_structure} was opened into {new}.')
                    return new
                else:
                    set_logging(True)
                    log(f'\t\t\t\t\t{phrase_structure} was not opened into left branch, it would not constitute a legitimate left branch at LF.')
            # Note. If the conditions are not satisfies, nothing is done but the same head will be targeted later by Alternative 2.

        # Alternative 2. Reconstruct complex phrase
        else:
            if phrase_structure.is_complex():
                phrase_structure = self.reconstruct_head_movement(phrase_structure)

        return phrase_structure

     # Detect complex heads requiring reconstruction and reconstruct them
    def reconstruct_head_movement(self, phrase_structure):

        # ------------------ minimal search ----------------------------------------------#
        for node in phrase_structure:
            complex_head = self.detect_complex_head(node)
            if complex_head:
                log(f'\t\t\t\t\tReconstruct {complex_head.right_const} from within {complex_head}.')
                self.controlling_parser_process.number_of_head_Move += 1
                intervention_feature = self.determine_intervention_feature(complex_head)
                self.create_head_chain(complex_head, self.get_affix_out(complex_head), intervention_feature)
                log(f'\t\t\t\t\t={phrase_structure.top()}')
        #------------------------------------------------------------------------------------#
        return phrase_structure.top()

    @staticmethod
    # Detecting for complex head to be reconstructed
    def detect_complex_head(h):
        if h.is_primitive() and h.has_affix():
            return h
        elif h.left_const and h.left_const.is_primitive() and h.left_const.has_affix():
            return h.left_const

    # Definition for chain creation
    def create_head_chain(self, complex_head, affix, intervention_feature):

        # Special case when the complex head requiring reconstruction is bottom node
        if self.no_structure_for_reconstruction(complex_head):
            self.reconstruct_to_sister(complex_head, affix)         # X(Y) => [X Y]

        # Standard cases
        else:
            phrase_structure = complex_head.sister()       # Starting point for reconstruction
            current_node = complex_head.sister()

            # --------------- minimal search -----------------------------------------------#
            for node in phrase_structure:
                if self.causes_intervention(node, intervention_feature, phrase_structure):
                    self.local_head_reconstruction_as_last_resort(phrase_structure, affix)
                    return
                # Try solution
                node.merge_1(affix, 'left')
                if self.reconstruction_is_successful(affix):
                    return
                current_node = node
                affix.remove()
            # --------------------------------------------------------------------------------#

            # Reached bottom X, still no solution
            # Extract possible affixes first X(Y) => [X Y]
            if current_node.has_affix():
                log(f'\t\t\t\t\tMust reconstruct {current_node} first.')
                self.reconstruct_head_movement(current_node)

            # In the case [X Y] = [D N], create [DP H], H = affix.
            if 'D' in current_node.mother.head().features:
                current_node.mother.merge_1(affix, 'right')
            else:
                # [Z(H) [X Y]]
                current_node = current_node.top().bottom()  # Target Y
                if intervention_feature not in current_node.features and intervention_feature not in current_node.sister().features:
                    current_node.merge_1(affix, 'right')  # [Z(_) [X [Y H]]]
                else:
                    current_node.merge_1(affix, 'left')   # [Z(_) [X [H Y]]]

            if self.reconstruction_is_successful(affix):
                return      # Successful chain
            else:
                affix.remove()

            self.local_head_reconstruction_as_last_resort(phrase_structure, affix)
            return

    # Defines the conditions for dropping a head H into a position X
    def reconstruction_is_successful(self, affix):
        if not self.head_is_selected(affix):
            return False
        if not self.extra_condition(affix):
            return False
        return True

    def extra_condition(self, affix):
        if self.head_is_EPP_selected_by_C_fin(affix):
            if affix.local_edge():
                # Exception with Finnish third person forms (ultimate reason unknown)
                if 'pro' in affix.local_edge().features and 'PHI:PER:3' in affix.local_edge().features:
                    return False
                return True
            else:
                # Exception if [Affix, X], Affix finite EPP head and with X  primitive head
                if affix.sister() and affix.sister().terminal_node():
                    return True
        return True

    def get_affix_out(self, node):

        # Internal function
        # Returns the highest affix (if available)
        def highest_affix(h):
            if not h.left_const and h.is_primitive():
                return h.right_const
            else:
                return None

        # Main function
        affix = highest_affix(node)
        node.right_const = None  # Head reconstruction is not copying
        return affix

    def determine_intervention_feature(self, node):
        if node.has_op_feature():
            return 'D'
        else:
            return '!COMP:*'

    def local_head_reconstruction_as_last_resort(self, phrase_structure, affix):
        log(f'\t\t\t\t\tHead reconstruction of {affix} failed, merge locally as a last resort.')
        phrase_structure.merge_1(affix, 'left')
        return True

    def no_structure_for_reconstruction(self, complex_head):
        if not complex_head.sister() or complex_head.is_right():
            return True
        else:
            return False

    def reconstruct_to_sister(self, complex_head, affix):
        complex_head.merge_1(affix, 'right')  # If X(Y) => [X Y]
        if affix.has_affix():  # If Y(Z) => reconstruct Y(Z)
            self.reconstruct_head_movement(affix)

    @staticmethod
    def head_is_selected(affix):

        # Internal function
        def selects(h, selectee):
            if h.has_affix():
                selector = h.bottom_affix()
            else:
                selector = h
            return selectee.features & selector.licensed_complements()

        # Main function
        return affix.selector() and selects(affix.selector(), affix)

    def head_is_EPP_selected_by_C_fin(self, affix):
        if 'C/fin' in affix.selector().features and affix.EPP():
            return True

    @staticmethod
    # Definition for intervention
    def causes_intervention(h, feature, phrase_structure):
        if h != phrase_structure.minimal_search()[0]:                    # Ignore the first node
            if feature in h.sister().features:
                log(f'\t\t\t\t\tFeature {feature} causes HM intervention.')
                return True
            else:
                return False
