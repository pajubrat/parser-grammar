from phrase_structure import PhraseStructure
from support import set_logging, log, show_results, report_LF_problem, disable_logging, enable_logging, report_tail_head_problem, reset_number_of_operations, log_result, illu

class AdjunctConstructor:
    def __init__(self, controlling_parser_process):
        self.controlling_parser_process = controlling_parser_process

    # Definition for creation of adjuncts
    def create_adjunct(self, ps):
        if ps.head().is_adjoinable():
            if ps.is_complex():
                self.make_adjunct(ps)
            else:
                if self.adjunct_in_correct_position(ps):
                    self.make_adjunct_with_surrounding_structure(ps)
                else:
                    self.make_adjunct_with_surrounding_structure_(ps)

    def make_adjunct_with_surrounding_structure_(self, ps):
        if self.eat_specifier_(ps):
                self.make_adjunct_with_specifier(ps)
                return ps.mother.mother
        else:
            self.make_adjunct_with_complement(ps.head())
            return ps.mother

    def eat_specifier_(self, ps):
        if ps.head().edge() and \
                not '-SPEC:*' in ps.head().features and \
                not (set(ps.head().specifiers_not_licensed()) & set(ps.edge()[0].head().features)) and \
                not ps.edge()[0].is_primitive() and \
                '-ARG' not in ps.head().features and \
                ps.head().mother.mother:
            return True
        else:
            return False

    def make_adjunct_with_surrounding_structure(self, ps):
        if self.eat_specifier(ps):
            self.make_adjunct_with_specifier(ps.head())
            return ps.mother.mother
        else:
            if self.eat_complement(ps):
                self.make_adjunct_with_complement(ps)
            else:
                self.make_adjunct(ps.head())
            return ps.mother

    def eat_complement(self, ps):
        if ps.head().mother and ps.head().mother.head() == ps.head():
            return True
        else:
            return False

    def eat_specifier(self, ps):
        if '!SPEC:*' in ps.head().features and ps.head().mother.mother and ps.head().mother.sister() and ps.head().mother.sister().is_complex():
            return True
        else:
            return False

    def adjunct_in_correct_position(self, ps):
        if ps.head().external_tail_head_test():
            return True
        else:
            return False

    def make_adjunct_with_complement(self, ps):
        self.make_adjunct(ps.head().mother)

    def make_adjunct_with_specifier(self, ps):
        self.make_adjunct(ps.head().mother.mother)

    def make_adjunct(self, ps):
        if ps == ps.top():
            log(f'\t\t\t\t\tCannot push the whole structure {ps} into the secondary processing stream (adjunct).')
            return False
        ps.adjunct = True
        log(f'\t\t\t\t\t{ps} was pulled into secondary processing stream (made an adjunct).')
        self.add_tail_features_if_missing(ps)
        self.transfer_adjunct(ps)
        return True

    def add_tail_features_if_missing(self, ps):
        if not {f for f in ps.head().features if f[:4] == 'TAIL'}:
            ps.head().features.add('TAIL:T')
            ps.head().features.add('ADV')

    def transfer_adjunct(self, ps):
        original_mother = ps.mother
        ps.detach()
        log(f'\t\t\t\t\t{ps} is transferred to LF as a phase.')
        disable_logging()
        ps = self.controlling_parser_process.transfer_to_lf(ps, 5)
        enable_logging()
        if original_mother:
            ps.mother = original_mother
        return ps