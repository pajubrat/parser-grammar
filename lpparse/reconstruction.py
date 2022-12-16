from support import log
from lexical_interface import LexicalInterface


class Reconstruct:
    def __init__(self, controlling_parsing_process):
        self.brain_model = controlling_parsing_process
        self.access_lexicon = LexicalInterface(self.brain_model)

    def reconstruct(self, probe, instructions):
        while probe:
            if instructions['need repair'](probe):
                for i, target in enumerate(probe.select_objects_from_edge(instructions)):
                    self.repair(probe, target, instructions, i)
            probe = probe.move_upwards()

    def repair(self, probe, target, instructions, i):
        if not instructions['repair function']:
            self.create_chain(probe, target, instructions, i)
        else:
            instructions['repair function'](probe, self.brain_model)
            self.brain_model.consume_resources(instructions['type'], probe)

    def create_chain(self, probe, target, instructions, i):
        instructions, target = self.prepare_chain(probe, target, instructions, i > 0, target.scan_operators())
        probe.form_chain(target, instructions)
        self.brain_model.consume_resources('Chain', target)
        if instructions['need repair'](target):
            self.create_chain(target, target.right, instructions, False)

    def prepare_chain(self, probe, target, instructions, new_head_needed, op_features):
        if instructions['type'] == 'Phrasal':
            if not op_features:
                instructions = {'selection': lambda x: x.has_vacant_phrasal_position(), 'sustain': lambda x: not x.referential(), 'legible': lambda x, y: True, 'need repair': lambda x: False}
            elif new_head_needed and (op_features or target.unlicensed_specifier()):
                probe = target.sister().merge_1(self.access_lexicon.PhraseStructure(), 'left').left
            probe.features |= self.access_lexicon.apply_parameters(self.access_lexicon.apply_redundancy_rules({'OP:_'} | target.checking_domain('OP*' in op_features).scan_operators() | probe.add_scope_information()))
        return instructions, target.copy_for_chain(self.brain_model.babtize())
