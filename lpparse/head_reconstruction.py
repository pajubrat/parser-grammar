from support import set_logging, log, get_number_of_operations, reset_number_of_operations, log_result, illu
from lexical_interface import LexicalInterface

class HeadMovement:
    def __init__(self, controlling_parser_process):
        self.controlling_parser_process = controlling_parser_process
        self.name_provider_index = 0
        self.memory_buffer = []
        self.lexical_access = LexicalInterface(self.controlling_parser_process)
        self.lexical_access.load_lexicon(self.controlling_parser_process)

    # Definition for head reconstruction
    def reconstruct(self, ps):
        """
        Reconstructs all complex heads from phrase structure structure [ps].

        A complex head is by definition a constituent that contains a right constituent and no left constituent.
        This version separates two situations:
        (1) [ps] is a complex phrase structure, in which case all complex heads are reconstructed from
        its right edge after being detected by minimal search.
        (2) [ps] is a complex head itself which can generate a legitimate left branch all by itself,
        in which case it will be reconstructed into the left branch. Example: D(N) => [D N]

        Literature: Brattico (submitted). Predicate clefting and long head movement in Finnish.
        """
        if ps.is_complex():
            return self.reconstruct_head_movement(ps)
        if ps.is_complex_head() and self.left_branch_constituent(ps) and \
                self.controlling_parser_process.LF_legibility_test(self.reconstruct_head_movement(ps.copy())):
                    return self.reconstruct_head_movement(ps)
        return ps

    def left_branch_constituent(self, ps):
        """
        Defines the notion of left branch constituent for head movement by enumeration,
        contains DP, PP, AP and D/relP.
        """
        return {'D', 'P', 'A', 'D/rel'} & ps.features

    def LF_legible(self, ps):
        """
        Tests whether phrase structure [ps] passes LF-legibility.

        This function verifies that head reconstruction of some constituent can generate a structure
        that can pass all LF-legibility tests. This is a precondition for its being a left branch.
        """
        return self.controlling_parser_process.LF_legibility_test(ps.copy())

     # Detect complex heads requiring reconstruction and reconstructs them
    def reconstruct_head_movement(self, phrase_structure):
        """
        Reconstructs all head movement from phrase structure [ps]

        Performs minimal search on the right edge of the phrase structure and detects complex left heads.
        Once detected, the head is reconstructed. Once reconstructed, the algorithm continues the process
        from where it left. Minimal search is terminated by intervention feature that is determined by
        the type of the head, which is used to explain why C-heads tolerate long distance reconstruction
        while A-heads do not.

        Literature: Brattico, P. (submitted). Predicate clefting and long head movement in Finnish.
        """
        # ------------------ minimal search ----------------------------------------------#
        for node in phrase_structure:
            if self.detect_complex_head(node):
                complex_head = self.detect_complex_head(node)
                log(f'Reconstruct {complex_head.right_const} from within {complex_head}...')
                intervention_feature = self.determine_intervention_feature(complex_head)
                self.create_head_chain(complex_head, self.get_affix_out(complex_head), intervention_feature)
                log(f'={phrase_structure.top()}...')
        #------------------------------------------------------------------------------------#
        return phrase_structure.top()

    @staticmethod
    def detect_complex_head(h):
        """
        Detecting whether node h contains a complex head.

        X is a complex head if and only if it is primitive and has an affix. H "contains" such head
        if and only if H = X or H contains X has a left constituent. This defines the conditions for
        triggering head reconstruction for X.
        """
        if h.left_const and h.left_const.is_primitive() and h.left_const.has_affix():
            return h.left_const
        if h.is_primitive() and h.has_affix():
            return h

    # Definition for chain creation
    # Complex head = original head
    # Affix = affix that was extracted out
    def create_head_chain(self, complex_head, affix, intervention_feature):
        """
        Creates a head reconstruction chain for one complex head [complex_head] H.

        If H has no sister XP that reconstruction could use as a target, then H will be
        reconstructed into its own sister, H(X) = [H X]. Else a minimal search is called for
        the right edge of its sister XP. If minimal search encounter intervention feature,
        it will trigger last resort reconstruction.
        """
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
                    self.controlling_parser_process.consume_resources("Move Head")
                    return
                affix.remove()
            # --------------------------------------------------------------------------------#
            # Still no solution
            if self.try_manipulate_bottom_node(node, affix, intervention_feature):
                return
            else:
                affix.remove()
            self.last_resort(phrase_structure, affix)

    def try_manipulate_bottom_node(self, node, affix, intervention_feature):

        # Case 1. If the bottom node is complex, it must first be reconstructed
        if node.has_affix():
            log(f'Must reconstruct {node} first...')
            self.reconstruct_head_movement(node)

        # Case 2. If the bottom head is DP, we try to make it a specifier of affix
        if 'D' in node.mother.head().features:
            node.mother.merge_1(affix, 'right')

        # Case 3. For all other labels, we try the solutions #1 and #2 below
        else:
            node = node.top().bottom()
            if intervention_feature not in node.features and intervention_feature not in node.sister().features:
                node.merge_1(affix, 'right')  # Solution #1 [Z(_) [X [Y H]]]
            else:
                node.merge_1(affix, 'left')   # Solution #2 [Z(_) [X [H Y]]]
        if self.reconstruction_is_successful(affix):
            self.controlling_parser_process.consume_resources("Move Head")
            return True

    # Defines conditions for dropping a head H into a position X
    def reconstruction_is_successful(self, affix):
        if not self.head_is_selected(affix):
            return False
        if not self.extra_condition(affix):
            return False
        return True

    def extra_condition(self, affix):
        if self.head_is_EPP_selected_by_C_fin(self, affix):
            if affix.local_edge():
                # Exception 1. Finnish third person forms (ultimate reason unknown)
                if 'pro' in affix.local_edge().features and 'PHI:PER:3' in affix.local_edge().features:
                    return False
                return True
            else:
                # Exception 2. The the structure is [Affix, X], Affix finite EPP head and with X  primitive head
                if affix.sister() and affix.sister().terminal_node():
                    return True
                else:
                    return False
        return True

    def get_affix_out(self, node):
        if node.is_complex_head():
            affix = node.right_const
            node.right_const = None                  # Head reconstruction is not copying
            return affix
        else:
            return node

    @staticmethod
    def determine_intervention_feature(node):
        if node.has_op_feature():
            return 'D'
        return '!COMP:*'

    def last_resort(self, phrase_structure, affix):
        log(f'Head reconstruction of {affix} failed, merge locally as a last resort...')
        phrase_structure.merge_1(affix, 'left')
        self.controlling_parser_process.consume_resources("Move Head")

    def reconstruct_to_sister(self, complex_head, affix):
        complex_head.merge_1(affix, 'right')                    # If X(Y) => [X Y]
        self.controlling_parser_process.consume_resources("Move Head")
        if affix.has_affix():                                   # If Y(Z) => reconstruct Y(Z)
            self.reconstruct_head_movement(affix)

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
    def head_is_EPP_selected_by_C_fin(self, affix):
        return 'C/fin' in affix.selector().features and affix.EPP()

    @staticmethod
    def causes_intervention(node, feature, phrase_structure):
        if node != phrase_structure.minimal_search()[0] and feature in node.sister().features:
            return True