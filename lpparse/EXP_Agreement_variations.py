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
        if self.brain_model.local_file_system.settings['Agree'] == 'variation1':
            self.variation1(probe)
        if self.brain_model.local_file_system.settings['Agree'] == 'variation2':
            self.variation2(probe)
        if self.brain_model.local_file_system.settings['Agree'] == 'variation3':
            self.variation3(probe)
        if self.brain_model.local_file_system.settings['Agree'] == 'variation4':
            self.variation4(probe)

    def revised(self, probe):
        return probe.Agree()

    # Standard theory (Chomsky 2000, 2001, 2008)
    # We construct this entity for experimental purposes by backtracking the changes of the revised model
    def standard(self, probe):
        def value_features(probe, goal):
            log(f'\n\t\t{probe} Agree with {goal.illustrate()} and values ')
            # Replace iPHI features with PHI features
            valuations = [(i(phi), probe.unvalued_counterparty(i(phi))) for phi in goal.head().features if
                          probe.target_phi_feature(phi, goal)]
            for incoming_phi, unvalued_counterparty in valuations:
                probe.value_feature(incoming_phi, unvalued_counterparty, goal)

        def Agree(self):
            probe.features.discard('!SELF:Φ1')
            probe.features.discard('!SELF:Φ12')
            probe.features.discard('-SELF:Φ1')
            probe.features.discard('-SELF:Φ12')
            probe.features.discard('!SELF:ΦPF')
            probe.features.discard('-COMP:PER')
            probe.features.discard('PER')
            probe.features.discard('-PER')
            probe.features = {i(f) for f in probe.features}
            self.value_features(next(self.sister().minimal_search(lambda x: x.head().referential() or x.phase_head(),
                                                                  lambda x: not x.phase_head()), self))

        # --- main ---
        Agree(probe)

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

