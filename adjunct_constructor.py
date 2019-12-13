from phrase_structure import PhraseStructure
from support import set_logging, log, show_results, report_LF_problem, report_tail_head_problem, reset_number_of_operations, log_result, illu

class AdjunctConstructor:
    def __init__(self, controlling_parser_process):
        self.controlling_parser_process = controlling_parser_process

    def create_adjunct(self, ps):

        head = ps.get_head()

        # If the head is primitive, we must decide how much of the surrounding structure he will eat
        if ps.is_primitive():

            # If a complex adjunct has found an acceptable position, we use !SPEC:* feature
            if head.external_tail_head_test():
                # Condition 1. The head requires a mandatory specifier
                # Condition 2. The specifier exists
                if '!SPEC:*' in head.features and head.mother.mother and ps.get_generalized_specifiers():
                    # Result. The specifier is eaten inside the adjunct
                    self.make_adjunct(head.mother.mother)
                    return ps.mother.mother
                else:
                    # The specifier is not eaten inside the adjunct
                    if head.mother and head.mother.get_head() == head:
                        self.make_adjunct(head.mother)
                    else:
                        self.make_adjunct(head)
                    return ps.mother

            # If the adjunct is still in wrong position, we eat the specifier if accepted
            else:
                # Condition 1. There are specifiers
                # Condition 2. The head does not reject specifiers
                # Condition 3. The specifier is accepted by the head
                # Condition 4. The specifier is not pro/PRO
                # Condition 5. The head is not marked for -ARG
                if ps.get_generalized_specifiers() and not '-SPEC:*' in head.features and \
                        not set(head.get_not_specs()).intersection(
                            set(ps.get_generalized_specifiers()[0].get_labels())) and \
                        not ps.get_generalized_specifiers()[0].is_primitive() and '-ARG' not in ps.features:
                    if head.mother.mother:
                        self.make_adjunct(head.mother.mother)
                    return ps.mother.mother
                else:
                    self.make_adjunct(head.mother)
                    return ps.mother
        else:
            self.make_adjunct(ps)

    def make_adjunct(self, ps):
        ps.adjunct = True
        self.transfer_adjunct(ps)
        log(f'\t\t\t\t\t\t{ps} was made an adjunct.')
        if ps.geometrical_sister() and ps.geometrical_sister().adjunct:
            ps.mother.adjunct = True
        return True

    def transfer_adjunct(self, ps):
        original_mother = ps.mother
        ps.detach()
        ps = self.controlling_parser_process.transfer_to_lf(ps)
        if original_mother:
            ps.mother = original_mother
        return ps
