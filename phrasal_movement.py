from support import set_logging, log, get_number_of_operations, reset_number_of_operations, log_result, illu
from LexicalInterface import LexicalInterface
from adjunct_constructor import AdjunctConstructor
from LF import LF
import phrase_structure

class PhrasalMovement():
    def __init__(self, controlling_parser_process):
        self.controlling_parser_process = controlling_parser_process
        self.controlling_parser_process.name_provider_index = 1
        self.controlling_parser_process.syntactic_working_memory = []
        self.context = controlling_parser_process
        self.access_LF = LF()

        # Access to the lexicon
        self.lexical_access = LexicalInterface(self.controlling_parser_process)
        self.lexical_access.load_lexicon(self.controlling_parser_process)
        self.adjunct_constructor = AdjunctConstructor(self.controlling_parser_process)

    # Definition for A/A'-movement reconstruction
    def reconstruct(self, ps):
        self.controlling_parser_process.syntactic_working_memory = []
        # ------------------------------ minimal search -----------------------------------------------#

        for node in ps.minimal_search():
            head = self.visible_head(node)
            if head:
                self.activate_phrase_for_reconstruction(head)
                self.try_reconstruct(head)

        # ------------------------------------------------------------------------------------------#

    def try_reconstruct(self, head):
        self.access_LF.LFmerge(head, self.controlling_parser_process)

    def activate_phrase_for_reconstruction(self, h):
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
                        log(f'\t\t\t\t\tNew {criterial_features} head was spawned due to the occurrence of multiple specifiers at {h.get_cats_string()}P')
                        if new_h.get_tail_sets():
                            log('\t\t\t\t\tThe new head has tail features, must be an adjunct floater.')
                            self.adjunct_constructor.create_adjunct(new_h)
                else:
                    count_specifiers = + 1
                    if criterial_features:
                        h.features |= self.get_features_for_criterial_head(h, criterial_features)
                        log(f'\t\t\t\t\tCriterial features {criterial_features} copied to {h}')
                        if h.get_tail_sets():
                            log(f'\t\t\t\t\tTail features ' + illu(
                                h.get_tail_sets()) + f' were detected at {h}, this must head an adjunct floater.')
                            self.adjunct_constructor.create_adjunct(h)
                iterator = iterator.walk_upstream()
            # --------------------------------------------------------------------------------------------------#

            # Add everything into memory buffer
            self.controlling_parser_process.syntactic_working_memory = specifiers_to_add_memory_buffer + self.controlling_parser_process.syntactic_working_memory
            if len(specifiers_to_add_memory_buffer) > 0:
                log(f'\t\t\t\t\tMemory buffer: {self.controlling_parser_process.syntactic_working_memory}')

    def get_features_for_criterial_head(self, h, criterial_features):
        feature_set = {'OP:_'}
        if 'FIN' in h.features:
            feature_set |= {'OP', 'FIN'}
            feature_set |= {'FORCE:' + criterial_feature for criterial_feature in criterial_features}
        return self.lexical_access.apply_parameters(self.lexical_access.apply_redundancy_rules(feature_set))

    # Definition for generating a new head
    def engineer_head_from_specifier(self, h, criterial_features):
        new_h = self.lexical_access.PhraseStructure()
        new_h.features |= self.get_features_for_criterial_head(h, criterial_features)
        if 'FIN' in h.features:
            new_h.features |= {'C', 'PF:C'}
        return new_h

    # Definition for A-reconstruction
    def A_reconstruct(self, spec, iterator):
        if self.candidate_for_A_reconstruction(spec):
            log(f'\t\t\t\t\t{spec} will undergo A-reconstruction.')
            iterator = self.reconstruct_inside_next_projection(spec, iterator)
        return iterator

    def candidate_for_A_reconstruction(self, ps):
        if 'D' in ps.head().features and ps.sister() and ps.is_left() and not ps.is_primitive():
            return True

    def reconstruct_inside_next_projection(self, spec, iterator):
        local_head = spec.sister().head()
        if local_head.is_right():
            local_head.merge_1(spec.copy_from_memory_buffer(self.controlling_parser_process.babtize()), 'right')
            return iterator.mother
        else:
            if local_head.sister():
                if local_head.is_left():
                    local_head.sister().merge_1(spec.copy_from_memory_buffer(self.controlling_parser_process.babtize()),
                                              'left')
                    self.controlling_parser_process.number_of_phrasal_Move += 1
                else:
                    local_head.sister().merge_1(spec.copy_from_memory_buffer(self.controlling_parser_process.babtize()),
                                              'right')
                    self.controlling_parser_process.number_of_phrasal_Move += 1
        return iterator

    # Definition for spec selection match
    def spec_match(self, head, spec):

        if 'SPEC:*' in head.features or '!SPEC:*' in head.features:
            return True
        for feature_in_head in head.convert_features_for_parsing(head.licensed_specifiers()):
            for feature_in_spec in spec.head().features:
                if feature_in_head == feature_in_spec:
                    return True
        return False

    # get_specifiers() wrapper that implements the modular interface to the PhraseStructure class
    @staticmethod
    def get_specifiers(h):
        return [spec for spec in h.edge() if not spec.is_primitive()]

    @staticmethod
    def visible_head(h):
        if h.is_primitive():
            return h
        elif h.left_const.is_primitive():
            return h.left_const
        else:
            return None

    @staticmethod
    # Definition for constituent that can implement A-bar move
    def Abar_movable(h):
        if h.scan_criterial_features():
            return True
        elif 'A/inf' in h.head().features:
            return True
        else:
            return False

    @staticmethod
    # Definition for phrase that requires a local licensing head (used in connection with A-bar head generation)
    def must_have_head(h):
        if h.adjunct and not h.scan_criterial_features():
            return False
        else:
            return True

    @staticmethod
    def get_phrasal_left_sister(h):
        if h.sister() and not h.sister().is_primitive() and h.sister().is_left():
            return h.sister()
        else:
            return None