from support import set_logging, log, get_number_of_operations, reset_number_of_operations, log_result, illu
from LF import LF
from adjunct_constructor import AdjunctConstructor


class Extraposition:
    def __init__(self, controlling_parser_process):
        self.LF_access = LF()
        self.adjunct_constructor = AdjunctConstructor(controlling_parser_process)
        self.controlling_parser_process = controlling_parser_process

    def reconstruct(self, ps):
        set_logging(False)
        self.LF_access.test(ps)
        set_logging(True)

        if not self.LF_access.wrong_complement_test_result:
            log(f'\t\t\t\t\t{ps} contains wrong head selection. Extraposition will be tried.')
            set_logging(False)
            self.try_extraposition(ps)
            set_logging(True)

    # Definition for extraposition
    # Presupposition 1. LF-legibility fails (checked before call)
    # Presupposition 2. Only target branches which are "referential" (T/fin, D)
    # Condition 1. Find first [H XP] from bottom such that
    # Condition 2. H is adjoinable and
    # Condition 3. Either (i) [XP][HP] or (ii) [X HP] with X not selecting for H

    def try_extraposition(self, ps):
        # Returns the bottom node on the right edge (not geometrical)

        # Presupposition 2
        # Extraposition can be attempted only for "referential" structures (T/fin, D)
        if not (ps.get_top().contains_feature('CAT:FIN') or 'D' in ps.get_top().get_labels()):
            return

        log(f'\t\t\t\t\tExtraposition will be tried on {ps.get_top()}.')
        ps_ = self.get_bottom(ps).mother

        while ps_:
            # Condition 1. Find first [H XP] (=ps_) such that
            # Condition 2. H is adjoinable and
            if ps_.left_const.is_primitive() and ps_.left_const.is_adjoinable() and ps_.sister():
                # If its phrase, then we can select HP (=i)
                # Condition 3.
                # Condition (3i) [XP][HP]
                if not ps_.sister().is_primitive():
                    break
                else:
                    # Condition 3(ii). [X HP] with X not selecting for H (HP = ps_)
                    if ps_.left_const.get_labels() & ps_.sister().get_not_comps():
                        break
            ps_ = ps_.walk_upstream()

        if ps_:
            # This is LF-requirement: the adjunct must get semantic interpretation
            for head in ps_.left_const.get_feature_vector():
                if 'FIN' in head.get_labels() or 'D' in head.get_labels():
                    self.adjunct_constructor.create_adjunct(ps_.get_head())
                    log(f'\t\t\t\t\t{ps_} was made adjunct by an extraposition rule.')
                    if not ps_.get_top().LF_legibility_test().all_pass():
                        # If phi set is available...
                        log(f'\t\t\t\t\tThe structure is still illicit! Try phi-tailing as a last resort?')
                        # self.drop_floater(ps_.get_top())
                        # log(f'\t\t\t\t={ps_.get_top()}')

                    return True
        return False

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

