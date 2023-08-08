from itertools import chain
from feature_processing import *
from support import set_logging, log, report_failure, report_success, log_new_sentence

# Separate class for alternative formulations for the Agree mechanism
# Standard agreement is implemented in the phrase structure class; this contains only experimental versions
class AgreementVariations:
    def __init__(self, brain_model):
        self.brain_model = brain_model
        pass

    def Agree(self, probe, transfer):
        if self.brain_model.local_file_system.settings['Agree'] == 'standard':
            self.standard(probe)
        if self.brain_model.local_file_system.settings['Agree'] == 'revised':
            self.revised(probe)

    def revised(self, probe):
        return probe.AgreeLF()

    # Standard theory (Chomsky 2000, 2001, 2008)
    def standard(self, probe):
        def phase_head(probe):
            return probe.check_some({'v', 'C', 'FORCE'}) and not probe.check_some({'v-'})

        def goal_selection(probe):
            return not probe.find_me_elsewhere and (probe.head().referential() or phase_head(probe))

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
                goal = next(probe.sister().minimal_search(lambda x: goal_selection(x), lambda x: not phase_head(x)), None)
                probe.value_features_from(goal)

        Agree(probe)