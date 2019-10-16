from support import set_logging, log, get_number_of_operations, reset_number_of_operations, log_result, illu
from LexicalInterface import LexicalInterface
import phase_structure


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

        # Operation 2. phi-Agree via edge
        # Acquires phi-features from edge
        def acquire_from_edge(h):
            edge_list = h.get_edge()
            if edge_list:
                for edge in edge_list:
                    edge_head = edge.get_head()
                    # Condition 1. The element must be D(P)
                    # Condition 2. The element must not have moved away
                    if 'CAT:D' in edge_head.features and not edge.find_me_elsewhere:
                        phi_features = set()
                        for f in edge_head.features:
                            # Condition 3. Get valued phi-features from DP
                            if self.phi(f) and self.valued(f):
                                phi_features.add(f)
                        return edge_head, phi_features  # We only consider the first DP
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
        # Operation 2. If there are unvalued features left, try edge-Agree
        #
        if self.is_unvalued(h):
            # Condition 2. Acquire phi-features from SPEC
            goal, phi_features = acquire_from_edge(h)
            for phi in phi_features:
                if value(h, phi):
                    log(f'\t\t\t\t\t{h} acquired ' + str(phi) + f' from the edge of {h}.')

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

        # If the type match but value does not, the result is feature conflict
        if self.get_type(f) == self.get_type(phi) and self.get_value(f) != self.get_value(phi) and self.valued(f):

            log(f'\t\t\t\t\t\tFeature conflict between {f} and {phi}.')
            return True
        else:
            return False

    # Checks if the probe ('h') already has valued phi-features (e.g. from agreement suffixes) and if yes,
    # that a matching (licensing) feature is found
    # Condition 1. If h has only unvalued features, valuation is never blocked (only check valued features)
    # Condition 2. If h has valued features, then check if a valued feature of the same type must exist
    # Thus, valued features are interpreted as licensors.
    def valuation_check(self, h, valued_feature):

        # Completely unvalued heads do not raise an error
        if not self.is_valued(h):
            return True

        # Technical preparations
        valued_feature_type = self.get_type(valued_feature)
        phi_set = self.get_phi_set(h)

        # Must find a matching valued feature from head h (if exists)
        for phi in phi_set:

            # If we find an existing feature of the same type...
            if self.valued(phi) and self.get_type(phi) == valued_feature_type:

                # ...then we must also find a matching feature
                for g in phi_set:
                    if g == valued_feature:
                        return True

                # If matching feature is not found, valuation is not licensed
                log(f'\t\t\t\t\tFeature {valued_feature} was not matched in {h} and was marked as bad.')
                return False

        # If type was not matched, then valuation is again possible
        return True

    def mark_bad(self, phi):
        return phi + '*'
