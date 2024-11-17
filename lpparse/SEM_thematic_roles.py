from support import log

class ThematicRoles:
    def __init__(self):
        self.failure = False

    def reconstruct(self, X):
        assignee = None
        self.failre = False
        theta_role = ''

        if ['COMP:φ', 'COMP:D', '!COMP:φ', '!COMP:D'] in X.core and X.complement():
            assignee = X.complement()
            if assignee.core.property('preposition'):
                theta_role = 'Goal'
            else:
                theta_role = 'Patient'
        elif not X.core.property('EPP') and ['SPEC:φ', 'SPEC:D', '!SPEC:φ', '!SPEC:D'] in X.core and X.pro_edge():
            assignee = X.pro_edge()[0]
            if assignee.core.property('referential'):
                if X.core.property('nominal'):
                    theta_role = 'Agent/Possessor'
                elif X.core.property('light_verb'):
                    theta_role = 'Causer/Agent'
                else:
                    theta_role = 'Agent'
            else:
                theta_role = '?'
        elif X.check({'V'}) and X.check({'CLASS/TR'}) and X.pro_edge():
            assignee = X.pro_edge()[0]
            theta_role = 'Patient'
        if assignee:
            if assignee.check({'EXPL'}):
                log(f'\n\t\tExpletive cannot receive a thematic role from {X}.')
                self.failure = True
                return
            if assignee.H().core.property('referential'):
                if assignee.H().mother_:
                    argument_str = f'{assignee.H().mother_.illustrate()}'
                else:
                    argument_str = f'{assignee.H()}'
            else:
                argument_str = f'{assignee.label()}'
            return theta_role + f' of {X.label()}°({X.gloss()}): ' + argument_str


