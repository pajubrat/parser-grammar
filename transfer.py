import phrase_structure
from agreement_reconstruction import AgreementReconstruction
from support import log
from phrasal_movement import PhrasalMovement
from floater_movement import FloaterMovement
from head_movement import HeadMovement
from feature_disambiguation import FeatureProcessing
from extraposition import Extraposition

# Transfer performs a normalization mapping from phrase structure object into LF-object
# Its function is to repair the first pass parse from errors
class Transfer():

    def __init__(self, controlling_parser_process):
        self.controlling_parser_process = controlling_parser_process
        self.agreement_module = AgreementReconstruction()
        self.phrasal_movement_module = PhrasalMovement(self.controlling_parser_process)
        self.floater_movement_module = FloaterMovement(self.controlling_parser_process)
        self.head_movement_module = HeadMovement(self.controlling_parser_process)
        self.feature_process = FeatureProcessing(self.controlling_parser_process)
        self.extraposition = Extraposition(self.controlling_parser_process)

    # Transfer
    def transfer(self, ps, embedding=3):
        log_embedding = embedding * '\t'

        log(log_embedding + f'Transferring {ps} to LF.')

        # Activate modules
        feature_process = self.feature_process
        head_movement = self.head_movement_module
        floater_movement = self.floater_movement_module
        phrasal_movement = self.phrasal_movement_module
        agreement = self.agreement_module
        extraposition = self.extraposition

        log_embedding = log_embedding + '\t'

        # Allow each module to operate with the phrase structure in a sequence

        # Stage 1. Reconstruct head movement
        log(log_embedding + '1. Head movement reconstruction:')
        ps, ops = head_movement.reconstruct(ps)
        log(log_embedding + f'={ps}')

        # Stage 2. Reconstruct features
        log(log_embedding + '2. Feature processing:')
        feature_process.disambiguate(ps)
        log(log_embedding + f'={ps}')

        log(log_embedding + '3. Extraposition:')
        extraposition.reconstruct(ps)
        log(log_embedding + f'={ps}')

        # Stage 3. Reconstruct floater movement
        log(log_embedding + '4. Floater movement reconstruction:')
        floater_movement.reconstruct(ps)
        log(log_embedding + f'={ps}')

        # Stage 4. Reconstruct phrasal movement
        log(log_embedding + '5. Phrasal movement reconstruction:')
        phrasal_movement.reconstruct(ps)
        log(log_embedding + f'={ps}')

        # Stage 5. Reconstruct agreement
        log(log_embedding + '6. Agreement reconstruction:')
        agreement.reconstruct(ps)
        log(log_embedding + f'={ps}')

        return ps



