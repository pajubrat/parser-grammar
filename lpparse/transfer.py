from support import log, is_logging_enabled
from adjunct_reconstruction import FloaterMovement
from lexical_interface import LexicalInterface


class Transfer:
    def __init__(self, brain_model):
        self.brain_model = brain_model
        self.floater_movement_module = FloaterMovement(self.brain_model)
        self.access_lexicon = LexicalInterface(self.brain_model)
        self.instructions = {'Head':            {'type': 'Head',
                                                 'need repair': lambda x: x.has_affix() and not x.right.find_me_elsewhere,
                                                 'repair function': None,
                                                 'selection': lambda x: True,
                                                 'sustain': lambda x: True,
                                                 'legible': lambda x, y: y.properly_selected() and not y.empty_finite_EPP() and y.right_sister() != x},
                             'Phrasal':         {'type': 'Phrasal',
                                                 'need repair': lambda x: x.EF(),
                                                 'repair function': None,
                                                 'selection': lambda x: not x.finite() and not x.edge(),
                                                 'sustain': lambda x: True,
                                                 'legible': lambda x, y: (x.specifier_match(y) and x.specifier_sister().tail_match(x.specifier_sister(), 'left')) or x.complement_match(y),
                                                 'last resort': lambda x: x == x.container().licensed_phrasal_specifier() or x.VP_for_fronting()},
                             'Feature':         {'type': 'Feature',
                                                 'need repair': lambda x: x.check({'?ARG'}),
                                                 'repair function': lambda x, y: x.resolve_neutralized_feature(y)},
                             'Agree':           {'type': 'Agree',
                                                 'need repair': lambda x: x.EF(),
                                                 'repair function': lambda x, y: x.Agree(y)},
                             'Extraposition':   {'type': 'Extraposition',
                                                 'need repair': lambda x: (x.top().contains_finiteness() or x.top().referential()) and x.induces_selection_violation() and not x.sister().adjunct,
                                                 'repair function': lambda x, y: x.extrapose(y)},
                             'Last Resort Extraposition': {'type': 'Last Resort Extraposition',
                                                           'need repair': lambda x: (x.top().contains_finiteness() or x.top().referential()) and not self.brain_model.LF_legibility_test(x.top()),
                                                           'repair function': lambda x, y: x.last_resort_extrapose(self.brain_model)}
                             }

    def execute_sequence(self, ps):
        output_to_interfaces = {'spellout structure': ps.copy()}
        self.reconstruct(ps.bottom(), self.instructions['Head'])
        self.reconstruct(ps.bottom(), self.instructions['Feature'])
        self.reconstruct(ps.bottom(), self.instructions['Extraposition'])
        ps = self.floater_movement_module.reconstruct(ps)
        self.reconstruct(ps.bottom(), self.instructions['Phrasal'])
        self.reconstruct(ps.bottom(), self.instructions['Agree'])
        self.reconstruct(ps.bottom(), self.instructions['Last Resort Extraposition'])
        return ps, output_to_interfaces

    def reconstruct(self, probe, inst):
        while probe:
            if inst['need repair'](probe):
                for i, target in enumerate(probe.select_objects_from_edge(inst)):
                    self.repair(probe, target, inst, i)
            probe = probe.move_upwards()

    def repair(self, probe, target, inst, i):
        if not inst['repair function']:
            self.create_chain(probe, target, inst, i)
        else:
            inst['repair function'](probe, self.brain_model)
            self.brain_model.consume_resources(inst['type'], probe)

    def create_chain(self, probe, target, inst, i):
        inst, target = self.prepare_chain(probe, target, inst, i > 0, target.scan_operators())
        probe.form_chain(target, inst)
        self.brain_model.consume_resources('Chain', target)
        if inst['need repair'](target):
            self.create_chain(target, target.right, inst, False)

    def prepare_chain(self, probe, target, inst, new_head_needed, op_features):
        if inst['type'] == 'Phrasal':
            if not op_features:
                inst = {'selection': lambda x: x.has_vacant_phrasal_position(), 'sustain': lambda x: not x.referential(), 'legible': lambda x, y: True, 'need repair': lambda x: False}
            elif new_head_needed and (op_features or target.unlicensed_specifier()):
                probe = target.sister().merge_1(self.access_lexicon.PhraseStructure(), 'left').left
            probe.features |= self.access_lexicon.apply_parameters(self.access_lexicon.apply_redundancy_rules({'OP:_'} | target.checking_domain('OP*' in op_features).scan_operators() | probe.add_scope_information()))
        return inst, target.copy_for_chain(self.brain_model.babtize())
