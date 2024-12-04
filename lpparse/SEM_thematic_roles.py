from support import log

class ThematicRoles:
    def __init__(self):
        self.failure = False

    def reconstruct(self, X):
        assignee = None
        self.failre = False
        theta_role = ''
        pro_edge = X.EXT(acquire='all') + [X.generate_pro()]

        if ['COMP:φ', 'COMP:D', '!COMP:φ', '!COMP:D'] in X.core and X.complement():
            assignee = X.complement()
            if assignee.core('preposition'):
                theta_role = 'Goal'
            else:
                theta_role = 'Patient'
        elif not X.core('EPP') and ['SPEC:φ', 'SPEC:D', '!SPEC:φ', '!SPEC:D'] in X.core and pro_edge:
            assignee = pro_edge[0]
            if assignee.core('referential'):
                if X.core('nominal'):
                    theta_role = 'Agent/Possessor'
                elif X.core('light_verb'):
                    theta_role = 'Causer/Agent'
                else:
                    theta_role = 'Agent'
            else:
                theta_role = '?'
        elif X.INT({'V'}) and X.INT({'CLASS/TR'}) and pro_edge:
            assignee = pro_edge[0]
            theta_role = 'Patient'
        if assignee:
            if assignee.INT({'EXPL'}):
                log(f'\n\t\tExpletive cannot receive a thematic role from {X}.')
                self.failure = True
                return
            if assignee.INT('referential'):
                if assignee.head().mother_:
                    argument_str = f'{assignee.head().mother_.illustrate()}'
                else:
                    argument_str = f'{assignee.head()}'
            else:
                argument_str = f'{assignee.label()}'
            return theta_role + f' of {X.label()}°({X.gloss()}): ' + argument_str


