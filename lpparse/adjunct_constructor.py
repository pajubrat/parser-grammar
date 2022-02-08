from support import log, disable_logging, enable_logging

class AdjunctConstructor:
    def __init__(self, controlling_parser_process):
        self.controlling_parser_process = controlling_parser_process

    def externalize_structure(self, ps):
        if ps.head().is_adjoinable():
            # Simple externalization: we change the constituency relation to that of adjunction.
            if ps.is_complex():
                self.externalize(ps)
            # Complex externalization: primitive lexical item is externalized and must take some structure with it.
            # This is the nontrivial part.
            elif ps.is_primitive():
                if self.adjunct_in_correct_position(ps):
                    self.externalize_with_extra_structure_rule_1(ps) # Simple rule
                else:
                    self.externalize_with_extra_structure_rule_2(ps) # Complex rule

    def externalize_with_extra_structure_rule_1(self, ps):
        # If specifier must be externalized with the head, we take it with to the other side
        if self.condition_for_externalization_with_specifier_rule_1(ps):
            self.externalize_with_specifier(ps.head())
        # If specifier should not be externalized, we take only the complement to the other side
        else:
            if self.condition_for_externalize_with_complement(ps):
                self.externalize_with_complement(ps)
            else:
                self.externalize(ps.head())

    def externalize_with_extra_structure_rule_2(self, ps):
        # If specifier must be externalized with the head, we take it to the other side
        if self.condition_for_externalization_with_specifier_rule_2(ps):
            self.externalize_with_specifier(ps)
            return ps.mother.mother
        # If specifier should not be externalized, we take only the complement to the other side
        else:
            self.externalize_with_complement(ps.head())
            return ps.mother

    def condition_for_externalization_with_specifier_rule_1(self, ps):
        return '!SPEC:*' in ps.head().features and ps.head().mother.mother and ps.head().mother.sister() and ps.head().mother.sister().is_complex()

    def condition_for_externalization_with_specifier_rule_2(self, ps):
        return ps.head().edge() and \
               not '-SPEC:*' in ps.head().features and \
               not (set(ps.head().specifiers_not_licensed()) & set(next((const for const in ps.head().edge()), None).head().features)) and \
               not next((const for const in ps.edge()), None).is_primitive() and \
                '-ARG' not in ps.head().features and \
               ps.head().mother.mother

    def has_adjoinable_specifier(self, ps):
        local_head = next((const for const in ps.head().edge()), None)
        if local_head:
            return local_head.contains_feature('OP:REL')

    def condition_for_externalize_with_complement(self, ps):
        return ps.head().mother and ps.head().mother.head() == ps.head()

    def adjunct_in_correct_position(self, ps):
        return ps.head().external_tail_head_test()

    def externalize_with_complement(self, ps):
        self.externalize(ps.head().mother)

    def externalize_with_specifier(self, ps):
        for edge in ps.head().edge():
            if edge.contains_feature('OP:REL'):
                self.externalize(edge.mother)
                return
        self.externalize(ps.head().mother.mother)

    def externalize(self, ps):
        if ps == ps.top():
            log(f'Cannot externalize the whole structure {ps}...')
            return False
        ps.adjunct = True
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

    def transfer_adjunct(self, ps):
        original_mother = ps.mother
        ps.detach()
        disable_logging()
        ps, output_from_interfaces = self.controlling_parser_process.transfer_to_LF(ps)
        enable_logging()
        if original_mother:
            ps.mother = original_mother
        return ps