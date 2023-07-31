from support import log
from lexical_interface import LexicalInterface
from EXP_Agreement_variations import AgreementVariations


class Transfer:
    def __init__(self, brain_model):
        self.brain_model = brain_model
        self.i = 0
        self.target = None
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
                                                 'test integrity': lambda x: x.EF(),
                                                 'repair': lambda x, y, z: x.create_chain(y, z),
                                                 'selection': lambda x: x.primitive() and not x.finite(),
                                                 'sustain': lambda x: not (x.primitive() and x.referential()),
                                                 'legible': lambda x, y: x.Abar_legible(y),
                                                 'last resort A-chain conditions': lambda x: x == x.container().licensed_phrasal_specifier() or x.VP_for_fronting()},
                             'Feature':         {'type': 'Feature Chain',
                                                 'test integrity': lambda x: x.check({'ARG?'}) or x.check({'Fin'}),
                                                 'repair': lambda x, y, z: x.feature_inheritance()},
                             'Agree':           {'type': 'Agree',
                                                 'test integrity': lambda x: x.is_unvalued(),
                                                 'repair': lambda x, y, z: self.Agree_variations.Agree(x, y)},
                             'Extraposition':   {'type': 'Extraposition',
                                                 'test integrity': lambda x: (x.top().contains_finiteness() or x.top().referential()) and x.induces_selection_violation() and x.sister() and not x.sister().adjunct,
                                                 'repair': lambda x, y, z: x.extrapose(self)},
                             'Right Scramble':  {'type': 'Right Scrambling',
                                                 'test integrity': lambda x: x.trigger_right_adjunct_reconstruction(),
                                                 'repair': lambda x, y, z: x.right_scramble(y, z)},
                             'Left Scramble':   {'type': 'Left Scrambling',
                                                 'test integrity': lambda x: True,
                                                 'repair': lambda x, y, z: x.left_scramble(y, z)},
                             'Last Resort Extraposition': {'type': 'Last Resort Extraposition',
                                                           'test integrity': lambda x: (x.top().contains_finiteness() or x.top().referential()) and not self.brain_model.LF.LF_legibility_test_detached(x.top()),
                                                           'repair': lambda x, y, z: x.last_resort_extrapose(y)}
                             }
        self.transfer_sequence = [self.instructions['Head'],
                                  self.instructions['Feature'],
                                  self.instructions['Extraposition'],
                                  self.instructions['Right Scramble'],
                                  self.instructions['Left Scramble'],
                                  self.instructions['Phrasal'],
                                  self.instructions['Agree'],
                                  self.instructions['Last Resort Extraposition']]

    def transfer_to_LF(self, ps):
        self.name_provider_index = 0
        original_mother, is_right = ps.detach()
        ps = self.execute_sequence(ps)
        if original_mother:
            ps.mother = original_mother
        return ps

    def execute_sequence(self, ps):
        log(f'\n\tTransfer {ps} to LF:----------------------------------------------------------------------\n ')
        for operation in self.transfer_sequence:
            ps.reconstruct(self, operation.copy())
        log(f'\n\n\t\tSyntax-semantics interface endpoint:\n\t\t{ps.top()}\n')
        return ps.top()
