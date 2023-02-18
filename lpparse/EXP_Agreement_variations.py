from itertools import chain
from feature_processing import *
from support import set_logging, log, report_failure, report_success, log_new_sentence

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
            self.revised(probe)
        if self.brain_model.local_file_system.settings['Agree'] == 'variation1':
            self.variation1(probe)
        if self.brain_model.local_file_system.settings['Agree'] == 'variation2':
            self.variation2(probe)
        if self.brain_model.local_file_system.settings['Agree'] == 'variation3':
            self.variation3(probe)
        if self.brain_model.local_file_system.settings['Agree'] == 'variation4':
            self.variation4(probe)

    def revised(self, probe):
        probe.Agree()

    # Standard theory (Chomsky 2000, 2001, 2008)
    def standard(self, probe):
        pass

    # Standard Agree without PIC
    def variation1(self, probe):
        probe.value_features(next(probe.sister().minimal_search(lambda x: x.head().referential()), probe))
        probe.update_phi_interactions()

    # Standard Agree with specifier agreement as a last resort
    def variation2(self, probe):
        probe.value_features(next(probe.sister().minimal_search(lambda x: x.head().referential() or x.phase_head(), lambda x: not x.phase_head()), next((x for x in probe.edge()), probe)))
        probe.update_phi_interactions()

    # Agree with only specifier-head agreement
    def variation3(self, probe):
        probe.value_features(next((x for x in probe.edge()), probe))
        probe.update_phi_interactions()

    def variation4(self, probe):
        # Go through all unvalued phi-features at the probe
        for unvalued_probe_phi in [phi for phi in probe.head().features if unvalued(phi)]:
            log(f'\n\t\tProbe feature {unvalued_probe_phi} at {probe} ')

            # find goal
            goal = next(probe.sister().minimal_search(lambda x: x.head().referential() or x.phase_head(), lambda x: not x.phase_head()), probe)
            log(f'finds goal {goal} with ')

            # Examine all possible phi-feature candidates at the goal
            for goal_phi in [i(phi_) for phi_ in goal.head().features if probe.target_phi_feature(phi_, goal)]:

                # Examine if valuation of probe_phi by goal_phi is possible
                if goal_phi.startswith(i(unvalued_probe_phi[:-1])):
                    log(f'{goal_phi} and values ')
                    probe.value_feature(goal_phi, unvalued_probe_phi, goal)

        probe.update_phi_interactions()


