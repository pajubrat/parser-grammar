from support import set_logging, log, get_number_of_operations, reset_number_of_operations, log_result, illu

# Agreement reconstruction is performed as part of Transfer
# It tries to value unvalued phi-features of head H, if any, by Agree-1
# The function motivation is to locate a DP argument from the surface PF-input


class AgreementReconstruction:
    def __init__(self):
        pass

    # Definition for agreement reconstruction
    # Walk downstream, force any head H to acquire phi-features if and only if
    # Condition 1. H is a primitive head to the left AND
    # Condition 2. H requires feature valuation (VAL)
    #
    # Note: Even if H has valued phi, we must Agree-1 to verify that there is no mismatching subject inside sister
    def reconstruct(self, ps):

        # Downstream walk
        ps_ = ps
        while ps_:

            # Condition 1. There is a primitive head to the left
            if ps_.left_const and ps_.left_const.is_primitive():
                h = ps_.left_const

                # Condition 2. The head requires feature valuation (does not have feature -VAL)
                # (Thus, VAL is assumed to be the default unless explicitly blocked)
                if '-VAL' not in h.features:
                    #
                    # The head acquires phi-feature
                    #
                    log(f'\t\t\t\t\tHead {h} triggers Agree-1:')
                    self.acquire_phi(h)

            ps_ = ps_.walk_downstream()

    # Definition for phi-feature acquisition (Agree-1)
    # H (with unvalued phi) acquires phi-features from
    # (1) ....the left branch DPs within the sister, up to first target and a phase boundary, and
    # (2) ....the edge (DP specs plus head)...
    # in the order of Operation 1 => Operation 2.
    #
    # Note: order is based on the relationship between case and agreement. Position (1) is the canonical
    # position for NOM assignment, which is also the canonical position for phi-agreement
    #
    def acquire_phi(self, h):

        #
        # Operation 1. Head H acquires phi-features from sister
        #
        goal, phi_features = self.acquire_from_sister(h.sister())
        for phi in phi_features:  # Try to value
            if self.value(h, phi):
                log(f'\t\t\t\t\t\t{h} acquired ' + str(phi) + f' by phi-Agree from {goal.mother}.')
                # Agreement leads into phi-checking
                h.features.add('PHI_CHECKED')
        #
        # Operation 2. Try edge-Agree
        #
        # Pick up the target (goal) and its phi-features
        if self.is_unvalued(h):
            goal, phi_features = self.acquire_from_edge(h)
            for phi in phi_features:
                # Try to value phi-features from the goal into the probe head h
                if self.value(h, phi):
                    log(f'\t\t\t\t\t\t{h} acquired ' + str(phi) + f' from the edge of {h}.')

    # Definition for phi-acquisition from sister
    # H acquires phi-features from DP inside the sister if and only if
    # Condition 1. DP is the closest left branch DP
    # Condition 2. A phase boundary (v, C, BE, Force) does not intervene the search
    # Condition 3. D contains valued phi-features other than [PHI:DET...]
    def acquire_from_sister(self, ps):

        # ps = sister of the head acquiring phi-features
        ps_ = ps

        # Downstream loop
        while ps_:

            # Condition 1. XP is left and is not primitive
            if ps_.left_const and ps_.is_complex():
                goal = ps_.left_const.head()

                # Condition 2. Stop at a phase boundary (no long distance probing)
                # Phase is defined as {v, C, Force, BE}, but this is stipulation
                if goal.is_phase():
                    break

                # Condition 3. Look for DPs
                if 'CAT:D' in goal.features:

                    # Condition 3. Collect all valued phi-features (ignore unvalued features and PHI:DET)
                    return goal, sorted({f for f in goal.features if self.phi(f) and f[:7] != 'PHI:DET' and self.valued(f)})

            ps_ = ps_.walk_downstream()

        # If search finds nothing,  return an empty set
        return ps_, {}

    # Definition for phi-acquisition from the edge
    # H acquires phi-features from the XP at the edge of H if and only if
    # Condition 1. XP is inside the edge
    # Condition 2. XP is a DP
    # Condition 3. Acquire valued phi features from the DP
    # Condition 4. XP is the first DP from the edge
    def acquire_from_edge(self, h):

        # Condition 1. XP is inside the edge
        edge_list = self.edge_for_Agree(h)
        if edge_list:
            for edge in edge_list:
                edge_head = edge.head()

                # Condition 2. The element must be D(P)
                if 'CAT:D' in edge_head.features:

                    # Condition 3. We acquire valued phi-features
                    phi_features = {f for f in edge_head.features if self.phi(f) and self.valued(f)}

                    # Condition 4. Only the first potential phi-donor is accepted
                    return edge_head, sorted(phi_features)

        # If nothing is found, we return an empty set (i.e. nothing)
        return None, {}

    # Definition for phi-feature valuation
    # Head H values phi-feature PHI:T:V if and only if
    # Condition 1. H has an unvalued phi-feature of the same type, PHI:T:_.
    # The operation has the following implications:
    # Implication 1. The unvalued feature PHI:T:_ is removed from H,
    # Implication 2. If H has a conflicting phi-features, the valued phi-feature is marked bad.
    def value(self, h, phi):

        # Implication 2. If H has a conflicting phi-features, the valued phi-feature is marked bad.
        if not self.valuation_blocked(h, phi):
            phi = self.mark_bad(phi)
            h.features.add(phi)
            return False

        # Condition 1. H has an unvalued phi-feature of the same type, PHI:T:_
        target = self.find_unvalued_target(h, phi)
        if target:

            # Remove the unvalued version of the phi-feature F:_
            h.features = h.features - target

            # Add the valued version F:X
            h.features.add(phi)
            return True

        return False

    # Definition for unvalued target feature
    # PHI1 is an unvalued target for PHI2 if and only if
    # Condition 1.  PHI1 is unvalued and has the same type as PHI2.
    # Example:      PHI1 = [PHI:F:_] and PHI2 = [PHI:F:x]
    # Condition 1 is defined formally as "are identical up until the last _".
    def find_unvalued_target(self, h, phi):
        return {f for f in h.features if self.unvalued(f) and f[:-1] == phi[:len(f[:-1])]}

    # Definition for the notion of phi-set for head H
    # phi is a phi-set of H if and only if
    # Condition 1. All its members have three parts separated by ":"
    # Condition 2. All its members have the same form PHI:...
    # Condition 3. It contains all elements of H that satisfy (1-2)
    def get_phi_set(self, h):
        return {f for f in h.head().features if f[:4] == 'PHI:' and len(f.split(':')) == 3}

    # Definition for unvalued phi-features of H
    # {phi...} is H's phi-set if and only
    # Condition 1. All features begin with PHI:
    # Condition 2. All features end with _
    # Condition 3. It contains all elements satisfying (1-2)
    # Condition 3. H is called "unvalued" if the set is not empty
    def is_unvalued(self, h):
        return {f for f in h.features if f[:4] == 'PHI:' and f[-1] == '_'}

    # Definition for valued phi-features of H
    # {phi...} is H's valued phi-set if and only if
    # Condition 1.  All features f begin with PHI:
    # Condition 2.  and f does not end with _.
    # Condition 3.  H is called "valued" if the set is not empty
    # Comment:      Notice that having unvalued features does not make H "not valued".
    def is_valued(self, h):
        return {f for f in h.features if f[:4] == 'PHI:' and f[-1] != '_'}

    # Definition for unvalued feature
    # Feature F is unvalued if and only if
    # Condition 1. F ends with "_"
    def unvalued(self, input_feature):
        return {f for f in {input_feature} if f[-1] == '_'}

    # Definition for valued faeture
    # Feature F is valued if and only if
    # Condition 1. F is not unvalued
    def valued(self, input_feature):
        return {f for f in {input_feature} if not self.unvalued(f)}

    # Definition of feature TYPE
    # T is the type of feature F if and only if
    # T is the second element when F is split (by :)
    def get_type(self, f):
        return f.split(':')[1]  # Notice that 0 = first element, 1 = second element

    # Definition of feature VALUE
    # V is the value of feature F if and only if
    # V is the third element when F is split (by :)
    def get_value(self, f):
        return f.split(':')[2]  # Notice that 0 = first element, 1 = second element, 2 = third element

    # Definition for PHI-feature
    # Feature F is a phi-feature if and only if
    # F beings with PHI:
    def phi(self, input_feature):
        return {f for f in {input_feature} if f[:4] == 'PHI:'}

    # Definition for feature conflict
    # Features F and G conflict if and only if
    # Condition 1. F and G match in type but not in value,
    # Condition 2. F is valued.
    def feature_conflict(self, f, phi):

        # Condition 1. If the type match but value does not, the result is feature conflict
        if self.get_type(f) == self.get_type(phi) and self.get_value(f) != self.get_value(phi) and self.valued(f):
            log(f'\t\t\t\t\t\tFeature conflict between {f} and {phi}.')
            return True
        else:
            return False

    # Head H does not block valuation by feature F if and only if
    # Condition 1. H has only unvalued features OR
    # Condition 2. if H has valued feature of the same type, it must also have a matching 'type:value'.
    def valuation_blocked(self, h, f):

        # Condition 1. Completely unvalued (no valued feature) heads do not raise an error
        if not self.is_valued(h):
            return True

        # Technical preparations
        valued_input_feature_type = self.get_type(f)
        heads_phi_set = self.get_phi_set(h)

        # Condition 2. If H has valued feature of the same type (a), then it must have a matching 'type:value' (b).
        # Condition a) H has a phi-feature of the same type T.
        valued_phi_in_h = {phi for phi in heads_phi_set if self.valued(phi) and self.get_type(phi) == valued_input_feature_type}
        if valued_phi_in_h:

            # Condition b) H has a phi-feature of the same type T and same value V
            type_value_matches = {phi for phi in valued_phi_in_h if phi == f}
            if type_value_matches:
                return True

            # Condition a) but not b) => valuation is  blocked.
            else:
                log(f'\t\t\t\t\t\tFeature {f} cannot be valued into {h}. Reason:')
                log(f'\t\t\t\t\t\t{h} already has a feature with the same type but with different value.')
                return False

        # Neither a) nor b) => valuation is not blocked.
        return True

    # Definition for bad agreement
    # Feature F is marked bad if and only if
    # Condition 1. It ends with *
    def mark_bad(self, phi):
        return phi + '*'

    # Definition of edge (for Agree-1)
    # Ordered list [X1...Xn] constitutes the edge E of H if and only if
    # Condition 1:  H is not complex,
    # Condition 2.  E contains all (a) left (b) complex sisters collected form upstream walk from H,
    #               including possible pro-element from H, until an element is found that does not satisfy (a-b).
    # Condition 3.  E is ordered top-down
    #
    # Example:      [G [XP [YP [ZP [H_pro WP]]]] returns [XP, YP, ZP, pro]
    def edge_for_Agree(self, h):

        # Condition 1. h is now complex
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

        # Condition 2. Walk upstream and include every XPs such that
        #   a)  XP is left to dominating node
        #   b)  XP is complex
        #   until first element is found that does not satisfy (a-b).
        while ps_ and ps_.sister() and (ps_.sister().is_left() and ps_.sister().is_complex()):
            edge_list.append(ps_.sister())
            ps_ = ps_.walk_upstream()

        # Condition 3. Reverse the list (top-down order)
        return edge_list[::-1]