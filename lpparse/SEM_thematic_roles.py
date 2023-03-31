
class ThematicRoles:
    def __init__(self):
        pass

    def reconstruct(self, ps):
        assignee = None
        predix = ''

        if ps.check_some({'COMP:φ', 'COMP:D', '!COMP:φ', '!COMP:D'}) and ps.proper_selected_complement():
            assignee = ps.proper_selected_complement()
            if assignee.preposition():
                theta_role = 'Goal'
            else:
                theta_role = 'Patient'
        elif not ps.EF() and ps.check_some({'SPEC:φ', 'SPEC:D', '!SPEC:φ', '!SPEC:D'}) and ps.pro_edge():
            assignee = ps.pro_edge()[0]
            if ps.nominal():
                theta_role = 'Agent/Possessor'
            elif ps.light_verb():
                theta_role = 'Causer/Agent'
            else:
                theta_role = 'Agent'
        elif ps.check({'V'}) and ps.check({'CLASS/TR'}) and ps.pro_edge():
            assignee = ps.pro_edge()[0]
            theta_role = 'Patient'
        if assignee:
            if assignee.head().referential():
                if assignee.head().mother:
                    argument_str = f'{assignee.head().mother.illustrate()}'
                else:
                    argument_str = f'{assignee.head()}'
            else:
                argument_str = f'{assignee.label()}'
            return theta_role + f' of {ps.label()}°({ps.gloss()}): ' + argument_str


