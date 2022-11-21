from adjunct_constructor import AdjunctConstructor

class Extraposition:
    def __init__(self, controlling_parser_process):
        self.adjunct_constructor = AdjunctConstructor(controlling_parser_process)
        self.brain_model = controlling_parser_process

    def reconstruct(self, ps):
        if ps.license_extraposition():
            self.try_extraposition(ps.get_head_violating_selection())

    def try_extraposition(self, head_violating_selection):
        if head_violating_selection:
            self.adjunct_constructor.externalize_structure(head_violating_selection)

    def last_resort_reconstruct(self, ps):
        if ps.license_extraposition() and not self.brain_model.LF_legibility_test(ps.top()):
            self.adjunct_constructor.externalize_structure(ps.scan_next(ps.bottom().working_memory_path(), lambda x: x.cutoff_point_for_last_resort_extraposition()))
