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
        for node in phrase_structure:
            complex_head = node.detect('complex head')
            if complex_head:
                log(f'\t\t\t\t\tTarget \'{complex_head.get_affix()}\' inside complex head {complex_head} for head reconstruction.')
                self.controlling_parser_process.number_of_head_Move += 1
                intervention_feature = self.determine_intervention_feature(complex_head)
                self.create_head_chain(complex_head, self.get_affix_out(complex_head), intervention_feature)
                log(f'\t\t\t\t\t={phrase_structure.top()}')
        return phrase_structure.top()

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
            for node in phrase_structure.minimal_search():
                if node.causes_intervention(intervention_feature, phrase_structure):
                    self.local_head_reconstruction_as_last_resort(phrase_structure, affix)
                    return
                # Try solution
                node.merge(affix, 'left')
                if self.reconstruction_is_successful(affix):
                    return       # Accept solution
                current_node = node
                affix.remove()
            # --------------------------------------------------------------------------------#

            # Reached bottom X, still no solution
            # Extract possible affixes first X(Y) => [X Y]
            if current_node.has_affix():
                log(f'\t\t\t\t\tMust reconstruct {current_node} first.')
                self.reconstruct_head_movement(current_node)

            # In the case of D(N), => [DP H]
            if 'D' in current_node.mother.head().features:
                current_node.mother.merge(affix, 'right')
            else:
                # [X Y] => [X [Y H]]
                current_node = current_node.mother.bottom()  # Target Y
                if intervention_feature not in current_node.features and intervention_feature not in current_node.sister().features:
                    current_node.merge(affix, 'right')  # [X [Y H]]
                else:
                    current_node.merge(affix, 'left')   # [X [H Y]]

            if self.reconstruction_is_successful(affix):
                return      # Successful chain
            else:
                affix.remove()

            self.local_head_reconstruction_as_last_resort(phrase_structure, affix)
            return

    # Defines the conditions for dropping a head H into a position X
    # Condition 1. H is selected by a higher head in position X and H does not require SPEC, or
    # Condition 2. If it does require SPEC, then H has suitable edge/specifier at the position, with three exceptions:
    #   Exception A to 2. Finnish third person exception
    #   Exception B to 2. [affix, b], b is primitive
    def reconstruction_is_successful(self, affix):

        # Head gap must be selected
        if not self.head_is_selected(affix):
            return False
        else:
            # Only finite EPP heads selected by C/fin cause special, because their EPP cannot be satisfied by future operation
            if not self.head_is_EPP_selected_by_C_fin(affix):
                return True
            else:
                if affix.local_edge():
                    # Exception with Finnish third person forms (ultimate reason unknown)
                    if 'pro' in affix.local_edge().features and 'PHI:PER:3' in affix.local_edge().features:
                        return False
                    return True
                else:
                    # Exception if [Affix, X], Affix finite EPP head and with X  primitive head
                    if affix.sister() and affix.sister().is_primitive_head():
                        return True
        return False

    def get_affix_out(self, node):
        affix = node.get_affix()
        node.right_const = None  # Head reconstruction is not copying
        return affix

    def determine_intervention_feature(self, node):
        if node.has_op_feature():
            return 'D'
        else:
            return '!COMP:*'

    def local_head_reconstruction_as_last_resort(self, phrase_structure, affix):
        log(f'\t\t\t\t\tHead reconstruction of {affix} failed, merge locally as a last resort.')
        phrase_structure.merge(affix, 'left')
        return True

    def no_structure_for_reconstruction(self, complex_head):
        if not complex_head.sister() or complex_head.is_right():
            return True
        else:
            return False

    def reconstruct_to_sister(self, complex_head, affix):
        complex_head.merge(affix, 'right')  # If X(Y) => [X Y]
        if affix.has_affix():  # If Y(Z) => reconstruct Y(Z)
            self.reconstruct_head_movement(affix)

    def head_is_selected(self, affix):
        if affix.selector() and affix.selector().selects(affix):
            return True

    def head_is_EPP_selected_by_C_fin(self, affix):
        if 'C/fin' in affix.selector().features and affix.EPP():
            return True

