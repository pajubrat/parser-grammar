from support import log
from lexical_interface import LexicalInterface

selection = lambda x: True
sustain = lambda x: True
legibility = lambda x: x.properly_selected() and not x.empty_finite_EPP()

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
                node = self.brain_model.reconstruct.create_chain(node, node.right.copy_for_reconstruction(self.brain_model.babtize()), selection, sustain, legibility)
                self.brain_model.consume_resources('A-Chain', node)
            elif node.mother:
                node = node.mother.sister()
            else:
                node = None
