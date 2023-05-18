from support import log, set_logging, is_logging_enabled
from scrambling_reconstruction import ScramblingReconstruction
from lexical_interface import LexicalInterface
from EXP_Agreement_variations import AgreementVariations

class Transfer:
    def __init__(self, brain_model):
        self.brain_model = brain_model
        self.i = 0
        self.target = None
        self.scrambling_module = ScramblingReconstruction(self.brain_model)
        self.access_lexicon = LexicalInterface(self.brain_model)
        self.Agree_variations = AgreementVariations(self.brain_model)
        self.name_provider_index = 0
        self.instructions = {'Head':            {'type': 'Head Chain',
                                                 'test integrity': lambda x: x.has_affix() and not x.right.find_me_elsewhere,
                                                 'repair': lambda x, y, z: x.create_chain(y, z),
                                                 'selection': lambda x: True,
                                                 'sustain': lambda x: True,
                                                 'legible': lambda x, y: y.properly_selected() and not y.empty_finite_EPP() and y.right_sister() != x},
                             'Phrasal':         {'type': 'Phrasal Chain',
                                                 'test integrity': lambda x: True,
                                                 'repair': lambda x, y, z: x.create_chain(y, z),
                                                 'selection': lambda x: x.primitive() and not x.finite(),
                                                 'sustain': lambda x: not (x.primitive() and x.referential()),
                                                 'legible': lambda x, y: x.Abar_legible(y),
                                                 'last resort A-chain conditions': lambda x: x == x.container().licensed_phrasal_specifier() or x.VP_for_fronting()},
                             'Feature':         {'type': 'Feature Chain',
                                                 'test integrity': lambda x: x.check({'?ARG'}) or x.check({'Fin'}),
                                                 'repair': lambda x, y, z: x.feature_inheritance()},
                             'Agree':           {'type': 'Agree',
                                                 'test integrity': lambda x: x.is_unvalued() and x.check_some({'!SELF:d', 'd'}),
                                                 'repair': lambda x, y, z: self.Agree_variations.Agree(x, y)},
                             'Extraposition':   {'type': 'Extraposition',
                                                 'test integrity': lambda x: (x.top().contains_finiteness() or x.top().referential()) and x.induces_selection_violation() and x.sister() and not x.sister().adjunct,
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
        log(f'\n\tTransfer {ps} to LF:----------------------------------------------------------------------\n ')
        self.reconstruct(ps, self.instructions['Head'].copy())
        self.reconstruct(ps, self.instructions['Feature'].copy())
        self.reconstruct(ps, self.instructions['Extraposition'].copy())
        self.scrambling_module.reconstruct(ps)
        self.reconstruct(ps, self.instructions['Phrasal'].copy())
        self.reconstruct(ps, self.instructions['Agree'].copy())
        self.last_resort(ps, self.instructions['Last Resort Extraposition'].copy())
        log(f'\n\n\t\tSyntax-semantics interface endpoint:\n\t\t{ps.top()}\n')
        return ps.top()

    def reconstruct(self, probe, inst):
        x = probe.bottom()
        while x:
            if inst['test integrity'](x):
                inst['repair'](x, self, inst)
            x = x.selector()

    def last_resort(self, x, inst):
        if inst['test integrity'](x):
            inst['repair'](x, self, inst)

    def babtize(self):
        self.name_provider_index += 1
        return str(self.name_provider_index)
