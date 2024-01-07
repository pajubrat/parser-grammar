from feature_processing import *


# Separate class for alternative formulations for the Agree mechanism
# Standard agreement is implemented in the phrase structure class; this contains only experimental versions
class ExperimentalFunctions:
    def __init__(self, speaker_model):
        self.speaker_model = speaker_model
        pass

    def Agree(self, probe):
        if self.speaker_model.settings.get()['UG_parameter_Agree'] == 'standard':
            self.standard(probe)
        if self.speaker_model.settings.get()['UG_parameter_Agree'] == 'revised':
            self.revised(probe)

    def revised(self, probe):
        return probe.AgreeLF()

    # Standard theory (Chomsky 2000, 2001, 2008)
    def standard(self, probe):
        def goal_selection(probe):
            return not probe.find_me_elsewhere and (probe.head().referential() or self.standard_Chomskian_phase_head(probe))

        def Agree(probe):
            probe.features.discard('+ΦLF,ΦPF')
            probe.features.discard('!ΦLF,ΦPF')
            probe.features.discard('-ΦLF,ΦPF')
            probe.features.discard('!ΦPF')
            probe.features.discard('!ΦLF')
            probe.features.discard('!PER')
            probe.features.discard('-PER')
            # Remove distinction between [PHI] and [iPHI]
            probe.features = {i(f) for f in probe.features}
            if probe.sister():
                goal = next(probe.sister().minimal_search(lambda x: goal_selection(x), lambda x: not self.standard_Chomskian_phase_head(x)), None)
                probe.value_features_from(goal)

        Agree(probe)

    def standard_Chomskian_phase_head(self, probe):
        return probe.primitive() and probe.check_some({'v', 'C', 'FORCE'}) and not probe.check_some({'v-'})

