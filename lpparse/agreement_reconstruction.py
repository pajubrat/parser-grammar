from support import log

# Abbreviations and simple pattern recognition algorithms
def get_type(f):
    return f.split(':')[1]
def get_value(f):
    return f.split(':')[2]
def unvalued(input_feature):
    if input_feature:
        return {f for f in {input_feature} if f[-1] == '_'}
def valued(input_feature):
    return {f for f in {input_feature} if not unvalued(f)}
def find_unvalued_target(h, phi):
    return {f for f in h.features if unvalued(f) and f[:-1] == phi[:len(f[:-1])]}
def mark_bad(phi):
    return phi + '*'
def phi(input_feature):
    return {f for f in {input_feature} if f[:4] == 'PHI:'}


class AgreementReconstruction:
    def __init__(self, controlling_parsing_process):
        self.controlling_parsing_process = controlling_parsing_process

    def reconstruct(self, ps):
        """
        Reconstructs agreement by exploring the right edge of the phrase structure. All nodes that have property
        [VAL] enter into the mechanism.
        """
        # ---------------------------- minimal search ----------------------------------------#
        for node in ps.minimal_search():
            if node.left_primitive() and 'VAL' in node.left_const.features:
                self.Agree_1(node.left_const)
        # ------------------------------------------------------------------------------------#

    # Definition for phi-feature acquisition (Agree-1)
    def Agree_1(self, head):
        """
        Acquires phi-features from local structure for a head with feature [VAL].

        Agree will first try to acquire phi-features from its sister. If unvalued features remain,
        it will then try to acquire them from the edge. Edge refers to specifiers and to the head itself that
        may carry valued phi-features after seeing agreement suffixes in the input or after receiving them
        from the lexicon.

        Both operations contain two stages. The first is the search and acquisition of the features, and then second
        is the valuation in which the acquired features are used to value unvalued features in the head.

        We know that the purpose of this function is to saturate arguments for predicates, as valued phi-features
        will prevent LF-recovery from applying. Agree is currently part of the outer edge of transfer, but it could
        be implemented at the LF-interface as well. The reason it is here is because there is evidence that Agree
        could apply during transfer and/or be sensitive to more surface properties.

        Literature: Brattico (2021). Null arguments and the inverse problem. Glossa.
        """
        self.controlling_parsing_process.consume_resources("Agree")
        self.controlling_parsing_process.consume_resources("Phi")

        # 1. Acquisition of phi-features from the sister
        goal, phi_features = self.Agree_1_from_sister(head)
        # 2. Valuation of the acquired phi-features to the head
        for phi in phi_features:
            self.value(head, goal, phi, 'sister')
        if not head.is_unvalued():
            return

        # 1. Acquisition of phi-features from the edge
        goal, phi_features = self.Agree_1_from_edge(head)
        # 2. Valuation of the acquired phi-features to the head
        for phi in phi_features:
            if find_unvalued_target(head, phi):
               self.value(head, goal, phi, 'edge')

    # Definition for phi-acquisition from sister
    def Agree_1_from_sister(self, head):
        """
        Acquires phi-features from the sister of head [head] (if there is a sister).

        Searches on the right edge while terminating at the first primitive left constituent (no long-distance Agree).
        If the left constituent is complex and can be exploited for phi-features, then the head of that constituent
        and its valued phi-features (without PHI:DET) are acquired (returned). A constituent can be exploited for
        phi-features if it is a DP. In Finnish, with free word order, a special rule is required which ties
        agreement to case features whose ultimate explanation remains an open problem.
        """
        if head.sister():
            # ---------------------------- minimal search ----------------------------#
            for node in head.sister().minimal_search():
                if self.termination_condition_for_Agree_search(node):
                    break
                if node.left_complex():
                    if self.agreement_condition(head, node.left_const):
                        return node.left_const.head(), \
                               sorted({f for f in node.left_const.head().features
                                       if phi(f) and f[:7] != 'PHI:DET' and valued(f)})
            # ---------------------------------------------------------------------------#
        return head.sister(), {}    # This line is executed only if nothing is found

    def termination_condition_for_Agree_search(self, node):
        return node.left_const and node.left_const.is_primitive()

    # Definition for phi-acquisition from the edge
    def Agree_1_from_edge(self, head):
        if self.edge_for_Agree(head):
            for e in self.edge_for_Agree(head):
                if self.agreement_condition(head, e):
                    phi_features = {f for f in e.head().features if phi(f) and valued(f)}
                    return e.head(), sorted(phi_features)
        return None, {}

    def agreement_condition(self, head, phrase):
        """
        Defines whether [phrase] can donate phi-features to [head].

        The general procedure is that we look if the head of the phrase has feature [D], thus we assume that
        D-elements can donate phi-features and thus saturate argument positions of predicates.

        There is currently an exceptional rule for Finnish which states the generalization that only
        nominative and genitive DPs can donate phi-features. This rule is needed because due to the free
        word order partitive and accusative DPs may occur in agreement configurations and wrongly trigger
        agreement. I do not understand what is behind this empirical generalization. Features [NOM] and [GEN]
        are abbreviations and should be replaced with the corresponding TAIL-features.
        """
        if 'D' in phrase.head().features:
            if self.controlling_parsing_process.language != 'LANG:FI':
                return True
            else:
                if 'pro' in phrase.head().features:
                    return True
                else:
                    # This is a descriptive stipulation that must be replaced with a generalization
                    if 'FIN' in head.features and 'NOM' in phrase.head().features:
                        return True
                    if 'INF' in head.features and 'GEN' in phrase.head().features:
                        return True

    # Definition for phi-feature valuation
    def value(self, h, goal, phi, location):
        """
        Attempts to values [phi] from [goal] into head [h].

        If there is a feature conflict, then a badness marker will be inserted to signal agreement mismatch.
        A phi-feature [PHI:F:V] can value [PHI:F:_]. If valuation occurs, a [PHI_CHECKED] feature will be added
        to the head to signal that the constituent is ready for interpretation.
        """

        # Checks that there is no feature conflicts (agreement mismatches)
        if h.get_valued_features() and self.valuation_blocked(h, phi):
            h.features.add(mark_bad(phi))

        # Performs valuation by [PHI:F:V] for a matching unvalued feature [PHI:F:_]
        if find_unvalued_target(h, phi):
            h.features = h.features - find_unvalued_target(h, phi)
            h.features.add(phi)
            if goal.mother:
                log(f'"{h}" acquired ' + str(phi) + f' by Agree-1 from {goal.mother} inside its {location}...')
            else:
                log(f'"{h}" acquired ' + str(phi) + f' by Agree-1 from {goal} inside its {location}...')
            h.features.add('PHI_CHECKED')

    # Definition for blocked valuation
    def valuation_blocked(self, head, f):
        """
        Checks whether valuation by feature [f] is blocked at [h].

        Recall that unvalued phi-features (from lexicon) and valued phi-features from input can coexist in the same
        head.

        Valuation can only be blocked by existing valued features. If a fully matching valued phi-feature
        already exists at the head, then the trivial "checking" valuation is not blocked (Condition 2). If a fully
        matching valued phi-feature does not exist, then a conflicting type-value feature blocks further
        valuation (Condition 1). If there is neither matching value nor conflicting value, the operation is not
        blocked (Condition 3).

        Empirical example cases.
        I + V.1sg       = not blocked, checking valuation (#2)
        you + V.1sg     = blocked: [PHI:PER:1] blocks valuation by [PHI:PER:2] from the subject
        I + V.1sg, 2sg  = not blocked, checking valuation (#2), existence of [2sg] does not matter.

        The intuition is that valued phi-features at a head license subjects. If the subject is not licensed,
        then feature conflict will present it from occurring.

        """
        valued_input_feature_type = get_type(f)                                 # Type of the incoming feature [f]
        heads_phi_set = head.get_phi_set()                                      # All phi-features at head [h]
        valued_phi_in_h = {phi for phi in heads_phi_set if valued(phi) and get_type(phi) == valued_input_feature_type}
        # If phi has no valued features, then valuation cannot be blocked
        if valued_phi_in_h:                                                     # Condition (1)
            type_value_matches = {phi for phi in valued_phi_in_h if phi == f}   # Condition (2)
            if type_value_matches:
                return False
            else:
                log(f'Feature {f} cannot be valued into {head}. Reason:')
                log(f'{head} has no matching feature but has a feature with the same type but with different value...')
                return True
        return False    # Valuation is not blocked

    # Definition of edge (for Agree-1)
    def edge_for_Agree(self, h):
        edge_list = h.phrasal_edge()
        if h.extract_pro():
            edge_list.append(h.extract_pro())
        return edge_list