from support import log, is_logging_enabled
from adjunct_reconstruction import FloaterMovement
from reconstruction import Reconstruct

instructions = {'Head':  {'type': 'Head',
                          'need repair': lambda x: x.has_affix() and not x.right.find_me_elsewhere,
                          'repair function': None,
                          'selection': lambda x: True,
                          'sustain': lambda x: True,
                          'legible': lambda x, y: y.properly_selected() and not y.empty_finite_EPP() and y.right_sister() != x},
                'Phrasal': {'type': 'Phrasal',
                            'need repair': lambda x: x.EF(),
                            'repair function': None,
                            'selection': lambda x: not x.finite() and not x.edge(),
                            'sustain': lambda x: True,
                            'legible': lambda x, y: (x.specifier_match(y) and x.specifier_sister().tail_match(x.specifier_sister(), 'left')) or x.complement_match(y),
                            'last resort': lambda x: x == x.container().licensed_phrasal_specifier() or x.VP_for_fronting()},
                'Feature': {'type': 'Feature',
                            'need repair': lambda x: x.check({'?ARG'}),
                            'repair function': lambda x, y: x.resolve_neutralized_feature(y)},
                'Agree':   {'type': 'Agree',
                            'need repair': lambda x: x.EF(),
                            'repair function': lambda x, y: x.Agree(y)},
                'Extraposition':    {'type': 'Extraposition',
                                     'need repair': lambda x: (x.top().contains_finiteness() or x.top().referential()) and x.induces_selection_violation() and not x.sister().adjunct,
                                     'repair function': lambda x, y: x.extrapose(y)},
                'Last Resort Extraposition':    {'type': 'Last Resort Extraposition',
                                                 'need repair': lambda x: x.top().contains_finiteness() or x.top().referential(),
                                                 'repair function': lambda x, y: x.last_resort_extrapose(y)},
                }


class Transfer:
    def __init__(self, brain_model):
        self.brain_model = brain_model
        self.floater_movement_module = FloaterMovement(self.brain_model)
        self.reconstruction = Reconstruct(self.brain_model)

    def transfer(self, ps):
        if not is_logging_enabled():
            log(f'Transferring {ps} to LF:')

        output_to_interfaces = {}
        output_to_interfaces['spellout structure'] = ps.copy()
        self.reconstruction.reconstruct(ps.bottom(), instructions['Head'])
        self.reconstruction.reconstruct(ps.bottom(), instructions['Feature'])
        self.reconstruction.reconstruct(ps.bottom(), instructions['Extraposition'])
        ps = self.floater_movement_module.reconstruct(ps)
        self.reconstruction.reconstruct(ps.bottom(), instructions['Phrasal'])
        self.reconstruction.reconstruct(ps.bottom(), instructions['Agree'])
        self.reconstruction.reconstruct(ps.bottom(), instructions['Last Resort Extraposition'])
        return ps, output_to_interfaces
