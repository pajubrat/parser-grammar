from support import set_logging, log, get_number_of_operations, reset_number_of_operations, log_result, illu
from LexicalInterface import LexicalInterface
from adjunct_constructor import AdjunctConstructor
import phrase_structure

class PhrasalMovement():
    def __init__(self, controlling_parser_process):
        self.controlling_parser_process = controlling_parser_process
        self.name_provider_index = 1
        self.memory_buffer = []
        self.context = controlling_parser_process

        # Access to the lexicon
        self.lexical_access = LexicalInterface(self.controlling_parser_process)
        self.lexical_access.load_lexicon(self.controlling_parser_process)
        self.adjunct_constructor = AdjunctConstructor(self.controlling_parser_process)

    # Definition for A/A'-movement reconstruction
    def reconstruct(self, ps):
        self.memory_buffer = []
        _ps_iterator = ps
        _ps_last_site = _ps_iterator

        # ------------------------------ minimal search -----------------------------------------------#
        for node in ps.minimal_search():

            # Target primitive heads on our way downstream
            h = self.target_head(node)
            if h:
                #
                # Case 1. Missing SPEC, if any, is filled if suitable phrase is in the memory buffer
                #
                if self.free_spec_positions(h):
                    self.fill_spec_from_memory(h)
                #
                # Case 2. EPP head has SPECs that are stored into memory
                #
                if h.EPP():
                    self.store_specs_into_memory(h)
                #
                # Case 3. Missing complement
                #
                self.fill_comp_from_memory(h)

            _ps_last_site = node
        # ------------------------------------------------------------------------------------------#

    # Case 1. Fill specifier position from memory buffer
    def fill_spec_from_memory(self, h):
        ps = h.get_iterator()
        for constituent_in_memory_buffer in self.memory_buffer:
            if self.spec_match(h, constituent_in_memory_buffer):
                    ps.merge(constituent_in_memory_buffer.copy(), 'left')
                    if ps.geometrical_sister().head().external_tail_head_test():
                        log(f'\t\t\t\t\tDropping constituent {constituent_in_memory_buffer} from memory buffer into Spec of ' + f'{h}')
                        log(f'\t\t\t\t\tResult {ps.top()}')
                        # Replace the hypothetical candidate with proper chain
                        ps.geometrical_sister().remove()
                        new_const = constituent_in_memory_buffer.copy_from_memory_buffer(self.babtize())
                        ps.merge(new_const, 'left')
                        self.memory_buffer.remove(constituent_in_memory_buffer)
                        self.controlling_parser_process.number_of_phrasal_Move += 1
                        break
                    else:
                        # If there was a tail-head violation, dropping is cancelled
                        ps.geometrical_sister().remove()

    def free_spec_positions(self, h):
        specs = self.get_specifiers(h)
        if not specs or (specs and specs[0].adjunct):
            return True
        else:
            return False

    # Case 2. Store specifier into memory buffer
    def store_specs_into_memory(self, h):
        specifiers_to_add_memory_buffer = []
        iterator = h.get_iterator()
        while iterator and iterator.get_phrasal_left_sister():
            spec = iterator.get_phrasal_left_sister()
            if not spec.find_me_elsewhere:
                if spec.Abar_movable():
                    specifiers_to_add_memory_buffer.append(spec)
                    log(f'\t\t\t\t\tMoving \"' + spec.spellout() + f'\" into memory buffer from SPEC of \"{h}\".')
                else:
                    self.A_reconstruct(spec)

            criterial_features = spec.scan_criterial_features()

            # Case 1: if there already was another spec
            if len(specifiers_to_add_memory_buffer) > 1:
                if spec.must_have_head():
                    new_h = self.engineer_head_from_specifier(h, criterial_features)
                    iterator.merge(new_h, 'left')
                    log(f'\t\t\t\t\tNew {criterial_features} head was spawned due to the occurrence of multiple specifiers at {h.get_pf()}')
                    if new_h.get_tail_sets():
                        log('\t\t\t\t\tThe new head has tail features, must be an adjunct floater.')
                        self.adjunct_constructor.create_adjunct(new_h)

            # Case 2: This is the first spec
            else:
                if criterial_features:
                    h.features |= self.get_features_for_criterial_head(h, criterial_features)
                    log(f'\t\t\t\t\tCriterial features {criterial_features} copied to {h}')
                    if h.get_tail_sets():
                        log(f'\t\t\t\t\tTail features ' + illu(
                            h.get_tail_sets()) + f' were detected at {h}, this must head an adjunct floater.')
                        self.adjunct_constructor.create_adjunct(h)

            iterator = iterator.walk_upstream()

        # Add everything into memory buffer
        self.memory_buffer = specifiers_to_add_memory_buffer + self.memory_buffer

        if len(specifiers_to_add_memory_buffer) > 0:
            log(f'\t\t\t\t\tMemory buffer: {self.memory_buffer}')

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

    # Case 3. Fill complement from memory buffer
    def fill_comp_from_memory(self, h):
        # Condition 1. H is a primitive head without complements that it needs
        if h.is_primitive() and not h.complement() and h.get_comps():
            const = self.hit_from_memory_buffer(h)
            if const:
                h.merge(const.copy_from_memory_buffer(self.babtize()), 'right')
                self.memory_buffer.remove(const)
                self.controlling_parser_process.number_of_phrasal_Move += 1
                log(f'\t\t\t\t\tDropping {repr(const)}(=' + const.spellout() + f') from memory buffer into Comp of {h.features}.')
                log(f'\t\t\t\t\tResult {h.top()}')

        #  Condition 2. The head has a non-matching complement
        if h.is_left() and h.complement() and not (h.get_comps() & h.complement().features):
            const = self.hit_from_memory_buffer(h)
            if const and const.features & h.get_comps():
                h.complement().merge(const.copy_from_memory_buffer(self.babtize()), 'left')
                self.controlling_parser_process.number_of_phrasal_Move += 1
                self.memory_buffer.remove(const)
                log(f'\t\t\t\t\tDropping {repr(const)}(=' + const.spellout() + f') from memory buffer into Comp of {h.features} '
                    f'due to the presence of mismatching complement {h.complement()}.')
                # Mismatching complement will be made floater
                if h.complement().right_const.is_adjoinable():
                    log('\t\t\t\t\tThe mismatching complement will be transformed into floater adjunct.')
                    self.adjunct_constructor.create_adjunct(h.complement().right_const)

    def hit_from_memory_buffer(self, h):
        for const in self.memory_buffer:
            if h.get_comps() & const.head().features:
                return const

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
                    H.sister().merge(ps.copy_from_memory_buffer(self.babtize()), 'left')
                    self.controlling_parser_process.number_of_phrasal_Move += 1

                # If [DP [XP H]] then [__ [[XP DP] H]
                else:
                    H.sister().merge(ps.copy_from_memory_buffer(self.babtize()), 'right')
                    self.controlling_parser_process.number_of_phrasal_Move += 1

    # Definition for targeting a head
    def target_head(self, _ps_iterator):
        if _ps_iterator.is_primitive():
            h = _ps_iterator
        elif _ps_iterator.left_const.is_primitive():
            h = _ps_iterator.left_const
        else:
            h = None
        return h

    # This will provide unique names when chains are formed
    # It is used only for output purposes
    def babtize(self):
        self.name_provider_index += 1
        return str(self.name_provider_index)

    # Definition for intervention
    def memory_intervention(self, criterial_features):
        for constituent in self.memory_buffer:
            if constituent.scan_criterial_features().intersection(criterial_features):
                return True
        return False

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
        specs = h.edge()
        return [spec for spec in specs if not spec.is_primitive()]


