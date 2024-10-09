from feature_processing import *


# Separate class for alternative formulations for the Agree mechanism
# Standard agreement is implemented in the phrase structure class; this contains only experimental versions
class ExperimentalFunctions:
    def __init__(self, speaker_model):
        self.speaker_model = speaker_model
        pass

    def Agree(self, X):
        if self.speaker_model.settings.retrieve('UG_parameter_Agree', 'revised') == 'standard':
            self.standard(X)
        else:
            self.revised(X)

    def revised(self, X):
        return X.AgreeLF()

    # Standard theory (Chomsky 2000, 2001, 2008)
    def standard(self, X):
        """
        This implements the standard Agree model and replaces the revised model that
        is part of the current model. It is implemented by regressing from the
        revised model.
        """
        def goal_selection(X):
            return not X.copied and (X.H().referential() or self.standard_Chomskian_phase_head(X))

        def value_from_goal(X, goal):
            if goal:
                goal.H().features = {i(f) for f in goal.H().features}
                log(f'\n\t\tAgree({X}°, {goal.H()}) ')
                if feature_licensing(goal.H().phi_features(), X.phi_bundles()) and X.Condition_on_agreement_and_EPP(goal):
                    value(X, goal)
                else:
                    X.features.add('*')

        def value(X, goal):
            log(f'valued features ')
            for phi in (x for x in goal.H().features if x.startswith('PHI') and f'PHI:{x.split(":")[1]}:_' in X.features):
                log(f'[{phi[4:]}] ')
                X.features.discard(f'PHI:{phi.split(":")[1]}:_')
                X.features.add(f'{phi}')
            X.features.add(f'PHI:IDX:{goal.H().get_id()}')
            X.features.add('ΦLF')

        def Agree(X):
            """
            Remove features that are part of the revised model
            """
            X.features.discard('+ΦLF,ΦPF')  #   Removes PHI>0 condition
            X.features.discard('-ΦLF,ΦPF')  #   Removes PHI=1 condition
            X.features.discard('?ΦLF,ΦPF')  #
            X.features.discard('!ΦPF')      #   Cannot force agreement
            X.features.discard('!ΦLF')      #   Cannot force Agree
            X.features.discard('!PER')      #   This removes the inheritance mechanism
            X.features.discard('-PER')      #
            X.features.discard('weak_pro')  #   This removes the pro-projection principle
            if X.sister():
                goal = next((x for x in X.sister().minimal_search(lambda x: self.standard_Chomskian_phase_head(x)) if x.goal_selection()), None)
                value_from_goal(X, goal)
        Agree(X)

    def standard_Chomskian_phase_head(self, X):
        return X.zero_level() and X.check_some({'v', 'C', 'FORCE'}) and not X.check_some({'v-'})

