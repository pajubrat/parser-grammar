from support import log, disable_logging, enable_logging

class AdjunctConstructor:
    def __init__(self, controlling_parser_process):
        self.controlling_parser_process = controlling_parser_process

    def externalize_structure(self, ps):
        if ps.head().is_adjoinable():
            if ps.is_complex():
                self.externalize(ps)
            else:
                self.externalize_head(ps, ps.tail_test())

    def externalize_head(self, head, tail_test):
        if (tail_test and '!SPEC:*' in head.features and head.edge()) or (not tail_test and self.capture_specifier_rule(head)):
            self.externalize(head.mother.mother)  # Externalize with specifier
        else:
            self.externalize(head.mother)  # Externalize without specifier

    def capture_specifier_rule(self, head):
        return head.edge() and '-ARG' not in head.features and head.mother.mother and '-SPEC:*' not in head.features and \
               not (set(head.specifiers_not_licensed()) & set(next((const for const in head.edge()), None).head().features))

    def externalize(self, ps):
        if ps.mother:
            ps.adjunct = True
            self.add_tail_features_if_missing(ps)
            self.transfer_adjunct(ps)
            return True
        log(f'Cannot externalize root. ')

    def add_tail_features_if_missing(self, ps):
        if not {f for f in ps.head().features if f[:4] == 'TAIL'}:
            if 'D' in ps.head().features:
                ps.head().features.add('TAIL:V')
            elif 'T' not in ps.head().features:       # TP can only become relative clause, e.g. 'che dorme'
                ps.head().features.add('TAIL:T')
                ps.head().features.add('ADV')

    def transfer_adjunct(self, ps):
        original_mother, is_right = ps.detach()
        disable_logging()
        ps, output_from_interfaces = self.controlling_parser_process.transfer_to_LF(ps)
        enable_logging()
        if original_mother:
            ps.mother = original_mother
            if is_right:
                ps.mother.right_const = ps
            else:
                ps.mother.left_const = ps
        return ps
