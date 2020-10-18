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
                self.controlling_parser_process.LF.try_LFmerge(self.visible_head(node))
        # ---------------------------------------------------------------------------------------------#

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
                        log(f'\t\t\t\t\tMoving {spec} into memory buffer from Spec{head.get_cats_string()}P.')
                    else:
                        iterator = self.A_reconstruct(spec, iterator)

                if count_specifiers > 0:
                    if self.specifier_phrase_must_have_supporting_head(spec):
                        new_h = self.engineer_head_from_specifier(head, spec)
                        iterator.merge_1(new_h, 'left')
                        iterator = iterator.mother # Prevents looping over the same Spec element
                        log(f'\t\t\t\t\tNew head was spawned at {head.get_cats_string()}P')
                        if new_h.get_tail_sets():
                            self.adjunct_constructor.create_adjunct(new_h)
                else:
                    count_specifiers = + 1
                    if spec.scan_criterial_features():
                        log(f'\t\t\t\t\tCriterial features {spec.scan_criterial_features()} copied to {head}.')
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

    # Definition for A-reconstruction
    def A_reconstruct(self, spec, iterator):
        if self.candidate_for_A_reconstruction(spec):
            log(f'\t\t\t\t\t{spec} undergoes A-reconstruction.')
            iterator = self.reconstruct_inside_next_projection(spec, iterator)
            self.controlling_parser_process.consume_resources("Move Phrase")
            self.controlling_parser_process.consume_resources("A-Move Phrase")
        return iterator

    def candidate_for_A_reconstruction(self, ps):
        if ps == ps.container_head().licensed_specifier():
            return 'D' in ps.head().features and ps.sister() and ps.is_left() and not ps.is_primitive()

    def reconstruct_inside_next_projection(self, spec, iterator):
        local_head = spec.sister().head()
        if local_head.is_right():
            # [Y X] => [Y [X Y]]
            local_head.merge_1(spec.copy_from_memory_buffer(self.controlling_parser_process.babtize()), 'right')
            return iterator.mother
        if local_head.is_left():
            if local_head.sister():
                # [Y [X ZP]] => [Y [X [Y YP]]]
                local_head.sister().merge_1(spec.copy_from_memory_buffer(self.controlling_parser_process.babtize()), 'left')
            else:
                # [Y [X <ZP>]] => [Y [X Y] <ZP>]
                local_head.sister().merge_1(spec.copy_from_memory_buffer(self.controlling_parser_process.babtize()), 'right')
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