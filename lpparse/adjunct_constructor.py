from support import log, disable_logging, enable_logging

class AdjunctConstructor:
    def __init__(self, controlling_parser_process):
        self.controlling_parser_process = controlling_parser_process

    def externalize_structure(self, ps):
        """
        Externalizes [ps], i.e. creates an adjunct from phrase structure [ps] if applicable.

        Externalization means intuitively that the structure is moved aside into a separate cognitive space. The
        effects are defined mostly in the phrase structure class which reacts to this property when computing
        heads, sisterhood and other fundamental grammatical relations.

        A necessary condition for simple adjunct creation is that the phrase is adjoinable (Brattico 2012), so that it
        can be adjoined in the first place. Another condition is that it must be complex: lexical items cannot be
        externalized alone. If a lexical item is targeted for externalization, then this results in a nontrivial
        situation in which we must take some surrounding structure with it to the other side. There are two possibilities:
        [H YP] (externalize with complement) and [XP [H YP]] (externalize with specifier). The latter happens, for example,
        if we externalize a relative clause, so we must take the relative pronoun with the structure. The former is the
        case with English PPs, for example. The rules used in this version have been written so that the simulations
        give correct results, they have no intuitive content.

        If the structure is externalized, it will get also transferred immediately after the operation.

        Literature: Brattico (2012). Pied-piping domains and adjunction coincide in Finnish. Nordic Journal of Linguistics.
        """
        if ps.head().is_adjoinable():
            # Simple externalization: we change the constituency relation to that of adjunction.
            if ps.is_complex():
                self.externalize(ps)
            # Complex externalization: primitive lexical item is externalized and must take some structure with it.
            # This is the nontrivial part that takes most of the lines here.
            elif ps.is_primitive():
                if self.adjunct_in_correct_position(ps):
                    self.externalize_with_extra_structure_rule_1(ps) # Simple rule
                else:
                    self.externalize_with_extra_structure_rule_2(ps) # Complex rule

    def externalize_with_extra_structure_rule_1(self, ps):
        """
        This rule, which is relatively simple, is used when the adjunct is already in the correct position.
        """
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
        """
        This rule, which is complex, is used when the adjunct is not in the correct position.
        """
        # If specifier must be externalized with the head, we take it to the other side
        if self.condition_for_externalization_with_specifier_rule_2(ps):
            self.externalize_with_specifier(ps)
            return ps.mother.mother
        # If specifier should not be externalized, we take only the complement to the other side
        else:
            self.externalize_with_complement(ps.head())
            return ps.mother

    def condition_for_externalization_with_specifier_rule_1(self, ps):
        """
        Rule 1 determining whether a specifier is externalized to the other side together with a head. Rule 1
        relies on simple EPP-feature.
        """
        return ps.head().EPP() and ps.head().mother.mother and ps.head().mother.sister() and ps.head().mother.sister().is_complex()

    def condition_for_externalization_with_specifier_rule_2(self, ps):
        """
        Rule 2 determining whether [ps] must take its specifier to the other side during externalization.
        Rule 2 is complex. The intuitive idea is to look whether the putative specifier XP could be licensed by H.
        Suppose the head is H and XP is what looks to be its specifier. Then [XP [H YP]] will be externalized
        if and only if

        (1) H must have edge that can be taken;
        (2) H cannot have a feature that prevents it from having a specifier;
        (3) XP cannot have a feature that H does not license;
        (4) XP cannot be primitive head;
        (5) H cannot have [-ARG] feature;
        (6) There must exists node [X(P) [H YP]].
        """
        return ps.head().edge() and \
                not '-SPEC:*' in ps.head().features and \
                not (set(ps.head().specifiers_not_licensed()) & set(ps.edge()[0].head().features)) and \
                not ps.edge()[0].is_primitive() and \
                '-ARG' not in ps.head().features and \
                ps.head().mother.mother

    def has_adjoinable_specifier(self, ps):
        return ps.head().local_edge() and ps.head().local_edge().contains_feature('OP:REL')

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
        """
        Externalizes structure [ps] and transfer it. If a tail-feature is missing, it will be added.

        The highest node cannot be externalized. Otherwise this operation applies to anything, so all
        conditions must be secured before this operation is performed. If will also add the missing
        tail-features (if any) and transfers the structure. The element is also wired semantically
        if that has not already taken place.
        """
        if ps == ps.top():
            log(f'Cannot push the whole structure {ps} into the secondary processing stream (adjunct)...')
            return False
        ps.adjunct = True
        log(f'{ps} was pulled into secondary processing stream (made an adjunct)...')
        self.add_tail_features_if_missing(ps)
        self.transfer_adjunct(ps)
        return True

    def add_tail_features_if_missing(self, ps):
        """
        Adds a tail feature if the head does not have one. Prototypical "default" tail features are used.
        """
        if not {f for f in ps.head().features if f[:4] == 'TAIL'}:
            if 'D' in ps.head().features:
                ps.head().features.add('TAIL:V')
            elif 'T' not in ps.head().features:       # TP can only become relative clause, e.g. 'che dorme'
                ps.head().features.add('TAIL:T')
                ps.head().features.add('ADV')

    def transfer_adjunct(self, ps ):
        """
        Transfers an externalized constituent to the syntax-semantic interface.

        Implements the normal detached transfer process.
        """
        original_mother = ps.mother
        ps.detach()
        log(f'{ps} is transferred to LF as a phase...')
        disable_logging()
        ps = self.controlling_parser_process.transfer_to_LF(ps)
        enable_logging()
        if original_mother:
            ps.mother = original_mother
        return ps