from support import log, illu
from lexical_interface import LexicalInterface
from adjunct_constructor import AdjunctConstructor


class FloaterMovement():
    def __init__(self, controlling_parser_process):
        self.controlling_parser_process = controlling_parser_process
        self.name_provider_index = 0
        self.memory_buffer = []
        self.lexical_access = LexicalInterface(self.controlling_parser_process)
        self.lexical_access.load_lexicon(self.controlling_parser_process)
        self.adjunct_constructor = AdjunctConstructor(self.controlling_parser_process)

    # Definition for floater reconstruction
    def reconstruct(self, ps):
        """
        Reconstruct floaters that are in a wrong position.

        The operation consists of two steps: detecting of misplaced floaters and dropping. Dropping
        refers to reconstruction that takes the local finite clause as its domain. Detection uses
        unvalued tail-features but can be blocked by features [-adjoinable] and [-float]. In addition, a phrase
        with tail features that occurs in a EPP position or in the specifier position of -SPEC:* head will be
        marked for reconstruction, as it cannot be in such position at the syntax-semantic interface. Finally,
        if the phrase has been moved, the leftover copy will not be reconstructed.

        [+/-adjoinable] determines if a phrase can be externalized and processed independently (Brattico 2012).
        [+/-float] determines if a phase can be floated.

        Empirical facts show that these properties much be specified, but it is not clear what their ultimate
        explanation is.
        """
        # ------------------------------------ minimal search ----------------------------------------#
        for node in ps.top().minimal_search():
            floater = self.detect_floater(node)
            if floater:
                log(f'Dropping {floater}...')
                self.drop_floater(floater, ps)
        # -------------------------------------------------------------------------------------------#
        return ps.top()  # Return top, because it is possible that an adjunct expands the structure

    def detect_floater(self, ps):
        """
        Detects floaters that are in a position that required reconstruction.

        A potential left or right floater is first recognized by a complex set of properties.
        If the test passes, then there are three cases which trigger reconstruction:
        (1) XP fails the tail-test;
        (2) XP sits in an EPP-position;
        (3) XP sits in a specifier position of a head which does not accept specifiers [-SPEC:*]
        """
        if self.detect_left_floater(ps):
            floater = ps.left_const

            # Case (1): XP fails the tail test
            if not floater.head().external_tail_head_test():
                log(floater.illustrate() + ' failed to tail ' + illu(floater.head().get_tail_sets()) + '...')
                return floater.max()

            # Case (2): XP sits in an EPP position;
            if floater.mother and floater.mother.head().EPP() and 'FIN' in floater.mother.head().features:
                log(floater.illustrate() + ' is in an EPP SPEC position...')
                return floater.max()

            # Case (3): XP sits in a specifier position that does not exist
            if floater.mother and '-SPEC:*' in floater.mother.head().features and floater == floater.mother.head().local_edge():
                log(floater.illustrate() + ' is in an specifier position that cannot be projected...')
                return floater.max()

        # Right floater
        if self.detect_right_floater(ps):
            floater = ps.right_const.head()
            if not floater.external_tail_head_test():
                log(floater.illustrate() + ' failed to tail ' + illu(floater.head().get_tail_sets()) + '...')
                if 'ADV' not in floater.features and floater.top().contains_feature('FIN'):
                    self.adjunct_constructor.externalize_structure(floater)
                    return floater.max()
                if 'ADV' in floater.features and not ps.right_const.adjunct:
                    self.adjunct_constructor.externalize_structure(floater)

    def detect_left_floater(self, ps):
        """
        Detects if structure [ps] contains a floater as a left constituent XP, ps = [XP YP], that requires reconstruction.

        The following conditions must be met:
        (1) ps = [XP YP] is complex;
        (2) XP is complex;
        (3) XP has not been moved elsewhere;
        (4) X has tail features (tail sets);
        (5) X is adjoinable (and also not -adjoinable);
        (6) X has not been prevents from floating;
        (7) XP does not have criterial features.
        """
        return ps.is_complex() and \
                ps.left_const.is_complex() and \
                not ps.left_const.find_me_elsewhere and \
                ps.left_const.head().get_tail_sets() and \
                'adjoinable' in ps.left_const.head().features and \
                '-adjoinable' not in ps.left_const.head().features and \
                '-float'not in ps.left_const.head().features and \
                not ps.scan_criterial_features()

    def detect_right_floater(self, ps):
        """
        Detects a right floater.

        XP is a right floater if and only if (1) its head has tail features, (2) it is adjoinable and (3) floating has
        not been prevented by [-float].
        """
        return ps.is_complex() and \
                ps.right_const.head().get_tail_sets() and \
                'adjoinable' in ps.right_const.head().features and \
                '-adjoinable' not in ps.right_const.head().features and \
                '-float' not in ps.right_const.head().features

    # Definition for floater reconstruction (dropping)
    def drop_floater(self, floater, ps):
        """
        Drops a floater, i.e. reconstructs it.

        Searches from the local finite clause boundary downstream for the first position in which the
        tail-feature(s) of the floater can be satisfies and then drops the floater there. The floater is
        also externalized.
        """
        starting_point_head = floater.container_head()
        floater_copy = floater.copy()
        # ------------------------------------ minimal search ------------------------------------#
        for node in self.local_tense_edge(floater).minimal_search():
            if self.termination_condition(node, floater):
                break
            self.merge_floater(node, floater_copy) # Right adjuncts to right, left adjuncts to left
            if self.is_drop_position(floater_copy, starting_point_head):
                if not floater.adjunct:
                    self.adjunct_constructor.externalize_structure(floater)
                dropped_floater = floater.copy_from_memory_buffer(self.babtize())
                self.merge_floater(node, dropped_floater)
                self.controlling_parser_process.consume_resources("Move Adjunct")
                self.controlling_parser_process.consume_resources("Move Phrase", f'{dropped_floater.illustrate()}')
                floater_copy.remove()
                return
            floater_copy.remove()
        # ---------------------------------------------------------------------------------------#

    def merge_floater(self, node, floater_copy):
        """
        Merges a floater into a node. Right adjuncts are merged to right, left adjuncts are merged to left.
        """
        if self.is_right_adjunct(floater_copy):
            node.merge_1(floater_copy, 'right')
        else:
            node.merge_1(floater_copy, 'left')

    def termination_condition(self, node, floater):
        return node == floater or node.find_me_elsewhere

    def is_right_adjunct(self, node):
        return 'ADV' in node.head().features or 'P' in node.head().features

    def is_drop_position(self, floater_copy, starting_point_head):
        """"
        Definition for a legitimate target position for floater reconstruction.
        """
        return self.conditions_for_right_adjuncts(floater_copy) or \
                self.conditions_for_left_adjuncts(floater_copy, starting_point_head)

    def conditions_for_right_adjuncts(self, floater):
        """
        Defines the conditions under which a phrase can be adjoined to right during floater reconstruction.
        Tests tail features and whether the phrase is a suitable right adjunct.
        """
        return floater.head().external_tail_head_test() and self.is_right_adjunct(floater)

    def conditions_for_left_adjuncts(self, floater, starting_point_head):
        """
        Defines conditions for left adjuncts.
        Tests tail features and whether this position can host specifiers ([-SPEC:*]/[-AGR] heads cannot)
        """
        return floater.head().external_tail_head_test() and self.license_to_specifier_position(floater, starting_point_head)

    def license_to_specifier_position(self, floater, starting_point_head):
        """
        Determiners whether floater can occur in a given specifier position during reconstruction.

        It can if and only if
        (1) it does not occur inside any projection from a head or
        (2) it does not occur its own the starting position or
        (3) the container head is not marked for [-SPEC:*]
        (4) the container head is not selected by head marked for [-ARG]
        """
        if not floater.container_head():
            return True
        if floater.container_head() == starting_point_head:
            return False
        if '-SPEC:*' in floater.container_head().features:
            return False
        if not floater.container_head().selector():
            return True
        if '-ARG' not in floater.container_head().selector().features:
            return True

    # Definition for minimal tense edge
    def local_tense_edge(self, ps):
        """
        Determines the minimal tense edge from which adjunct reconstruction begins.

        The minimal tense node is defined as first node N inside projection of a head that as [FIN] but which is
        not the sister of FinP or head with [FIN]. Thus for example N = [Fin vP] satisfies this condition.
        """
        node = ps.top()
        # --------------------------- upstream search ---------------------------------------- #
        for node in ps.upstream_search():
            if 'FIN' in node.head().features and node.sister() and node.sister().is_primitive() and 'FIN' not in node.sister().head().features:
                break
        # --------------------------------------------------------------------------------------#
        return node

    # Provide unique names when chains are formed
    def babtize(self):
        self.name_provider_index += 1
        return str(self.name_provider_index)