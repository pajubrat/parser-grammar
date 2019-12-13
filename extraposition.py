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



