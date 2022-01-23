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
        log_embedding = embedding * '\t'
        if not is_logging_enabled():
            log(log_embedding + f'Transferring {ps} to LF.')

        log_embedding = log_embedding + '\t'

        self.brain_model.consume_resources("Transfer", f'{ps}')
        output_to_interfaces['spellout structure'] = ps.copy()

        log('\n')
        log(log_embedding + '1. Head movement reconstruction...')
        ps = self.head_movement_module.reconstruct(ps)
        output_to_interfaces['surface structure'] = ps.copy()
        log('Done.\n')
        log(log_embedding + f'\t= {ps}\n')

        log(log_embedding + '2. Feature processing...')
        self.feature_process_module.disambiguate(ps)
        log('Done.\n')
        log(log_embedding + f'\t= {ps}\n')

        log(log_embedding + '3. Extraposition...')
        self.extraposition_module.reconstruct(ps)
        log('Done.\n')
        log(log_embedding + f'\t= {ps}\n')

        log(log_embedding + '4. Floater movement reconstruction...')
        ps = self.floater_movement_module.reconstruct(ps)
        log('Done.\n')
        log(log_embedding + f'\t= {ps}\n')
        output_to_interfaces['s-structure'] = ps.copy()

        log(log_embedding + '5. Phrasal movement reconstruction...')
        self.phrasal_movement_module.reconstruct(ps)
        log('Done.\n')
        log(log_embedding + f'\t= {ps}\n')

        log(log_embedding + '6. Agreement reconstruction...')
        self.agreement_module.reconstruct(ps)
        log('Done.\n')
        log(log_embedding + f'\t= {ps}\n')

        log(log_embedding + '7. Last resort extraposition...')
        self.extraposition_module.last_resort_reconstruct(ps)
        log('Done.\n')
        log(log_embedding + f'\t= {ps}\n')
        output_to_interfaces['LF structure'] = ps.copy()

        return ps, output_to_interfaces