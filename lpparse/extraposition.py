from adjunct_constructor import AdjunctConstructor
from support import log

class Extraposition:
    def __init__(self, controlling_parser_process):
        self.adjunct_constructor = AdjunctConstructor(controlling_parser_process)
        self.brain_model = controlling_parser_process

    def reconstruct(self, ps):
        if ps.license_extraposition():
            self.try_extraposition(ps.get_constituent_containing_selection_violation())

    def try_extraposition(self, node_violating_selection):
        if node_violating_selection:
            self.adjunct_constructor.externalize_structure(node_violating_selection.sister().head())

    def last_resort_reconstruct(self, ps):
        if ps.license_extraposition() and not self.brain_model.LF_legibility_test(ps.top()):
            self.adjunct_constructor.externalize_structure(ps.bottom().next(ps.bottom().upward_path, lambda x: x.cutoff_point_for_last_resort_extraposition()))
