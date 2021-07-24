from support import set_logging, log, get_number_of_operations, reset_number_of_operations, log_result, illu
from lexical_interface import LexicalInterface

#
# This class implements the head reconstruction algorithm proposed in
# Brattico (to appear). Predicate clefting and long head movement in Finnish. Linguistic Inquiry.
# I will refer to this paper in the comments below.
#

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
        its right edge after being detected by minimal search (Rule 43A in the article).
        (2) [ps] is a complex head itself which can generate a legitimate left branch all by itself,
        in which case it will be reconstructed into the left branch. Example: D(N) => [D N]
        (discussed in §4.3)
        """
        # If the target phrase structure is complex, reconstruct all complex heads inside it
        if ps.is_complex():
            return self.reconstruct_head_movement(ps)
        # If the argue is a complex head, we have to considerate generating left branch (§4.3)
        if ps.is_complex_head() and self.left_branch_constituent(ps) and \
                self.controlling_parser_process.LF_legibility_test(self.reconstruct_head_movement(ps.copy())):
                    return self.reconstruct_head_movement(ps)
        return ps

    def left_branch_constituent(self, ps):
        """
        Defines the notion of left branch constituent for head movement by enumeration,
        contains DP, PP, AP and D/relP. Discussed in §4.3. This is the extra "parsing intelligence"
        that we have to give to the head reconstruction algorithm
        """
        return {'φ', 'D', 'P', 'A', 'D/rel'} & ps.features

    def LF_legible(self, ps):
        """
        Tests whether phrase structure [ps] passes LF-legibility.

        This function verifies that head reconstruction of some constituent can generate a structure
        that can pass all LF-legibility tests. This is a precondition for its being a left branch. Uses
        the general LF legibility test that is defined in the linear phase parser class.
        """
        return self.controlling_parser_process.LF_legibility_test(ps.copy())

    def reconstruct_head_movement(self, phrase_structure):
        """
        Reconstructs all head movement from phrase structure [ps]

        Performs minimal search on the right edge of the phrase structure and detects complex left heads.
        Once detected, the head is reconstructed. Once reconstructed, the algorithm continues the process
        from where it left. Minimal search is terminated by intervention feature that is determined by
        the type of the head, which is used to explain why C-heads tolerate long distance reconstruction
        while A-heads do not. This implements rules (43A-B).
        """
        # ------------------ minimal search ----------------------------------------------#
        for node in phrase_structure:
            if self.detect_complex_head(node):
                complex_head = self.detect_complex_head(node)
                log(f'Reconstruct {complex_head.right_const} from within {complex_head}...')
                intervention_feature = self.determine_intervention_feature(complex_head)
                # Inverse head chain is created here (Rule 43A-B)
                self.create_head_chain(complex_head, self.get_affix_out(complex_head), intervention_feature)
                log(f'={phrase_structure.top()}...')
        #------------------------------------------------------------------------------------#
        return phrase_structure.top()

    @staticmethod
    def detect_complex_head(h):
        """
        Detecting whether node h contains a complex head.

        X is a complex head if and only if it is primitive and has an affix. H "contains" such head
        if and only if H = X or H contains X as a right constituent. This defines the conditions for
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
        it will trigger the last resort reconstruction. If it is allowed to continue, it will
        try to merge the reconstructed affix into this position and, if the operation succeeds,
        the affix will remain at that position. If the operation does not succeed, the affix
        will be removed and the procedure continues. If it reaches the end of the structure,
        one more solution will be attempted and, if that does not work, then last resort.
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
            # Result: True = successful, False = unsuccessful
            # Expanded_node: when D(N) is expanded, we need to target [D N] = Expanded node next, not D.
            Result, Expanded_node = self.try_manipulate_bottom_node(node, affix, intervention_feature)
            if Result:
                return  # The result is legible, leave it and return
            else:
                affix.remove()  # The result still fails, we go for last resort with the expanded node
                if phrase_structure == node:
                    phrase_structure = Expanded_node

            self.last_resort(phrase_structure, affix)

    def try_manipulate_bottom_node(self, node, affix, intervention_feature):
        """
        This function handles the edge case when the complex head is the bottom right node.
        It should be incorporated into the main algorithm at some point, which means that
        the algorithm cannot be exactly correct as it stands.
        """
        expanded_node = node
        # Case 1. If the bottom node is complex, we try to reconstruct it first
        if node.has_affix():
            log(f'Try reconstruct {node} first...')
            self.reconstruct_head_movement(node)
            expanded_node = node.mother

        # Case 2. If the bottom head is DP, we try to make it a specifier of affix
        if 'D' in expanded_node.head().features:
            expanded_node.merge_1(affix, 'right')
        # Case 3. For all other labels, we try solutions #1 and #2 below. The intuitive idea is that solution
        # [X Affix], X = bottom node, is usually adopted with the exception that if X has an intervention
        # feature, then the solution honors intervention and is [Affix X] instead. Affix = reconstructing affix.
        else:
            node = node.top().bottom()
            if intervention_feature not in node.features and intervention_feature not in node.sister().features:
                node.merge_1(affix, 'right')  # Solution #1 [Z(_) ...[X [Y Affix]]]
            else:
                node.merge_1(affix, 'left')   # Solution #2 [Z(_) ...[X [Affix Y]]]
        if self.reconstruction_is_successful(affix):
            self.controlling_parser_process.consume_resources("Move Head")
            return True, expanded_node
        return False, expanded_node

    def reconstruction_is_successful(self, affix):
        """
        Defines the condition under which a reconstructed head can remain at position X.

        There are two ways to satisfy this condition. One is if the head is elected by a local head.
        This is the default and intuitively obvious requirement. Another is the extra condition that
        takes care of one edge case and which must be assimilated later.
        """
        if not self.head_is_selected(affix):    # Default behavior
            return False
        if not self.extra_condition(affix):     # One edge case
            return False
        return True

    def extra_condition(self, affix):
        """
        Takes care of an edge cass that have to do with reconstruction of an EPP head.

        If the reconstructed head is an EPP head selected by finite C, then head reconstruction must
        eat the EPP specifier argument. In other words, instead of mapping 'C(T) John' into 'C-T-John',
        we map it into 'C-John-T' and thus check the presence of the argument at SPEC.

        The algorithm allows for two exception to the general rule.
        (1) Finnish third person pro is not strong enough to count as a subject (Vainikka & Levy observation).
        (2) No lower structure exist into which reconstruct the EPP head (true edge case)

        Note. It is obvious that something else is going on here. The edge cases correspond to 'added intelligence'
        that we must ultimately generalize everywhere or the problems must be solved by some other means.
        """
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
        """
        Extracts an affix from a complex head.

        The operation does not use copying, by extracts the affix literally from the complex head,
        leaving nothing inside. The complex head then becomes a terminal node.
        """
        if node.is_complex_head():
            affix = node.right_const
            node.right_const = None     # Head reconstruction is not copying
            return affix
        else:
            return node

    @staticmethod
    def determine_intervention_feature(node):
        """
        Determines the nature of the intervention feature on the basis of the nature of the reconstructed node.

        There are two cases. Case 1: the node has an operator (C*) feature, in which case the intervention feature
        will be [D]. Case 2: else the intervention feature will be [!COMP:*].
        """
        if node.has_op_feature():
            return 'φ'
        return '!COMP:*'

    def last_resort(self, phrase_structure, affix):
        """
        Last resort solution which merges the reconstructed head locally.
        """
        log(f'Reconstruction of {affix} failed, use last resort...{phrase_structure}')
        phrase_structure.merge_1(affix, 'left')
        self.controlling_parser_process.consume_resources("Move Head")

    def reconstruct_to_sister(self, complex_head, affix):
        """
        Special condition that applies if we are targeting the bottom right node.
        """
        complex_head.merge_1(affix, 'right')                    # If X(Y) => [X Y]
        self.controlling_parser_process.consume_resources("Move Head")
        if affix.has_affix():                                   # If Y(Z) => reconstruct Y(Z)
            self.reconstruct_head_movement(affix)

    @staticmethod
    def no_structure_for_reconstruction(complex_head):
        """
        Defines the situation in which there is no structure into which reconstruct the head.
        """
        if not complex_head.sister() or complex_head.is_right():
            return True

    @staticmethod
    def head_is_selected(affix):
        """
        Returns [True] if and only if the head H is selected in the position it occurs in the phrase structure.

        The function works by locating the local selector and checking if it selects for H by means of
        lexical COMP features. If the selector is missing or it cannot select for H, the function returns
        [False].
        """
        def selects(h, selectee):
            if h.has_affix():
                selector = h.bottom_affix()
            else:
                selector = h
            return selectee.features & selector.licensed_complements()
        return affix.selector() and selects(affix.selector(), affix)

    @staticmethod
    def head_is_EPP_selected_by_C_fin(affix):
        """
        Defines if the head is selected by C/fin and has the EPP property.
        """
        return 'C/fin' in affix.selector().features and affix.EPP()

    @staticmethod
    def causes_intervention(node, feature, phrase_structure):
        """
        Checks if [node] causes intervention by feature [feature].

        The intervention occurs if and only if (i) we are not at the starting point,
        (ii) the sister of [node] has [feature].

        Condition (i) is motivated by the fact that in most cases the relevant intervention feature is
        present at the starting point, but we want to ignore it. Condition (ii) is motivated by the fact
        that intervention is caused by primitive sister of node, e.g. H in [H node] causes potential
        intervention. [Node] is then not penetrated.
        """
        if node != phrase_structure.minimal_search()[0] and feature in node.sister().features:
            return True