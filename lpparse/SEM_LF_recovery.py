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
        self.LF_recovery_results = []
        self.interpretation_failed = False

    def perform_LF_recovery(self, probe, semantic_interpretation_dict):
        unvalued = must_be_valued({f for f in probe.features if f[:4] == 'PHI:' and f[-1] == '_'})
        if unvalued:
            antecedent = self.LF_recovery(probe, unvalued)  # This version returns only the local antecedent
            self.interpret_antecedent(antecedent, probe, unvalued, semantic_interpretation_dict)

    def LF_recovery(self, probe, unvalued_phi):
        log(f'\n\t\t\t\"{probe.illustrate()}\" was controlled by ')
        list_of_antecedents = []
        working_memory = []

        # Standard control
        if 'PHI:NUM:_' in unvalued_phi and 'PHI:PER:_' in unvalued_phi:
            if probe.is_primitive() and probe.is_left() and probe.sister().is_complex():
                working_memory.append(probe.sister())
            working_memory.extend(list(takewhile(self.recovery_termination, probe.working_memory_path())))
            antecedent = next((const for const in working_memory if self.is_possible_antecedent(const, probe)), None)
            if antecedent:
                return antecedent

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
            if not {'φ', 'T/prt', 'MODAL'} & probe.features:
                # self.interpretation_failed = True
                return None

        if list_of_antecedents:
            return list_of_antecedents[0]

    def recovery_termination(self, node):
        return 'SEM:external' not in node.features

    def special_local_edge_antecedent_rule(self, const, ps, list_of_antecedents):
        if ps.edge_specifiers() and const == next((const for const in ps.edge_specifiers()), None):
            if not const.head().is_referential():
                self.LF_recovery_results.append(f'{ps}(generic)')
                list_of_antecedents.append(const)
                ps.features.add('PHI:DET:GEN')
            else:
                list_of_antecedents.append(const)
            return True

    def is_possible_antecedent(self, antecedent, probe):
        unchecked = get_semantically_relevant_phi(probe)
        for F in antecedent.head().get_valued_features():
            for G in get_semantically_relevant_phi(probe):
                unchecked = check(F, G, unchecked)
        log(f'Antecedent {antecedent} could not check {unchecked}')
        if not unchecked:
            return True

    def interpret_antecedent(self, list_of_antecedents, probe, unvalued, semantic_interpretation_dict):
        self.LF_recovery_results = []
        if list_of_antecedents:
            antecedent = self.interpret_antecedent_for_output(probe, list_of_antecedents[0])
            self.LF_recovery_results.append(antecedent)
            self.brain_model.narrow_semantics.predicate_argument_dependencies.append((probe, list_of_antecedents[0].head()))
            semantic_interpretation_dict['Recovery'].append(f'{antecedent}')
        else:
            self.LF_recovery_results.append(f'{probe}(' + self.antecedent_does_not_exist(probe, unvalued) + ')')
        self.report_to_log(probe, list_of_antecedents, unvalued)

    def interpret_antecedent_for_output(self, probe, antecedent):
        def get_valued_phi_set(h):
            phi_set = set()
            if h.is_complex():
                if h.left_const:
                    phi_set = get_valued_phi_set(h.left_const)
                if h.right_const:
                    phi_set = phi_set | get_valued_phi_set(h.right_const)
            else:
                if 'PHI:NUM:SG' in h.features and 'PHI:PER:1' in h.features:
                    phi_set.add(f'pro at {h}')
                elif 'PHI:NUM:SG' in h.features and 'PHI:PER:2' in h.features:
                    phi_set.add(f'pro at {h}')
                elif 'PHI:NUM:SG' in h.features and 'PHI:PER:3' in h.features:
                    phi_set.add(f'pro at {h}')
                elif 'PHI:NUM:PL' in h.features and 'PHI:PER:1' in h.features:
                    phi_set.add(f'pro at {h}')
                elif 'PHI:NUM:PL' in h.features and 'PHI:PER:2' in h.features:
                    phi_set.add(f'pro at {h}')
                elif 'PHI:NUM:PL' in h.features and 'PHI:PER:3' in h.features:
                    phi_set.add(f'pro at {h}')
            if 'PHI:DET:GEN' in h.features:
                phi_set.add(f'generic')
            return phi_set

        if probe.sister() and probe.is_left() and antecedent == probe.sister() and antecedent.is_right():
            prefix = 'Patient of'
        else:
            prefix = 'Agent of'

        if antecedent.head().is_referential():
            if antecedent.head().sister() and 'N' in antecedent.head().sister().head().features:
                arg_str = antecedent.head().sister().head().illustrate()
            else:
                arg_str = antecedent.illustrate()
        elif 'C' in antecedent.head().features or 'FORCE' in antecedent.head().features and antecedent.is_complex():
            arg_str = 'C-proposition'
        elif 'V' in antecedent.head().features and antecedent.is_complex():
            arg_str = 'Agent of V-event'
        elif 'T' in antecedent.head().features:
            if antecedent.is_complex():
                arg_str = 'Agent of T-event'
            else:
                arg_str = f'{sorted(get_valued_phi_set(antecedent))}'
        else:
            arg_str = antecedent.illustrate()

        return prefix + f' {probe.illustrate()}: {arg_str}'

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
                return 'Uninterpretable, interpretation failed.'
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