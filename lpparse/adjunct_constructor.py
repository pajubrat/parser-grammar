from support import log, disable_logging, enable_logging

class AdjunctConstructor:
    def __init__(self, controlling_parser_process):
        self.controlling_parser_process = controlling_parser_process

    # Definition for creation of adjuncts
    def create_adjunct(self, ps):
        if ps.head().is_adjoinable():
            if ps.is_complex():
                self.make_adjunct(ps)
            elif ps.is_primitive():
                if self.adjunct_in_correct_position(ps):
                    self.make_adjunct_with_surrounding_structure(ps)
                else:
                    self.make_adjunct_with_surrounding_structure_(ps)

    def has_adjoinable_specifier(self, ps):
        return ps.head().local_edge() and ps.head().local_edge().contains_feature('OP:REL')

    def make_adjunct_with_surrounding_structure(self, ps):
        if self.eat_specifier(ps):
            self.make_adjunct_with_specifier(ps.head())
        else:
            if self.eat_complement(ps):
                self.make_adjunct_with_complement(ps)
            else:
                self.make_adjunct(ps.head())

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

    def eat_complement(self, ps):
        if ps.head().mother and ps.head().mother.head() == ps.head():
            return True

    def eat_specifier(self, ps):
        if ps.head().EPP() and ps.head().mother.mother and ps.head().mother.sister() and ps.head().mother.sister().is_complex():
            return True

    def adjunct_in_correct_position(self, ps):
        if ps.head().external_tail_head_test():
            return True

    def make_adjunct_with_complement(self, ps):
        self.make_adjunct(ps.head().mother)

    def make_adjunct_with_specifier(self, ps):
        for edge in ps.head().edge():
            if edge.contains_feature('OP:REL'):
                self.make_adjunct(edge.mother)
                return
        self.make_adjunct(ps.head().mother.mother)

    def make_adjunct(self, ps):
        if ps == ps.top():
            log(f'Cannot push the whole structure {ps} into the secondary processing stream (adjunct)...')
            return False
        ps.adjunct = True
        log(f'{ps} was pulled into secondary processing stream (made an adjunct)...')
        self.add_tail_features_if_missing(ps)
        self.transfer_adjunct(ps)
        return True

    def add_tail_features_if_missing(self, ps):
        if not {f for f in ps.head().features if f[:4] == 'TAIL'}:
            if 'D' in ps.head().features:
                ps.head().features.add('TAIL:V')
            elif 'T' not in ps.head().features:       # TP can only become relative clause, e.g. 'che dorme'
                ps.head().features.add('TAIL:T')
                ps.head().features.add('ADV')

    def transfer_adjunct(self, ps ):
        original_mother = ps.mother
        ps.detach()
        log(f'{ps} is transferred to LF as a phase...')
        disable_logging()
        ps = self.controlling_parser_process.transfer_to_LF(ps)
        enable_logging()
        if original_mother:
            ps.mother = original_mother
        return ps