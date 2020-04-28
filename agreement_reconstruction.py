from support import set_logging, log, get_number_of_operations, reset_number_of_operations, log_result, illu


class AgreementReconstruction:
    def __init__(self):
        pass

    # Definition for agreement reconstruction
    # Walk downstream, force head H acquire phi-features if and only if
    # Condition 1. H is a primitive head to the left AND
    # Condition 2. H requires feature valuation
    def reconstruct(self, ps):

        # Downstream walk
        ps_ = ps
        while ps_:

            # Condition 1. There is a primitive head to the left
            if ps_.left_const and ps_.left_const.is_primitive():
                h = ps_.left_const

                # Condition 2. The head requires feature valuation
                if '-VAL' not in h.features and self.is_unvalued(h):
                    # The head acquires phi-feature
                    log(f'\t\t\t\t\tHead {h}, lacking -VAL, has unvalued phi probe and triggered Agree-1:')
                    self.acquire_phi(h)

            ps_ = ps_.walk_downstream()

    # Definition for phi-feature acquisition
    # H (with unvalued phi) acquires phi-features from
    # Operation 1. The edge (DP specs plus head, in that order)
    # Operation 2. From the left branch DPs within the sister, up to first target and a phase boundary
    def acquire_phi(self, h):

        #
        # Operation 1. Try edge-Agree
        #
        # Pick up the target (goal) and its phi-features
        goal, phi_features = self.acquire_from_edge(h)
        for phi in phi_features:
            # Try to value phi-features fromm the goal into the probe head h
            if self.value(h, phi):
                log(f'\t\t\t\t\t\t{h} acquired ' + str(phi) + f' from the edge of {h}.')
                # Agreement leads into phi-checking, which prevents pro-extraction from the same head

        #
        # Operation 2. Acquire phi-features from sister by sister-Agree
        #
        # Condition 1. The head has unvalued phi-features after edge-Agree (Operation 1)
        if self.is_unvalued(h):
            goal, phi_features = self.acquire_from_sister(h.sister())  # Acquire phi-features
            for phi in phi_features:  # Try to value
                if self.value(h, phi):
                    log(f'\t\t\t\t\t\t{h} acquired ' + str(phi) + f' by phi-Agree from {goal.mother}.')
                    # Agreement leads into phi-checking
                    h.features.add('PHI_CHECKED')

    # Definition for sister-Agree
    # Looks for the closest left branch DP with D containing valued phi-features inside its sister
    # [H [...DP XP]] and returns the goal and a set of phi-features in it.
    # ps = sister of the head acquiring phi-features
    def acquire_from_sister(self, ps):

        ps_ = ps

        # Downstream loop
        while ps_:

            # Condition 1. XP is left and is not primitive
            # [H [XP YP]]
            if ps_.left_const and ps_.is_complex():

                goal = ps_.left_const.get_head()

                # Condition 2. Stop at a phase boundary (no long distance probing)
                # Phase is defined as {v, C, Force, BE}, but this is stipulation
                if goal.is_phase():
                    break

                # Condition 3. Look for DPs
                if 'CAT:D' in goal.features:

                    # Collect all valued phi-features (ignore unvalued features)
                    return goal, sorted({f for f in goal.features if self.phi(f) and self.valued(f)})
            ps_ = ps_.walk_downstream()
        return ps_, {}

    # Operation 2. phi-Agree via edge
    # Acquires phi-features from edge
    def acquire_from_edge(self, h):
        edge_list = self.get_edge_for_Agree(h)
        if edge_list:
            for edge in edge_list:
                edge_head = edge.get_head()
                # Condition 1. The element must be D(P)
                if 'CAT:D' in edge_head.features:
                    phi_features = set()
                    for f in edge_head.features:
                        # Condition 3. Get valued phi-features from DP
                        if self.phi(f) and self.valued(f):
                            phi_features.add(f)
                    return edge_head, sorted(phi_features)  # We only consider the first DP
        return None, set()

    # Values unvalued features in a head h with valued feature phi
    def value(self, h, phi):

        # Provides a target feature set inside h for feature phi
        # e.g. all [PHI:F:__] is a target for [PHI:F:x]
        target = self.find_unvalued_target(h, phi)
        if target:

            # Checks for phi-feature conflicts
            # In the case of conflict, we mark the feature bad
            if not self.valuation_check(h, phi):
                phi = self.mark_bad(phi)

            # Remove the unvalued version of the phi-feature F:_
            h.features = h.features - target

            # Add the valued version F:X
            h.features.add(phi)
            return True
        return False

    # Definition for unvalued target feature
    # [PHI:F:_] in h is a target for [PHI:F:x] (phi)
    def find_unvalued_target(self, h, phi):
        return {f for f in h.features if self.unvalued(f) and f[:-1]==phi[:len(f[:-1])]}

    # Get a set of phi-features from head pf
    # Condition 1. Feature begins with "PHI:"
    # Condition 2. It has three parts separated by ":"
    def get_phi_set(self, ps):
        return {f for f in ps.get_head().features if f[:4] == 'PHI:' and len(f.split(':')) == 3}

    # Definition for whether h has unvalued phi-features
    # Condition 1. Feature begins with "PHI:"
    # Condition 2. Feature ends with "_"
    def is_unvalued(self, h):
        return {f for f in h.features if f[:4] == 'PHI:' and f[-1] == '_'}

    # Definition for valued phi-feature
    # Condition 1. Feature begins with "PHI:"
    # Condition 2. Feature does not end with "_"
    def is_valued(self, h):
        return {f for f in h.features if f[:4] == 'PHI:' and f[-1] != '_'}

    # Definition for unvalued feature
    # Condition 1. Feature ends with "_"
    def unvalued(self, input_feature):
        return {f for f in {input_feature} if f[-1] == '_'}

    # Definition for valued feature
    # Condition 1. Feature is not unvalued
    def valued(self, input_feature):
        return {f for f in {input_feature} if not self.unvalued(f)}

    # Definition of the phi-feature TYPE
    def get_type(self, f):
        return f.split(':')[1]

    # Definition of phi-feature VALUE
    def get_value(self, f):
        return f.split(':')[2]

    # Definition for PHI-feature
    def phi(self, input_feature):
        return {f for f in {input_feature} if f[:4] == 'PHI:'}

    # Definition for feature conflict
    def feature_conflict(self, f, phi):
        # If the type match but value does not, the result is feature conflict
        if self.get_type(f) == self.get_type(phi) and self.get_value(f) != self.get_value(phi) and self.valued(f):
            log(f'\t\t\t\t\t\tFeature conflict between {f} and {phi}.')
            return True
        else:
            return False

    # Allow valuation if and only if
    # Condition 1. h has only unvalued features OR
    # Condition 2. if h has valued feature of the same type, it must have a matching 'type:value'.
    def valuation_check(self, h, valued_feature):

        # Condition 1.
        # Completely unvalued (no valued feature) heads do not raise an error
        if not self.is_valued(h):
            return True

        # Technical preparations
        valued_input_feature_type = self.get_type(valued_feature)
        heads_phi_set = self.get_phi_set(h)

        # Condition 2.
        # Must find a matching valued feature from head h (if exists)
        for heads_phi_feature in heads_phi_set:

            # If we find an existing feature of the same type...
            if self.valued(heads_phi_feature) and self.get_type(heads_phi_feature) == valued_input_feature_type:

                # ...then we must also find a matching feature
                for g in heads_phi_set:
                    if g == valued_feature:
                        return True

                # If matching feature is not found, valuation is not licensed
                log(f'\t\t\t\t\t\tFeature {valued_feature} was not matched in {h} and was marked as bad.')
                return False

        # If type was not matched, then valuation is again possible
        return True

    def mark_bad(self, phi):
        return phi + '*'

    # Definition of edge (of head h ('self'), h must be primitive)
    def get_edge_for_Agree(self, h):

        # Presupposition 1. h is complex
        if h.is_complex():
            return None

        if h.is_right():
            ps_ = h
        else:
            ps_ = h.mother

        edge_list = []

        # Condition 1. If there is pro, include it as the first element
        if h.extract_pro():
            edge_list.append(h.extract_pro())

        # Condition 2. Include XPs if and only if
        #   Condition 2A. XP is left to dominating node
        #   Condition 2B. XP is complex
        # until an element is found that does not satisfy 2A-B
        while ps_ and ps_.sister() and (ps_.sister().is_left() and ps_.sister().is_complex()):
            edge_list.append(ps_.sister())
            ps_ = ps_.walk_upstream()

        # Reverse the list (top-down order)
        return edge_list[::-1]