from support import set_logging, log, get_number_of_operations, reset_number_of_operations, log_result, illu
from LexicalInterface import LexicalInterface
import phrase_structure


class HeadMovement:
    def __init__(self, controlling_parser_process):
        self.controlling_parser_process = controlling_parser_process
        self.name_provider_index = 0
        self.memory_buffer = []

        # Access to the lexicon
        self.lexical_access = LexicalInterface(self.controlling_parser_process)
        self.lexical_access.load_lexicon(self.controlling_parser_process)

    # Definition of head movement reconstruction (part 1)
    def reconstruct(self, ps):
        # Condition 1. If the target is a complex primitive D, P or A head, we try to open it into a new left branch
        if ps.is_primitive() and ps.has_affix() and \
                ('D' in ps.features or 'P' in ps.features or 'A' in ps.features):

            if self.reconstruct_head_movement(ps.copy()).LF_legibility_test().all_pass():
                new = self.reconstruct_head_movement(ps)
                set_logging(True)
                log(f'\t\t\t\t\t{ps} was opened into {new}.')
                return new
            else:
                set_logging(True)
                log(f'\t\t\t\t\t{ps} was not opened into left branch, it would not constitute a legitimate left branch at LF.')

        # Condition 2. If the target is a non-D head, we reconstruct head movement inside it
        else:
            if ps.is_complex():
                ps = self.reconstruct_head_movement(ps)

        return ps

    # Recursive definition of head movement reconstruction (part 2)
    def reconstruct_head_movement(self, ps):
        ps_ = ps
        top = ps

        # Move downwards and locate heads that require reconstruction
        while ps_:

            # Condition 1. The target is a phrase with a complex head at left
            if ps_.left_const and ps_.left_const.is_primitive() and ps_.left_const.has_affix():

                # Set the source head from which we extract
                source_head = ps_.left_const

                # Get the highest affix out
                affix = source_head.get_affix()
                source_head.right_const = None

                log(f'\t\t\t\t\tTarget {affix} inside complex head {source_head} for head reconstruction.')

                # Condition 2. Intervention feature (A-bar versus A-system)
                # Condition 2.1. D-label in the C-system
                if source_head.has_op_feature():
                    intervention_feature = 'D'  # This is in reality a more general feature, but I don't know what
                # Condition 2.2. Functional head elsewhere
                else:
                    intervention_feature = '!COMP:*'

                # Keep record of the computational operations consumed
                self.controlling_parser_process.number_of_head_Move += 1

                # Drop the head
                self.drop_head(ps_.right_const, affix, intervention_feature)

            # Condition 2. The target is a primitive element
            elif ps_.is_primitive and ps_.has_affix():
                affix = ps_.get_affix()
                new_ps = ps_ + affix
                ps_.right_const = None

                # We are creating a new phrase structure [A B] and need to return that
                top = new_ps.top()

                # Condition 2b. If the affix has another affix inside, we reconstruct it recursively
                # This has the effect that all heads are always spread out
                if affix.has_affix():
                    self.reconstruct_head_movement(affix)

            ps_ = ps_.walk_downstream()

        return top

    # Definition for dropping a head
    def drop_head(self, ps, affix_, intervention_feature):

        #
        # Internal functions
        #
        # Defines the conditions for dropping a head H into a position X
        # Condition 1. H is selected by a higher head in position X and H does not require SPEC
        # Condition 2. If it does require SPEC, then H has suitable edge/specifier at the position. three exceptions:
        # Exception A to 2. Finnish third person exception
        # Exception B to 2. [affix, b], b is primitive
        # Exception C to 2. If there is complex left sister, we can accept the solution
        def drop_condition_for_heads(affix_):

            # Condition 1. The head is selected at this position by a higher head...
            if affix_.selector() and affix_.selector().selects(affix_):
                # ...and does not require a formal SPEC, we accept this position
                if not affix_.EPP() or ('T/fin' not in affix_.features and 'Neg/fin' not in affix_.features):
                    return True  # If the affix has no EPP, we accept the solution

                # Condition 2. If it requires SPEC,
                else:
                    # Condition 2a. We accept the solution if the local specifier (incl. pro) is found
                    if affix_.local_edge():
                        # Exception A. Finnish third person T (deficient agreement does not constitute edge here)
                        # Note: this follows from a more general principle that I do not know, 3sg is deficient.
                        if 'pro' in affix_.local_edge().features and 'PHI:PER:3' in affix_.local_edge().features:
                            return False
                        else:
                            return True

                    # Exception B. [affix, b], b is primitive
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

                        # Exception C. If there is complex left sister, we can accept the solution
                        if affix_.sister() and not affix_.sister().is_primitive() and affix_.sister().is_left():
                            return True
                        else:
                            return False
            else:
                return False

        # --------------- main function ---------------------------------

        # This function, although empirically correct, is written in a clumsy way and must cleaned
        # The logic is: 1. Walk downstream and try each solution to the left
        #               2. If solution is found, accept it and return
        #               3. If solution is not found, then we do one of the two things:
        #                   a. If there was intervention, we use last resort strategy
        #                   b. If we reached bottom, we can try Merge Right solution, and then (a)

        iterator_ = ps
        reached_bottom = False

        # Walk downwards looking for possible dropping positions
        while iterator_:

            # Try each solution
            iterator_.merge(affix_, 'left')
            # If the drop condition is satisfied, then we leave the head and return
            if drop_condition_for_heads(affix_):
                log(f'\t\t\t\t\t={ps.top()}')
                return True
            else:
                # Remove the head and go next step downwards
                affix_.remove()
                if iterator_.is_primitive():
                    reached_bottom = True
                iterator_ = iterator_.walk_downstream(intervention_feature)

        # If we come here, we have reached the bottom or search was interrupted
        # If we reached bottom, then we can try Merge Right solution
        if reached_bottom:
            # Special condition 1: bottom right position
            # Condition 1.1 If the node has affix, we must open it first
            if intervention_feature not in ps.bottom().features:
                if ps.bottom().has_affix():
                    self.reconstruct_head_movement(ps.bottom())
                    ps_ = ps.bottom().mother  # keep the pointer at [D,N] after D(N) => [D N]
                    if 'D' in ps_.head().features:
                        ps_.merge(affix_, 'right')
                    else:
                        # Condition 1.4. ...Otherwise we merge to the sister.
                        ps.bottom().merge(affix_, 'right')
                else:
                    # If the bottom node is simple, we try to merge to its right
                    ps.bottom().merge(affix_, 'right')

            # Special condition 2: if the affix was merged to the right of the bottom node, we check if it is accetable
            if affix_.mother:
                # Test if the solution is acceptable
                if drop_condition_for_heads(affix_):
                    return True
                else:
                    # If the solution is not acceptable, we remove the candidate
                    affix_.remove()

        # Special condition 3: No position was found
        # Merge to the local position as a last resort
        log(f'\t\t\t\t\tHead reconstruction failed for {affix_}, merged locally as a last resort.')
        if ps.right_const:
            ps.merge(affix_, 'left')
        else:
            ps.merge(affix_, 'left')
        # We need to reconstruct head movement for the left branch
        return True
