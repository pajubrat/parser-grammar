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
        self.name_provider_index = 0
        self.instructions = {'Head':            {'type': 'Head Chain',
                                                 'test integrity': lambda x: x.has_affix() and not x.right.find_me_elsewhere,
                                                 'repair': lambda x, y, z: x.create_chain(y, z),
                                                 'selection': lambda x: True,
                                                 'sustain': lambda x: True,
                                                 'legible': lambda x, y: y.properly_selected() and not y.empty_finite_EPP() and y.right_sister() != x},
                             'Phrasal':         {'type': 'Phrasal Chain',
                                                 'test integrity': lambda x: x.EF(),
                                                 'repair': lambda x, y, z: x.create_chain(y, z),
                                                 'selection': lambda x: not x.finite() and not x.edge(),
                                                 'sustain': lambda x: not x.referential(),
                                                 'legible': lambda x, y: (x.specifier_match(y) and x.specifier_sister().tail_match(x.specifier_sister(), 'left')) or x.complement_match(y),
                                                 'last resort A-chain conditions': lambda x: x == x.container().licensed_phrasal_specifier() or x.VP_for_fronting()},
                             'Feature':         {'type': 'Feature Chain',
                                                 'test integrity': lambda x: x.check({'?ARG'}),
                                                 'repair': lambda x, y, z: x.resolve_neutralized_feature()},
                             'Agree':           {'type': 'Agree',
                                                 'test integrity': lambda x: x.EF(),
                                                 'repair': lambda x, y, z: x.sister() and x.Agree()},
                             'Extraposition':   {'type': 'Extraposition',
                                                 'test integrity': lambda x: (x.top().contains_finiteness() or x.top().referential()) and x.induces_selection_violation() and not x.sister().adjunct,
                                                 'repair': lambda x, y, z: x.extrapose(self)},
                             'Last Resort Extraposition': {'type': 'Last Resort Extraposition',
                                                           'test integrity': lambda x: (x.top().contains_finiteness() or x.top().referential()) and not self.brain_model.LF.LF_legibility_test_detached(x.top()),
                                                           'repair': lambda x, y, z: x.last_resort_extrapose(self)}
                             }

    def transfer_to_LF(self, ps):
        self.name_provider_index = 0
        original_mother, is_right = ps.detach()
        ps = self.execute_sequence(ps)
        if original_mother:
            ps.mother = original_mother
        return ps

    def execute_sequence(self, ps):
        log(f'\n\tTransfer to LF:----------------------------------------------------------------------\n ')
        self.reconstruct(ps, self.instructions['Head'])
        self.reconstruct(ps, self.instructions['Feature'])
        self.reconstruct(ps, self.instructions['Extraposition'])
        ps = self.scrambling_module.reconstruct(ps)
        self.reconstruct(ps, self.instructions['Phrasal'])
        self.reconstruct(ps, self.instructions['Agree'])
        self.reconstruct(ps, self.instructions['Last Resort Extraposition'])
        log(f'\n\n\t\tSyntax-semantics interface endpoint:\n\t\t{ps}\n')
        return ps

    def reconstruct(self, probe, inst):
        x = probe.bottom()
        while x:
            if inst['test integrity'](x):
                inst['repair'](x, self, inst)
            x = x.selector()

    def babtize(self):
        self.name_provider_index += 1
        return str(self.name_provider_index)
