from support import log

class ThematicRoles:
    def __init__(self):
        self.failure = False

    def reconstruct(self, ps):
        assignee = None
        self.failre = False
        theta_role = ''

        if ps.check_some({'COMP:φ', 'COMP:D', '!COMP:φ', '!COMP:D'}) and ps.complement():
            assignee = ps.complement()
            if assignee.preposition():
                theta_role = 'Goal'
            else:
                theta_role = 'Patient'
        elif not ps.EF() and ps.check_some({'SPEC:φ', 'SPEC:D', '!SPEC:φ', '!SPEC:D'}) and ps.pro_edge():
            assignee = ps.pro_edge()[0]
            if assignee.referential():
                if ps.nominal():
                    theta_role = 'Agent/Possessor'
                elif ps.light_verb():
                    theta_role = 'Causer/Agent'
                else:
                    theta_role = 'Agent'
            else:
                theta_role = '?'
        elif ps.check({'V'}) and ps.check({'CLASS/TR'}) and ps.pro_edge():
            assignee = ps.pro_edge()[0]
            theta_role = 'Patient'
        if assignee:
            if assignee.head().check({'EXPL'}):
                log(f'\n\t\tExpletive cannot receive a thematic role from {ps}.')
                self.failure = True
                return
            if assignee.head().referential():
                if assignee.head().mother_:
                    argument_str = f'{assignee.head().mother_.illustrate()}'
                else:
                    argument_str = f'{assignee.head()}'
            else:
                argument_str = f'{assignee.label()}'
            return theta_role + f' of {ps.label()}°({ps.gloss()}): ' + argument_str


