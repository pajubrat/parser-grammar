from support import set_logging, log, get_number_of_operations, reset_number_of_operations, log_result, illu
from LexicalInterface import LexicalInterface
import minimalist


class Reconstruction():
    def __init__(self, context):
        self.name_provider_index = 0
        self.memory_buffer = []
        self.context = context

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

        if ps.is_primitive() and ps.has_affix():
            set_logging(False)
            if self.reconstruct_head_movement(ps.copy()).LF_legibility_test().all_pass():
                new = self.reconstruct_head_movement(ps)
                set_logging(True)
                log(f'\t\t\t{ps} was opened.')
                return new
            else:
                set_logging(True)
                log(f'\t\t\t{ps} cannot be opened.')
        else:
            self.reconstruct_head_movement(ps)
            self.reconstruct_floaters(ps)
            self.reconstruct_phrasal_movement(ps)
        return ps

    def reconstruct_head_movement(self, ps):
        log(f'\t\t\t!Reconstructing head movement for {ps}.')
        ps_ = ps
        top = ps

        while ps_:
            # Condition for dealing with phrase
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

    def reconstruct_floaters(self, ps):
        _ps_iterator = ps.get_top()  # Begin from the top and move downstream
        log(f'\t\t\t!Dropping floaters...')

        while _ps_iterator:
            floater = self.detect_floater(_ps_iterator)
            if floater:
                self.drop_floater(floater, ps)
            _ps_iterator = _ps_iterator.walk_downstream()

        log(f'\t\t\t\t= ' + ps.illustrate())

    # Reverse-engineers A-movement and A-bar movement and uses Chesi memory buffer
    def reconstruct_phrasal_movement(self, ps):
        log(f'\t\t\t!Dropping A-/A-bar movement.')
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
        # we have either [XP][HP] or [X HP] with X not selecting for H
        while ps_:
            if ps_.left_const.is_primitive() and ps_.left_const.is_adjoinable() and ps_.sister():
                # If its phrase, then we can select HP
                if not ps_.sister().is_primitive():
                    break
                # If it is head, then we select HP if the head rejects HP as complement
                elif set(ps_.left_const.get_labels()) & set(ps_.sister().get_not_comps()):
                    break
            ps_ = ps_.walk_upstream()

        if ps_:
            # It only applies this rule if there is a verb (V) or D
            # This is LF-requirement: the adjunct must get semantic interpretation
            for head in ps_.left_const.get_feature_vector():
                if 'FIN' in head.get_labels() or 'D' in head.get_labels():
                    ps_.adjunct = True
                    log(f'\t\t\t\t{ps_} was made adjunct by an extraposition rule.')
                    if not ps_.get_top().LF_legibility_test().all_pass():
                        # If phi set is available...
                        if self.promote_phi_set(ps_.left_const):
                            log(f'\t\t\t\tThe structure is still illicit. Try phi-tailing as a last resort.')
                            drop_floaters(ps_.get_top())
                            log(f'\t\t\t\t={ps_.get_top()}')
                    return True

        return False

    # This locates node XP in [T/fin XP] or return the highest node if not found
    # It is required because many operations are restricted by a minimal tense condition
    # e.g. argument/adjunct float
    # todo the implementation is ugly and descriptive this must be re-thought
    # todo we have the same condition in other places but written differently
    def locate_minimal_tense_edge(self, ps):

        ps_iterator_ = ps
        node = ps

        # If we do not detect T/fin... go upwards
        while ps_iterator_ and \
                ps_iterator_.geometrical_sister() and \
                not ps_iterator_.is_finite() and \
                not ps_iterator_.geometrical_sister().is_finite():
            node = ps_iterator_
            ps_iterator_ = ps_iterator_.walk_upstream()

        if not ps_iterator_:
            ps_iterator_ = node

        # If we are inside T/fin..., we need to climb down to XP, [T/Fin XP]
        while ps_iterator_ and ps_iterator_.is_finite():
            node = ps_iterator_
            ps_iterator_ = ps_iterator_.walk_downstream()

        if not ps_iterator_:
            ps_iterator_ = node

        return ps_iterator_

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
            if ps.geometrical_sister() and ps.geometrical_sister().adjunct:
                log(f'\t\t\t\t{ps} cannot be made an adjunct because its sister is an adjunct.')
                return False
            ps.adjunct = True
            log(f'\t\t\t\t{ps} was made an adjunct.')
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
    def engineer_head_from_specifier(self, features):
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
        # We also create artificial phonological matrix for illustration
        for f in features:
            new_h.features.add('CAT:u' + f)
            new_h.features.add('PF:u' + f)
            new_h.features.add('CAT:i' + f)

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

    def fill_spec_from_memory(self, h):

        target_const = None
        if h.mother:
            ps = h.mother
        else:
            ps = h

        if ps.sister() and ps.sister().is_primitive():
            # Select the first possible Spec constituent from memory buffer
            for const in self.memory_buffer:
                if self.spec_match(h, const) and not target_const:
                    target_const = const
            # Transfer it from memory buffer into the phrase structure
            if target_const:
                # Try to merge it to Spec
                ps.merge(target_const.transfer(self.babtize()), 'left')
                # Check that this does not cause tail-head violations
                if ps.geometrical_sister().get_head().external_tail_head_test():
                    log(f'\t\t\t\tDropping constituent {target_const} from memory buffer into Spec of ' +
                        f'{h}')
                    self.memory_buffer.remove(target_const)
                else:
                    # If there was a tail-head violation, dropping is cancelled
                    ps.geometrical_sister().remove()

    def store_specs_into_memory(self, h):
        if h.EPP():

            _ps_iterator = h.mother

            # spec-iterator iterated over multiple Specs (if possible) into upward direction
            _ps_spec_iterator = _ps_iterator
            list_ = []
            spec_found = False
            while _ps_spec_iterator:

                # If a phrase is found from left...
                if _ps_spec_iterator.sister() and \
                        not _ps_spec_iterator.sister().is_primitive() and \
                        _ps_spec_iterator.sister().is_left():

                    # we gather criterial features from the Spec (WH, FOC, REL, TOP)
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
                            log(
                                f'\t\t\t\tMoving \"' + _ps_spec_iterator.sister().spellout() + f'\" into memory buffer from SPEC of \"{h}\".')
                        #... if it is a PHI:0 head...
                        else:
                            #...we reconstruct  A-movement (a version of phi-agreement)
                            self.A_reconstruct(_ps_spec_iterator.sister())


                    # If we already have processed one Spec, then we are gonna need to spawn phantom heads
                    if spec_found:

                        if not criterial_features:
                            log(f'\t\t\t\tNew head was spawned due to multiple specifiers at {h}'
                                ' but its category is unknown!')
                        else:
                            log(f'\t\t\t\tNew {criterial_features} head was spawned due to '
                                f'the occurrence of multiple specifiers at {h.get_pf()}')

                        # Create and merge the new head, then move the pointer over it so we don't repeat
                        new_h = self.engineer_head_from_specifier(criterial_features)
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
                        if criterial_features:
                            log(f'\t\t\t\tCriterial features {criterial_features} copied to {h_labels}')
                            for f in criterial_features:
                                # Create formal copies of features
                                h.features.add('CAT:u' + f)
                                # Add scope marker if needed, todo this looks stipulative in the present form
                                if 'C/fin' in h.get_labels() or 'T/fin' in h.get_labels() or 'FORCE' in h.get_labels():
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
                # The mismatching complement will be demoted to floater status
                if h.complement().right_const.is_adjoinable():
                    log('\t\t\t\tThe mismatching complement will be trasformed into floater adjunct.')
                    self.create_adjunct(h.complement().right_const)
                self.memory_buffer.remove(target_const)
                log(f'\t\t\t\tRemaining memory buffer: {self.memory_buffer}')

    def drop_head(self, ps, affix_):
        def drop_condition_for_heads(affix_):
            if affix_.get_selector() and (set(affix_.get_selector().get_comps()) & set(affix_.get_cats())):
                if '!SPEC:*' not in affix_.features:
                    return True
                else:
                    if affix_.specifier():
                        return True
                    else:
                        return False
            else:
                return False

        iterator_ = ps

        while iterator_:
            iterator_.merge(affix_, 'left')  # We try a solution
            if drop_condition_for_heads(affix_):
                return True
            else:
                affix_.remove()
                iterator_ = iterator_.walk_downstream()
        return False

    def A_reconstruct(self, ps):
        """
        Implements A-movement from SPEC to the left edge of COMP.

        This is the other side of phi-agreement.
        """
        if 'CAT:D' in ps.get_head().features:
            if ps.sister() and ps.is_left() and not ps.is_primitive():
                log(f'\t\t\t\t{ps} will undergo A-reconstruction (form of Agree).')
                if not ps.sister().is_primitive():
                    ps.sister().right_const.merge(ps.transfer(self.babtize()), 'left')
                else:
                    ps.sister().merge(ps.transfer(self.babtize()), 'right')

    def detect_floater(self, _ps_iterator):
        # Check if a phrase at the left requires reconstruction
        if not _ps_iterator.is_primitive() and \
                not _ps_iterator.left_const.is_primitive() and \
                not _ps_iterator.left_const.find_me_elsewhere and \
                _ps_iterator.left_const.get_head().get_tail_sets():
            floater = _ps_iterator.left_const
            # Also check if its tail features fail to find a head
            if not floater.get_head().external_tail_head_test():
                log('\t\t\t\t' + floater.illustrate() + ' failed to tail ' + illu(
                    floater.get_head().get_tail_sets()))
                # Target the floater
                return floater

            # Or if it (constituent with tail features) sits in an EPP SPEC position of a finite clause edge
            elif floater.mother and floater.mother.get_head().EPP() and floater.mother.is_finite():
                log('\t\t\t\t' + floater.illustrate() + ' is in an EPP SPEC position.')
                return floater

        # Check if the right edge itself has tail features (e.g. DP at the bottom, floaters/adjuncts)
        if not _ps_iterator.is_primitive() and \
                _ps_iterator.right_const.get_head().get_tail_sets():
            floater = _ps_iterator.right_const.get_head()
            # If tail features fail to find a head, the constituent must be dropped
            if not floater.external_tail_head_test():
                log('\t\t\t\t' + floater.illustrate() + ' failed to tail.')
                # This is empirically very contentious matter:
                # A right DP inside a finite clause with failed tail-test must be an adjunct(?)
                if 'D' in floater.get_labels() and floater.get_top().contains_feature('CAT:T/fin'):
                    self.create_adjunct(floater)
                    return floater.mother
            else:
                if 'ADV' in floater.get_labels() and not _ps_iterator.right_const.adjunct:
                    self.create_adjunct(floater)

    # Drops one floater that is targeted fro dropping
    def drop_floater(self, floater, ps):

        Tfin = None
        T_fin_intervention = False

        # We need to locate the appropriate starting point, the node XP in [T/fin XP]
        ps_iterator_ = self.locate_minimal_tense_edge(floater.mother)
        floater_copy = floater.copy()

        # This downward loop searches a position for the floater
        while not T_fin_intervention and ps_iterator_ and not ps_iterator_ == floater and not ps_iterator_.find_me_elsewhere:

            # Determine if T/fin intervenes (blocks further downward search)
            if ps_iterator_.sister() and 'T/fin' in ps_iterator_.sister().get_labels():
                if not Tfin:
                    Tfin = ps_iterator_.sister().get_head()
                else:
                    if not ps_iterator_.sister().get_head() == Tfin:
                        T_fin_intervention = True

            # Create hypothetical structure for testing
            if 'ADV' in floater_copy.get_labels():
                ps_iterator_.merge(floater_copy, 'right')
            else:
                ps_iterator_.merge(floater_copy, 'left')

            # If a suitable position is found, dropping will be executed
            if floater_copy.get_head().external_tail_head_test():
                self.create_adjunct(floater)
                dropped_floater = floater.transfer(self.babtize())
                if 'ADV' in floater_copy.get_labels() or 'P' in floater_copy.get_labels():
                    ps_iterator_.merge(dropped_floater, 'right')
                else:
                    ps_iterator_.merge(dropped_floater, 'left')
                floater_copy.remove()
                floater.find_me_elsewhere = True
                log(f'\t\t\t\tFloater ' + dropped_floater.illustrate() + ' dropped.')
                return
            else:
                floater_copy.remove()

            ps_iterator_ = ps_iterator_.walk_downstream()

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