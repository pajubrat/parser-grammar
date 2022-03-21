from support import log
from itertools import takewhile

def must_be_valued(phi_set):
    return {phi for phi in phi_set if semantically_relevant_phi(phi)}
def semantically_relevant_phi(phi):
    return phi[:7] == 'PHI:NUM' or phi[:7] == 'PHI:PER' or phi[:7] == 'PHI:DET'
def get_semantically_relevant_phi(h):
    return {f for f in h.features if semantically_relevant_phi(f)}
def check(F, G, unchecked):
    if F == G:
        unchecked.discard(G)
    else:
        if valued_check(F, G):
            unchecked.discard(G)
    return unchecked
def valued_check(F, G):
    if is_unvalued(G):
        return residuum_identity(F, G)
def is_unvalued(G):
    return G[-1] == '_'
def residuum_identity(F, G):
    return F[:len(G[:-1])] == G[:-1]

class LF_Recovery:
    def __init__(self, controlling_parsing_process):
        self.brain_model = controlling_parsing_process
        self.LF_recovery_results = set()
        self.interpretation_failed = False

    def perform_LF_recovery(self, head, semantic_interpretation_dict):
        unvalued = must_be_valued({f for f in head.features if f[:4] == 'PHI:' and f[-1] == '_'})
        if unvalued:
            self.interpret_antecedent(self.LF_recovery(head, unvalued), head, unvalued, semantic_interpretation_dict)

    def LF_recovery(self, probe, unvalued_phi):
        log(f'\n\t\t\t\"{probe.illustrate()}\" with {sorted(unvalued_phi)} was associated with ')
        list_of_antecedents = []
        working_memory = []

        # Standard control
        if 'PHI:NUM:_' in unvalued_phi and 'PHI:PER:_' in unvalued_phi:
            if probe.is_primitive() and probe.is_left() and probe.sister().is_complex():
                working_memory.append(probe.sister())
            working_memory.extend(list(takewhile(self.recovery_termination, probe.working_memory_path())))
            antecedent = next((const for const in working_memory if self.is_possible_antecedent(const, probe)), None)
            if antecedent:
                return [antecedent]

        # Finite control in Finnish
        if 'PHI:DET:_' in unvalued_phi:
            # ---------------- minimal search----------------------------------------------------
            for const in probe.working_memory_path():
                if self.special_local_edge_antecedent_rule(const, probe, list_of_antecedents):
                    break
                if self.is_possible_antecedent(const, probe):
                    list_of_antecedents.append(const)
            #------------------------------------------------------------------------------------

        # One exception due to the lack of analysis of φ control
        if not list_of_antecedents:
            log(f'nothing. ')
            if 'φ' not in probe.features and 'T/prt' not in probe.features:
                self.interpretation_failed = True
                return None
        return list_of_antecedents

    def recovery_termination(self, node):
        return not 'SEM:external' in node.features

    def special_local_edge_antecedent_rule(self, const, ps, list_of_antecedents):
        if ps.edge() and const == next((const for const in ps.edge()), None):
            if 'D' not in const.head().features:
                self.LF_recovery_results.add(f'{ps}(generic)')
                list_of_antecedents.append(const)
                ps.features.add('PHI:DET:GEN')
            else:
                list_of_antecedents.append(const)
            return True

    def is_possible_antecedent(self, antecedent, head):
        unchecked = get_semantically_relevant_phi(head)
        for F in antecedent.head().get_valued_features():
            for G in get_semantically_relevant_phi(head):
                unchecked = check(F, G, unchecked)
        if not unchecked:
            return True

    def interpret_antecedent(self, list_of_antecedents, probe, unvalued, semantic_interpretation_dict):
        self.LF_recovery_results = set()
        if list_of_antecedents:
            self.LF_recovery_results.add(self.antecedent_exists(probe, list_of_antecedents[0]))
            self.brain_model.narrow_semantics.predicate_argument_dependencies.append((probe, list_of_antecedents[0].head()))
            semantic_interpretation_dict['Recovery'].append(self.LF_recovery_results)
        else:
            self.LF_recovery_results.add(f'{probe}(' + self.antecedent_does_not_exist(probe, unvalued) + ')')
        self.report_to_log(probe, list_of_antecedents, unvalued)
        self.brain_model.consume_resources("LF recovery")
        self.brain_model.consume_resources("Phi")

    def antecedent_exists(self, trigger, antecedent):
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


    def antecedent_does_not_exist(self, ps, features):
        if 'PHI:NUM:_' in features and 'PHI:PER:_' in features:
            if ps.sister() and ps.sister().is_complex() and \
                    ('CAT:INF' in ps.sister().head().features or 'CAT:FIN' in ps.sister().head().features):
                return 'Clausal argument'
            else:
                return 'Generic'
        elif 'PHI:PER:_' in features and 'PHI:NUM:_' not in features:
            return 'Discourse antecedent'
        else:
            if 'T/fin' in ps.head().features or 'Neg/fin' in ps.head().features:    # Finnish EPP ad hoc rule
                self.interpretation_failed = True                                   # I still don't fully understand this
                return 'Uninterpretable'
            else:
                return 'Generic'

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
            log(f'({self.antecedent_does_not_exist(ps, unvalued_phi_features)})')
        log('. ')