from support import log
from lexical_interface import LexicalInterface
oper = {'Head':        {'need repair': lambda x: x.has_affix() and not x.right.find_me_elsewhere,
                        'selection': lambda x: True,
                        'sustain': lambda x: True,
                        'legible': lambda x, y: y.properly_selected() and not y.empty_finite_EPP() and y.right_sister() != x},
        'Phrasal':     {'need repair': lambda x: x.EF(),
                        'selection': lambda x: not x.finite() and not x.edge(),
                        'sustain': lambda x: True,
                        'legible': lambda x, y: (x.specifier_match(y) and x.specifier_sister().tail_match(x.specifier_sister(), 'left')) or x.complement_match(y),
                        'last resort': lambda x: x == x.container().licensed_phrasal_specifier() or x.VP_for_fronting()},
        'Last resort': {'selection': lambda x: x.has_vacant_phrasal_position(), 'sustain': lambda x: not x.referential(), 'legible': lambda x, y: True}
        }


class Reconstruct:
    def __init__(self, controlling_parsing_process):
        self.brain_model = controlling_parsing_process
        self.access_lexicon = LexicalInterface(self.brain_model)

    def reconstruct(self, node, typ):
        while node:
            if oper[typ]['need repair'](node):
                for i, obj in enumerate(node.select_objects(typ)):
                    self.create_chain(typ, node, obj, i > 0, oper[typ]['selection'], oper[typ]['sustain'], oper[typ]['legible'])
            node = node.move_upwards()

    def create_chain(self, typ, node, obj, new_head, selection, sustain, legible):
        typ, obj = self.prepare_chain(typ, node, obj, new_head, obj.scan_operators())
        for head in node.search_domain().minimal_search(selection, sustain):
            if head.test_merge(obj, legible, 'left'):
                break
            obj.remove()
        else:
            if not head.test_merge(obj, legible, 'right'):
                obj.remove()
                node.sister().merge_1(obj, 'left')
        self.brain_model.consume_resources('Chain', obj, typ)
        if obj.has_affix():
            self.create_chain(typ, obj, obj.right, False, oper[typ]['selection'], oper[typ]['sustain'], oper[typ]['legible'])

    def prepare_chain(self, typ, head, obj, new_head, operator_features):
        def transfer_features(head, spec, features):
            features = {'OP:_'} | spec.checking_domain('OP*' in features).scan_operators() | head.add_scope_information()
            return self.access_lexicon.apply_parameters(self.access_lexicon.apply_redundancy_rules(features))
        if typ == 'Phrasal':
            if not operator_features:
                typ = 'Last resort'
            elif new_head and (operator_features or obj.unlicensed_specifier()):
                head = obj.sister().merge_1(self.access_lexicon.PhraseStructure(), 'left').left
            head.features |= transfer_features(head, obj, operator_features)
        return typ, obj.copy_for_chain(self.brain_model.babtize())
