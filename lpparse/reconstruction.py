from support import log
from lexical_interface import LexicalInterface

#
# All reconstruction operations will be taken care by these functions
#

class Reconstruct:
    def __init__(self, controlling_parsing_process):
        self.brain_model = controlling_parsing_process
        self.access_lexicon = LexicalInterface(self.brain_model)
        self.access_operators = self.brain_model.narrow_semantics.operator_variable_module
        self.funct = {'head':       {'need repair': lambda x: x.has_affix() and not x.right.find_me_elsewhere,
                                     'selection': lambda x: True,
                                     'sustain': lambda x: True,
                                     'legible': lambda x, y: y.properly_selected() and not y.empty_finite_EPP() and y.right_sister() != x},
                      'phrase':         {'need repair': lambda x: x.EF(),
                                         'selection': lambda x: not x.finite() and not x.edge(),
                                         'sustain': lambda x: True,
                                         'legible': lambda x, y: (x.specifier_match(y) and x.specifier_sister().tail_match(x.specifier_sister(), 'left')) or x.complement_match(y), 'last resort': lambda x: x == x.container().licensed_phrasal_specifier() or x.VP_for_fronting(), 'Abar': lambda x: self.access_operators.scan_operators(x)},
                      'last resort':    {'selection': lambda x: x.has_vacant_phrasal_position(),
                                         'sustain': lambda x: not x.referential(),
                                         'legible': lambda x, y: True}
                      }

    def reconstruct(self, node, typ):
        while node:
            if self.funct[typ]['need repair'](node):
                for i, obj in enumerate(self.select_objects(typ, node)):
                    node = self.create_chain(typ, node, obj, i)
            else:
                node = node.move_upwards()

    def select_objects(self, typ, node):
        if typ == 'head':
            return [node.right]
        return [spec for spec in node.edge() if not spec.find_me_elsewhere]

    def create_chain(self, typ, node, obj, i):
        if typ == 'phrase':
            if self.access_operators.scan_operators(obj):
                self.process_criterial_features(node, obj, i, self.access_operators.scan_operators(obj))
            else:
                typ = 'last resort'
        return self.chain(node, obj.copy_for_chain(self.brain_model.babtize()), self.funct[typ]['selection'], self.funct[typ]['sustain'], self.funct[typ]['legible'])

    def chain(self, node, obj, selection, sustain, legible):
        for head in node.search_domain().minimal_search(selection, sustain):
            head.specifier_sister().merge_1(obj, 'left')
            if legible(head, obj):
                break
            obj.remove()
        else:
            head.merge_1(obj, 'right')
            if not legible(head, obj):
                obj.remove()
                node.sister().merge_1(obj, 'left')
        self.brain_model.consume_resources('Chain', obj)
        if obj.is_primitive():
            return obj
        return node.move_upwards()

    def process_criterial_features(self, head, spec, i, operator_features):
        def transfer_features(head, spec, features):
            features = {'OP:_'} | self.access_operators.scan_operators(spec.checking_domain('OP*' in features)) | head.add_scope_information()
            return self.access_lexicon.apply_parameters(self.access_lexicon.apply_redundancy_rules(features))

        if i > 0 and (operator_features or spec.unlicensed_specifier()):
            head = spec.sister().merge_1(self.access_lexicon.PhraseStructure(), 'left').left
        head.features |= transfer_features(head, spec, operator_features)
