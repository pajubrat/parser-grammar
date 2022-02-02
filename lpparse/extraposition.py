from support import log
from LF import LF
from adjunct_constructor import AdjunctConstructor

class Extraposition:
    def __init__(self, controlling_parser_process):
        self.adjunct_constructor = AdjunctConstructor(controlling_parser_process)
        self.brain_model = controlling_parser_process

    def reconstruct(self, ps):
        if ps.top().contains_feature('FIN') or 'D' in ps.top().features:
            head_violating_selection = next((node.right_const.head() for node in ps.minimal_search() if self.selection_violation_at(node)), None)
            if head_violating_selection:
                self.try_extraposition(head_violating_selection)

    def selection_violation_at(self, node):
        if node.is_complex():
            if node.left_const.complements_not_licensed() & node.right_const.head().features or \
                    node.left_const.get_mandatory_comps() and not (node.left_const.get_mandatory_comps() & node.right_const.head().features):
                return True

    def try_extraposition(self, unselected_head):
        log(f'Extraposition will be tried on {unselected_head.mother}...')
        self.brain_model.consume_resources("Extraposition")
        self.adjunct_constructor.externalize_structure(unselected_head)

    def last_resort_reconstruct(self, ps):
        if self.preconditions_for_extraposition(ps):
            log(f'Last resort extraposition on {ps.head().illustrate()}P...')
            target = next((node for node in ps.bottom().working_memory_path() if self.possible_extraposition_target(node)), None)
            if target:
                self.brain_model.consume_resources("Extraposition")
                self.adjunct_constructor.externalize_structure(target)
                return True
            log(f'No suitable node found...')

    def preconditions_for_extraposition(self, ps):
        if ps.top().contains_feature('FIN') or {'D','φ'} & ps.top().head().features:
            if not self.brain_model.LF_legibility_test(ps.top()):
                return True

    def possible_extraposition_target(self, node):
        if node.is_primitive() and node.is_adjoinable() and node.mother and node.mother.sister():
            if node.mother.sister().is_complex():
                return True
            if node.mother.sister().is_primitive():
                if node.features & node.mother.sister().complements_not_licensed():
                    return True
                if node.mother.sister().get_mandatory_comps() and not (node.features & node.mother.sister().get_mandatory_comps()):
                    return True