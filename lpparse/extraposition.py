from support import log
from LF import LF
from adjunct_constructor import AdjunctConstructor

class Extraposition:
    def __init__(self, controlling_parser_process):
        self.adjunct_constructor = AdjunctConstructor(controlling_parser_process)
        self.brain_model = controlling_parser_process

    def reconstruct(self, ps):
        if self.license_extraposition(ps):
            self.try_extraposition(self.get_head_violating_selection(ps))

    def get_head_violating_selection(self, ps):
        return next((node.right_const.head() for node in ps if
                     node.contains_selection_violation() and
                     not node.right_const.head().adjunct), None)

    def license_extraposition(self, ps):
        return ps.top().contains_finiteness() or ps.top().referential()

    def try_extraposition(self, head_violating_selection):
        if head_violating_selection:
            self.adjunct_constructor.externalize_structure(head_violating_selection)

    def last_resort_reconstruct(self, ps):
        if self.license_extraposition(ps) and not self.brain_model.LF_legibility_test(ps.top()):
            self.adjunct_constructor.externalize_structure(next((node for node in ps.bottom().working_memory_path() if self.possible_extraposition_target(node)), None))

    def possible_extraposition_target(self, node):
        return node.is_primitive() and \
               node.is_adjoinable() and \
               node.mother and node.mother.sister() and node.mother.sister().is_complex() and \
               (node.mother.sister().is_primitive() or node.mother.mother.contains_selection_violation())
