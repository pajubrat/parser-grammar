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
        if not (ps.top().contains_feature('FIN') or 'D' in ps.top().features):
            return

        # Presupposition 2. Extraposition for unselected heads (i.e. *X selects Y)
        unselected_head = self.find_selection_violation(ps)
        if unselected_head:
            self.try_extraposition(unselected_head)

    def try_extraposition(self, unselected_head):
        log(f'\t\t\t\t\tExtraposition will be tried on {unselected_head.mother}.')
        self.adjunct_constructor.create_adjunct(unselected_head)
        return True

    def get_bottom(self, ps):
        return ps.minimal_search()[-1]

    def find_selection_violation(self, ps):
        # ------------------------- minimal search --------------------------------#
        for node in ps.minimal_search():
            if node.is_complex():
                selector = node.left_const
                not_comps = selector.complements_not_licensed()
                mandatory_comps = self.get_mandatory_comps(selector)
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
        if not (ps.top().contains_feature('FIN') or 'D' not in ps.top().features):
            return
        if ps.top().LF_legibility_test().all_pass():
            return

        log(f'\t\t\t\t\tLast resort extraposition will be tried on {ps.top()}.')

        node = self.get_bottom(ps).mother

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
                    if node.left_const.features & node.sister().complements_not_licensed():
                        break
                    # Condition 2(ii)-b. Mandatory selection for something else
                    if self.get_mandatory_comps(node.sister()) and not (node.left_const.features & self.get_mandatory_comps(node.sister())):
                        break
            node = node.walk_upstream()
        # -----------------------------------------------------------------------------------------#

        if node:
            self.adjunct_constructor.create_adjunct(node)
            if not node.top().LF_legibility_test().all_pass():
                log(f'\t\t\t\t\tSomething is still wrong. The structure is still uninterpretable.')
            return True
        else:
            log(f'\t\t\t\t\tNo suitable node for extraposition found. No action was taken.')
        return False

    @staticmethod
    # Definition for mandatory complement selection
    def get_mandatory_comps(h):
        return  {f[6:] for f in h.features if f[:5] == '!COMP' and f != '!COMP:*'}