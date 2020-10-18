from support import log

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

    def interpret(self, ps):
        self.semantic_interpretation = set()
        self.semantic_interpretation_failed = False
        return self._interpret(ps)

    def _interpret(self, ps):
        if ps.is_primitive():
            self.perform_LF_recovery(ps)
            self.detect_phi_conflicts(ps)
            self.interpret_tail_features(ps)
            self.bind_variables(ps)
        else:
            if not ps.left_const.find_me_elsewhere:
                self._interpret(ps.left_const)
            if not ps.right_const.find_me_elsewhere:
                self._interpret(ps.right_const)
            if self.semantic_interpretation_failed:
                return set()
            return self.semantic_interpretation | {' '}

    def perform_LF_recovery(self, head):
        unvalued = must_be_valued(head.get_unvalued_features())
        if unvalued:
            log(f'\t\t\t\t{head.illustrate()} with {sorted(unvalued)} was associated at LF with:')
            list_of_antecedents = self.LF_recovery(head, unvalued)
            if list_of_antecedents:
                self.semantic_interpretation.add(self.interpret_antecedent(head, list_of_antecedents[0]))
            else:
                self.semantic_interpretation.add(f'{head}(' + self.interpret_no_antecedent(head, unvalued) + ')')
            self.report_to_log(head, list_of_antecedents, unvalued)

    def detect_phi_conflicts(self, ps):
        for phi in ps.get_phi_set():
            if phi[-1] == '*':
                log(f'\t\t\t\t{ps} induces a phi-feature conflict.')
                self.semantic_interpretation_failed = True

    def interpret_tail_features(self, ps):
        for tail_set in ps.get_tail_sets():
            self.interpret_argument_tailing(ps, self.get_tailed_head(ps, tail_set))

    def interpret_argument_tailing(self, ps, tailed_head):
        if tailed_head and 'ASP:BOUNDED' in tailed_head.features:
            if 'PAR' in ps.features and not ps.bind_to_operator('POL:NEG'):
                    self.semantic_interpretation.add('Aspectually anomalous')
            else:
                self.semantic_interpretation.add('Aspectually bounded')

    def get_tailed_head(self, ps, tail_set):
        for head in ps.feature_vector()[1:]:
            if head.match_features(tail_set) == 'complete match':
                return head

    # Definition for LF-recovery
    def LF_recovery(self, head, unvalued_phi):
        self.controlling_parsing_process.consume_resources("LF recovery")
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
            log(f'\t\t\t\t\tNo antecedent found, LF-object crashes.')
            self.semantic_interpretation_failed = True
            return []

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
        return node.sister() and 'SEM:external' in node.sister().head().features

    # Defines the category of possible antecedent for a goal head H
    def is_possible_antecedent(self, antecedent, head):
        if antecedent.find_me_elsewhere:
            return False
        unchecked = get_relevant_phi(head)
        for F in antecedent.head().get_valued_features():
            for G in get_relevant_phi(head):
                check(F, G, unchecked)
        if not unchecked:
            return True

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
                log(f'\t\t\t\t\t{ps}{self.interpret_no_antecedent(ps, unvalued_phi_features)}')
            return True

    def bind_variables(self, ps):
        if 'C' not in ps.head().features:
            for f in ps.head().features:
                if f[:3] == 'OP:' and f != 'OP:_':
                    if not ps.bind_to_operator('OP'):
                        log(f'\t\t\t\t{ps.max().illustrate()} with feature {f} is not properly bound by an operator.')
                        self.semantic_interpretation_failed = True
                    else:
                        self.semantic_interpretation.add(f'{ps.max().illustrate()} with feature {f} was bound to an operator.')
