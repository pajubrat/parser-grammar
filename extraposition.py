from support import set_logging, log, get_number_of_operations, reset_number_of_operations, log_result, illu
from LF import LF
from adjunct_constructor import AdjunctConstructor


class Extraposition:
    def __init__(self, controlling_parser_process):
        self.LF_access = LF()
        self.adjunct_constructor = AdjunctConstructor(controlling_parser_process)
        self.controlling_parser_process = controlling_parser_process

    def reconstruct(self, ps):

        # Extraposition can be attempted only for "referential" structures (T/fin, D)
        if not (ps.get_top().contains_feature('CAT:FIN') or 'D' in ps.get_top().get_labels()):
            return

        # Extraposition for unselected heads (i.e. *X selects Y)
        unselected_head = self.find_selection_violation(ps)
        if unselected_head:
            self.try_extraposition(unselected_head)

    def try_extraposition(self, unselected_head):
        log(f'\t\t\t\t\tExtraposition will be tried on {unselected_head.mother}.')
        self.adjunct_constructor.create_adjunct(unselected_head)
        return True

    # This will promote a phi set (if any) into tail features
    # (Not correct, only relates to Italian postverbal subjects.)
    def promote_phi_set(self, ps):

        if ps.get_phi_set():
            new_tail_feature_list = list(ps.get_phi_set())
            new_tail_feature = f'TAIL:{",".join([str(f) for f in sorted(new_tail_feature_list)])},!COMP:*'
            ps.features.add(new_tail_feature)
            return True
        else:
            return False

    def get_bottom(self, ps):
        iterator_ = ps
        while iterator_:
            if iterator_.is_primitive():
                return iterator_
            else:
                iterator_ = iterator_.walk_downstream()
        return

    def find_selection_violation(self, ps):
        ps_ = ps
        selectee = None
        while ps_:
            if ps_.is_complex():
                selector = ps_.left_const
                not_comps = selector.get_not_comps()
                selectee = ps_.right_const.get_head()
                if not_comps & selectee.get_labels():
                    return selectee
            ps_ = ps_.walk_downstream()
        return None

        # Definition for extraposition

    def last_resort_reconstruct(self, ps):

        # Presupposition 1
        # LF - legibility fails (last resort)
        if ps.get_top().LF_legibility_test().all_pass():
            return

        # Presupposition 2
        # Do this only for referential structures (T/fin, D)
        if not (ps.get_top().contains_feature('CAT:FIN') or 'D' in ps.get_top().get_labels()):
            return

        log(f'\t\t\t\t\tLast resort extraposition will be tried on {ps.get_top()}.')

        ps_ = self.get_bottom(ps).mother

        # Find first [H XP] where H is adjoinable and
        # we have either (i) [XP][HP] or (ii) [X HP] with X not selecting for H,
        # then try is HP could be an adjunct
        while ps_:
            # If (i), we select HP (=ps_)
            if ps_.left_const.is_primitive() and ps_.left_const.is_adjoinable() and ps_.sister():
                if ps_.sister().is_complex():
                    break

                # (ii) If X HP, then select HP if and only if the head rejects HP as complement
                else:
                    # Explicit non-selection
                    if ps_.left_const.get_labels() & ps_.sister().get_not_comps():
                        break
                    # Mandatory selection for something else
                    if ps_.sister().get_mandatory_comps() and not (
                            ps_.left_const.get_labels() & ps_.sister().get_mandatory_comps()):
                        break
            ps_ = ps_.walk_upstream()

        # If a suitable node was found, we try to turn it into an adjunct
        if ps_:
            # Presupposition 1. The adjunct must be interpretable
            # (This is like presupposition 2 but I will leave it here for now)
            for head in ps_.left_const.get_feature_vector():
                if 'FIN' in head.get_labels() or 'D' in head.get_labels():
                    self.adjunct_constructor.create_adjunct(ps_)
                    if not ps_.get_top().LF_legibility_test().all_pass():
                            log(f'\t\t\t\t\tThe structure is still uninterpretable!')
                    return True
        else:
            log(f'\t\t\t\t\tNo suitable node for extraposition found; no action was taken.')
        return False





