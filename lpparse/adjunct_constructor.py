from support import log, disable_logging, enable_logging

class AdjunctConstructor:
    def __init__(self, controlling_parser_process):
        self.controlling_parser_process = controlling_parser_process

    def externalize_structure(self, ps):
        if ps.head().is_adjoinable():
            if ps.is_complex():
                self.externalize_and_transfer(ps)
            else:
                self.externalize_head(ps, ps.tail_test())

    def externalize_head(self, head, tail_test):
        if head.sister() and head.sister().is_primitive() and 'P' in head.features:  # [X Y], both primitive, externalize Y
            self.externalize_and_transfer(head)
            return
        if '-EF:φ' not in head.features and ((tail_test and head.EF() and head.edge_specifiers()) or (not tail_test and self.capture_specifier_rule(head))):
            if head.is_right():
                self.externalize_and_transfer(head.mother)
            else:
                self.externalize_and_transfer(head.mother.mother)  # Externalize with specifier
        else:
            self.externalize_and_transfer(head.mother)  # Externalize without specifier

    def capture_specifier_rule(self, head):
        return head.edge_specifiers() and '-ARG' not in head.features and head.mother.mother and '-EDGE:*' not in head.features and \
               not (set(head.specifiers_not_licensed()) & set(next((const for const in head.edge_specifiers()), None).head().features))

    def externalize_and_transfer(self, ps):
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
                ps.head().features.add('Adv')

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
