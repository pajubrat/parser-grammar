from support import log, disable_logging, enable_logging

class AdjunctConstructor:
    def __init__(self, controlling_parser_process):
        self.controlling_parser_process = controlling_parser_process

    def externalize_structure(self, ps):
        if ps and ps.head().is_adjoinable():
            if ps.is_complex():
                self.externalize_and_transfer(ps)
            else:
                self.externalize_head(ps)

    def externalize_head(self, probe):
        if probe.isolated_preposition():
            self.externalize_and_transfer(probe)
            return
        if probe.externalize_with_specifier():
            self.externalize_and_transfer(probe.mother.mother)
        else:
            self.externalize_and_transfer(probe.mother)

    def externalize_and_transfer(self, ps):
        if ps.mother:
            ps.adjunct = True
            self.add_tail_features_if_missing(ps)
            self.transfer_adjunct(ps)

    def add_tail_features_if_missing(self, ps):
        if not ps.head().get_tail_sets():
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
                ps.mother.right = ps
            else:
                ps.mother.left = ps
        return ps
