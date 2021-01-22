from support import log
from lexical_interface import LexicalInterface
from adjunct_constructor import AdjunctConstructor
from LF import LF

class PhrasalMovement:
    def __init__(self, controlling_parser_process):
        self.controlling_parser_process = controlling_parser_process
        self.controlling_parser_process.name_provider_index = 1
        self.controlling_parser_process.syntactic_working_memory = []
        self.context = controlling_parser_process
        self.lexical_access = LexicalInterface(self.controlling_parser_process)
        self.lexical_access.load_lexicon(self.controlling_parser_process)
        self.adjunct_constructor = AdjunctConstructor(self.controlling_parser_process)

    # Definition for A/A'-movement reconstruction
    def reconstruct(self, ps):
        """
        Reconstructs phrasal A-bar and A-movement.

        A-reconstruction is triggered if the moved phrase does not have criterial operator features.
        A-bar operator reconstruction is triggered if there is a criterial operator feature.

        Literature. Brattico & Chesi (2020).
        """
        self.controlling_parser_process.syntactic_working_memory = []
        # ------------------------------ minimal search -----------------------------------------------#
        for node in ps.minimal_search():
            if self.visible_head(node):
                self.pull_into_working_memory(self.visible_head(node))
                if self.visible_head(node):
                    self.controlling_parser_process.LF.try_LFmerge(self.visible_head(node))
            if self.intervention(node):
                break
        # ---------------------------------------------------------------------------------------------#

    def intervention(self, node):
        """
        Defines the set of nodes/features that cause intervention for A-bar reconstruction.

        The set of enumerative and stipulative. This matter remains to be studied.
        """
        if node.left_const and node.left_const.is_primitive() and 'D' in node.left_const.features:
            if self.controlling_parser_process.syntactic_working_memory:
                return True
        return False

    def pull_into_working_memory(self, head):
        """
        Pulls constituents into working memory if they occur in a nonthematic position inside some head H.

        A nonthematic head is defined by the property EPP. All phrasal specifiers must be considered, which
        constitute a large part of the nontriviality of this mechanism. The function considers that
        if a local head exists, criterial features are simply copied, as in Who did John admire, where [wh] is copied
        into T/fin. If we are looking at a second or third (etc) specifier, then we have to generate the head before
        criterial features are copied.
        """
        if head.EPP():
            specifiers_to_add_memory_buffer = []
            iterator = head.get_specifier_sister()
            count_specifiers = 0
            # ------------------------ upstream walk------------------------------------------------ #
            while iterator and self.get_phrasal_left_sister(iterator):  # Examine all specifiers
                spec = self.get_phrasal_left_sister(iterator)           # Obtain a handle to the specifier phrase
                if not spec.find_me_elsewhere:                          # React to it if it has not been moved already
                    if self.Abar_movable(spec):                         # Determine if the sister is operator phrase
                        specifiers_to_add_memory_buffer.append(spec)
                        log(f'Moving {spec} into memory buffer from Spec{head.get_cats_string()}P...')
                    else:
                        iterator = self.A_reconstruct_(spec, iterator)  # A-reconstruction is applied if there are no cr-features

                if count_specifiers > 0:    # This handles the case if we are finding the second or more specifiers.
                    # If there are several operator specifiers, then we need to project a supporting phonologically null head
                    if self.specifier_phrase_must_have_supporting_head(spec):
                        new_h = self.engineer_head_from_specifier(head, spec)
                        iterator.merge_1(new_h, 'left')
                        iterator = iterator.mother # Prevents looping over the same Spec element
                        log(f'New head was spawned at {head.get_cats_string()}P...')
                        if new_h.get_tail_sets():
                            self.adjunct_constructor.create_adjunct(new_h)
                else:
                   # We are working with a local specifier, no need to project extra heads
                    count_specifiers = + 1
                    if spec.scan_criterial_features():
                        log(f'Criterial features {spec.scan_criterial_features()} copied to {head}...')
                        head.features |= self.get_features_for_criterial_head(head, spec)
                        if head.get_tail_sets():
                            self.adjunct_constructor.create_adjunct(head)
                iterator = iterator.walk_upstream()

            # --------------------------------------------------------------------------------------------------#
            # Add everything into memory buffer
            self.controlling_parser_process.syntactic_working_memory = specifiers_to_add_memory_buffer + self.controlling_parser_process.syntactic_working_memory

    # Definition for generating a new head
    def engineer_head_from_specifier(self, head, spec):
        """
        Generates a new head based on criterial features.

        It is assumed that a head that is phonologically null can occur if its features are marked on the
        phrase at its specifier.
        """
        new_h = self.lexical_access.PhraseStructure()
        new_h.features |= self.get_features_for_criterial_head(head, spec)
        if 'FIN' in head.features:
            new_h.features |= {'C', 'PF:C'}
        return new_h

    def get_features_for_criterial_head(self, head, spec):
        """
        Copied criterial features from a constituent. A criterial feature is one beginning with pattern [op:].
        They are features that can be understood by the operator system.
        """
        criterial_features = spec.scan_criterial_features()
        if criterial_features:
            feature_set = {'OP:_'}
            if 'FIN' in head.features:
                feature_set |= {'OP', 'FIN'}
                feature_set |= {'FORCE:' + criterial_feature for criterial_feature in criterial_features}
            return self.lexical_access.apply_parameters(self.lexical_access.apply_redundancy_rules(feature_set))
        else:
            return {'?'}

    def candidate_for_A_reconstruction(self, ps):
        """
        A constituent is not a candidate for A-reconstruction if it is not a licensed specifier. If it is,
        then it must also be a left DP (right DPs, such as 'whole day', are not A-reconstructed). A licensed specifier
        is in essence the local "prioritized" constituent that it targeted by the head for selection and thematic role assignments.
        """
        if ps == ps.container_head().licensed_specifier():
            return 'D' in ps.head().features and ps.sister() and ps.is_left() and not ps.is_primitive()

    # THis is the new generalized A-reconstruction
    # I leave extensive comments because the theory is not optimal
    def A_reconstruct_(self, spec, iterator):
        """
        Implements local A-reconstruction.
        """

        # Left DPs that are licensed specifiers can be A-reconstructed
        if not self.candidate_for_A_reconstruction(spec):
            return iterator

        # Special case: [DP H] => [__ [H DP]]
        if iterator.is_primitive():
            iterator.merge_1(spec.copy_from_memory_buffer(self.controlling_parser_process.babtize()), 'right')
            return iterator.mother

        moved_constituent = spec.copy()
        #-----------------minimal search---------------------------------------------------------------------------#
        for node in iterator.minimal_search():
            # Condition 1. No trivial merge [XP [H YP]] => [XP [H YP]]
            if node != iterator:
                # Condition 2. No tucking if there is already something, [XP K [YP [H ZP]] =/=> [XP K [__ YP [H ZP]]]
                if (node.left_const
                    and node.left_const.is_primitive()
                    and node.sister().is_primitive()) \
                        or node.is_primitive():
                    node.merge_1(moved_constituent, 'left')
                    # Condition 3. Genitives must satisfy additional tail-head test (try remove later)
                    if 'GEN' in moved_constituent.head().features and not moved_constituent.external_tail_head_test():
                        moved_constituent.remove()
                    else:
                        moved_constituent.remove()
                        node.merge_1(spec.copy_from_memory_buffer(self.controlling_parser_process.babtize()), 'left')
                        break
        #-----------------------------------------------------------------------------------------------------------#
        return iterator


    @staticmethod
    def visible_head(h):
        """
        Primitive heads are and primitive heads to the left are visible for node
        """
        if h.is_primitive():
            return h
        if h.left_const.is_primitive():
            return h.left_const

    @staticmethod
    # Definition for constituent that can implement A-bar move
    def Abar_movable(h):
        """
        A phrase is A-bar movable (understood by the operator system) if and only if it is marked
        by an operator feature or is an A-infinitival. The latter condition is obviously a stipulation and
        is made on the basis of Finnish VP-fronting data.
        """
        return h.scan_criterial_features() or \
               'A/inf' in h.head().features

    @staticmethod
    # Definition for phrase that requires a local licensing head (used in connection with A-bar head generation)
    def specifier_phrase_must_have_supporting_head(h):
        # Criterial feature represents a licensing head that must be present
        if h.scan_criterial_features():
            return True
        # Adjuncts do not need licensing heads
        if h.max().externalized():
            return False
        # Bare non-adjunct DPs that are not licensed by the containing head need support
        if h.max() != h.max().container_head().licensed_specifier():
            return True

    @staticmethod
    def get_phrasal_left_sister(h):
        if h.sister() and not h.sister().is_primitive() and h.sister().is_left():
            return h.sister()