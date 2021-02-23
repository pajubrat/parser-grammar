from agreement_reconstruction import AgreementReconstruction
from support import log, is_logging_enabled
from phrasal_reconstruction import PhrasalMovement
from adjunct_reconstruction import FloaterMovement
from head_reconstruction import HeadMovement
from feature_disambiguation import FeatureProcessing
from extraposition import Extraposition
from surface_conditions import SurfaceConditions

# Transfer performs a normalization mapping from phrase structure object into LF-object
# Its function is to repair the first pass parse from errors
class Transfer:
    def __init__(self, controlling_parser_process):
        self.controlling_parser_process = controlling_parser_process
        self.agreement_module = AgreementReconstruction(self.controlling_parser_process)
        self.phrasal_movement_module = PhrasalMovement(self.controlling_parser_process)
        self.floater_movement_module = FloaterMovement(self.controlling_parser_process)
        self.head_movement_module = HeadMovement(self.controlling_parser_process)
        self.feature_process_module = FeatureProcessing(self.controlling_parser_process)
        self.extraposition_module = Extraposition(self.controlling_parser_process)
        self.surface_conditions_module = SurfaceConditions()

    def transfer(self, ps, embedding=3):
        """
        Transfers the spellout structure to the LF-interface.
        """

        log_embedding = embedding * '\t'
        if not is_logging_enabled():
            log(log_embedding + f'Transferring {ps} to LF.')

        log_embedding = log_embedding + '\t'

        self.controlling_parser_process.consume_resources("Transfer", f'{ps}')

        log('\n')
        log(log_embedding + '1. Head movement reconstruction...')
        ps = self.head_movement_module.reconstruct(ps)
        log('Done.\n')
        log(log_embedding + f'\t= {ps}(' + str(self.controlling_parser_process.time_from_stimulus_onset) + 'ms).\n')

        log(log_embedding + '2. Feature processing...')
        self.feature_process_module.disambiguate(ps)
        log('Done.\n')
        log(log_embedding + f'\t= {ps}(' + str(self.controlling_parser_process.time_from_stimulus_onset) + 'ms).\n')

        log(log_embedding + '3. Extraposition...')
        self.extraposition_module.reconstruct(ps)
        log('Done.\n')
        log(log_embedding + f'\t= {ps}(' + str(self.controlling_parser_process.time_from_stimulus_onset) + 'ms).\n')

        log(log_embedding + '4. Floater movement reconstruction...')
        ps = self.floater_movement_module.reconstruct(ps)
        log('Done.\n')
        log(log_embedding + f'\t= {ps}(' + str(self.controlling_parser_process.time_from_stimulus_onset) + 'ms).\n')

        log(log_embedding + '5. Phrasal movement reconstruction...')
        self.phrasal_movement_module.reconstruct(ps)
        log('Done.\n')
        log(log_embedding + f'\t= {ps}(' + str(self.controlling_parser_process.time_from_stimulus_onset) + 'ms).\n')

        log(log_embedding + '6. Agreement reconstruction...')
        self.agreement_module.reconstruct(ps)
        log('Done.\n')
        log(log_embedding + f'\t= {ps}(' + str(self.controlling_parser_process.time_from_stimulus_onset) + 'ms).\n')

        log(log_embedding + '7. Last resort extraposition...')
        self.extraposition_module.last_resort_reconstruct(ps)
        log('Done.\n')
        log(log_embedding + f'\t= {ps}(' + str(self.controlling_parser_process.time_from_stimulus_onset) + 'ms).\n')

        return ps