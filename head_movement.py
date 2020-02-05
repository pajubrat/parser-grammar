from support import set_logging, log, get_number_of_operations, reset_number_of_operations, log_result, illu
from LexicalInterface import LexicalInterface
import phrase_structure


class HeadMovement:
    def __init__(self, controlling_parser_process):
        self.controlling_parser_process = controlling_parser_process
        self.name_provider_index = 0
        self.memory_buffer = []
        self.number_of_Moves = 0

        # Access to the lexicon
        self.lexical_access = LexicalInterface(self.controlling_parser_process)
        self.lexical_access.load_lexicon(self.controlling_parser_process)

    # Definition of head movement reconstruction (part 1)
    def reconstruct(self, ps):

        self.number_of_Moves = 0

        # Condition 1. If the target is a complex primitive D head, we try to open it into a new left branch
        if ps.is_primitive() and ps.has_affix() and ('CAT:D' in ps.features or 'CAT:P' in ps.features):

            # If the element is D or P, it is opened into a new left branch
            if self.reconstruct_head_movement(ps.copy()).LF_legibility_test().all_pass():
                new = self.reconstruct_head_movement(ps)
                set_logging(True)
                log(f'\t\t\t\t\t{ps} was opened into {new}.')
                return new, self.number_of_Moves
            else:
                set_logging(True)
                log(f'\t\t\t\t\t{ps} was not opened into left branch, it would not constitute a legitimate left branch at LF.')

        # Condition 2. If the target is a non-D head, we reconstruct head movement inside it
        else:
            if ps.is_complex():
                ps = self.reconstruct_head_movement(ps)

        return ps, self.number_of_Moves

    # Recursive definition of head movement reconstruction (part 2)
    def reconstruct_head_movement(self, ps):
        ps_ = ps
        top = ps

        # Move downwards and locate heads that require reconstruction
        while ps_:

            # Condition 1. The target is a phrase with a complex head at left
            if ps_.left_const and ps_.left_const.is_primitive() and ps_.left_const.has_affix():

                source_head = ps_.left_const

                # Get the highest affix out
                affix = source_head.get_affix()
                source_head.right_const = None

                log(f'\t\t\t\t\tTarget {affix} in {source_head}')

                # Drop the affix
                self.drop_head(ps_.right_const, affix)

            # Condition 2. The target is a primitive element
            elif ps_.is_primitive and ps_.has_affix():
                affix = ps_.get_affix()
                new_ps = ps_ + affix
                ps_.right_const = None
                top = new_ps

                # We are creating a new phrase structure [A B] and need to return that
                top = new_ps.get_top()

                # Condition 2b. If the affix has another affix inside, we reconstruct it recursively
                # This has the effect that all heads are always spread out
                if affix.has_affix():
                    self.reconstruct_head_movement(affix)

            ps_ = ps_.walk_downstream()

        return top

    # Definition for dropping a head
    def drop_head(self, ps, affix_):

        # Defines the conditions for dropping a head into a position X
        def drop_condition_for_heads(affix_):

            # Check if the head is correctly selected at this position
            if affix_.get_selector() and affix_.get_selector().selects(affix_):

                # If it does not require a SPEC, we accept this position
                if not affix_.EPP():
                    return True  # If the affix has no EPP, we accept the solution

                # If it requires SPEC...
                else:
                    # we accept the solution is the local specifier is complex phrase
                    # (we must ignore pro-solution here)
                    if affix_.get_local_specifier() and affix_.get_local_specifier().is_complex():  # If the EPP is satisfied, we accept the solution
                        return True

                    # What if the EPP is satisfied later by movement reconstruction?
                    # First exception: [affix, b], b is primitive
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

        # --------------- main function ---------------------------------

        iterator_ = ps

        # walk downwards looking for possible dropping positions
        while iterator_:
            self.number_of_Moves += 1

            # Try each solution
            iterator_.merge(affix_, 'left')

            # If the drop condition is satisfied, then we leave the head and return
            if drop_condition_for_heads(affix_):
                log(f'\t\t\t\t\t={ps.get_top()}')
                return True
            else:

                # Remove the head and go next step downwards
                affix_.remove()
                iterator_ = iterator_.walk_downstream('CAT:D')

        # Special condition 1: bottom right position
        # Condition 1.1. If the bottom node is complex, we must open it first
        if ps.get_bottom().has_affix():
            self.reconstruct_head_movement(ps.get_bottom())
            # Condition 1.2 If the bottom node was DP, we don't merge to the sister of N but to the DP...
            if 'CAT:D' in ps.get_bottom().get_labels():
                ps.get_bottom().mother.merge(affix_, 'right')
            else:
                # Condition 1.2. ...Otherwise we merge to the sister.
                ps.get_bottom().merge(affix_, 'right')
        else:
            # If the bottom node is simple, we try to merge to its right
            ps.get_bottom().merge(affix_, 'right')

        # Test if the solution is accetable
        if drop_condition_for_heads(affix_):
            return True
        else:
            # If the solution is not accetable, we remove the candidate
            affix_.remove()

        # Special condition 2: what to do if head reconstruction doesn't find any position?
        # This will merge it to the local position as a last resort
        log(f'\t\t\t\t\tHead reconstruction failed for {affix_}, merged locally as a last resort.')
        ps.merge(affix_, 'left')
        # We need to reconstruct head movement for the left branch
        return True
