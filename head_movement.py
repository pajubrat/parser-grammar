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

    # Definition for head movement reconstruction
    #
    # Adopts head reconstruction either (1) left or (2) downstream
    # Alternative 1. A(B) C => [[A B] C]
    #   Used if primitive A(B) is targeted for reconstruction and conditions 1-3 (below) are satisfied,
    #   otherwise primitive elements are not reconstructed into left branches independently.
    # Alternative 2. A(B) C => [A [B C]]
    #   Applies when head reconstruction is applied to a complex phrase XP, and heads are
    #   reconstructed inside XP.
    #
    def reconstruct(self, ps):
        # Alternative 1. Reconstruct X(Y) into left if and only if
        # Condition 1. X has an affix and is primitive
        # Condition 2. X is D, P or A.
        # Condition 3. [X Y] passes LF-legibility
        #
        # Condition 1. X has an affix and is primitive
        if ps.is_primitive() and ps.has_affix():

            # Condition 2. X is D, P or A
            if 'D' in ps.features or 'P' in ps.features or 'A' in ps.features:

                # Condition 3. [X Y] passes LF-legibility
                if self.reconstruct_head_movement(ps.copy()).LF_legibility_test().all_pass():
                    new = self.reconstruct_head_movement(ps)
                    set_logging(True)
                    log(f'\t\t\t\t\t{ps} was opened into {new}.')
                    return new
                else:
                    set_logging(True)
                    log(f'\t\t\t\t\t{ps} was not opened into left branch, it would not constitute a legitimate left branch at LF.')

        # Alternative 2. Reconstruct complex phrase
        else:
            if ps.is_complex():
                ps = self.reconstruct_head_movement(ps)

        return ps

    # Iterative definition for head movement reconstruction inside XP
    #
    # Move downstream from XP.
    #
    # H is targeted for head reconstruction if and only if
    # Condition 1. H is primitive, has an affix, as is left [H(A) K], or
    # Condition 1'. X(P) = primitive head (bottom head).
    # Condition 2. Intervention feature is determined by the nature of H:
    #   Condition 2a)   If H has OP, intervention = D
    #   Condition 2b)   otherwise intervention = !COMP* (any functional head)
    # Reconstruction itself is defined in drop_head()
    def reconstruct_head_movement(self, ps):
        ps_ = ps
        top = ps

        # ----------------------while loop begins---------------------------------------------#
        # Move downstream
        while ps_:

            # Condition 1. H is primitive, has an affix, as is left, i.e. [H(A) K]
            if ps_.left_const and ps_.left_const.is_primitive() and ps_.left_const.has_affix():

                source_head = ps_.left_const
                affix = source_head.get_affix()
                source_head.right_const = None
                log(f'\t\t\t\t\tTarget {affix} inside complex head {source_head} for head reconstruction.')

                # Condition 2. Intervention feature is determined by the nature of H:
                # Condition 2a) If H has OP (C* feature), intervention = D
                if source_head.has_op_feature():
                    intervention_feature = 'D'
                # Condition 2b) otherwise intervention = !COMP* (any functional head)
                else:
                    intervention_feature = '!COMP:*'

                self.controlling_parser_process.number_of_head_Move += 1

                # Drop the head
                # ps_ = [H B], H is the head from which we reconstruct, B is where we start reconstruction
                # affix = affix to be reconstructed
                # intervention feature (see Condition 3 above)
                self.create_head_chain(ps_.right_const, affix, intervention_feature)

            # Condition 1', special case: X(P) = primitive head (bottom head)
            # [X H(K)] => [X [H K]]
            elif ps_.is_primitive and ps_.has_affix():
                affix = ps_.get_affix()     # K from H(K)
                new_ps = ps_ + affix        # Merge [H(K) K]
                ps_.right_const = None      # [H K]
                top = new_ps.top()
                # If the affix has another affix inside, we reconstruct it recursively
                # [H K(L)] = [H [K L]]
                if affix.has_affix():
                    self.reconstruct_head_movement(affix)

            ps_ = ps_.walk_downstream()
            # -----------------------while loop ends-----------------------------------------#

        return top

    # Definition for head chain creation
    # Condition 1. Walk downstream and try each solution to the left
    # Condition 2. If solution is found, accept it and return
    # Condition 3. If solution is not found, then we do one of the two things:
    #   3a) If there was intervention, we use last resort strategy
    #   3b) If we reached bottom, we can try Merge Right solution, and then (3a)
    def create_head_chain(self, ps, affix_, intervention_feature):

        iterator_ = ps
        reached_bottom = False

        # ------------------- while loop begins -----------------------------#
        while iterator_:

            # Try each solution [H X(P)], H = reconstructed head
            iterator_.merge(affix_, 'left')

            # If [H X(P) is accepted, we leave the solution into the tree
            if self.drop_condition_for_heads(affix_):
                log(f'\t\t\t\t\t={ps.top()}')
                return True
            else:
                # If [H X(P)] is not accepted, we remove the head and continue
                affix_.remove()
                if iterator_.is_primitive():
                    reached_bottom = True
                iterator_ = iterator_.walk_downstream(intervention_feature)
        # --------------------- while loop end ------------------------------#

        # Condition 3. Definition for what happens if we reach the bottom (termination not due to intervention)
        if reached_bottom:
            # If the bottom node is X(Y), we open it to determine if this creates a position for the reconstructed head H
            if ps.bottom().has_affix():
                self.reconstruct_head_movement(ps.bottom())
                ps_ = ps.bottom().mother  # keep the pointer at [X Y] after X(Y) => [X Y]
                # In the case of D(N), we try solution [DP H]
                if 'D' in ps_.head().features:
                    ps_.merge(affix_, 'right')  # [DP H]
                # In the case something else than D(N), we try solution [X [Y H]]
                else:
                    if intervention_feature not in ps_.left_const.head().features:
                        ps.bottom().merge(affix_, 'right')  # [X [Y H]]
            # If the bottom node is simple X, and X does not intervene,  try to merge to its right
            else:
                if intervention_feature not in ps.bottom().features:
                    ps.bottom().merge(affix_, 'right')  # [X H]

            # Test if any solution created above is accepted
            if affix_.mother:
                # Test if the solution is acceptable
                if self.drop_condition_for_heads(affix_):
                    return True
                else:
                    # If the solution is not acceptable, we remove the candidate
                    affix_.remove()

        # Special condition 3: No position was found (e.g., intervention)
        # Merge to the local position as a last resort
        # [X(Y) K] = [X [K [Y ...]]]
        log(f'\t\t\t\t\tHead reconstruction failed for {affix_}, merged locally as a last resort.')
        if ps.right_const:
            ps.merge(affix_, 'left')
        else:
            ps.merge(affix_, 'left')
        return True

    # Defines the conditions for dropping a head H into a position X
    # Condition 1. H is selected by a higher head in position X and H does not require SPEC, or
    # Condition 2. If it does require SPEC, then H has suitable edge/specifier at the position, with three exceptions:
    #   Exception A to 2. Finnish third person exception
    #   Exception B to 2. [affix, b], b is primitive
    #   Exception C to 2. If there is complex left sister, we can accept the solution
    def drop_condition_for_heads(self, affix_):

        # Condition 1. The head is selected at this position by a higher head...
        if affix_.selector() and affix_.selector().selects(affix_):

            # Condition 2. If the head is finite EPP head, further conditions apply
            #
            # Note: These conditions have the effect that head movement is done in such a way that the finite EPP
            # feature could be satisfied, since often there is no later mechanism that could do it. The code looks
            # messy and arbitrary, so there is presumably something else involved.
            if affix_.EPP() and affix_.finite():

                # Condition 2a. Accept if a local specifier (incl. pro) is found that satisfies finite EPP
                if affix_.local_edge():
                    # Exception A. Finnish third person T (deficient agreement does not constitute edge here)
                    if 'pro' in affix_.local_edge().features and 'PHI:PER:3' in affix_.local_edge().features:
                        return False
                    else:
                        return True

                # Exception B. Affix A is finite EPP head in [A, K] or [K A], K primitive, but nothing at the edge, solution is accepted
                elif affix_.sister() and affix_.sister().is_primitive() and not affix_.sister().get_affix():
                    return True
                elif affix_.sister() and affix_.sister().left_const and affix_.sister().left_const.is_primitive() and not affix_.sister().left_const.get_affix():
                    return True
                else:
                    # Exception C. [K(L) affix] is accepted without specifier/edge, affix = finite EPP head
                    if affix_.sister() and not affix_.sister().is_primitive() and affix_.sister().is_left():
                        return True
                    else:
                        return False
            else:
                # Condition 1. H is selected by a higher head in this position and is not finite EPP head
                return True

        # If H is not selected, the solution cannot be accepted (no matter what other conditions hold)
        else:
            return False

