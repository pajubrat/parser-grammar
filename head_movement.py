from support import set_logging, log, get_number_of_operations, reset_number_of_operations, log_result, illu
from LexicalInterface import LexicalInterface
import minimalist

class HeadMovement():
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
        Performs head movement reconstruction.
        """

        self.number_of_Moves = 0

        if ps.is_primitive() and ps.has_affix():
            if self.reconstruct_head_movement(ps.copy()).LF_legibility_test().all_pass():
                if 'CAT:D' in ps.features or 'CAT:P' in ps.features:
                    new = self.reconstruct_head_movement(ps)
                    set_logging(True)
                    log(f'\t\t\t\t\t{ps} was opened into {new}.')
                    return new, self.number_of_Moves
                else:
                    log(f'\t\t\t\t\t{ps} was not opened because it is not DP.')
            else:
                set_logging(True)
                log(f'\t\t\t\t\t{ps} was not opened because it would not constitute a legitimate left branch at LF.')
        else:
            self.reconstruct_head_movement(ps)

        return ps, self.number_of_Moves

    def reconstruct_head_movement(self, ps):
        log(f'\t\t\t\t\tReconstructing head movement for {ps}.')
        ps_ = ps
        top = ps

        while ps_:
            # Condition when the head is part of a complex phrase structure
            if ps_.left_const and ps_.left_const.is_primitive() and ps_.left_const.has_affix():
                affix = ps_.left_const.get_affix()
                if self.drop_head(ps_.right_const, affix):
                    ps_.left_const.right_const = None
                    log(f'\t\t\t\t\t\tExtracted head \"{affix}\" and reconstructed it = {ps_.get_top()}')
                else:
                    log(f'\t\t\t\t\t\tHead reconstruction failed for {affix}.')
            # Condition for dealing with primitive element
            elif ps_.is_primitive and ps_.has_affix():
                affix = ps_.get_affix()
                new_ps = ps_ + affix
                ps_.right_const = None
                top = new_ps
                log(f'\t\t\t\t\tExtracted head \"{affix}\" from {ps_} and created {new_ps}')
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
