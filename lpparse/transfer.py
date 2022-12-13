from agreement_reconstruction import AgreementReconstruction
from support import log, is_logging_enabled
from adjunct_reconstruction import FloaterMovement
from feature_disambiguation import FeatureProcessing
from extraposition import Extraposition
from surface_conditions import SurfaceConditions


class Transfer:
    def __init__(self, controlling_parser_process):
        self.brain_model = controlling_parser_process
        self.agreement_module = AgreementReconstruction(self.brain_model)
        self.floater_movement_module = FloaterMovement(self.brain_model)
        self.feature_process_module = FeatureProcessing(self.brain_model)
        self.extraposition_module = Extraposition(self.brain_model)
        self.surface_conditions_module = SurfaceConditions()
        self.narrow_semantics = controlling_parser_process.narrow_semantics

    def transfer(self, ps):
        output_to_interfaces = {}
        if not is_logging_enabled():
            log(f'Transferring {ps} to LF...')
        output_to_interfaces['spellout structure'] = ps.copy()
        self.brain_model.consume_resources("Phase Transfer", ps)
        self.brain_model.reconstruction.reconstruct(ps.bottom(), 'Head')
        output_to_interfaces['surface structure'] = ps.copy()
        self.feature_process_module.disambiguate(ps)
        self.extraposition_module.reconstruct(ps)
        ps = self.floater_movement_module.reconstruct(ps)
        output_to_interfaces['s-structure'] = ps.copy()
        self.brain_model.reconstruction.reconstruct(ps.bottom(), 'Phrasal')
        self.agreement_module.reconstruct(ps)
        self.extraposition_module.last_resort_reconstruct(ps)
        output_to_interfaces['LF structure'] = ps.copy()

        return ps, output_to_interfaces