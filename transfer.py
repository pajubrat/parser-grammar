import minimalist
from reconstruction import Reconstruction
from morphology import Morphology
from agreement_reconstruction import AgreementReconstruction
from support import log
from context import Context
from phrasal_movement import PhrasalMovement
from floater_movement import FloaterMovement
from head_movement import HeadMovement
from feature_disambiguation import FeatureProcessing

class Transfer():
    def __init__(self, context):
        self.context = Context()
        self.movement_module = Reconstruction(context)
        self.agreement_module = AgreementReconstruction()
        self.phrasal_movement_module = PhrasalMovement(context)
        self.floater_movement_module = FloaterMovement(context)
        self.head_movement_module = HeadMovement(context)
        self.feature_process = FeatureProcessing()

    def transfer(self, ps, context):
        log(f'\t\t\tTransferring {ps} to LF.')

        # Activate modules
        feature_process = self.feature_process
        head_movement = self.head_movement_module
        floater_movement = self.floater_movement_module
        phrasal_movement = self.phrasal_movement_module
        agreement = self.agreement_module

        # Allow each module to operate with the PS representation in a sequence
        log('\t\t\t\thead movement reconstruction:')
        ps, ops = head_movement.reconstruct(ps)
        log('\t\t\t\tFeature processing:')
        feature_process.disambiguate(ps)
        log('\t\t\t\tFloater movement reconstruction:')
        floater_movement.reconstruct(ps)
        log('\t\t\t\tPhrasal movement reconstruction:')
        phrasal_movement.reconstruct(ps)
        log('\t\t\t\tAgreement reconstruction:')
        agreement.reconstruct(ps)

        return ps



