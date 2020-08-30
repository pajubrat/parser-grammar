from support import set_logging, log, get_number_of_operations, reset_number_of_operations, log_result, illu
from LexicalInterface import LexicalInterface
from adjunct_constructor import AdjunctConstructor
from LF import LF

class PhrasalMovement():
    def __init__(self, controlling_parser_process):
        self.controlling_parser_process = controlling_parser_process
        self.controlling_parser_process.name_provider_index = 1
        self.controlling_parser_process.syntactic_working_memory = []
        self.context = controlling_parser_process
        self.access_LF = LF()
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
                self.push(self.visible_head(node))
        # ---------------------------------------------------------------------------------------------#

    def push(self, head):
        self.access_LF.LFmerge(head, self.controlling_parser_process)

    def pull(self, h):
        if h.EPP():
            specifiers_to_add_memory_buffer = []
            iterator = h.get_specifier_sister()
            count_specifiers = 0
            # ------------------------ upstream walk------------------------------------------------ #
            while iterator and self.get_phrasal_left_sister(iterator):
                spec = self.get_phrasal_left_sister(iterator)
                if not spec.find_me_elsewhere:
                    if self.Abar_movable(spec):
                        specifiers_to_add_memory_buffer.append(spec)
                        log(f'\t\t\t\t\tMoving \"' + spec.spellout() + f'\" into memory buffer from Spec{h.get_cats_string()}P.')
                    else:
                        iterator = self.A_reconstruct(spec, iterator)

                criterial_features = spec.scan_criterial_features()

                if count_specifiers > 0:
                    if self.must_have_head(spec):
                        new_h = self.engineer_head_from_specifier(h, criterial_features)
                        iterator.merge_1(new_h, 'left')
                        iterator = iterator.mother # Prevents looping over the same Spec element
                        log(f'\t\t\t\t\tNew {criterial_features} head was spawned at {h.get_cats_string()}P')
                        if new_h.get_tail_sets():
                            self.adjunct_constructor.create_adjunct(new_h)
                else:
                    count_specifiers = + 1
                    if criterial_features:
                        h.features |= self.get_features_for_criterial_head(h, criterial_features)
                        if h.get_tail_sets():
                            self.adjunct_constructor.create_adjunct(h)
                iterator = iterator.walk_upstream()
            # --------------------------------------------------------------------------------------------------#

            # Add everything into memory buffer
            self.controlling_parser_process.syntactic_working_memory = specifiers_to_add_memory_buffer + self.controlling_parser_process.syntactic_working_memory
            if len(specifiers_to_add_memory_buffer) > 0:
                log(f'\t\t\t\t\tMemory buffer: {self.controlling_parser_process.syntactic_working_memory}')

    # Definition for generating a new head
    def engineer_head_from_specifier(self, h, criterial_features):
        new_h = self.lexical_access.PhraseStructure()
        new_h.features |= self.get_features_for_criterial_head(h, criterial_features)
        if 'FIN' in h.features:
            new_h.features |= {'C', 'PF:C'}
        return new_h

    def get_features_for_criterial_head(self, h, criterial_features):
        feature_set = {'OP:_'}
        if 'FIN' in h.features:
            feature_set |= {'OP', 'FIN'}
            feature_set |= {'FORCE:' + criterial_feature for criterial_feature in criterial_features}
        return self.lexical_access.apply_parameters(self.lexical_access.apply_redundancy_rules(feature_set))

    # Definition for A-reconstruction
    def A_reconstruct(self, spec, iterator):
        if self.candidate_for_A_reconstruction(spec):
            log(f'\t\t\t\t\t{spec} undergoes A-reconstruction.')
            iterator = self.reconstruct_inside_next_projection(spec, iterator)
        return iterator

    def candidate_for_A_reconstruction(self, ps):
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
                self.controlling_parser_process.number_of_phrasal_Move += 1
            else:
                # [Y [X <ZP>]] => [Y [X Y] <ZP>]
                local_head.sister().merge_1(spec.copy_from_memory_buffer(self.controlling_parser_process.babtize()), 'right')
                self.controlling_parser_process.number_of_phrasal_Move += 1
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
        return h.scan_criterial_features() or 'A/inf' in h.head().features

    @staticmethod
    # Definition for phrase that requires a local licensing head (used in connection with A-bar head generation)
    def must_have_head(h):
        return not (h.externalized() and not h.scan_criterial_features())

    @staticmethod
    def get_phrasal_left_sister(h):
        if h.sister() and not h.sister().is_primitive() and h.sister().is_left():
            return h.sister()