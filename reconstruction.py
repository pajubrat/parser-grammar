from support import set_logging, log, get_number_of_operations, reset_number_of_operations, log_result, illu
from LexicalInterface import LexicalInterface
import minimalist


class Reconstruction():
    def __init__(self, context):
        self.name_provider_index = 0
        self.memory_buffer = []
        self.context = context
        self.number_of_Moves = 0

        # Access to the lexicon
        self.lexical_access = LexicalInterface(context.redundancy_rules_file)
        self.lexical_access.load_lexicon(context.lexicon_file, context.language)
        self.lexical_access.load_lexicon(context.ug_morpheme_file, context.language, combine=True)

    def reconstruct(self, ps):
        """
        Performs movement reconstruction.

        The phrase structure is first detached from its context (mother). Then,
        (i) Head movement reconstruction is applied first,
        (ii) Floater reconstruction is applied second,
        (iii) A/A-bar reconstruction.

        (i) Head movement.

        (ii) The right edge of the phrase structure is explored to locate constituents (at left) with tail-head features
        at their heads that are not satisfied. Once found, the constituent is dropped. Dropping is implemented by
        going back to the highest node, walking downwards and looking for the first position that would satisfy the
        tail-features.

        (iii) Walk downwards on the right edge, while locating left heads with the EPP feature. If found, put the
        phrase from SPEC into M-buffer. Conversely, if we encounter a head that has a SPEC or COMP feature
        matching with something in M-buffer but missing in the phrase structure, elements are transferred from
        M-buffer into these positions. The result is that phrases are dropped from SPEC/EPP positions into
        positions in which they are lexically selected (either SPEC or COMP).
        """

        self.number_of_Moves = 0

        if ps.is_primitive() and ps.has_affix():
            set_logging(False)
            if self.reconstruct_head_movement(ps.copy()).LF_legibility_test().all_pass():
                new = self.reconstruct_head_movement(ps)
                set_logging(True)
                log(f'\t\t\t{ps} was opened.')
                return new, self.number_of_Moves
            else:
                set_logging(True)
                log(f'\t\t\t{ps} cannot be opened.')
        else:
            self.reconstruct_head_movement(ps)
            self.reconstruct_floaters(ps)
            self.reconstruct_phrasal_movement(ps)

        return ps, self.number_of_Moves

    def reconstruct_head_movement(self, ps):
        log(f'\t\t\tReconstructing head movement for {ps}.')
        ps_ = ps
        top = ps

        while ps_:
            # Condition when the head is part of a complex phrase structure
            if ps_.left_const and ps_.left_const.is_primitive() and ps_.left_const.has_affix():
                affix = ps_.left_const.get_affix()
                if self.drop_head(ps_.right_const, affix):
                    ps_.left_const.right_const = None
                    log(f'\t\t\t\tExtracted head \"{affix}\" and reconstructed it = {ps_.get_top()}')
                else:
                    log(f'\t\t\t\tHead reconstruction failed for {affix}.')
            # Condition for dealing with primitive element
            elif ps_.is_primitive and ps_.has_affix():
                affix = ps_.get_affix()
                new_ps = ps_ + affix
                ps_.right_const = None
                top = new_ps
                log(f'\t\t\t\tExtracted head \"{affix}\" from {ps_} and created {new_ps}')
                if affix.has_affix():
                    self.reconstruct_head_movement(affix)
            ps_ = ps_.walk_downstream()

        return top

    def drop_head(self, ps, affix_):
        def drop_condition_for_heads(affix_):
            # Check if the head is correctly selected at this position
            if affix_.get_selector() and (affix_.get_selector().get_affix_comps() & affix_.get_cats()):
                # If it does not require a SPEC, we accept this position
                if not affix_.EPP():
                    return True # If the affix has no EPP, we accept the solution
                # If it requires SPEC . . .
                else:
                    if affix_.specifier():  # If the EPP is satisfied, we accept the solution
                        return True
                    # If the EPP is not satisfied but there is a primitive head below, we accept the solution
                    # because the SPEC could be filled in later by movement
                    elif affix_.sister() and \
                            affix_.sister().is_primitive() and \
                            not affix_.sister().get_affix():
                        return True
                    elif affix_.sister() and \
                            affix_.sister().left_const and \
                            affix_.sister().left_const.is_primitive() and \
                            not affix_.sister().left_const.get_affix():
                        return True
                    else:
                        # If there is complex left sister, we can accept the solution
                        if affix_.sister() and not affix_.sister().is_primitive() and affix_.sister().is_left():
                            return True
                        else:
                            return False
            else:
                return False

        iterator_ = ps

        while iterator_:
            self.number_of_Moves += 1
            iterator_.merge(affix_, 'left') # We try a solution
            if drop_condition_for_heads(affix_):
                return True
            else:
                affix_.remove()
                iterator_ = iterator_.walk_downstream()

        # We try the bottom right position
        # This is relevant if a reconstructed head needs to eat a DP at the right node due to EPP
        # If there is affix (D{N}), it must be reconstructed first
        if ps.get_bottom().has_affix():
            self.reconstruct_head_movement(ps.get_bottom())
            # We merge to the mother DP, not to the bottom N that was generated by head reconstruction
            ps.get_bottom().mother.merge(affix_, 'right')
        else:
            ps.get_bottom().merge(affix_, 'right')
        log(f'{ps}')
        if drop_condition_for_heads(affix_):
            return True
        else:
            affix_.remove()

        # What do we do if head reconstruction doesn't find any position?
        # we will merge it to the local position as a last resort
        log(f'\t\t\t\tHead reconstruction failed for {affix_}, merged locally as a last resort.')
        ps.merge(affix_, 'left')
        # We need to reconstruct head movement for the left branch
        return True

    def reconstruct_floaters(self, ps):
        _ps_iterator = ps.get_top()  # Begin from the top and move downstream
        log(f'\t\t\tDropping floaters...')

        while _ps_iterator:
            floater = self.detect_floater(_ps_iterator)
            if floater:
                self.drop_floater(floater, ps)
                self.number_of_Moves += 1
            _ps_iterator = _ps_iterator.walk_downstream()

        log(f'\t\t\t\t= ' + ps.illustrate())

    def detect_floater(self, _ps_iterator):
        # Check if a phrase at the left requires reconstruction
        if not _ps_iterator.is_primitive() and \
                not _ps_iterator.left_const.is_primitive() and \
                not _ps_iterator.left_const.find_me_elsewhere and \
                _ps_iterator.left_const.get_head().get_tail_sets() and \
                not '-FLOAT' in _ps_iterator.left_const.get_head().features:

            floater = _ps_iterator.left_const
            # Check if its tail features fail to find a head
            if not floater.get_head().external_tail_head_test():
                log('\t\t\t\t' + floater.illustrate() + ' failed to tail ' + illu(floater.get_head().get_tail_sets()))
                # Target the floater
                return floater
            # or if it (constituent with tail features) sits in an EPP SPEC position of a finite clause edge
            elif floater.mother and floater.mother.get_head().EPP() and floater.mother.is_finite():
                log('\t\t\t\t' + floater.illustrate() + ' is in an EPP SPEC position.')
                return floater
            # or if its in a wrong SPEC position
            elif floater.mother and '-SPEC:*' in floater.mother.get_head().features:
                if floater == floater.mother.get_head().specifier():
                    return floater
            # or if its a floating DP
            # This is needed to get arguments to move into a higher EPP position from otherwise legit position (e.g. antanut __ ei Pekka . . .)
            # This rule causes problems elsewhere because it makes it possible to double drop floaters, lets fix this later
            #elif 'D' in floater.get_labels():
            #    return floater

        # Check if the right edge itself has tail features (e.g. DP at the bottom, floaters/adjuncts)
        if not _ps_iterator.is_primitive() and \
                _ps_iterator.right_const.get_head().get_tail_sets() and \
                not '-FLOAT' in _ps_iterator.right_const.get_head().features:
            floater = _ps_iterator.right_const.get_head()
            # If tail features fail to find a head, the constituent must be dropped
            if not floater.external_tail_head_test():
                log('\t\t\t\t' + floater.illustrate() + ' failed to tail.')
                # This is empirically very contentious matter:
                # A right DP inside a finite clause with failed tail-test must be an adjunct(?)
                if ('D' in floater.get_labels() or 'P' in floater.get_labels()) and floater.get_top().contains_feature('CAT:FIN'):
                    self.create_adjunct(floater)
                    return floater.mother
            else:
                if 'ADV' in floater.get_labels() and not _ps_iterator.right_const.adjunct:
                    self.create_adjunct(floater)

    # Drops one floater that is targeted for dropping
    def drop_floater(self, floater, ps):

        # This is stored so we don't implement reconstruction inside the same projection (leads into regress)
        starting_point = floater.mother.get_head()

        # We need to locate the appropriate starting point, XP in [fin XP]
        ps_iterator_ = self.locate_minimal_tense_edge(floater.mother)

        floater_copy = floater.copy()

        # This downward loop searches a position for the floater
        while ps_iterator_ and not ps_iterator_ == floater and not ps_iterator_.find_me_elsewhere:

            # Lower bound must be the edge of next fin, this condition is missing (not needed for 1.x)

            # Create hypothetical structure for testing
            if 'ADV' in floater_copy.get_labels():
                ps_iterator_.merge(floater_copy, 'right')
            else:
                ps_iterator_.merge(floater_copy, 'left')

            # If a suitable position is found, dropping will be executed
            # Condition 1: tail test succeeds,
            # Condition 2: we are not reconstructing inside the same projection (does not apply to Adv which are right-adjoined)
            # Condition 3: dropped non-ADV will become the only SPEC
            if self.is_drop_position(ps_iterator_, floater_copy, starting_point):
                self.create_adjunct(floater)
                dropped_floater = floater.transfer(self.babtize())
                if 'ADV' in floater_copy.get_labels() or 'P' in floater_copy.get_labels():
                    ps_iterator_.merge(dropped_floater, 'right')
                else:
                    ps_iterator_.merge(dropped_floater, 'left')
                floater_copy.remove()
                floater.find_me_elsewhere = True
                log(f'\t\t\t\tFloater ' + dropped_floater.illustrate() + f' dropped: {ps}')
                return
            else:
                floater_copy.remove()

            ps_iterator_ = ps_iterator_.walk_downstream()

    def is_drop_position(self, ps_iterator_, floater_copy, starting_point):
        if floater_copy.get_head().external_tail_head_test():
            # Conditions for merging to the right (no additional conditions)
            if 'ADV' in floater_copy.get_labels() or 'P' in floater_copy.get_labels():
                return True
            # Conditions for merging to the left
            else:
                if ps_iterator_.get_head() is not starting_point.get_head(): # Don't go inside where you started
                    if ps_iterator_.get_head().count_specifiers() < 2: # Don't fill in more than one SPEC position
                        return True
                    else:
                        return False
                else:
                    return False
        else:
            return False


    # Reverse-engineers A-movement and A-bar movement and uses Chesi memory buffer
    def reconstruct_phrasal_movement(self, ps):
        log(f'\t\t\tDropping A-/A-bar movement.')
        self.memory_buffer = []
        _ps_iterator = ps
        _ps_last_site = _ps_iterator

        while _ps_iterator:
            # Target primitive heads on our way downstream
            h = self.target_head(_ps_iterator)
            if h:
                # Case 1a. MISSING SPEC, IF ANY, IS FILLED IF SUITABLE PHRASE IS FOUND FROM MEMORY.
                self.fill_spec_from_memory(h)
                # Case 1b. EPP HEAD HAS SPECS THAT ARE STORED INTO MEMORY.
                self.store_specs_into_memory(h)
                # Case 1c. MISSING COMP.
                self.fill_comp_from_memory(h)
            # Walk downwards on the right edge
            _ps_last_site = _ps_iterator
            _ps_iterator = _ps_iterator.walk_downstream()

        self.try_extraposition(_ps_last_site)

    def target_head(self, _ps_iterator):
        if _ps_iterator.is_primitive():
            h = _ps_iterator
        elif _ps_iterator.left_const.is_primitive():
            h = _ps_iterator.left_const
        else:
            h = None
        return h

    def try_extraposition(self, ps):
        # Returns the bottom node on the right edge (not geometrical)

        def get_bottom(ps):
            iterator_ = ps
            while iterator_:
                if iterator_.is_primitive():
                    return iterator_
                else:
                    iterator_ = iterator_.walk_downstream()
            return

        # Presupposition 1
        # LF - legibility fails(last resort)
        if ps.get_top().LF_legibility_test().all_pass():
            return

        # Presupposition 2
        # Do this only for referential structures (T/fin, D)
        if not (ps.get_top().contains_feature('CAT:FIN') or 'D' in ps.get_top().get_labels()):
            return

        log(f'\t\t\t\tExtraposition will be tried on {ps.get_top()}.')
        ps_ = get_bottom(ps).mother

        # Find first [H XP] where H is adjoinable and
        # we have either (i) [XP][HP] or (ii) [X HP] with X not selecting for H
        while ps_:
            if ps_.left_const.is_primitive() and ps_.left_const.is_adjoinable() and ps_.sister():
                # If its phrase, then we can select HP (=i)
                if not ps_.sister().is_primitive():
                    break
                # If it is head, then we select HP if the head rejects HP as complement (=ii)
                else:
                    # Explicit non-selection
                    if ps_.left_const.get_labels() & ps_.sister().get_not_comps():
                        break
                    # Mandatory selection for something else
                    if ps_.sister().get_mandatory_comps() and not(ps_.left_const.get_labels() & ps_.sister().get_mandatory_comps()):
                        break

            ps_ = ps_.walk_upstream()

        if ps_:
            # It only applies this rule if there is a verb (V) or D
            # This is LF-requirement: the adjunct must get semantic interpretation
            for head in ps_.left_const.get_feature_vector():
                if 'FIN' in head.get_labels() or 'D' in head.get_labels():
                    self.create_adjunct(ps_)
                    log(f'\t\t\t\t{ps_} was made adjunct by an extraposition rule.')
                    if not ps_.get_top().LF_legibility_test().all_pass():
                        # If phi set is available...
                        if self.promote_phi_set(ps_.left_const):
                            log(f'\t\t\t\tThe structure is still illicit. Try phi-tailing as a last resort.')
                            drop_floaters(ps_.get_top())
                            log(f'\t\t\t\t={ps_.get_top()}')
                    return True

        return False

    # This locates node XP in [fin XP] or return the highest node if not found
    # It is required because many operations are restricted by a minimal tense condition
    # e.g. argument/adjunct float
    def locate_minimal_tense_edge(self, ps):

        ps_iterator_ = ps
        node = ps

        # Go upwards to the upper edge of the finite construction
        while ps_iterator_:
            node = ps_iterator_
            if ps_iterator_.sister() \
                    and 'FIN' in ps_iterator_.get_labels() \
                    and 'FIN' not in ps_iterator_.sister().get_labels():
                break
            ps_iterator_ = ps_iterator_.walk_upstream()

        # we return the right const because that is the upper edge
        if node.right_const and not node.right_const.adjunct:
            return node.right_const
        else:
            return node

    # Creates an adjunct of a constituent
    def create_adjunct(self, ps):
        """
        Creates an adjunct out of a constituent.

        Adjuncts are marked as such by a specific feature of the constituent. Right adjuncts are processes in a
        separate syntactic working space. This function sets that feature to true.

        If the sister is already an adjunct, the operation is cancelled. In other words, [<XP>, <YP>] is not possible.
        This constituent is anomalous in the current system.

        If the constituent is a phrase, it is marked as adjunct and no further steps are taken. If the constituent
        is a head, then we have to consider how much of the surrounding structure will be eaten into the adjunct. If
        the head is marked for EPP, we eat the SPEC (if any). If not, we can eat only the complement. The procedure here
        is complex and must be verified by empirical tests.
        """

        def make_adjunct(ps):
            #if ps.geometrical_sister() and ps.geometrical_sister().adjunct:
            #    log(f'\t\t\t\t{ps} cannot be made an adjunct because its sister is an adjunct.')
            #    return False
            ps.adjunct = True
            log(f'\t\t\t\t{ps} was made an adjunct.')
            if ps.geometrical_sister() and ps.geometrical_sister().adjunct:
                ps.mother.adjunct = True
            return True

        # --- Main function begins here --- #

        head = ps.get_head()

        # If the head is primitive, we must decide how much of the surrounding structure we will eat
        if ps.is_primitive():
            # If the adjunct has found an acceptable position, we use !SPEC:* feature
            if head.external_tail_head_test():
                if '!SPEC:*' in head.features and head.mother.mother:
                    make_adjunct(head.mother.mother)
                    return ps.mother.mother
                else:
                    make_adjunct(head.mother)
                    return ps.mother
            # If the adjunct is still in wrong position, we eat the specifier if accepted
            else:
                # If potential Spec exists and the head accepts specifiers...
                if head.specifier() and not '-SPEC:*' in head.features and \
                        not set(head.get_not_specs()).intersection(set(head.specifier().get_labels())):
                    if head.mother.mother:
                        make_adjunct(head.mother.mother)
                    return ps.mother.mother
                else:
                    make_adjunct(head.mother)
                    return ps.mother
        else:
            make_adjunct(ps)

    # This will create a head from a specifier that lacks a head
    def engineer_head_from_specifier(self, features, labels):
        """
        This operation spawns a head H from a detected specifier XP that lacks a head.

        The category of the new head will be constructed from the criterial features F... scanned from XP,
        by creating uninterpretable (uF) and interpretable (iF) copies of the original features (F).

        The uninterpretable feature uF is the probe feature that agrees with F, but does not have
        semantic effects. The interpretable feature iF represents the scope-marker or the criterial head.
        Accordingly, a head that is spawned is always a criterial head. Then, other required features
        are added to the head on the basis of lexical rules (or the language).
        """

        new_h = self.lexical_access.PhraseStructure()

        # The category of the new head is going to be a copy of criterial feature of Spec
        # and the label of the original head (inverse feature inheritance)
        # We also create artificial phonological matrix for illustration
        for f in features:
            new_h.features.add('CAT:u' + f)
            new_h.features.add('PF:u' + f)
        if features:
            for label in labels:
                new_h.features.add('CAT:' + label)

        # We add EPP required features
        new_h.features = self.lexical_access.apply_parameters(
            self.lexical_access.apply_redundancy_rules(new_h.features))

        return new_h

    # This will provide unique names when chains are formed
    # It is used only for output purposes
    def babtize(self):
        self.name_provider_index += 1
        return str(self.name_provider_index)

    # Checks intervention
    def memory_intervention(self, criterial_features):
        for constituent in self.memory_buffer:
            if constituent.get_criterial_features().intersection(criterial_features):
                return True
        return False

    # Returns True if a spec-feature of H matches with the category of the head of G
    def spec_match(self, H, G):

        if 'SPEC:*' in H.features or '!SPEC:*' in H.features:
            return True

        for f_ in H.for_parsing(H.get_specs()):
            for g_ in G.get_labels():
                if f_ == g_:
                    return True
        return False

    # This function returns a pointer to a constituent in the memory buffer if it should/could be become SPEC,hP
    def fit_spec(self, h):

        # Retrieve the list of specifiers for h
        specs = h.get_specifiers()

        # This is the pointer to memory buffer constituent that is selected for merge
        # None, if nothing is selected
        target_const = None

        # To preserve working code I keep here the old and just add the required extra condition;
        # these can later be merged into one simple code

        # No SPEC situation
        if not specs:
            # Select the first possible Spec constituent from memory buffer
            for const in self.memory_buffer:
                # Check if SPEC,h could accept the constituent from memory, take the first match
                if self.spec_match(h, const) and not target_const:
                    target_const = const
                # Check if SPEC,h is a EPP position
                if '+PHI' in h.features and 'PHI:0' in h.features and 'CAT:D' in const.features and not target_const:
                    target_const = const
        # The second option is "tucking in": to insert SPEC and push adjuncts upwards
        else:
            if specs[0].adjunct:
                for const in self.memory_buffer:
                    # Check if SPEC,h could accept the constituent from memory, take the first match
                    if self.spec_match(h, const) and not target_const:
                        target_const = const
                    # Check if SPEC,h is a EPP position
                    if '+PHI' in h.features and 'PHI:0' in h.features and 'CAT:D' in const.features and not target_const:
                        target_const = const

        return target_const

    def fill_spec_from_memory(self, h):

        target_const = None

        if h.mother and h.is_left():
            ps = h.mother
        else:
            ps = h

        # Select the target if applicable
        target_const = self.fit_spec(h)

        # Transfer it from memory buffer into the phrase structure
        if target_const:
            # Try to merge it to Spec
            ps.merge(target_const.transfer(self.babtize()), 'left')
            # Check that this does not cause tail-head violations
            if ps.geometrical_sister().get_head().external_tail_head_test(): # Checks the head of the dropped constituent
                log(f'\t\t\t\tDropping constituent {target_const} from memory buffer into Spec of ' + f'{h}')
                log(f'\t\t\t\tResult {ps.get_top()}')
                self.memory_buffer.remove(target_const)
                self.number_of_Moves += 1
            else:
                # If there was a tail-head violation, dropping is cancelled
                ps.geometrical_sister().remove()

    # todo this is such a mess now that I have tried to make it work empirically in a correct way
    # todo must be revised later. Perhaps use get_specifiers() function
    def store_specs_into_memory(self, h):
        if h.EPP():

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

                    # we gather a set of criterial features from the Spec (WH, FOC, REL, TOP)
                    criterial_features = _ps_spec_iterator.sister().get_criterial_features()

                    # Reset memory if there is intervention
                    if self.memory_intervention(criterial_features):
                        self.memory_buffer = []

                    # ...and it has not been moved already...
                    if not _ps_spec_iterator.sister().find_me_elsewhere:
                        # ...and it is not a PHI:0 head...
                        if 'PHI:0' not in h.features:
                            # ...we put a pointer to the specifier into memory buffer.
                            list_.append(_ps_spec_iterator.sister())
                            log(f'\t\t\t\tMoving \"' + _ps_spec_iterator.sister().spellout() + f'\" into memory buffer from SPEC of \"{h}\".')
                        #... if it is a PHI:0 head...
                        else:
                            #...we reconstruct  A-movement (a version of phi-agreement)
                            self.A_reconstruct(_ps_spec_iterator.sister())

                    # If we already have processed one Spec, and there is additional non-adjunct phrase, then we might need phantom heads
                    if spec_found:
                        # If the lower SPEC is adjunct and there are no criterial features in the upper SPEC, we don't do anything
                        if not criterial_features and adjunct_found:
                            adjunct_found = _ps_spec_iterator.sister().adjunct
                        # If the lower SPEC is not an adjunct, or if there are criterial features in the higher SPEC, we need to spawn a head
                        else:
                            # If the second SPEC has no criterial features and is adjunct, we do nothing
                            if not criterial_features and _ps_spec_iterator.sister().adjunct:
                                pass
                            else:
                                if not criterial_features and not _ps_spec_iterator.sister().adjunct:
                                    log(f'\t\t\t\tNew head was spawned due to multiple specifiers at {h}'
                                        ' but its category is unknown!')
                                else:
                                    log(f'\t\t\t\tNew {criterial_features} head was spawned due to '
                                        f'the occurrence of multiple specifiers at {h.get_pf()}')

                                # If we are at finite level, we need to get FIN also to the new head
                                labels = h.get_labels()

                                # Create and merge the new head, then move the pointer over it so we don't repeat
                                new_h = self.engineer_head_from_specifier(criterial_features, labels)
                                _ps_spec_iterator.merge(new_h, 'left')

                                # Move to the new constituent (otherwise we will loop this)
                                _ps_spec_iterator = _ps_spec_iterator.walk_upstream()
                                if new_h.get_tail_sets():
                                    log('\t\t\t\tThe new head has tail features, must be an adjunct floater.')
                                    self.create_adjunct(new_h)

                                    # Drop inside the right-adjunct
                                    if _ps_spec_iterator.mother:
                                        _ps_spec_iterator = _ps_spec_iterator.mother  # Move one step up

                    else:
                        # If its just one Spec, copy criterial features
                        spec_found = True  # We register that one head has been found

                        # Register if it was an adjunct
                        adjunct_found = _ps_spec_iterator.sister().adjunct

                        if criterial_features:
                            log(f'\t\t\t\tCriterial features {criterial_features} copied to {h.get_labels()}')
                            for f in criterial_features:
                                # Create formal copies of features
                                h.features.add('CAT:u' + f)
                                # Add scope marker if needed
                                if 'FIN' in h.get_labels():
                                    h.features.add('CAT:i' + f)
                                h.features = self.lexical_access.apply_parameters(
                                    self.lexical_access.apply_redundancy_rules(h.features))
                            if h.get_tail_sets():
                                log(f'\t\t\t\tTail features ' + illu(
                                    h.get_tail_sets()) + f' were detected at {h}, this must head an adjunct floater.')
                                self.create_adjunct(h)
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
                log(f'\t\t\t\tMemory buffer: {self.memory_buffer}')

    def fill_comp_from_memory(self, h):
        if h.is_primitive() and not h.complement():
            # If H has comp features
            if h.get_comps():
                target_const = None
                for const in self.memory_buffer:
                    for c in h.get_comps():
                        # If suitable candidate exists in the memory buffer
                        if c in const.get_labels() and target_const == None:
                            target_const = const

                if target_const:
                    h.merge(target_const.transfer(self.babtize()), 'right')
                    self.number_of_Moves += 1
                    log(f'\t\t\t\tDropping {repr(target_const)}(=' + target_const.spellout()
                        + f') from memory buffer into Comp of {h.get_labels()}.')
                    log(f'\t\t\t\tResult {h.get_top()}')
                    self.memory_buffer.remove(target_const)
                    log(f'\t\t\t\tRemaining items in memory buffer: {self.memory_buffer}')

        # The head has a non-matching complement and matching item is found from memory
        if h.is_left() and h.complement():
            match_found = False
            target_const = None
            for label in h.complement().get_labels():
                for comp in h.get_comps():
                    if label == comp:
                        match_found = True  # matching H-comp feature was found => don't bring anything from memory
            # look if there is something in MB
            if not match_found:
                for const in self.memory_buffer:
                    for comp in h.get_comps():
                        if comp in const.get_labels() and target_const == None:
                            target_const = const

            if not match_found and target_const:
                log(f'\t\t\t\tDropping {repr(target_const)}(=' + target_const.spellout()
                    + f') from memory buffer into Comp of {h.get_labels()} '
                    f'due to the presence of mismatching complement {h.complement()}.')
                h.complement().merge(target_const.transfer(self.babtize()), 'left')
                self.number_of_Moves += 1
                # The mismatching complement will be demoted to floater status
                if h.complement().right_const.is_adjoinable():
                    log('\t\t\t\tThe mismatching complement will be trasformed into floater adjunct.')
                    self.create_adjunct(h.complement().right_const)
                self.memory_buffer.remove(target_const)
                log(f'\t\t\t\tRemaining memory buffer: {self.memory_buffer}')

    def A_reconstruct(self, ps):
        """
        Implements A-movement from SPEC to the left edge of COMP.

        This is the other side of phi-agreement.
        """
        if 'CAT:D' in ps.get_head().features:
            if ps.sister() and ps.is_left() and not ps.is_primitive():
                log(f'\t\t\t\t{ps} will undergo A-reconstruction (form of Agree).')
                head = ps.sister().get_head()
                if head.is_left():
                    head.sister().merge(ps.transfer(self.babtize()), 'left')
                    self.number_of_Moves += 1
                else:
                    head.sister().merge(ps.transfer(self.babtize()), 'right')
                    self.number_of_Moves += 1

    # This will promote a phi set (if any) into tail features
    def promote_phi_set(self, ps):
        """
        Promotes the phi-set into the status of a tail feature.

        An argument DP can be floated by allowing its phi-features to function as tail-features. When this happens,
        the DP will function like an adverb that tries to link with a functional element containing those phi-
        features. Intuitively, it links DPs with c-commanding heads that share their phi-features. This function
        must be scrutinized later when we add phi-feature mechanisms more generally.
        """

        if ps.get_phi_set():
            new_tail_feature_list = list(ps.get_phi_set())
            new_tail_feature = f'TAIL:{",".join([str(f) for f in sorted(new_tail_feature_list)])},!COMP:*'
            ps.features.add(new_tail_feature)
            return True
        else:
            return False
