from support import log
from lexical_interface import LexicalInterface
from adjunct_constructor import AdjunctConstructor

class PhrasalMovement:
    def __init__(self, controlling_parser_process):
        self.brain_model = controlling_parser_process
        self.brain_model.name_provider_index = 1
        self.brain_model.syntactic_working_memory = []
        self.context = controlling_parser_process
        self.lexical_access = LexicalInterface(self.brain_model)
        self.lexical_access.load_lexicon(self.brain_model)
        self.adjunct_constructor = AdjunctConstructor(self.brain_model)

    def reconstruct(self, ps):
        self.brain_model.syntactic_working_memory = []
        # ------------------------------ minimal search -----------------------------------------------#
        for node in ps.minimal_search():
            if self.visible_head(node):
                self.pull_into_working_memory(self.visible_head(node))
                if self.visible_head(node):
                    self.brain_model.LF.try_LFmerge(self.visible_head(node))
            if self.intervention(node):
                break
        # ---------------------------------------------------------------------------------------------#

    def intervention(self, node):
        if node.left_const and node.left_const.is_primitive() and 'D' in node.left_const.features:
            if self.brain_model.syntactic_working_memory:
                return True
        return False

    def pull_into_working_memory(self, head):

        def walk_upstream(node):
            while node.mother:
                node = node.mother
                if node.right_const.visible():
                    return node

        if head.EPP():
            specifiers_to_add_memory_buffer = []
            iterator = head.specifier_sister()
            count_specifiers = 0
            # ------------------------ upstream walk------------------------------------------------ #
            while iterator and self.get_phrasal_left_sister(iterator):  # Examine all specifiers
                spec = self.get_phrasal_left_sister(iterator)           # Obtain a handle to the specifier phrase
                if not spec.find_me_elsewhere:                          # React to it if it has not been moved already
                    if self.Abar_movable(spec):                         # Determine if the sister is operator phrase
                        specifiers_to_add_memory_buffer.append(spec)
                        log(f'Moving {spec} into memory buffer from Spec{head.get_cats_string()}P...')
                    else:
                        iterator = self.A_reconstruct(spec, iterator)  # A-reconstruction is applied if there are no cr-features

                if count_specifiers > 0:    # This handles the case if we are finding the second or more specifiers.
                    # If there are several operator specifiers, then we need to project a supporting phonologically null head
                    if self.specifier_phrase_must_have_supporting_head(spec):
                        new_h = self.engineer_head_from_specifier(head, spec)
                        iterator.merge_1(new_h, 'left')
                        iterator = iterator.mother # Prevents looping over the same Spec element
                        log(f'New head was spawned at {head.get_cats_string()}P...')
                        if new_h.get_tail_sets():
                            self.adjunct_constructor.externalize_structure(new_h)
                else:
                   # We are working with a local specifier, no need to project extra heads
                    count_specifiers = + 1
                    if self.brain_model.narrow_semantics.operator_variable_module.scan_criterial_features(spec):
                        log(f'Criterial features copied to {head}...')
                        head.features |= self.get_features_for_criterial_head(spec)
                        if head.get_tail_sets():
                            self.adjunct_constructor.externalize_structure(head)
                iterator = walk_upstream(iterator)

            # --------------------------------------------------------------------------------------------------#
            self.brain_model.syntactic_working_memory = specifiers_to_add_memory_buffer + self.brain_model.syntactic_working_memory

    def engineer_head_from_specifier(self, head, spec):
        new_h = self.lexical_access.PhraseStructure()
        new_h.features |= self.get_features_for_criterial_head(spec)
        if 'FIN' in head.features:
            new_h.features |= {'C', 'PF:C'}
        return new_h

    def get_features_for_criterial_head(self, spec):
        criterial_features = self.brain_model.narrow_semantics.operator_variable_module.scan_criterial_features(spec)
        if criterial_features:
            feature_set = criterial_features
            feature_set |= {'FIN', 'OP:_'}
            return self.lexical_access.apply_parameters(self.lexical_access.apply_redundancy_rules(feature_set))
        else:
            return {'?'}

    def candidate_for_A_reconstruction(self, ps):
        if ps == ps.container_head().licensed_phrasal_specifier():
            return {'φ'} & ps.head().features and ps.sister() and ps.is_left() and not ps.is_primitive()

    def A_reconstruct(self, spec, iterator):

        # Left DPs that are licensed specifiers can be A-reconstructed
        if not self.candidate_for_A_reconstruction(spec):
            return iterator

        # Special case: [DP H] => [__ [H DP]]
        if iterator.is_primitive():
            iterator.merge_1(spec.copy_from_memory_buffer(self.brain_model.babtize()), 'right')
            return iterator.mother

        moved_constituent = spec.copy()
        #-----------------minimal search---------------------------------------------------------------------------#
        for node in iterator.minimal_search():
            if node != iterator:
                if (node.left_const and node.left_const.is_primitive() and node.sister().is_primitive()) or node.is_primitive():
                    node.merge_1(moved_constituent, 'left')
                    # This genitive rule is ad hoc
                    if 'GEN' in moved_constituent.head().features and not moved_constituent.external_tail_head_test():
                        moved_constituent.remove()
                    else:
                        moved_constituent.remove()
                        node.merge_1(spec.copy_from_memory_buffer(self.brain_model.babtize()), 'left')
                        self.brain_model.consume_resources('A-Move Phrase')
                        self.brain_model.consume_resources('Move Phrase')
                        break
        #-----------------------------------------------------------------------------------------------------------#
        return iterator


    @staticmethod
    def visible_head(h):
        if h.is_primitive():
            return h
        if h.left_const.is_primitive():
            return h.left_const

    def Abar_movable(self, h):
        if self.brain_model.narrow_semantics.operator_variable_module.scan_criterial_features(h):
            return True
        if 'A/inf' in h.head().features:
            return True


    def specifier_phrase_must_have_supporting_head(self, h):
        if self.brain_model.narrow_semantics.operator_variable_module.scan_criterial_features(h):
            return True
        if h.max().externalized():
            return False
        if h.max() != h.max().container_head().licensed_phrasal_specifier():
            return True

    @staticmethod
    def get_phrasal_left_sister(h):
        if h.sister() and not h.sister().is_primitive() and h.sister().is_left():
            return h.sister()