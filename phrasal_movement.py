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
                self.fill_spec_from_memory(h)
                #
                # Case 2. EPP head has SPECs that are stored into memory
                #
                self.store_specs_into_memory(h)
                #
                # Case 3. Missing complement
                #
                self.fill_comp_from_memory(h)

            # Walk downwards on the right edge
            _ps_last_site = node
        # ------------------------------------------------------------------------------------------#


    #
    # Case 1. Fill specifier position from memory buffer
    #
    def fill_spec_from_memory(self, h):

        target_const_from_memory_buffer = None

        if h.mother and h.is_left():
            ps = h.mother
        else:
            ps = h

        # Try to fit each element in the memory buffer and select first that matches
        # Condition 1. Label must be selected
        # Condition 2. The head should not have non-adjuncts specifiers already
        # Condition 3. No head-tail violations can occur
        specs = self.get_specifiers(h)
        for constituent_from_memory_buffer in self.memory_buffer:
            # Condition 1: h must select the label of the constituent in the memory buffer
            if self.spec_match(h, constituent_from_memory_buffer):
                # Condition 2: h must not have non-adjunct specifiers already
                if not specs or (specs and specs[0].adjunct):
                    target_const_from_memory_buffer = constituent_from_memory_buffer
                    # Condition 3: the constituent must not cause tail violations
                    # Try to merge it to Spec
                    # Check that this does not cause tail-head violations
                    ps.merge(target_const_from_memory_buffer.copy(), 'left')
                    if ps.geometrical_sister().head().external_tail_head_test():  # Checks the head of the dropped constituent
                        log(f'\t\t\t\t\tDropping constituent {target_const_from_memory_buffer} from memory buffer into Spec of ' + f'{h}')
                        log(f'\t\t\t\t\tResult {ps.top()}')
                        # Replace the hypothetical candidate with proper chain
                        ps.geometrical_sister().remove()
                        new_const = target_const_from_memory_buffer.copy_from_memory_buffer(self.babtize())
                        ps.merge(new_const, 'left')
                        self.memory_buffer.remove(target_const_from_memory_buffer)

                        # Keep record of the computations consumed
                        self.controlling_parser_process.number_of_phrasal_Move += 1

                        break
                    else:
                        # If there was a tail-head violation, dropping is cancelled
                        ps.geometrical_sister().remove()

    #
    # Case 2. Store specifier into memory buffer
    #
    def store_specs_into_memory(self, h):
        if h.EPP():

            _ps_iterator = h
            if _ps_iterator.is_left():
                _ps_iterator = h.mother

            # spec-iterator iterated over multiple Specs (if possible) into upward direction
            _ps_spec_iterator = _ps_iterator
            list_ = []
            spec_found = False
            adjunct_found = False

            while _ps_spec_iterator:
                # If a phrase is found from left...
                if _ps_spec_iterator.sister() and \
                        not _ps_spec_iterator.sister().is_primitive() and \
                        _ps_spec_iterator.sister().is_left():

                    # we gather a set of criterial features from the Spec (OP:WH, OP:FOC, OP:REL, OP:TOP)
                    criterial_features = _ps_spec_iterator.sister().scan_criterial_features()
                    if not _ps_spec_iterator.sister().find_me_elsewhere:

                        # ...and it has criterial features
                        if criterial_features:
                            # ...we put a pointer to the specifier into memory buffer.
                            list_.append(_ps_spec_iterator.sister())
                            log(f'\t\t\t\t\tMoving \"' + _ps_spec_iterator.sister().spellout() + f'\" into memory buffer from SPEC of \"{h}\".')

                        # ... if there are no criterial features
                        else:
                            # ...we reconstruct  A-movement (a version of phi-agreement)

                            self.A_reconstruct(_ps_spec_iterator.sister())

                    # If we already have processed one Spec, and there is additional non-adjunct phrase,
                    # then we might need phantom heads
                    if spec_found:

                        # If the lower SPEC is adjunct and there are no criterial features in the upper SPEC,
                        # we don't do anything
                        if not criterial_features and adjunct_found:
                            adjunct_found = _ps_spec_iterator.sister().adjunct

                        #
                        # Spawn head
                        #
                        # If the lower SPEC is not an adjunct, or if there are criterial features in the higher SPEC,
                        # we need to spawn a head
                        else:
                            # If the second SPEC has no criterial features and is adjunct, we do nothing
                            if not criterial_features and _ps_spec_iterator.sister().adjunct:
                                pass
                            else:
                                if not criterial_features and not _ps_spec_iterator.sister().adjunct:
                                    log(f'\t\t\t\t\tNew head was spawned due to multiple specifiers at {h}'
                                        ' but its category is unknown!')
                                else:
                                    log(f'\t\t\t\t\tNew {criterial_features} head was spawned due to '
                                        f'the occurrence of multiple specifiers at {h.get_pf()}')

                                # Create and merge the new head, then move the pointer over it so we don't repeat
                                new_h = self.engineer_head_from_specifier(h, criterial_features)
                                _ps_spec_iterator.merge(new_h, 'left')

                                # Move to the new constituent (otherwise we will loop this)
                                _ps_spec_iterator = _ps_spec_iterator.walk_upstream()
                                if new_h.get_tail_sets():
                                    log('\t\t\t\t\tThe new head has tail features, must be an adjunct floater.')
                                    self.adjunct_constructor.create_adjunct(new_h)

                                    # Drop inside the right-adjunct
                                    if _ps_spec_iterator.mother:
                                        _ps_spec_iterator = _ps_spec_iterator.mother  # Move one step up

                    #
                    # Just one specifier, so we copy the criterial features into it
                    #
                    else:
                        spec_found = True  # We register that one head has been found

                        # Register if it was an adjunct
                        adjunct_found = _ps_spec_iterator.sister().adjunct

                        if criterial_features:
                            h.features |= self.get_features_for_criterial_head(h, criterial_features)
                            log(f'\t\t\t\t\tCriterial features {criterial_features} copied to {h}')
                            if h.get_tail_sets():
                                log(f'\t\t\t\t\tTail features ' + illu(
                                    h.get_tail_sets()) + f' were detected at {h}, this must head an adjunct floater.')
                                self.adjunct_constructor.create_adjunct(h)
                                if _ps_spec_iterator.mother:
                                    _ps_spec_iterator = _ps_spec_iterator.mother

                    # Move to next specifier
                    _ps_spec_iterator = _ps_spec_iterator.walk_upstream()

                # If there is primitive c-commanding head on the left, we must stop searching
                else:
                    _ps_spec_iterator = None

            # Add everything into memory buffer
            self.memory_buffer = list_ + self.memory_buffer

            if len(list_) > 0:
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

    #
    # Case 3. Fill complement from memory buffer
    #
    def fill_comp_from_memory(self, h):

        # Condition 1. H is a primitive head without complement
        if h.is_primitive() and not h.complement():

            # If (i) H has comp features and
            if h.get_comps():

                target_const = None

                # (ii) comp features can be satisfied by an element in the memory buffer
                for const in self.memory_buffer:

                    if h.get_comps() & const.head().features:

                        # then select the first such constituent from the memory buffer
                        target_const = const

                        # Merge the element into COMP,H position
                        h.merge(target_const.copy_from_memory_buffer(self.babtize()), 'right')

                        # Keep record of the computations consumed
                        self.controlling_parser_process.number_of_phrasal_Move += 1

                        log(f'\t\t\t\t\tDropping {repr(target_const)}(=' + target_const.spellout()
                            + f') from memory buffer into Comp of {h.features}.')
                        log(f'\t\t\t\t\tResult {h.top()}')

                        # Remove the merged element from the memory buffer
                        self.memory_buffer.remove(target_const)
                        log(f'\t\t\t\t\tRemaining items in memory buffer: {self.memory_buffer}')

                        # Do not continue search from the memory buffer
                        break

        #  Condition 2. The head has a non-matching complement
        if h.is_left() and h.complement() and not (h.get_comps() & h.complement().features):

            target_const = None

            # Search the memory buffer
            for const in self.memory_buffer:

                # If a matching complement is found from the memory buffer
                if const.features & h.get_comps():
                    target_const = const

                    log(f'\t\t\t\t\tDropping {repr(target_const)}(=' + target_const.spellout()
                        + f') from memory buffer into Comp of {h.features} '
                        f'due to the presence of mismatching complement {h.complement()}.')

                    # The constituent from memory buffer will be merged to left of the complement
                    h.complement().merge(target_const.copy_from_memory_buffer(self.babtize()), 'left')

                    # Keep record of the computations consumed
                    self.controlling_parser_process.number_of_phrasal_Move += 1

                    # Empty the memory buffer
                    self.memory_buffer.remove(const)

                    # The mismatching complement will be made floater
                    if h.complement().right_const.is_adjoinable():
                        log('\t\t\t\t\tThe mismatching complement will be transformed into floater adjunct.')
                        self.adjunct_constructor.create_adjunct(h.complement().right_const)

    # Definition for A-reconstruction
    # XP undergoes A-reconstruction if and only if
    # Condition 1. XP is a DP
    # Condition 2. XP is inside projection HP and H has a complement into which to reconstruct
    # Condition 3. XP is in a non-thematic SPEC position
    # Condition 4. XP has no criterial feature
    def A_reconstruct(self, ps):

        # Condition 1.
        if 'D' in ps.head().features:

            # Condition 2. There is a right sister HP
            if ps.sister() and ps.is_left() and not ps.is_primitive():
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


