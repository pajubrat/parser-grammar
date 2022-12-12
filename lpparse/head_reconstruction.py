from support import log
from lexical_interface import LexicalInterface

selection = lambda x: True
sustain = lambda x: True
legibility = lambda x, y: y.properly_selected() and not y.empty_finite_EPP() and y.right_sister() != x

class HeadMovement:
    def __init__(self, controlling_parser_process):
        self.brain_model = controlling_parser_process
        self.name_provider_index = 0
        self.memory_buffer = []
        self.lexical_access = LexicalInterface(self.brain_model)
        self.lexical_access.load_lexicon(self.brain_model)

    def reconstruct(self, node):
        while node:
            if node.has_affix() and not node.right.find_me_elsewhere:
                node = self.brain_model.reconstruct.create_chain(node, node.right.copy_for_chain(self.brain_model.babtize()), selection, sustain, legibility)
            elif node.mother:
                node = node.mother.sister()
            else:
                node = None
