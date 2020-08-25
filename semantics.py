from support import log, illu

class Semantics:
    def __init__(self):
        self.semantic_interpretation = set()
        self.semantic_interpretation_failed = False

    def interpret(self, ps):
        if ps.is_primitive():
            self.perform_LF_recovery(ps)
            self.detect_phi_conflicts(ps)
            self.interpret_tail_features(ps)
        else:
            if not ps.left_const.find_me_elsewhere:
                self.interpret(ps.left_const)
            if not ps.right_const.find_me_elsewhere:
                self.interpret(ps.right_const)
            if self.semantic_interpretation_failed:
                return set()
            else:
                return self.semantic_interpretation | {' '}

    def detect_phi_conflicts(self, ps):

        # Internal function
        # Definition for a well-formed phi-set
        def get_phi_set(h):
            return {f for f in h.head().features if f[:4] == 'PHI:' and len(f.split(':')) == 3}

        # Main function
        phi_set = get_phi_set(ps)
        for phi in phi_set:
            if phi[-1] == '*':
                log(f'\t\t\t\t{ps} induces a phi-feature conflict.')
                self.semantic_interpretation_failed = True
                return
        return

    def interpret_tail_features(self, ps):
        tail_sets = ps.get_tail_sets()
        if tail_sets:
            for tail_set in tail_sets:
                tailed_head = self.get_target_head(ps, tail_set)
                self.interpret_tailing(ps, tailed_head)

    def interpret_tailing(self, ps, tailed_head):
        if tailed_head:
            self.interpret_argument_tailing(ps, tailed_head)
            self.interpret_adjunct_predication(ps, tailed_head)

    def interpret_argument_tailing(self, ps, tailed_head):
        if 'ASP:BOUNDED' in tailed_head.features:
            self.semantic_interpretation.add('Aspectually bounded')
            if 'PAR' in ps.features:
                if not ps.bind_to_operator('POL:NEG'):
                    self.semantic_interpretation.discard('Aspectually bounded')
                    self.semantic_interpretation.add('Aspectually anomalous')

    def interpret_adjunct_predication(self, ps, tailed_head):
        pass

    def get_target_head(self, ps, tail_set):
        for head in ps.feature_vector()[1:]:
            if head.match_features(tail_set) == 'complete match':
                return head

    def perform_LF_recovery(self, ps):

        # Internal function
        # Returns a set of unvalued phi-features
        def get_unvalued_features(h):
            return {f for f in h.features if f[:4] == 'PHI:' and f[-1] == '_'}

        # Main function
        unvalued_phi_features = self.must_be_valued(get_unvalued_features(ps))
        if unvalued_phi_features:
            log(f'\t\t\t\t{ps.illustrate()} with {sorted(unvalued_phi_features)} was associated at LF with:')
            list_of_antecedents = self.LF_recovery(ps, unvalued_phi_features)
            if list_of_antecedents:
                self.semantic_interpretation.add(self.format_antecedent(ps, list_of_antecedents[0]))
            else:
                self.semantic_interpretation.add(f'{ps}(' + self.failed_recovery_outcome(ps, unvalued_phi_features) + ')')
            self.report_to_log(ps, list_of_antecedents, unvalued_phi_features)

    def must_be_valued(self, phi_set):
        return {phi for phi in phi_set if self.relevant_phi_at_LF(phi)}

    # Definition for phi-features which require antecedents at LF/C-I
    def relevant_phi_at_LF(self, phi):
        if phi[:7] == 'PHI:NUM' or phi[:7] == 'PHI:PER' or phi[:7] == 'PHI:DET':
            return True
        else:
            return False

    # Definition for LF-recovery
    def LF_recovery(self, ps, unvalued_phi):
        ps_ = ps
        head = ps
        list_of_antecedents = []
        #
        # Alternative 1: H has unvalued per/num features: standard control
        #
        if 'PHI:NUM:_' in unvalued_phi and 'PHI:PER:_' in unvalued_phi:
            while ps_:
                #
                # Termination condition: sister is a strong phase head
                # (Strong phase head = Force or v*)
                if ps_.sister() and 'SEM:external' in ps_.sister().head().features:
                    break
                #
                # XP is an antecedent is anf only if
                # Condition 1. Antecedent must be a sister of the node reached by upstream walk from H, and
                # Condition 2. The phrase must evaluate as a possible antecedent.
                if ps_.geometrical_sister() and self.is_possible_antecedent(ps_.geometrical_sister(), ps):
                    list_of_antecedents.append(ps_.geometrical_sister())
                ps_ = self.walk_upstream_geometrically(ps_)
            return list_of_antecedents
        #
        # Alternative 2. Only PER_ remains unvalued: standard control (currently, used in radical pro-drop)
        #
        elif 'PHI:PER:_' in unvalued_phi:
            while ps_:
                #
                # Termination condition: presence of SEM-external (control boundary)
                if ps_.sister() and 'SEM:external' in ps_.sister().head().features:
                    break
                #
                # Condition 1. Antecedent must be a sister of the node at the spine we climb up
                # Condition 2. The phrase must evaluate as a possible antecedent
                if ps_.sister() and self.is_possible_antecedent(ps_.sister(), ps):
                    list_of_antecedents.append(ps_.sister())
                ps_ = self.walk_upstream_geometrically(ps_)
            return list_of_antecedents
        #
        # Alternative 3. Only D_ remains unvalued: nonlocal/discourse antecedents
        #
        elif 'PHI:DET:_' in unvalued_phi:
            while ps_:
                #
                # Termination condition: presence of local specifier
                # Example: tässä istuu mukavasti 'here sit.3sg comfortably'
                if ps_.sister() and ps_.sister() == ps.local_edge():
                    #
                    # If the local candidate is not a DP, it will be interpreted as generic
                    if ps_.sister() and 'D' not in ps_.sister().head().features:
                        self.semantic_interpretation.add(f'{ps}(generic)')
                        list_of_antecedents.append(ps_.sister())
                        head.features.add('PHI:DET:GEN')
                    #
                    # If the local candidate is DP, it will be the antecedent
                    else:
                        list_of_antecedents.append(ps_.sister())
                    #
                    # Nothing else is searched (currently)
                    break
                #
                # If there is no local antecedent inside the edge of H, then we get all antecedents.
                if ps_.sister() and self.is_possible_antecedent(ps_.sister(), ps):
                    list_of_antecedents.append(ps_.sister())
                ps_ = self.walk_upstream_geometrically(ps_)

            # Condition 3c: if no antecedent is found, LF-recovery crashes
            if not list_of_antecedents:
                log(f'\t\t\t\t\tNo antecedent found, LF-object crashes.')
                self.semantic_interpretation_failed = True
            return list_of_antecedents

    # Defines the category of possible antecedent for a goal head H
    def is_possible_antecedent(self, antecedent, h):

        # Condition 1. X has not been moved into another position
        if antecedent.find_me_elsewhere:
            return False

        # Set of relevant phi-features at H (valued and unvalued)
        h_phi_features = {f for f in h.features if self.relevant_phi_at_LF(f)}

        # Set of unchecked features at H (will be checked by features of the antecedent)
        unchecked_features_at_h = h_phi_features.copy()

        # Condition 2. Antecedent X can check all H's relevant phi-features.
        for F in {phi for phi in antecedent.head().features if phi[:4] == 'PHI:' and phi[-1] != '_'}:
            for G in h_phi_features:

                # Condition 2a) Valued feature F at antecedent X checks G at H if F = G.
                if F == G:
                    unchecked_features_at_h.discard(G)  # Check feature

                # Condition 2b) Valued feature F at antecedent X checks G at H if F can value G.
                else:
                    if G[-1] == '_':
                        if F[:len(G)-1] == G[:-1]:
                            unchecked_features_at_h.discard(G)  # Check feature

        # If features remain unchecked, the antecedent is rejected
        if unchecked_features_at_h:
            return False
        else:
            return True

    # Definition for the notion of phrasal phase
    # XP is a phrasal phase if and only if
    # Condition 1. XP's sister is a phase head
    def phase(self, ps_):
        return ps_.sister() and \
               'v' in ps_.sister().features or \
               'C' in ps_.sister().features or \
               'FORCE' in ps_.sister().features or \
               'COPULA' in ps_.sister().features

    def report_to_log(self, ps, list_of_antecedents, unvalued_phi_features):
        s = ''
        i = 1
        if list_of_antecedents:
            for a in list_of_antecedents:
                s = s + str(i) + '. ' + a.illustrate() + ' '
                i = i + 1
                if i == 2:
                    s = s + '   (alternatives: '
            if i > 1:
                s = s + ')'
            if s:
                log(f'\t\t\t\t\t' + s)
            else:
                log(f'\t\t\t\t\t{ps}{self.failed_recovery_outcome(ps, unvalued_phi_features)}')
            return True

    # Definition for failed LF-recovery outcome
    # Presupposition. LF-recovery fails if and only if no antecedent is found
    # A failed outcome for LF-recovery for head H depends on unvalued phi-features:
    #   a) NUM_, PER_: "clausal argument" if the sister is a clause, "generic" otherwise;
    #   b) PER_: "discourse";
    #   c) "uninterpretable" otherwise
    def failed_recovery_outcome(self, ps, features):
        if 'PHI:NUM:_' in features and 'PHI:PER:_' in features:
            if ps.sister() and ps.sister().is_complex() and \
                    ('CAT:INF' in ps.sister().head().features or 'CAT:FIN' in ps.sister().head().features):
                return 'clausal argument'
            else:
                return 'generic'
        elif 'PHI:PER:_' in features and 'PHI:NUM:_' not in features:
            return 'discourse antecedent'
        else:
            return 'uninterpretable'

    # Provides a more readable alternative reading form for antecedents
    def format_antecedent(self, trigger, antecedent):

        # Internal function
        def get_valued_phi_set(h):
            phi_set = set()
            if h.is_complex():
                if h.left_const:
                    phi_set = get_valued_phi_set(h.left_const)
                if h.right_const:
                    phi_set = phi_set | get_valued_phi_set(h.right_const)
            else:
                if 'PHI:NUM:SG' in h.features and 'PHI:PER:1' in h.features:
                    phi_set.add(f'{h}.1sg')
                elif 'PHI:NUM:SG' in h.features and 'PHI:PER:2' in h.features:
                    phi_set.add(f'{h}.2sg')
                elif 'PHI:NUM:SG' in h.features and 'PHI:PER:3' in h.features:
                    phi_set.add(f'{h}.3sg')
                elif 'PHI:NUM:PL' in h.features and 'PHI:PER:1' in h.features:
                    phi_set.add(f'{h}.1pl')
                elif 'PHI:NUM:PL' in h.features and 'PHI:PER:2' in h.features:
                    phi_set.add(f'{h}.2pl')
                elif 'PHI:NUM:PL' in h.features and 'PHI:PER:3' in h.features:
                    phi_set.add(f'{h}.3pl')
            if 'PHI:DET:GEN' in h.features:
                phi_set.add(f'{h}.generic')
            return phi_set

        # Main function
        antecedent_head = antecedent.head()

        arg_str = ''
        # This is a rudimentary thematic theory that has not yet been implemented
        # These notions are simply returned as heuristic semantic interpretation to the user, and they have
        # no effect on anything
        if trigger.sister() and trigger.is_left() and antecedent == trigger.sister() and antecedent.is_right():
            prefix = 'Patient of'
        else:
            prefix = 'Agent of'

        if 'D' in antecedent_head.features:
            if antecedent_head.sister() and 'N' in antecedent_head.sister().head().features:
                arg_str = antecedent_head.sister().head().illustrate()
            else:
                arg_str = antecedent.illustrate()
        elif 'C' in antecedent_head.features or 'FORCE' in antecedent_head.features and antecedent.is_complex():
            arg_str = 'C-proposition'
        elif 'V' in antecedent_head.features and antecedent.is_complex():
            arg_str = 'agent of V-event'
        elif 'T' in antecedent_head.features:
            if antecedent.is_complex():
                arg_str = 'agent of T-event'
            else:
                arg_str = f'{sorted(self.get_valued_phi_set(antecedent))}'
        else:
            arg_str = antecedent.illustrate()

        return prefix + f' {trigger.illustrate()}({arg_str})'

    @staticmethod
    # Definition for geometrical upstream walk
    def walk_upstream_geometrically(h):
        if h.mother:
            return h.mother
        else:
            return None

