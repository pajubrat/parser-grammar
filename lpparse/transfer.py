from agreement_reconstruction import AgreementReconstruction
from support import log, is_logging_enabled
from phrasal_reconstruction import PhrasalMovement
from adjunct_reconstruction import FloaterMovement
from head_reconstruction import HeadMovement
from feature_disambiguation import FeatureProcessing
from extraposition import Extraposition
from surface_conditions import SurfaceConditions

class Transfer:
    def __init__(self, controlling_parser_process):
        self.brain_model = controlling_parser_process
        self.agreement_module = AgreementReconstruction(self.brain_model)
        self.phrasal_movement_module = PhrasalMovement(self.brain_model)
        self.floater_movement_module = FloaterMovement(self.brain_model)
        self.head_movement_module = HeadMovement(self.brain_model)
        self.feature_process_module = FeatureProcessing(self.brain_model)
        self.extraposition_module = Extraposition(self.brain_model)
        self.surface_conditions_module = SurfaceConditions()
        self.narrow_semantics = controlling_parser_process.narrow_semantics

    def transfer(self, ps, embedding=3):
        output_to_interfaces = {}
        if not is_logging_enabled():
            log(f'Transferring {ps} to LF...')

        output_to_interfaces['spellout structure'] = ps.copy()
        self.brain_model.consume_resources("Phase Transfers")

        log('\n')
        log('\t\t\t1.\tHead movement reconstruction:')
        ps = self.head_movement_module.reconstruct(ps)
        output_to_interfaces['surface structure'] = ps.copy()
        log(f'\n\t\t\t\t{ps}\n')

        log('\t\t\t2.\tFeature processing:')
        self.feature_process_module.disambiguate(ps)
        log(f'\n\t\t\t\t{ps}\n')

        log('\t\t\t3.\tExtraposition:')
        self.extraposition_module.reconstruct(ps)
        log(f'\n\t\t\t\t{ps}\n')

        log('\t\t\t4.\tFloater movement reconstruction:')
        ps = self.floater_movement_module.reconstruct(ps)
        log(f'\n\t\t\t\t{ps}\n')
        output_to_interfaces['s-structure'] = ps.copy()

        log('\t\t\t5\tPhrasal movement reconstruction:')
        self.phrasal_movement_module.reconstruct(ps)
        log(f'\n\t\t\t\t{ps}\n')

        log('\t\t\t6.\tAgreement reconstruction:')
        self.agreement_module.reconstruct(ps)
        log(f'\n\t\t\t\t{ps}\n')

        log('\t\t\t7.\tLast resort extraposition:')
        self.extraposition_module.last_resort_reconstruct(ps)
        log(f'\n\t\t\t\t{ps}\n')
        output_to_interfaces['LF structure'] = ps.copy()

        return ps, output_to_interfaces