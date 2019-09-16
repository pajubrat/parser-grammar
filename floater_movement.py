from support import set_logging, log, get_number_of_operations, reset_number_of_operations, log_result, illu
from LexicalInterface import LexicalInterface
import minimalist


class FloaterMovement():
    def __init__(self, context):
        self.name_provider_index = 0
        self.memory_buffer = []
        self.context = context
        self.number_of_Moves = 0

        # Access to the lexicon
        self.lexical_access = LexicalInterface(context.redundancy_rules_file)
        self.lexical_access.load_lexicon(context.lexicon_file, context.language)
        self.lexical_access.load_lexicon(context.ug_morpheme_file, context.language, combine=True)

    def reconstruct(self, ps):
        _ps_iterator = ps.get_top()  # Begin from the top and move downstream
        log(f'\t\t\tDropping floaters...')

        while _ps_iterator:
            floater = self.detect_floater(_ps_iterator)
            if floater:
                self.drop_floater(floater, ps)
                self.number_of_Moves += 1
            _ps_iterator = _ps_iterator.walk_downstream()

        log(f'\t\t\t\t= ' + ps.illustrate())

    def detect_floater(self, _ps_iterator):
        # Check if a phrase at the left requires reconstruction
        if not _ps_iterator.is_primitive() and \
                not _ps_iterator.left_const.is_primitive() and \
                not _ps_iterator.left_const.find_me_elsewhere and \
                _ps_iterator.left_const.get_head().get_tail_sets() and \
                not '-FLOAT' in _ps_iterator.left_const.get_head().features:

            floater = _ps_iterator.left_const
            # Check if its tail features fail to find a head
            if not floater.get_head().external_tail_head_test():
                log('\t\t\t\t' + floater.illustrate() + ' failed to tail ' + illu(floater.get_head().get_tail_sets()))
                # Target the floater
                return floater
            # or if it (constituent with tail features) sits in an EPP SPEC position of a finite clause edge
            elif floater.mother and floater.mother.get_head().EPP() and floater.mother.is_finite():
                log('\t\t\t\t' + floater.illustrate() + ' is in an EPP SPEC position.')
                return floater
            # or if its in a wrong SPEC position
            elif floater.mother and '-SPEC:*' in floater.mother.get_head().features:
                if floater == floater.mother.get_head().specifier():
                    return floater

        # Check if the right edge itself has tail features (e.g. DP at the bottom, floaters/adjuncts)
        if not _ps_iterator.is_primitive() and \
                _ps_iterator.right_const.get_head().get_tail_sets() and \
                not '-FLOAT' in _ps_iterator.right_const.get_head().features:
            floater = _ps_iterator.right_const.get_head()
            # If tail features fail to find a head, the constituent must be dropped
            if not floater.external_tail_head_test():
                log('\t\t\t\t' + floater.illustrate() + ' failed to tail ' + illu(floater.get_head().get_tail_sets()))
                # This is empirically very contentious matter:
                # A right DP inside a finite clause with failed tail-test must be an adjunct(?)
                if ('D' in floater.get_labels() or 'P' in floater.get_labels()) and floater.get_top().contains_feature('CAT:FIN'):
                    self.create_adjunct(floater)
                    return floater.mother
            else:
                if 'ADV' in floater.get_labels() and not _ps_iterator.right_const.adjunct:
                    self.create_adjunct(floater)

    # Drops one floater that is targeted for dropping
    def drop_floater(self, floater, ps):

        # This is stored so we don't implement reconstruction inside the same projection (leads into regress)
        starting_point = floater.mother.get_head()

        # We need to locate the appropriate starting point, XP in [fin XP]
        ps_iterator_ = self.locate_minimal_tense_edge(floater.mother)

        floater_copy = floater.copy()

        # This downward loop searches a position for the floater
        while ps_iterator_ and not ps_iterator_ == floater and not ps_iterator_.find_me_elsewhere:

            # Create hypothetical structure for testing
            if 'ADV' in floater_copy.get_labels():
                ps_iterator_.merge(floater_copy, 'right')
            else:
                ps_iterator_.merge(floater_copy, 'left')

            # If a suitable position is found, dropping will be executed
            # Condition 1: tail test succeeds,
            # Condition 2: we are not reconstructing inside the same projection (does not apply to Adv which are right-adjoined)
            # Condition 3: dropped non-ADV will become the only SPEC
            if self.is_drop_position(ps_iterator_, floater_copy, starting_point):
                self.create_adjunct(floater)
                dropped_floater = floater.transfer(self.babtize())
                if 'ADV' in floater_copy.get_labels() or 'P' in floater_copy.get_labels():
                    ps_iterator_.merge(dropped_floater, 'right')
                else:
                    ps_iterator_.merge(dropped_floater, 'left')
                floater_copy.remove()
                floater.find_me_elsewhere = True
                log(f'\t\t\t\tFloater ' + dropped_floater.illustrate() + f' dropped: {ps}')
                return
            else:
                floater_copy.remove()

            ps_iterator_ = ps_iterator_.walk_downstream()

    def is_drop_position(self, ps_iterator_, floater_copy, starting_point):
        if floater_copy.get_head().external_tail_head_test():
            # Conditions for merging to the right (no additional conditions)
            if 'ADV' in floater_copy.get_labels() or 'P' in floater_copy.get_labels():
                return True
            # Conditions for merging to the left
            else:
                if ps_iterator_.get_head() is not starting_point.get_head(): # Don't go inside where you started
                    if ps_iterator_.get_head().count_specifiers() < 2: # Don't fill in more than one SPEC position
                        return True
                    else:
                        return False
                else:
                    return False
        else:
            return False

    def locate_minimal_tense_edge(self, ps):

        ps_iterator_ = ps
        node = ps

        # Go upwards to the upper edge of the finite construction
        while ps_iterator_:
            node = ps_iterator_
            if ps_iterator_.sister() \
                    and 'FIN' in ps_iterator_.get_labels() \
                    and 'FIN' not in ps_iterator_.sister().get_labels():
                break
            ps_iterator_ = ps_iterator_.walk_upstream()

        # we return the right const because that is the upper edge
        if node.right_const and not node.right_const.adjunct:
            return node.right_const
        else:
            return node

    # Creates an adjunct of a constituent
    def create_adjunct(self, ps):
        """
        Creates an adjunct out of a constituent.
        """

        def make_adjunct(ps):
            #if ps.geometrical_sister() and ps.geometrical_sister().adjunct:
            #    log(f'\t\t\t\t{ps} cannot be made an adjunct because its sister is an adjunct.')
            #    return False
            ps.adjunct = True
            log(f'\t\t\t\t{ps} was made an adjunct.')
            if ps.geometrical_sister() and ps.geometrical_sister().adjunct:
                ps.mother.adjunct = True
            return True

        # --- Main function begins here --- #

        head = ps.get_head()

        # todo this has to be rewritted so that it uses projection (label projection) not geometry
        # If the head is primitive, we must decide how much of the surrounding structure we will eat
        if ps.is_primitive():
            # If a complex adjunct has found an acceptable position, we use !SPEC:* feature
            if head.external_tail_head_test():
                if '!SPEC:*' in head.features and head.mother.mother and self.get_specifiers(head):
                    make_adjunct(head.mother.mother)
                    return ps.mother.mother
                else:
                    if head.mother and head.mother.get_head() == head:
                        make_adjunct(head.mother)
                    else:
                        make_adjunct(head)
                    return ps.mother
            # If the adjunct is still in wrong position, we eat the specifier if accepted
            else:
                # If potential Spec exists and the head accepts specifiers...
                if self.get_specifiers(head) and not '-SPEC:*' in head.features and \
                        not set(head.get_not_specs()).intersection(set(self.get_specifiers(head)[0].get_labels())):
                    if head.mother.mother:
                        make_adjunct(head.mother.mother)
                    return ps.mother.mother
                else:
                    make_adjunct(head.mother)
                    return ps.mother
        else:
            make_adjunct(ps)

    # This will provide unique names when chains are formed
    # It is used only for output purposes
    def babtize(self):
        self.name_provider_index += 1
        return str(self.name_provider_index)

# get_specifiers() wrapper that implements the smodular interface to the PhraseStructure class
    def get_specifiers(self, h):
        specs = h.get_specifiers()
        return [spec for spec in specs if not spec.is_primitive()]