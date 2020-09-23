from support import log
from LF import LF
from adjunct_constructor import AdjunctConstructor

class Extraposition:
    def __init__(self, controlling_parser_process):
        self.adjunct_constructor = AdjunctConstructor(controlling_parser_process)
        self.controlling_parser_process = controlling_parser_process

    def reconstruct(self, ps):
        if ps.top().contains_feature('FIN') or 'D' in ps.top().features:
            if self.find_head_violating_selection(ps):
                self.try_extraposition(self.find_head_violating_selection(ps))

    def find_head_violating_selection(self, ps):
        # ------------------------- minimal search --------------------------------#
        for node in ps.minimal_search():
            if self.selection_violation_at(node):
                log(f'\t\t\t\t\t{node.left_const} cannot select {node.right_const.head()}')
                return node.right_const.head()
        # --------------------------------------------------------------------------#

    def selection_violation_at(self, node):
        if node.is_primitive():
            return False
        if node.left_const.complements_not_licensed() & node.right_const.head().features:
            return True
        if node.left_const.get_mandatory_comps() and not (node.left_const.get_mandatory_comps() & node.right_const.head().features):
            return True

    def try_extraposition(self, unselected_head):
        log(f'\t\t\t\t\tExtraposition will be tried on {unselected_head.mother}.')
        self.controlling_parser_process.consume_resources("Extraposition")
        self.adjunct_constructor.create_adjunct(unselected_head)

    # Definition for last resort extraposition
    def last_resort_reconstruct(self, ps):
        if self.preconditions_for_extraposition(ps):
            log(f'\t\t\t\t\tLast resort extraposition will be tried on {ps.top()}.')
            # ---------------------------- upstream search -----------------------------------------------#
            for node in ps.bottom().upstream_search():
                if self.possible_extraposition_target(node):
                    self.controlling_parser_process.consume_resources("Extraposition")
                    self.adjunct_constructor.create_adjunct(node.head())
                    return True
            # -------------------------------------------------------------------------------------------#
            log(f'\t\t\t\t\tNo suitable node for extraposition found.')

    def preconditions_for_extraposition(self, ps):
        return (ps.top().contains_feature('FIN') or 'D' in ps.top().head().features) and not self.controlling_parser_process.LF_legibility_test(ps.top())

    def possible_extraposition_target(self, node):
        if node.is_complex() and node.left_const.is_primitive() and node.left_const.is_adjoinable() and node.sister():
            if node.sister().is_complex():
                return True
            if node.sister().is_primitive():
                if node.left_const.features & node.sister().complements_not_licensed():
                    return True
                if node.sister().get_mandatory_comps() and not (node.left_const.features & node.sister().get_mandatory_comps()):
                    return True