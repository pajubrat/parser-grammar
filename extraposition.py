from support import set_logging, log, get_number_of_operations, reset_number_of_operations, log_result, illu
from LF import LF
from adjunct_constructor import AdjunctConstructor


class Extraposition:
    def __init__(self, controlling_parser_process):
        self.LF_access = LF()
        self.adjunct_constructor = AdjunctConstructor(controlling_parser_process)
        self.controlling_parser_process = controlling_parser_process

    def reconstruct(self, ps):

        # Presupposition 1. Extraposition can be attempted only for "referential" structures (T/fin, D)
        if not (ps.top().contains_feature('CAT:FIN') or 'D' in ps.top().features):
            return

        # Presupposition 2. Extraposition for unselected heads (i.e. *X selects Y)
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
        return ps.minimal_search()[-1]

    def find_selection_violation(self, ps):
        # ------------------------- minimal search --------------------------------#
        for node in ps.minimal_search():
            if node.is_complex():
                selector = node.left_const
                not_comps = selector.get_not_comps()
                mandatory_comps = selector.get_mandatory_comps()
                selectee = node.right_const.head()
                if not_comps & selectee.features:
                    log(f'\t\t\t\t\t{selector} cannot select {selectee}')
                    return selectee
                if mandatory_comps and not (mandatory_comps & selectee.features):
                    log(f'\t\t\t\t\t{selector} cannot select {selectee}')
                    return selectee
        # --------------------------------------------------------------------------#
        return None

    def last_resort_reconstruct(self, ps):

        # Presupposition 1. We operate only referential structures (T/fin, D)
        if not (ps.top().contains_feature('CAT:FIN') or 'D' not in ps.top().features):
            return

        # Presupposition 2. LF - legibility fails (last resort)
        if ps.top().LF_legibility_test().all_pass():
            return

        log(f'\t\t\t\t\tLast resort extraposition will be tried on {ps.top()}.')

        # The operation performs an upstream walk
        node = self.get_bottom(ps).mother

        # Promote HP into an adjunct if and only if
        # Condition 1. HP is the first [H XP] from the bottom where H is adjoinable,
        # Condition 2. The grammatical context of HP is either
        #   (i) [XP][HP] or
        #   (ii) [X HP] with X not selecting for H, if and only if
        #          a-X has explicit negative selection for H,
        #          b-X has mandatory election for another label than H
        # Condition 3. HP is adjoinable

        # ------------------------- upstream walk ------------------------------------------------#
        while node:
            # Condition 2(i), ps_ = [H YP], [XP][H YP]
            if node.left_const.is_primitive() and node.left_const.is_adjoinable() and node.sister():
                if node.sister().is_complex():
                    break
                # Condition 2(ii) ps_ = [H YP], [X0 [H YP]]
                # Select HP if and only if X0 rejects HP as complement
                else:
                    # Condition 2(ii)-a. Explicit negative selection
                    if node.left_const.features & node.sister().get_not_comps():
                        break
                    # Condition 2(ii)-b. Mandatory selection for something else
                    if node.sister().get_mandatory_comps() and not (node.left_const.features & node.sister().get_mandatory_comps()):
                        break
            node = node.walk_upstream()
        # -----------------------------------------------------------------------------------------#

        # If a suitable node was found, we try to turn it into an adjunct
        # [H XP] will be promoted into an adjunct if and only if
        # Condition 2. <H XP> will be LF-interpretable at that position
        if node:

            # The adjunct must be interpretable at this location
            self.adjunct_constructor.create_adjunct(node)

            # Condition 2. <H XP> is interpretable as an adjunct at that location.
            if not node.top().LF_legibility_test().all_pass():
                log(f'\t\t\t\t\tSomething is still wrong. The structure is still uninterpretable.')
            return True
        else:
            log(f'\t\t\t\t\tNo suitable node for extraposition found. No action was taken.')
        return False





