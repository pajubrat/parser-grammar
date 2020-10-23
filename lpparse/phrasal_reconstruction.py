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
        self.controlling_parser_process.syntactic_working_memory = []
        # ------------------------------ minimal search -----------------------------------------------#
        for node in ps.minimal_search():
            if self.visible_head(node):
                self.pull(self.visible_head(node))
                if self.visible_head(node):
                    self.controlling_parser_process.LF.try_LFmerge(self.visible_head(node))
            if self.intervention(node):
                break
        # ---------------------------------------------------------------------------------------------#

    def intervention(self, node):
        if node.left_const and node.left_const.is_primitive() and 'D' in node.left_const.features:
            if self.controlling_parser_process.syntactic_working_memory:
                return True
        return False

    def pull(self, head):
        if head.EPP():
            specifiers_to_add_memory_buffer = []
            iterator = head.get_specifier_sister()
            count_specifiers = 0
            # ------------------------ upstream walk------------------------------------------------ #
            while iterator and self.get_phrasal_left_sister(iterator):
                spec = self.get_phrasal_left_sister(iterator)
                if not spec.find_me_elsewhere:
                    if self.Abar_movable(spec):
                        specifiers_to_add_memory_buffer.append(spec)
                        log(f'Moving {spec} into memory buffer from Spec{head.get_cats_string()}P...')
                    else:
                        iterator = self.A_reconstruct_(spec, iterator)

                if count_specifiers > 0:

                    if self.specifier_phrase_must_have_supporting_head(spec):
                        new_h = self.engineer_head_from_specifier(head, spec)
                        iterator.merge_1(new_h, 'left')
                        iterator = iterator.mother # Prevents looping over the same Spec element
                        log(f'New head was spawned at {head.get_cats_string()}P...')
                        if new_h.get_tail_sets():
                            self.adjunct_constructor.create_adjunct(new_h)
                else:

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
        new_h = self.lexical_access.PhraseStructure()
        new_h.features |= self.get_features_for_criterial_head(head, spec)
        if 'FIN' in head.features:
            new_h.features |= {'C', 'PF:C'}
        return new_h

    def get_features_for_criterial_head(self, head, spec):
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
        if ps == ps.container_head().licensed_specifier():
            return 'D' in ps.head().features and ps.sister() and ps.is_left() and not ps.is_primitive()

    # THis is the new generalized A-reconstruction
    # I leave extensive comments because the theory is not optimal
    def A_reconstruct_(self, spec, iterator):
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
                if (node.left_const and node.left_const.is_primitive() and node.sister().is_primitive()) or node.is_primitive():
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
        if h.is_primitive():
            return h
        if h.left_const.is_primitive():
            return h.left_const

    @staticmethod
    # Definition for constituent that can implement A-bar move
    def Abar_movable(h):
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