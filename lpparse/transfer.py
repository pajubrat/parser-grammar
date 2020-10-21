import phrase_structure
from agreement_reconstruction import AgreementReconstruction
from support import log, enable_logging, disable_logging, is_logging_enabled
from phrasal_reconstruction import PhrasalMovement
from adjunct_reconstruction import FloaterMovement
from head_reconstruction import HeadMovement
from feature_disambiguation import FeatureProcessing
from extraposition import Extraposition
from surface_conditions import SurfaceConditions

# Transfer performs a normalization mapping from phrase structure object into LF-object
# Its function is to repair the first pass parse from errors
class Transfer():
    def __init__(self, controlling_parser_process):
        self.controlling_parser_process = controlling_parser_process
        self.agreement_module = AgreementReconstruction(self.controlling_parser_process)
        self.phrasal_movement_module = PhrasalMovement(self.controlling_parser_process)
        self.floater_movement_module = FloaterMovement(self.controlling_parser_process)
        self.head_movement_module = HeadMovement(self.controlling_parser_process)
        self.feature_process = FeatureProcessing(self.controlling_parser_process)
        self.extraposition = Extraposition(self.controlling_parser_process)
        self.surface_conditions_module = SurfaceConditions()

    def transfer(self, ps, embedding=3):

        log_embedding = embedding * '\t'
        if not is_logging_enabled():
            log(log_embedding + f'Transferring {ps} to LF.')

        surface_conditions = self.surface_conditions_module
        feature_process = self.feature_process
        head_movement = self.head_movement_module
        floater_movement = self.floater_movement_module
        phrasal_movement = self.phrasal_movement_module
        agreement = self.agreement_module
        extraposition = self.extraposition

        log_embedding = log_embedding + '\t'

        self.controlling_parser_process.consume_resources("Transfer")

        log('\n')
        log(log_embedding + '1. Head movement reconstruction...')
        ps = head_movement.reconstruct(ps)
        log('Done.\n')
        log(log_embedding + f'\t= {ps}(' + str(self.controlling_parser_process.time_from_stimulus_onset) + 'ms).\n')

        log(log_embedding + '2. Feature processing...')
        feature_process.disambiguate(ps)
        log('Done.\n')
        log(log_embedding + f'\t= {ps}(' + str(self.controlling_parser_process.time_from_stimulus_onset) + 'ms).\n')

        log(log_embedding + '3. Extraposition...')
        extraposition.reconstruct(ps)
        log('Done.\n')
        log(log_embedding + f'\t= {ps}(' + str(self.controlling_parser_process.time_from_stimulus_onset) + 'ms).\n')

        log(log_embedding + '4. Floater movement reconstruction...')
        ps = floater_movement.reconstruct(ps)
        log('Done.\n')
        log(log_embedding + f'\t= {ps}(' + str(self.controlling_parser_process.time_from_stimulus_onset) + 'ms).\n')

        log(log_embedding + '5. Phrasal movement reconstruction...')
        phrasal_movement.reconstruct(ps)
        log('Done.\n')
        log(log_embedding + f'\t= {ps}(' + str(self.controlling_parser_process.time_from_stimulus_onset) + 'ms).\n')

        log(log_embedding + '6. Agreement reconstruction...')
        agreement.reconstruct(ps)
        log('Done.\n')
        log(log_embedding + f'\t= {ps}(' + str(self.controlling_parser_process.time_from_stimulus_onset) + 'ms).\n')

        log(log_embedding + '7. Last resort extraposition...')
        extraposition.last_resort_reconstruct(ps)
        log('Done.\n')
        log(log_embedding + f'\t= {ps}(' + str(self.controlling_parser_process.time_from_stimulus_onset) + 'ms).\n')
        return ps