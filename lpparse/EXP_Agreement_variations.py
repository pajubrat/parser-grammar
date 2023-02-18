from itertools import chain

# Separate class for alternative formulations for the Agree mechanism
# Standard agreement is implemented in the phrase structure class; this contains only experimental versions
class AgreementVariations:
    def __init__(self, brain_model):
        self.brain_model = brain_model
        pass

    def Agree(self, probe):
        if self.brain_model.local_file_system.settings['Agree'] == 'standard':
            probe.standard(probe)
        if self.brain_model.local_file_system.settings['Agree'] == 'revised':
            probe.Agree()
        if self.brain_model.local_file_system.settings['Agree'] == 'variation1':
            self.variation1(probe)
        if self.brain_model.local_file_system.settings['Agree'] == 'variation2':
            self.variation2(probe)
        if self.brain_model.local_file_system.settings['Agree'] == 'variation3':
            self.variation3(probe)
        if self.brain_model.local_file_system.settings['Agree'] == 'variation4':
            self.variation4(probe)

    # Standard theory (Chomsky 2000, 2001, 2008)
    def standard(self, probe):
        pass

    # Standard Agree without PIC
    def variation1(self, probe):
        probe.value_features(next(probe.sister().minimal_search(lambda x: x.head().referential()), probe))
        probe.update_phi_interactions()  # Revised theory of Agree

    # Standard Agree with specifier agreement as a last resort
    def variation2(self, probe):
        edge = chain(probe.edge(), probe)
        probe.value_features(next(probe.sister().minimal_search(lambda x: x.head().referential() or x.phase_head(), lambda x: not x.phase_head()), edge))
        probe.update_phi_interactions()  # Revised theory of Agree

    # Standard Agree with unlimited upwards path as a last resort
    def variation3(self, probe):
        edge = chain(probe.upward_path(), probe)
        probe.value_features(next(probe.sister().minimal_search(lambda x: x.head().referential() or x.phase_head(), lambda x: not x.phase_head()), edge))
        probe.update_phi_interactions()  # Revised theory of Agree

    # Agree with only specifier-head agreement
    def variation4(self, probe):
        probe.value_features(next(probe.edge(), probe))
        probe.update_phi_interactions()  # Revised theory of Agree

