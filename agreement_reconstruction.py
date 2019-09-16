from support import set_logging, log, get_number_of_operations, reset_number_of_operations, log_result, illu
from LexicalInterface import LexicalInterface
import minimalist


class AgreementReconstruction():
    def __init__(self):
        pass

    # Processes unvalued (uD,uP) features
    # Checks that phi-agreement dependencies are correct
    def reconstruct(self, ps):
        """
        Current implementation: Finds unvalued phi-features from heads in 'self' and values them (inverse Agree)
        """
        ps_ = ps  # Set starting point

        while ps_:
            # If there is a primitive head to the left...
            if ps_.left_const and ps_.left_const.is_primitive():
                h = ps_.left_const
                # and it is not valued...
                if '-VAL' not in h.features and self.is_unvalued(h):
                    log(f'\t\t\t\t\t{h} has unvalued phi-features {h.get_unvalued_features()}')
                    self.acquire_phi(h)
            ps_ = ps_.walk_downstream()

    # Values phi-features either by phi-Agree or by SPEC
    def acquire_phi(self, h):
        """
        Values the phi-features of a primitive head, if unvalued
        """
        # Values phi_feature phi into h (only if matching unvalued feature is found)
        def value(h, phi):

            def find_unvalued_target(h, phi):
                for g in h.features:
                    if self.unvalued(g):  # We are only concerned with unvalued features
                        g_ = g[:-1]  # Remove the _
                        phi_ = phi[:len(g_)]  # match the remaining portion
                        if g_ == phi_:  # Check if the unvalued feature and the tested phi-feature match
                            return g
                return None

            # Find a possible target to replace
            # The head h must contain a corresponding unvalued feature
            target = find_unvalued_target(h, phi)
            if target:
                if not self.valuation_check(h, phi):
                     phi = self.mark_bad(phi)
                h.features.remove(target)
                h.features.add(phi)
                return True

            return False

        # phi-Agree via probe-goal
        # Returns phi-features, if found, and the goal for logging reasons
        # Looks for a left branch DP with D containing valued phi-features
        # Only consults the closest such element
        def acquire_from_sister(ps):

            ps_ = ps
            phi_features = set()

            while ps_:
                if ps_.left_const and not ps_.is_primitive():
                    goal = ps_.left_const.get_head()
                    if goal.is_phase():
                        break
                    if 'CAT:D' in goal.features:
                        # Collect all valued phi-features (ignore unvalued features)
                        for f in goal.features:
                            if self.phi(f) and self.valued(f):
                                phi_features.add(f)
                        return goal, phi_features  # We only consider the first DP
                ps_ = ps_.walk_downstream()
            return ps, []

        # phi-Agree via Spec-Head
        # Acquires phi-features from SPEC which includes phi-set at the head (from input)
        # Head features are only consulted if no phrase is found from SPEC
        def acquire_from_spec(h):
            if self.get_specifier(h) and 'CAT:D' in self.get_specifier(h)[0].get_head().features:
                head = self.get_specifier(h)[0].get_head()
                phi_features = set()
                for f in head.features:
                    if self.phi(f) and self.valued(f):
                        phi_features.add(f)
                return head, phi_features  # We only consider the first DP
            return None, set()

        # ------------ main function 'acquire_phi()' beings here ----------------#

        phi_features = set()

        # Acquire phi-features by phi-Agree
        goal, phi_features = acquire_from_sister(h.sister())    # Acquire phi-features
        for phi in phi_features:                                #
            if value(h, phi):
                log(f'\t\t\t\t\t{h} acquired ' + str(phi) + f' by phi-Agree from {goal.mother}.')

        # If there are unvalued features left, try Spec-Agree (currently only local DP at SPEC is accepted)
        if self.is_unvalued(h):
            goal, phi_features = acquire_from_spec(h)
            for phi in phi_features:
                if value(h, phi):
                    log(f'\t\t\t\t\t{h} acquired ' + str(phi) + f' from (Spec,{h}).')

    def get_phi_set(self, ps):
        head_ = ps.get_head()
        return {f for f in head_.features if f[:4] == 'PHI:' and len(f.split(':')) == 3}

    def is_unvalued(self, h):
        for feature in h.features:
            if feature[:4] == 'PHI:' and feature[-1] == '_':
                return True
        return False

    def is_valued(self, h):
        for f in h.features:
            if f[:4] == 'PHI:' and f[-1] != '_':
                return True
        return False

    def unvalued(self, f):
        if f[-1] == '_':
            return True
        else:
            return False

    def valued(self, f):
        if not self.unvalued(f):
            return True
        else:
            return False

    def get_type(self, f):
        return f.split(':')[1]

    def get_value(self, f):
        return f.split(':')[2]

    def phi(self, f):
        if f[:4] == 'PHI:':
            return True
        else:
            return False

    def verify_format(self, phi):
        if len(phi.split(':')) == 3:
            return True
        else:
            return False

    def feature_conflict(self, f, phi):
        if self.get_type(f) == self.get_type(phi) and self.get_value(f) != self.get_value(phi) and self.valued(f):
            log(f'\t\t\t\t\t\tFeature conflict between {f} and {phi}.')
            return True
        else:
            return False

    # Checks if head h's unvalued target feature [PHI:F:_] can be valued by phi [PHI:F:x]
    # Conditions:
    # 1. If h has only unvalued features, valuation is always accepted
    # 2. If h has valued features, then an extra condition is that if a valued feature of the same type exists,
    #    then there must exist a matching valued [type:value] pair (i.e. licensing feature).
    def valuation_check(self, h, valued_feature):

        # Completely unvalued heads do not raise an error
        if not self.is_valued(h):
            return True

        # Technical preparations
        valued_feature_type = self.get_type(valued_feature)
        phi_set = self.get_phi_set(h)
        # Must find a matching valued feature (if such exist)
        for phi in phi_set:
            # If we find an existing feature of the same type...
            if self.valued(phi) and self.get_type(phi) == valued_feature_type:
                # ...then we must also find a matching feature
                for g in phi_set:
                    if g == valued_feature:
                        return True
                # If matching feature is not found, valuation is not licensed
                log(f'\t\t\t\t\Feature {valued_feature} was not matched in {h}.')
                return False
        # If type was not matched, then valuation is again possible
        return True

    def mark_bad(self, phi):
        return phi + '*'

    # Interface wrapper for agreement module
    def get_specifier(self, h):
        return(h.get_specifiers_for_agreement_reconstruction())
