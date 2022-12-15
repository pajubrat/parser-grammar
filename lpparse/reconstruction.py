from support import log
from lexical_interface import LexicalInterface


class Reconstruct:
    def __init__(self, controlling_parsing_process):
        self.brain_model = controlling_parsing_process
        self.access_lexicon = LexicalInterface(self.brain_model)

    def reconstruct(self, node, chain):
        while node:
            if chain['need repair'](node):
                for i, obj in enumerate(node.select_objects(chain)):
                    self.create_chain(chain, node, obj, i > 0)
            node = node.move_upwards()

    def create_chain(self, chain, node, obj, new_head_needed):
        chain, obj = self.prepare_chain(chain, node, obj, new_head_needed, obj.scan_operators())
        for head in node.search_domain().minimal_search(chain['selection'], chain['sustain']):
            if head.test_merge(obj, chain['legible'], 'left'):
                break
            obj.remove()
        else:
            if not head.test_merge(obj, chain['legible'], 'right'):
                obj.remove()
                node.sister().merge_1(obj, 'left')
        self.brain_model.consume_resources('Chain', obj)
        if chain['need repair'](obj):
            self.create_chain(chain, obj, obj.right, False)

    def prepare_chain(self, chain, head, obj, new_head_needed, op_features):
        if chain['type'] == 'Phrasal':
            if not op_features:
                chain = {'selection': lambda x: x.has_vacant_phrasal_position(), 'sustain': lambda x: not x.referential(), 'legible': lambda x, y: True, 'need repair': lambda x: False}
            elif new_head_needed and (op_features or obj.unlicensed_specifier()):
                head = obj.sister().merge_1(self.access_lexicon.PhraseStructure(), 'left').left
            head.features |= self.access_lexicon.apply_parameters(self.access_lexicon.apply_redundancy_rules({'OP:_'} | obj.checking_domain('OP*' in op_features).scan_operators() | head.add_scope_information()))
        return chain, obj.copy_for_chain(self.brain_model.babtize())
