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
    def transfer(self, ps):
        log(f'\t\t\tTransferring {ps} to LF.')

        # Activate modules
        feature_process = self.feature_process
        head_movement = self.head_movement_module
        floater_movement = self.floater_movement_module
        phrasal_movement = self.phrasal_movement_module
        agreement = self.agreement_module
        extraposition = self.extraposition

        # Allow each module to operate with the phrase structure in a sequence

        # Stage 1. Reconstruct head movement
        log('\t\t\t\t1. Head movement reconstruction:')
        ps, ops = head_movement.reconstruct(ps)
        log(f'\t\t\t\t\t={ps}')

        # Stage 2. Reconstruct features
        log('\t\t\t\t2. Feature processing:')
        feature_process.disambiguate(ps)
        log(f'\t\t\t\t\t={ps}')

        log('\t\t\t\t3. Extraposition:')
        extraposition.reconstruct(ps)
        log(f'\t\t\t\t\t={ps}')

        # Stage 3. Reconstruct floater movement
        log('\t\t\t\t3. Floater movement reconstruction:')
        floater_movement.reconstruct(ps)
        log(f'\t\t\t\t\t={ps}')

        # Stage 4. Reconstruct phrasal movement
        log('\t\t\t\t4. Phrasal movement reconstruction:')
        phrasal_movement.reconstruct(ps)
        log(f'\t\t\t\t\t={ps}')

        # Stage 5. Reconstruct agreement
        log('\t\t\t\t5. Agreement reconstruction:')
        agreement.reconstruct(ps)
        log(f'\t\t\t\t\t={ps}')

        return ps



