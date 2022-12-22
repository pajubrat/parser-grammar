from support import log, is_logging_enabled
from scrambling_reconstruction import ScramblingReconstruction
from lexical_interface import LexicalInterface


class Transfer:
    def __init__(self, brain_model):
        self.brain_model = brain_model
        self.i = 0
        self.target = None
        self.scrambling_module = ScramblingReconstruction(self.brain_model)
        self.access_lexicon = LexicalInterface(self.brain_model)
        self.instructions = {'Head':            {'type': 'Head Chain',
                                                 'need repair': lambda x: x.has_affix() and not x.right.find_me_elsewhere,
                                                 'repair function': lambda x, y, z: x.create_chain(y, z),
                                                 'selection': lambda x: True,
                                                 'sustain': lambda x: True,
                                                 'legible': lambda x, y: y.properly_selected() and not y.empty_finite_EPP() and y.right_sister() != x},
                             'Phrasal':         {'type': 'Phrasal Chain',
                                                 'need repair': lambda x: x.EF(),
                                                 'repair function': lambda x, y, z: x.create_chain(y, z),
                                                 'selection': lambda x: not x.finite() and not x.edge(),
                                                 'sustain': lambda x: not x.referential(),
                                                 'legible': lambda x, y: (x.specifier_match(y) and x.specifier_sister().tail_match(x.specifier_sister(), 'left')) or x.complement_match(y),
                                                 'last resort A-chain conditions': lambda x: x == x.container().licensed_phrasal_specifier() or x.VP_for_fronting()},
                             'Feature':         {'type': 'Feature Chain',
                                                 'need repair': lambda x: x.check({'?ARG'}),
                                                 'repair function': lambda x, y, z: x.resolve_neutralized_feature()},
                             'Agree':           {'type': 'Agree',
                                                 'need repair': lambda x: x.EF(),
                                                 'repair function': lambda x, y, z: x.Agree(y)},
                             'Extraposition':   {'type': 'Extraposition',
                                                 'need repair': lambda x: (x.top().contains_finiteness() or x.top().referential()) and x.induces_selection_violation() and not x.sister().adjunct,
                                                 'repair function': lambda x, y, z: x.extrapose(self)},
                             'Last Resort Extraposition': {'type': 'Last Resort Extraposition',
                                                           'need repair': lambda x: (x.top().contains_finiteness() or x.top().referential()) and not self.brain_model.LF_legibility_test(x.top()),
                                                           'repair function': lambda x, y, z: x.last_resort_extrapose(self)}
                             }

    def execute_sequence(self, ps):
        output_to_interfaces = {'spellout structure': ps.copy()}
        self.reconstruct(ps.bottom(), self.instructions['Head'])
        self.reconstruct(ps.bottom(), self.instructions['Feature'])
        self.reconstruct(ps.bottom(), self.instructions['Extraposition'])
        ps = self.scrambling_module.reconstruct(ps)
        self.reconstruct(ps.bottom(), self.instructions['Phrasal'])
        self.reconstruct(ps.bottom(), self.instructions['Agree'])
        self.reconstruct(ps.bottom(), self.instructions['Last Resort Extraposition'])
        return ps, output_to_interfaces

    def reconstruct(self, probe, inst):
        while probe:
            if inst['need repair'](probe):
                inst['repair function'](probe, self, inst)
            probe = probe.move_upwards()
