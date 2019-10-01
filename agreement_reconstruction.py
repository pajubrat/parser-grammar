from support import set_logging, log, get_number_of_operations, reset_number_of_operations, log_result, illu
from LexicalInterface import LexicalInterface
import minimalist


class AgreementReconstruction():
    def __init__(self):
        pass

    # Definition for agreement reconstruction
    def reconstruct(self, ps):

        # Crawl through the structure in a downward direction
        ps_ = ps
        while ps_:

            # Condition 1. There is a primitive head to the left
            if ps_.left_const and ps_.left_const.is_primitive():
                h = ps_.left_const

                # Condition 2. The head requires feature valuation
                if '-VAL' not in h.features and self.is_unvalued(h):
                    log(f'\t\t\t\t\t{h} has unvalued phi-features {h.get_unvalued_features()}')

                    # The head acquires phi-feature
                    self.acquire_phi(h)

            ps_ = ps_.walk_downstream()

    # Definition for phi-feature acquisition
    def acquire_phi(self, h):

        # Internal functions
        # Function 1. Values phi_feature 'phi' into h if matching unvalued feature is found
        def value(h, phi):

            # Internal function
            # Definition for unvalued target feature
            def find_unvalued_target(h, phi):
                for g in h.features:
                    if self.unvalued(g):        # We are only concerned with unvalued features
                        g_ = g[:-1]             # Remove the _
                        phi_ = phi[:len(g_)]    # Match the remaining portion
                        if g_ == phi_:          # Check if the unvalued feature and the tested phi-feature match
                            return g
                return None

            # Provides a target feature inside h for feature 'phi'
            target = find_unvalued_target(h, phi)
            if target:

                # Checks for phi-feature conflicts
                if not self.valuation_check(h, phi):

                    # In the case of conflict, we mark the feature bad
                    phi = self.mark_bad(phi)

                # Remove the unvalued version of the phi-feature F:_
                h.features.remove(target)

                # Add the valued version F:X
                h.features.add(phi)
                return True

            return False

        # Operation 1. Acquire phi-feature from sister
        # Looks for the closest left branch DP with D containing valued phi-features inside its sister
        # [H [...DP XP]]
        def acquire_from_sister(ps):

            # (This could be defined by means of universal probe-goal search)
            ps_ = ps
            phi_features = set()

            # Downstream loop
            while ps_:

                # Condition 1. XP  is left and is not primitive
                if ps_.left_const and not ps_.is_primitive():

                    goal = ps_.left_const.get_head()

                    # Condition 2. Stop at a phase boundary (no long distance probing)
                    if goal.is_phase():
                        break

                    # Condition 3. Look for DPs
                    if 'CAT:D' in goal.features:

                        # Collect all valued phi-features (ignore unvalued features)
                        for f in goal.features:
                            if self.phi(f) and self.valued(f):
                                phi_features.add(f)
                        return goal, phi_features  # We only consider the first DP
                ps_ = ps_.walk_downstream()
            return ps, []

        # Operation 2. phi-Agree via Spec-Head
        # Acquires phi-features from SPEC which includes phi-set at the head (from input)
        # Head features are only consulted if no phrase is found from SPEC
        def acquire_from_spec(h):

            # Condition 1. We examine only the local specifier.
            # Condition 2. It must be a DP.
            if h.get_specifiers() and 'CAT:D' in h.get_specifiers()[0].get_head().features:
                head = h.get_specifiers()[0].get_head()
                phi_features = set()
                for f in head.features:

                    # Condition 3. Get valued phi-features from DP
                    if self.phi(f) and self.valued(f):
                        phi_features.add(f)

                return head, phi_features  # We only consider the first DP
            return None, set()

        # ------------ main function 'acquire_phi()' beings here ----------------#

        phi_features = set()

        #
        # Operation 1. Acquire phi-features by phi-Agree
        #
        goal, phi_features = acquire_from_sister(h.sister())    # Acquire phi-features
        for phi in phi_features:                                # Try to value
            if value(h, phi):
                log(f'\t\t\t\t\t{h} acquired ' + str(phi) + f' by phi-Agree from {goal.mother}.')

        #
        # Operation 2. If there are unvalued features left, try Spec-Agree
        #
        if self.is_unvalued(h):
            # Condition 1. Acquire phi-features from SPEC
            goal, phi_features = acquire_from_spec(h)
            for phi in phi_features:
                if value(h, phi):
                    log(f'\t\t\t\t\t{h} acquired ' + str(phi) + f' from (Spec,{h}).')

        # --------------- main function ends ---------------------------------------#

    # Get a set of phi-features from head
    def get_phi_set(self, ps):
        head_ = ps.get_head()
        return {f for f in head_.features if f[:4] == 'PHI:' and len(f.split(':')) == 3}

    # Definition for unvalued phi-feature
    def is_unvalued(self, h):
        for feature in h.features:
            if feature[:4] == 'PHI:' and feature[-1] == '_':
                return True
        return False

    # Definition for valued phi-feature
    def is_valued(self, h):
        for f in h.features:
            if f[:4] == 'PHI:' and f[-1] != '_':
                return True
        return False

    # Definition for unvalued feature
    def unvalued(self, f):
        if f[-1] == '_':
            return True
        else:
            return False

    # Definition for valued feature
    def valued(self, f):
        if not self.unvalued(f):
            return True
        else:
            return False

    # Definition of the phi-feature TYPE
    def get_type(self, f):
        return f.split(':')[1]

    # Definition of phi-feature VALUE
    def get_value(self, f):
        return f.split(':')[2]

    # Definition for PHI-feature
    def phi(self, f):
        if f[:4] == 'PHI:':
            return True
        else:
            return False

    # Definition for feature conflict
    def feature_conflict(self, f, phi):

        # If the type match but value does not, the result is a feature conflict
        if self.get_type(f) == self.get_type(phi) and self.get_value(f) != self.get_value(phi) and self.valued(f):
            log(f'\t\t\t\t\t\tFeature conflict between {f} and {phi}.')
            return True
        else:
            return False

    # Checks if head h's unvalued target feature [PHI:F:_] can be valued by phi [PHI:F:V]
    # Condition 1. If h has only unvalued features, valuation is never blocked
    # Condition 2. If h has valued features, then if a valued feature of the same type
    # exists, it must have a matching value.
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
