from support import log
from lexical_interface import LexicalInterface

class HeadMovement:
    def __init__(self, controlling_parser_process):
        self.brain_model = controlling_parser_process
        self.name_provider_index = 0
        self.memory_buffer = []
        self.lexical_access = LexicalInterface(self.brain_model)
        self.lexical_access.load_lexicon(self.brain_model)

    def reconstruct(self, node):
        while node:
            node = self.consider_reconstruction(node)

    def consider_reconstruction(self, node):
        if node.has_affix():
            return self.create_head_chain(node, node.extract_affix())
        return node.mother.sister()

    def create_head_chain(self, target_head, affix):
        if not target_head.right_sister():
            target_head.merge_around(affix)
        else:
            for node in target_head.sister().minimal_search(lambda x: True, lambda x: not x.check(target_head.intervention_for_head_reconstruction())):
                node.mother.merge_1(affix, 'left')
                if affix.legitimate_head_position():
                    break
                affix.remove()
            else:
                target_head.top().bottom().merge_around(affix)
        self.brain_model.consume_resources("Head Chain", affix)
        return affix