from support import log
#
# This class will be slowly dissolved into narrow_semantics and broad_semantics
#

def semantically_relevant_phi(phi):
    return phi[:7] == 'PHI:NUM' or phi[:7] == 'PHI:PER' or phi[:7] == 'PHI:DET'
def get_relevant_phi(h):
    return {f for f in h.features if semantically_relevant_phi(f)}
def must_be_valued(phi_set):
    return {phi for phi in phi_set if semantically_relevant_phi(phi)}
def check(F, G, unchecked):
    if F == G:
        unchecked.discard(G)
    else:
        if valued_check(F, G):
            unchecked.discard(G)
def valued_check(F, G):
    if is_unvalued(G):
        return residuum_identity(F, G)
def is_unvalued(G):
    return G[-1] == '_'
def residuum_identity(F, G):
    return F[:len(G[:-1])] == G[:-1]

class Semantics:
    def __init__(self, controlling_parsing_process):
        self.semantic_interpretation = set()
        self.semantic_interpretation_failed = False
        self.controlling_parsing_process = controlling_parsing_process
        self.antecedent_list = []

    def interpret(self, ps):
        """
        Generates a semantic interpretation for a phrase structure and assesses if it failed.
        """
        self.semantic_interpretation = set()
        self.semantic_interpretation_failed = False
        return self._interpret(ps)

    def _interpret(self, ps):
        """
        Generates a semantic interpretation for a node if it primitive, otherwise calls the function recursively.

        Each lexical item is subjected to several types of semantic interpretation, in this version
        (i) LF-recovery for predicates that have unsaturated arguments
        (ii) detection of phi-feature conflicts
        (iii) tail-feature interpretation
        (iv) variable binding.
        """
        if ps.is_primitive():
            self.perform_LF_recovery(ps)
            self.detect_phi_conflicts(ps)
            self.interpret_tail_features(ps)
            if not self.controlling_parsing_process.narrow_semantics.bind_variable(ps, self.controlling_parsing_process.first_solution_found):
                self.semantic_interpretation_failed = True
                return set()
            if not self.controlling_parsing_process.first_solution_found:
                if not self.controlling_parsing_process.narrow_semantics.discourse.reconstruct_discourse(ps):
                    self.semantic_interpretation_failed = True
                    return set()
        else:
            if not ps.left_const.find_me_elsewhere:
                self._interpret(ps.left_const)
            if not ps.right_const.find_me_elsewhere:
                self._interpret(ps.right_const)
            if self.semantic_interpretation_failed:
                return set()
            return self.semantic_interpretation | {' '}

    def perform_LF_recovery(self, head):
        """
        Provides each head [head] with unvalued phi-features an argument
        """
        unvalued = must_be_valued(head.get_unvalued_features())
        if unvalued:
            log(f'\"{head.illustrate()}\" with {sorted(unvalued)} was associated at LF with ')
            list_of_antecedents = self.LF_recovery(head, unvalued)
            if list_of_antecedents:
                self.semantic_interpretation.add(self.interpret_antecedent(head, list_of_antecedents[0]))
            else:
                self.semantic_interpretation.add(f'{head}(' + self.interpret_no_antecedent(head, unvalued) + ')')
            self.report_to_log(head, list_of_antecedents, unvalued)
            self.controlling_parsing_process.consume_resources("LF recovery")
            self.controlling_parsing_process.consume_resources("Phi")

    # Definition for LF-recovery
    def LF_recovery(self, head, unvalued_phi):
        """
        Associates a head [head] with unvalued phi-features with a list of antecedents.

        The operation relies on an upstream search (forming an upward path) that is based on dominance.
        Heads of the sisters of the nodes in the upward path are examined and,
        if the head has all valued phi-features that are missing from the head, then the sister is
        picked up as a possible antecedent and appended to the list of antecedents.

        Example. "John wants to leave". The predicate "leave" has unvalued [phi_], which triggers
        upstream search that finds the TP node whose sister is "John". The D head of this
        constituent [3sg] can value the [phi_] and thus the DP = John will be appended to the list of
        antecedents. Because it will end up as the first and most local antecedent, it is selected.
        The rule is modelled after Rosenbaum's (1967) Minimal Distance Principle. See also Lasnik (1991).

        Source: Brattico (2021). Null arguments and the inverse problem. Glossa: A journal for general linguistics.
        """
        list_of_antecedents = []
        if 'PHI:NUM:_' in unvalued_phi and 'PHI:PER:_' in unvalued_phi:
            # ----------------------- minimal upstream search -----------------------------------------------#
            for node in [head] + head.upstream_search():
                if self.recovery_termination(node):
                    break
                if node.geometrical_sister() and self.is_possible_antecedent(node.geometrical_sister(), head):
                    list_of_antecedents.append(node.geometrical_sister())
            # ------------------------------------------------------------------------------------------------#
            return list_of_antecedents

        if 'PHI:DET:_' in unvalued_phi:
            # ---------------- minimal search----------------------------------------------------
            for node in head.upstream_search():
                if self.special_local_edge_antecedent_rule(node, head, list_of_antecedents):
                    break
                elif node.sister() and self.is_possible_antecedent(node.sister(), head):
                    list_of_antecedents.append(node.sister())
            #--------------------------------------------------------------------------------
            return list_of_antecedents

        if not list_of_antecedents:
            log(f'No antecedent found, LF-object crashes...')
            self.semantic_interpretation_failed = True
            return []

    def is_possible_antecedent(self, antecedent, head):
        """
        Determines whether a constituent [antecedent] constitutes a suitable antecedent argument for [head].

        Copied constituents are ignored (i.e. are not considered twice). The algorithm targets the head of
        the antecedent constituent (e.g. D of DP) and examined whether it possess enough valued phi-features to value
        the unvalued features of the head. If it does, then it will be returned as a possible antecedent.
        """
        if antecedent.find_me_elsewhere:
            return False    # Do not consider elements that have been copied elsewhere.
        unchecked = get_relevant_phi(head)  # Gets the relevant unvalued phi-features from the head (NUM, PER, DET)
        for F in antecedent.head().get_valued_features():
            for G in get_relevant_phi(head):
                check(F, G, unchecked)
        if not unchecked:
            return True     # If the antecedent can value all unvalued features of the head, it is accepted.

    # Definition for failed LF-recovery outcome
    def interpret_no_antecedent(self, ps, features):
        if 'PHI:NUM:_' in features and 'PHI:PER:_' in features:
            if ps.sister() and ps.sister().is_complex() and \
                    ('CAT:INF' in ps.sister().head().features or 'CAT:FIN' in ps.sister().head().features):
                return 'clausal argument'
            else:
                return 'generic'
        elif 'PHI:PER:_' in features and 'PHI:NUM:_' not in features:
            return 'discourse antecedent'
        else:
            self.semantic_interpretation_failed = True
            return 'uninterpretable'

    # Provides a more fine-grained interpretation for antecedents
    def interpret_antecedent(self, trigger, antecedent):

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
                    phi_set.add(f'1sg pro at {h}')
                elif 'PHI:NUM:SG' in h.features and 'PHI:PER:2' in h.features:
                    phi_set.add(f'2sg pro at {h}')
                elif 'PHI:NUM:SG' in h.features and 'PHI:PER:3' in h.features:
                    phi_set.add(f'3sg pro at {h}')
                elif 'PHI:NUM:PL' in h.features and 'PHI:PER:1' in h.features:
                    phi_set.add(f'1pl pro at {h}')
                elif 'PHI:NUM:PL' in h.features and 'PHI:PER:2' in h.features:
                    phi_set.add(f'2pl pro at {h}')
                elif 'PHI:NUM:PL' in h.features and 'PHI:PER:3' in h.features:
                    phi_set.add(f'3pl pro at {h}')
            if 'PHI:DET:GEN' in h.features:
                phi_set.add(f'generic')
            return phi_set

        # Main function
        antecedent_head = antecedent.head()
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
                arg_str = f'{sorted(get_valued_phi_set(antecedent))}'
        else:
            arg_str = antecedent.illustrate()

        return prefix + f' {trigger.illustrate()}({arg_str})'

    # Definition for the special rule
    # This handles the exceptional antecedent properties of local D-antecedent specifier
    def special_local_edge_antecedent_rule(self, node, ps, list_of_antecedents):
        if node.sister() and node.sister() == ps.local_edge():
            if 'D' not in node.sister().head().features:
                self.semantic_interpretation.add(f'{ps}(generic)')
                list_of_antecedents.append(node.sister())
                ps.features.add('PHI:DET:GEN')
            else:
                list_of_antecedents.append(node.sister())
            return True

    # Definition for LF-recovery termination
    def recovery_termination(self, node):
        return node.sister() and 'SEM:external' in node.sister().features

    def detect_phi_conflicts(self, ps):
        """
        Detects phi-feature conflicts inside a head, and marks failed interpretation is found.
        """
        for phi in ps.get_phi_set():
            if phi[-1] == '*':
                log(f'{ps} induces a phi-feature conflict...')
                self.semantic_interpretation_failed = True

    def interpret_tail_features(self, ps):
        """
        Interprets semantic interpretation relying on tail-features.

        Currently only implements the aspectual ACC-PAR alteration in Finnish aspect.
        Vainikka (1989), Kiparsky (1997, 2001), Brattico (2020, submitted).
        """
        for tail_set in ps.get_tail_sets():
            self.interpret_argument_tailing(ps, self.get_tailed_head(ps, tail_set))

    def interpret_argument_tailing(self, ps, tailed_head):
        if tailed_head and 'ASP:BOUNDED' in tailed_head.features:
            if 'PAR' in ps.features and not ps.bind_to_scope_operator('POL:NEG'):
                    self.semantic_interpretation.add('Aspectually anomalous')
            else:
                self.semantic_interpretation.add('Aspectually bounded')

    def get_tailed_head(self, ps, tail_set):
        for head in ps.feature_vector()[1:]:
            if head.match_features(tail_set) == 'complete match':
                return head

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
                log(s)
        else:
            log(f'({self.interpret_no_antecedent(ps, unvalued_phi_features)})')
        log('. ')
