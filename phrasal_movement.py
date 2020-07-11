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
            head = node.visible_head()
            if head:
                self.activate_phrase_for_reconstruction(head)
                self.try_reconstruct(head)

        # ------------------------------------------------------------------------------------------#

    def try_reconstruct(self, head):
        self.access_LF.LFmerge(head, self.controlling_parser_process)

    def activate_phrase_for_reconstruction(self, h):
        if h.EPP():
            specifiers_to_add_memory_buffer = []
            iterator = h.get_specifier_anchor()
            count_specifiers = 0
            while iterator and iterator.get_phrasal_left_sister():
                spec = iterator.get_phrasal_left_sister()
                if not spec.find_me_elsewhere:
                    if spec.Abar_movable():
                        specifiers_to_add_memory_buffer.append(spec)
                        log(f'\t\t\t\t\tMoving \"' + spec.spellout() + f'\" into memory buffer from Spec{h.get_cats_string()}P.')
                    else:
                        self.A_reconstruct(spec)

                criterial_features = spec.scan_criterial_features()

                # Case 1: if there already was another spec
                if count_specifiers > 0:
                    if spec.must_have_head():
                        new_h = self.engineer_head_from_specifier(h, criterial_features)
                        iterator.merge(new_h, 'left')
                        iterator = iterator.mother # Prevents looping over the same Spec element
                        log(f'\t\t\t\t\tNew {criterial_features} head was spawned due to the occurrence of multiple specifiers at {h.get_cats_string()}P')
                        if new_h.get_tail_sets():
                            log('\t\t\t\t\tThe new head has tail features, must be an adjunct floater.')
                            self.adjunct_constructor.create_adjunct(new_h)
                # Case 2: This is the first spec
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
    # XP undergoes A-reconstruction if and only if
    # Condition 1. XP is a DP
    # Condition 2. XP is inside projection HP and H has a complement into which to reconstruct
    # Condition 3. XP is in a non-thematic SPEC position
    # Condition 4. XP has no criterial feature
    def A_reconstruct(self, ps):

        # Condition 1.
        if 'D' in ps.head().features and ps.sister() and ps.is_left() and not ps.is_primitive():
            log(f'\t\t\t\t\t{ps} will undergo A-reconstruction.')

            # XP will be reconstructed into CompHP, H = head of HP
            H = ps.sister().head()

            # Reconstruct only if CompHP exists
            if H.sister():

                # If [DP [H XP]] then [__ [H [DP XP]]]
                if H.is_left():
                    H.sister().merge(ps.copy_from_memory_buffer(self.controlling_parser_process.babtize()), 'left')
                    self.controlling_parser_process.number_of_phrasal_Move += 1

                # If [DP [XP H]] then [__ [[XP DP] H]
                else:
                    H.sister().merge(ps.copy_from_memory_buffer(self.controlling_parser_process.babtize()), 'right')
                    self.controlling_parser_process.number_of_phrasal_Move += 1

    # Definition for spec selection match
    # H = head whose SPEC position is tested
    #
    def spec_match(self, head, spec):

        if 'SPEC:*' in head.features or '!SPEC:*' in head.features:
            return True
        for feature_in_head in head.for_parsing(head.specs()):
            for feature_in_spec in spec.head().features:
                if feature_in_head == feature_in_spec:
                    return True
        return False

    # get_specifiers() wrapper that implements the modular interface to the PhraseStructure class
    def get_specifiers(self, h):
        return [spec for spec in h.edge() if not spec.is_primitive()]