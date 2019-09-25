# This modular and class defines basic linguistic competence, i.e. phrase structures and operations on phrase structure
from support import log
from LF import LF

major_category = {'N', 'Neg/fin', 'P', 'D', 'C/fin', 'T/fin', 'iWH', 'iR', 'A', 'v', 'V', 'ADV', 'Q', 'NUM', 'T', 'INF'}

class PhraseStructure:

    # Constituent constructor
    def __init__(self, left_constituent=None, right_constituent=None):
        """"
        Creates a new constituent by Merge or by out of the blue generation
        """

        # Merge(A,B)
        self.left_const = left_constituent
        self.right_const = right_constituent
        if self.left_const:
            self.left_const.mother = self
        if self.right_const:
            self.right_const.mother = self
        self.mother = None

        # Default feature set
        self.features = set()   # Primitive constituents have features
        self.morphology = ''
        self.internal = False   # Tells if the constituent is word-internal
        self.adjunct = False    # Marks the constituent as an adjunct. For right adjuncts this means the "location"
                                # of the constituent, so that it is stored into a separate syntactic working space

        # This tells if the constituent has been re-merged into another position
        # When False, the constituent should in its canonical first-Merge position
        self.find_me_elsewhere = False

        # --- Non-empirical support functions --- #

        # This name is used to identify chains for output, it has not other function
        # It possibly overlaps with "key" below
        self.identity = ''      # A unique handler/name for the constituent
        self.rebaptized = False # Support variable used in the creation of chain numbering

    # Returns the node 'item' at the right edge
    # E.g. ps[3] = 3rd node at the right edge
    def __getitem__(self, item):

        iterator_ = 0
        ps_ = self
        while ps_ and not iterator_ == item:
            if not ps_.is_primitive():
                ps_ = ps_.right_const
                iterator_ = iterator_ + 1
            else:
                ps_ = None

        if not ps_:
            raise IndexError
        else:
            return ps_

    # returns the index of 'site' inside 'self'
    def index(self, site):

        ps_ = self
        iterator_ = 0
        while not ps_ == site and ps_.right_const and not ps_.is_primitive():
            ps_ = ps_.right_const
            iterator_ = iterator_ + 1

        if ps_ == site:
            return iterator_
        else:
            return None

    # Merges 'ps' to 'self' at 'direction, i.e. H.merge(G, 'right'') = [H G]
    def merge(self, ps, direction='right'):
        """
        Countercyclic Merge
        """

        new_ps = None               # The resulting new complex constituent
        left = False
        right = False

        if self.mother:             # Determines whether 'self' is left or right
            if self.is_left():
                left = True
            else:
                right = True

        old_mother = self.mother    # Store link between mother and self
        old_mother = self.mother    # Store link between mother and self

        # Create new constituent
        if direction == 'left':
            new_ps = PhraseStructure(ps, self)          # An elementary Merge operation
        if direction == 'right':
            new_ps = PhraseStructure(self, ps)          # An elementary Merge operation

            if self.adjunct and self.is_primitive():    # Percolation adjuncthood from head to phrase
                new_ps.adjunct = True
                self.adjunct = False

        # Put the new constituent countercyclically into the tree into the position of original 'self'
        if right:
            old_mother.right_const = new_ps
        if left:
            old_mother.left_const = new_ps
        new_ps.mother = old_mother

        return new_ps.get_top()

    def __mul__(self, ps):

        def get_bottom(site):
            ps_ = site
            while ps_.right_const:
                ps_ = ps_.right_const
            return ps_

        get_bottom(self).right_const = ps
        ps.mother = get_bottom(self)
        get_bottom(self).left_const = None

        return self.get_top()

    # This is reductive definition for EPP under current feature system
    def EPP(self):
        """
        A reductive definition for the generalized EPP feature.
        """
        for f in self.features:
            if f == 'SPEC:*' or f == '!SPEC:*':
                return True
        return False

    # This function copies a constituent and does all other operations required for dropping
    # Babtize will be the name (index) given to the original and its copy,
    # and is used for chain identification in output only
    def transfer(self, babtize='1'):
        """
        Prepares an altered copy of a phrase for internal merge
        """

        # Removes tail-features (if any) from a constituent
        def remove_tail_features(ps):
            if not ps.is_primitive():
                remove_tail_features(ps.left_const)
                remove_tail_features(ps.right_const)
            else:
                remove_set = set()
                for f in ps.features:
                    if f[:4] == 'TAIL':
                        remove_set.add(f)
                ps.features = ps.features.difference(remove_set)

        # --- Main function begins here --- #

        if self.identity == '':
            self.identity = babtize

        # take copy
        self_copy = self.copy()             # Copy the constituent
        self_copy.find_me_elsewhere = False # Copy is marked for being where it is
        self_copy.silence_phonologically()  # Silence the new constituent phonologically
        self.find_me_elsewhere = True       # Mark that the constituent has been copied

        # neutralize the original
        remove_tail_features(self)         # Remove tail-features from the original

        return self_copy

    # Removes an element from the phrase structure
    def remove(self):
        """
        Removes a constituent countercyclically from the phrase structure.
        """

        mother = self.mother
        sister = self.geometrical_sister()
        grandparent = self.mother.mother

        sister.mother = sister.mother.mother    # Fixing the phrase structure after the leftover hole
        if mother.is_right():
            grandparent.right_const = sister
            self.mother = None
        elif mother.is_left():
            grandparent.left_const = sister
            self.mother = None

        return

    def get_affix_list(self):
        lst = [self]
        iterator_ = self

        while iterator_:
            if iterator_.right_const:
                iterator_ = iterator_.right_const
                lst.append(iterator_)
            else:
                iterator_ = None

        return lst

    def get_affix(self):
        if not self.left_const and self.is_primitive():
            return self.right_const
        else:
            return None

    # This function returns the highest mother node, i.e. identifies the phrase structure that contains 'self'
    def get_top(self):
        """
        Returns the highest node in the phrase structure.
        """
        result = self
        while result.mother:
            result = result.mother
        return result

    # Labeling
    def get_labels(self):
        """
        Returns the set of labels (all label features) of a constituent, complex or simple.
        """
        return self.get_head().get_cats()

    # Labeling algorithm
    # Looks for the closest primitive head, ignores right adjuncts
    def get_head(self):
        """
        Returns the head of a phrase (critical part of the labeling algorithm).
        """

        # We look at two cases

        # Case 1: head can be determined without recursive call
        # Case 1a: primitive constituent alone is always a head
        if self.is_primitive():
            return self

        # Case 1b: primitive constituent at left
        # [H XP] returns H: primitive constituent only at left is head
        if not self.is_primitive():
            if self.left_const.is_primitive():
                return self.left_const

        # Case 1c: primitive constituent at right: check this if (1b) fails
        # {XP H] returns H: primitive constituent only at right is head
        if not self.is_primitive():
            if self.right_const.is_primitive():
                return self.right_const

        # Side effect: if we have [H G] then H will be the head, because of the ordering between 1b and 1c.

        # Case 2: head cannot be determined without recursive call
        # [XP, YP] = look into YP if it is not an adjunct, otherwise look into XP
        if not self.is_primitive():
            if not self.left_const.is_primitive() and not self.right_const.is_primitive():
                if self.right_const.adjunct:
                    return self.left_const.get_head()
                return self.right_const.get_head()

    def get_unvalued_features(self):
        unvalued_phi_set = set()
        for f in self.features:
            if f[:4] == 'PHI:' and f[-1] == '_':
                unvalued_phi_set.add(f)
        return unvalued_phi_set

    # Returns the sister of the constituent X, right adjuncts are invisible
    # [Y <X>], <X> has no sister
    # [X <Y>], X has no sister, looks mother next
    # [X Y], [Y, X], both sisters to each other
    def sister(self):
        """
        Finds and returns the (first non-right adjunct) sister of a constituent in a phrase structure.
        """

        ps_ = self

        # Recursive loop that ignores right-adjuncts
        while ps_.mother:
            if ps_.is_right() and ps_.adjunct:
                return None
            if ps_.is_left() and not ps_.mother.right_const.adjunct:
                return ps_.mother.right_const
            if ps_.is_right():
                return ps_.mother.left_const
            ps_ = ps_.mother

        return None

    # Returns the specifier of head ('self') if available, otherwise returns 'None'
    def specifier(self):
        """
        Returns the specifier of a constituent (and None if no specifier exists).
        """

        # Checks that the left aunt node exists
        if self.is_primitive() and \
                self.is_left() and \
                self.mother.sister() and \
                not self.mother.adjunct and \
                self.mother.sister().is_left() and \
                not self.mother.sister().is_primitive():
            # Checks that the head projects, not the left branch (in which case the head is inside right adjunct)
            if self.mother.mother.get_head() == self.get_head():
                return self.mother.sister()
        # A phrasal sister to a right primitive node is its specifier
        elif self.is_primitive() and self.is_right() and self.sister() and not self.sister().is_primitive():
            return self.sister()
        # If there is no overt phrasal specifier, we try to construct a pro-element
        else:
            if self.extract_pro():
                return self.extract_pro()
            else:
                return None

    def count_specifiers(self):

        ps_ = self.mother
        count = 0

        while ps_ and ps_.sister() and \
                (ps_.sister().is_left() and \
                not ps_.sister().is_primitive()) and \
                ps_.sister().find_me_elsewhere:
            count = count + 1
            ps_ = ps_.walk_upstream()
        return count

    def get_specifiers(self):

        if not self.is_primitive():
            return None

        if self.is_right():
            ps_ = self
        else:
            ps_ = self.mother
        list = []

        while ps_ and ps_.sister() and (ps_.sister().is_left() and not ps_.sister().is_primitive()):
            list.append(ps_.sister())
            ps_ = ps_.walk_upstream()

        if not list:
            if self.extract_pro():
                list.append(self.extract_pro())

        return list

    # Checks that there is no phi-feature conflicts at 'self'
    # This is in reality a more general function that checks there are no feature conflicts of any kind
    # but is definite more narrowly in order not to create unnecessary problems
    def phi_conflict(self):
        for f in self.features:
            if f[:4] == 'PHI:' and f[-1] != '_':  # unvalued phi-feature
                for g in self.features:
                    if g[:4] == 'PHI:' and g[-1] != '_':  # another unvalued phi-feature
                        f_type = f.split(':')[1]
                        g_type = g.split(':')[1]
                        f_value = f.split(':')[2]
                        g_value = g.split(':')[2]
                        if f_type == g_type and f_value != g_value:
                            return True
        return False

    # This extracts a pro-element from a primitive head
    # A pro-element (pronominal element) is reconstructed from agreement features obtained originally from the input
    # The pro-element will count as a specifier if no phrasal SPEC element is found (by specifier() function).
    # Return the element if it can be construed
    # Conditions for pro: use only valued phi-features, cannot use contradicting/conflicting features
    def extract_pro(self):
        phi_set = set()

        if 'ARG' in self.features: # Only phi-active head can contain a pro-element
            for f in self.features:
                if f[:4] == 'PHI:':  # Only valued phi-features count as pronouns
                    phi_set.add(f)
            # Here we reconstruct the pro-element and its properties
            # It is a phonologically silent (D, p)^0 element
            if phi_set:
                pro = PhraseStructure()
                pro.features = pro.features | phi_set
                pro.features.add('CAT:D')
                pro.features.add('PF:pro')
                pro.silence_phonologically()
                pro.find_me_elsewhere = True
                # Only a consistent phi-set can create a pronoun
                if not pro.phi_conflict():
                    return pro
            return None

    # Returns the complement of head ('self') if available, otherwise returns None
    # Complement = right sister
    def complement(self):
        """
        Returns the complement of a head.
        """

        # todo, I don't understand why we don't check for primitiveness, this must be checked later.
        # Note that right adjunct bypassing is in the definition of "sisterhood"
        if self.sister() and self.sister().is_right():
            return self.sister()
        return None

    # Returns the geometrical sister (not ignoring right adjuncts)
    def geometrical_sister(self):
        """
        Returns the geometrical sister of a constituent. Geometrical sister is determined by Merge.
        """

        if self.mother:
            if self.is_left():
                return self.mother.right_const
            if self.is_right():
                return self.mother.left_const

        return None

    def get_selector(self):
        """
        Return the closest c-commanding primitive head or None if there is none.
        """
        feature_vector = self.get_feature_vector()
        if len(feature_vector) == 1:
            return None
        else:
            return feature_vector[1]

    def is_left(self):
        """
        Returns True is the constituent is the left constituent.
        """

        if self.mother and self.mother.left_const == self:
            return True
        else:
            return False

    def is_right(self):
        """
        Returns True is the constituent is the right constituent.
        """

        if self.mother and self.mother.right_const == self:
            return True
        else:
            return False

    def is_primitive(self):
        """
        Returns True is the constituent does not have two daughters.
        """

        if self.right_const and self.left_const:
            return False

        else:
            return True

    # todo this function no longer works as intended -- remove? we should use is_primitive
    def has_children(self):
        return self.left_const and self.right_const

    def has_affix(self):
        if self.right_const and not self.left_const:
            return True
        else:
            return False

    # todo, is this needed anymore?
    def is_word_internal(self):
        """
        Returns True is the constituent was internal to a word in the input string.
        """
        return self.internal

    def is_adjoinable(self):
        """
        Returns True if the constituent can be attached to the phrase structure as a non-selected adjunct.
        """

        adjoinable_categories = {'ADV', 'R', 'D', 'P', 'TO/inf'}
        if self.adjunct:
            return True
        if adjoinable_categories.intersection(self.get_labels()):
            return True
        else:
            return False

    def copy(self):
        """
        Copies a constituent and returns the newly created copy.
        """

        ps_ = PhraseStructure()
        if self.left_const:
            ps_.left_const = self.left_const.copy()
            ps_.left_const.mother = ps_
        if self.right_const:
            ps_.right_const = self.right_const.copy()
            ps_.right_const.mother = ps_
        if self.features:
            ps_.features = self.features.copy()
        ps_.morphology = self.morphology
        ps_.internal = self.internal
        ps_.adjunct = self.adjunct
        ps_.find_me_elsewhere = self.find_me_elsewhere
        ps_.identity = self.identity
        return ps_

    # Creates an adjunct of a constituent
    def create_adjunct(self):

        def make_adjunct(ps):
            ps.adjunct = True
            log(f'\t\t\t\t\t\t{ps} was made an adjunct.')
            if ps.geometrical_sister() and ps.geometrical_sister().adjunct:
                ps.mother.adjunct = True
            return True

        # --- Main function begins here --- #

        head = self.get_head()

        # If the head is primitive, we must decide how much of the surrounding structure he will eat
        if self.is_primitive():
            # If a complex adjunct has found an acceptable position, we use !SPEC:* feature
            if head.external_tail_head_test():
                if '!SPEC:*' in head.features and head.mother.mother and self.get_specifiers():
                    make_adjunct(head.mother.mother)
                    return self.mother.mother
                else:
                    if head.mother and head.mother.get_head() == head:
                        make_adjunct(head.mother)
                    else:
                        make_adjunct(head)
                    return self.mother
            # If the adjunct is still in wrong position, we eat the specifier if accepted
            else:
                # If potential Spec exists and the head accepts specifiers...
                if self.get_specifiers() and not '-SPEC:*' in head.features and \
                        not set(head.get_not_specs()).intersection(set(self.get_specifiers()[0].get_labels())) and \
                        not self.get_specifiers()[0].is_primitive():
                    if head.mother.mother:
                        log(f'{head}: {head.get_specifiers()}')
                        make_adjunct(head.mother.mother)
                    return self.mother.mother
                else:
                    make_adjunct(head.mother)
                    return self.mother
        else:
            make_adjunct(self)

    def LF_legibility_test(self):
        """
        Checks if the phrase structure, as a detached item, is interpretable at the LF-level
        """
        def detached(ps):
            ps.mother = None
            return ps

        lf = LF()
        lf.test(detached(self.copy()))
        return lf

    # This will separate ps from its host and return the mother (for later attachment)
    def detach(self):
        """
        Detaches the constituent from its mother (i.e. breaks their mother-daughter relation), returns the mother.
        """

        if self.mother:
            original_mother = self.mother
            self.mother = None
        else:
            original_mother = None

        return original_mother

    # Probe-goal function
    # Head ('self') probes for goal features ('goal features')
    def probe(self, probe_label, goal_feature):
        """
        Performs a probe-goal check and returns the goal constituent is match is found.
        """

        # Nothing to probe
        if self.is_primitive() and self.is_right():
            return None

        ps_ = self.sister()

        # Search loop
        while ps_:
            # If the current constituent ps_ is primitive, we have reached the end and should perform
            # feature match and return accordingly
            if ps_.is_primitive():
                if goal_feature in ps_.features:
                    return ps_
                else:
                    return None

            # If the current constituent is not primitive, match with the left constituent
            else:
                # Check left constituent head for goal feature
                if ps_.left_const.get_head().features and goal_feature in ps_.left_const.get_head().features:
                    return ps_.left_const

                # Check left constituent for a criterial feature
                elif goal_feature[:4] == 'TAIL' and goal_feature[5:] in ps_.left_const.get_criterial_features():
                    return ps_.left_const

                # Walk downstream
                else:
                    # Intervention clauses
                    # 1. Feature intervention (Rizzi-style): do not look past another probe of the same type (same label)
                    if ps_.left_const.is_primitive() and ps_.left_const.features and probe_label.issubset(ps_.left_const.features):
                        return None
                    else:
                        ps_ = ps_.walk_downstream()

    # This functions returns the feature vector associated with 'self'
    def get_feature_vector(self):
        """
        Returns the feature vector of a constituent.
        """

        feature_vector = [self]
        _ps_iterator = self

        # Go upwards from self and add all heads to the feature vector
        # Ignore complement (i.e. H in [G H])

        while _ps_iterator and _ps_iterator.mother:
            if _ps_iterator.geometrical_sister() \
                and _ps_iterator.geometrical_sister().is_primitive() \
                and _ps_iterator.geometrical_sister().is_left() \
                and not _ps_iterator.geometrical_sister() == self.complement():
                    feature_vector.append(_ps_iterator.geometrical_sister())

            # Here we don't use upstream walk because we don't want to ignore adjuncts
            if _ps_iterator.mother:
                _ps_iterator = _ps_iterator.mother
            else:
                _ps_iterator = None

        return feature_vector

    # Determines if a constituent if finite
    # Substitutes for a separate [fin] feature in this version
    def is_finite(self):
        """
        Returns True if the constituent is finite (contains a finite head).
        """
        head = self.get_head()
        if 'CAT:FIN' in head.features:
            return True
        else:
            return False

    # Implements the external tail head test
    def external_tail_head_test(self):
        """
        Executes the external tail-head test for head H.
        """
        def get_max(ps):
            ps_ = ps
            while ps_.mother and ps_.mother.get_head() == self.get_head():
                if ps_.mother:
                    ps_ = ps_.walk_upstream()
                else:
                    break
            return ps_

        # --- Main function begins here ---#
        tail_sets = self.get_tail_sets()
        if not tail_sets:
            return True

        feature_vector = self.get_feature_vector()

        for tail_set in tail_sets:

            # Condition i)
            # First check if the constituent is already inside the checking projection (Spec-Head checking)
            if get_max(self) and get_max(self).mother and get_max(self).mother.get_head().check_features(tail_set):
                if self.mysterious_property(): # False if self is DP without genitive Case (PP, Advs, genitive DPs are accepted)
                    return True

            # Condition ii)
            # Check if goal's tail features can be matched in the feature vector
            if 'CAT:ADV' not in self.features:
                for const in feature_vector:
                    # Ignore the first element which is the goal itself
                    if const is not self:
                        # If ALL goal's features are matched, the test is accepted
                        # Notice that we check also internal affixes
                        for m in const.get_affix_list():
                            if m.check_features(tail_set):
                                return True
                            # If there is PARTIAL match, it is left unchecked
                            elif tail_set & const.features:
                                return False

            return False

    def mysterious_property(self):
        # True if self is a DP with genitive case
        if 'CAT:D' in self.features and not 'TAIL:CAT:INF,A/HEAD' in self.features:
            return False
        else:
            return True

    # This returns the phi-set of a constituent
    # This version is only used when promoting a DP into adjunct on the basis of its phi-set (which is wrong)
    def get_phi_set(self):
        head_ = self.get_head()
        return {f for f in head_.features if f[:4] == 'PHI:' and len(f.split(':')) == 3}

    def get_bottom_affix(self):
        if not self.is_primitive:
            return None

        ps_ = self
        while ps_.right_const:
            ps_ = ps_.right_const

        return ps_

    # Returns a set of tail feature sets from the head of 'self'
    def get_tail_sets(self):
        tail_features = set()
        constituent_ = self.get_head()

        for f in constituent_.features:
            if f[:4] == 'TAIL':
                tail_features.add(frozenset((f[5:].split(','))))

        if tail_features:
            return tail_features
        else:
            return None

    # Checks that goal does not participate in illegal partial feature tailing
    def internal_tail_head_test(self):
        """
        Executes an internal tail-head test.
        """

        tail_sets = self.get_tail_sets()
        if not tail_sets:
            return True

        feature_vector = self.get_feature_vector()

        for tail_set in tail_sets:
            # Check if goal's tail features can be matched in the feature vector
            for const in feature_vector:
                # Ignore the first element which is the goal itself
                if const is not self:
                    # If ALL goal's features are matched, the test is accepted
                    if const.check_features(tail_set):
                        return True
                    # If there is PARTIAL match, the test is rejected
                    # (Intervention)
                    elif tail_set & const.features:
                        return False

        # If there there were NO overlapping features, this test is accepted
        return True

    def get_bottom(self):
        ps_ = self

        while not ps_.is_primitive():
            ps_ = ps_.right_const

        return ps_

    # This will return a set of criterial features found inside the constituent (self)
    # We don't search (a) below T/fin or (b) into right adjuncts
    # Conditions (a-b) are subject to revision
    def get_criterial_features(self):
        """
        Returns a set of criterial features found inside a constituent.
        """

        set_ = set()
        if self.left_const and not self.left_const.find_me_elsewhere:
            set_ = set_.union(self.left_const.get_criterial_features())
        if self.right_const and not self.right_const.adjunct and not 'T/fin' in self.right_const.get_labels():
            set_ = set_.union(self.right_const.get_criterial_features())
        if self.is_primitive():
            for f in self.features:
                if f[:5] == 'ABAR:':
                    set_.add(f[5:])
        return set_

    # Checks that constituent 'self' can check all features in the 'feature_set'
    def check_features(self, feature_set):
        return (feature_set & self.features) == feature_set

    # Checks if 'ps' contains a head with feature F
    def contains_feature(self, feature):
        """
        Checks if a constituent contains a head with some feature.
        """
        if self.left_const and self.left_const.contains_feature(feature):
            return True
        if self.right_const and self.right_const.contains_feature(feature):
            return True
        if self.is_primitive:
            if feature in self.features:
                return True
            else:
                return False

        return False

    # Walk downwards by following the heads
    def walk_downstream(self):
        """
        Returns the next constituent downward at the right edge.
        """

        if self.is_primitive():
            return None

        if self.left_const.is_primitive():
            if not self.right_const.adjunct:
                return self.right_const
            else:
                return self.left_const

        # Order matters: right phrase is prioritized if we have symmetric scenario
        if self.get_head() == self.right_const.get_head():
            return self.right_const

        if self.get_head() == self.left_const.get_head():
            return self.left_const

        return None

    def walk_upstream_geometrically(self):

        if self.mother:
            return self.mother
        else:
            return None

    # Walk upstream and ignore right-adjuncts
    def walk_upstream(self):
        """
        Returns the next constituent at the right edge in upward direction.
        """
        if self.mother:
            ps_ = self.mother

            # Climb upwards skipping all right-adjuncts
            while ps_.right_const.adjunct:
                if ps_.mother:
                    ps_ = ps_.mother
                else:
                    return ps_
            return ps_
        else:
            return None

    # This notion is currently used only at LF for antecedent search
    # I suspect that this is a semantically motivated property of the heads and not a phase.
    def is_phase(self):
        if 'CAT:v' in self.features or 'CAT:C' in self.features or 'CAT:FORCE' in self.features or 'CAT:COPULA' in self.features:
            return True
        else:
            return False

    def get_mandatory_comps(self):
        return  {f[6:] for f in self.features if f[:5] == '!COMP' and f != '!COMP:*'}

    def get_comps(self):
        return {f[5:] for f in self.features if f[:4] == 'COMP'} | {f[6:] for f in self.features if f[:5] == '!COMP'}

    def get_affix_comps(self):
        set_ = set()
        affixes = self.get_affix_list()
        for affix in affixes:
            for f in affix.features:
                if f[:4] == 'COMP':
                    set_.add(f[5:])
                if f[:5] == '!COMP':
                    set_.add(f[6:])

        return set_

    def get_not_comps(self):
        return {f[6:] for f in self.features if f[:5] == '-COMP'}

    # Return the set of POS categories
    def get_cats(self):
        return {f[4:] for f in self.features if f[:3] == 'CAT'}

    def get_specs(self):
        return {f[5:] for f in self.features if f[:4] == 'SPEC'} | {f[6:] for f in self.features if f[:5] == '!SPEC'}

    def get_not_specs(self):
        return {f[6:] for f in self.features if f[:5] == '-SPEC'}

    def get_rare_specs(self):
        return {f[6:] for f in self.features if f[:5] == '%SPEC'}

    # Transforms a set of lexical features to be used locally in parsing,
    def for_parsing(self, features):
        return {f[1:] if f.startswith('!') else f for f in features}

    # Transforms a set of lexical features to be used in checking LF-interface conditions
    def for_LF_interface(self, features):
        set_of_features = set()
        for f in features:
            if f[0] == '!' or f[0] == '-':
                set_of_features.add(f)
        return set_of_features

    # Silenced a constituent phonologically
    def silence_phonologically(self):
        """
        Silences the constituent phonologically.
        """

        if not self.features:
            self.features = {'null'}
        else:
            self.features.add('null')

        if self.left_const:
            self.left_const.silence_phonologically()
        if self.right_const:
            self.right_const.silence_phonologically()

# Below are support functions that will be moved to the support class and are not part of phrase structure at all

    def show_affix(self):
        i = ''
        if self.is_primitive() and self.right_const:
            i = self.right_const.get_cats_string()
            if self.right_const.right_const:
                i = i + ',' + self.right_const.show_affix()
        else:
            i = ''
        return i

    def get_pf(self):

        # We return phonological features but not inflectional features
        pfs = [f[3:] for f in self.features if f[:2] == 'PF' and f[3:] not in ['NOM', 'ACC', 'PAR', '3sg', 'FOC',
                                                                               'TOP']]
        if self.has_affix():
            affix_str = self.show_affix()
            return '.'.join(sorted(pfs)) + '{' + affix_str + '}'
        else:
            return '.'.join(sorted(pfs))

    def get_lf(self):
        # We return semantic features
        lfs = [f[3:] for f in self.features if f[:2] == 'LF']
        return '.'.join(sorted(lfs))

    def show_primitive_constituents(self):
        reply = ''
        if not self.is_primitive():
            reply += self.left_const.show_primitive_constituents()
            reply += self.right_const.show_primitive_constituents()
        else:
            reply += f'{self.get_pf()}:{sorted(self.features)}\n'
        return reply

    def spellout(self):
        pf = ''
        if self.left_const:
            if 'null' in self.left_const.features:
                pf = pf + '__'
            else:
                pf = pf + self.left_const.spellout()

        if self.right_const:

            if 'null' in self.right_const.features:
                pf = pf + '__'
            else:
                pf = pf + self.right_const.spellout()

        if self.is_primitive():
            pf = pf + self.get_pf() + ' '

        return pf

    def gloss(self):

        pf = ''
        if self.left_const:
            if 'null' in self.left_const.features:
                pf = pf + '__'
            else:
                pf = pf + self.left_const.gloss()

        if self.right_const:

            if 'null' in self.right_const.features:
                pf = pf + '__'
            else:
                pf = pf + self.right_const.gloss()

        if self.is_primitive():
            pf = pf + self.get_lf() + ' '

        return pf

    def show_all_vectors(self):
        if not self.is_primitive():
            return self.left_const.show_all_vectors() + self.right_const.show_all_vectors()
        return f'{self}: {self.get_feature_vector()}\n'

    # This function tries to create "informative" representation of the categories of the constituent ps
    def get_cats_string(self):
        cats = self.get_labels()
        major_cats = ''.join(sorted([label for label in cats if label in major_category]))
        if not self.is_primitive():
            suffix = 'P'
        else:
            suffix = ''
        return f'{major_cats}{suffix}'

    def show(self, start=True, label_only=False):

        s = f'{self.get_cats_string()} = ' if start else ''

        if self.identity != '':
            id_str = ':'+self.identity
        else:
            id_str = ''

        if self.features and 'null' in self.features:
            return s + '__' + id_str
        elif self.is_primitive():
            if not self.get_pf():
                return s + '?'
            else:
                return s + self.get_cats_string()
        elif label_only:
            if self.adjunct:
                return f'{s}{self.get_cats_string()}' + id_str
            else:
                return f'{s}{self.get_cats_string()}' + id_str
        else:
            if self.right_const.adjunct:
                left = self.left_const.show(start=False)
                right = self.right_const.show(start=False, label_only=True)
            else:
                left = self.left_const.show(start=False, label_only=True)
                right = self.right_const.show(start=False)

            return f'{s}[{left} {right}]' + id_str

    def illustrate(self):

        if self.is_primitive():
            if not self.get_pf():
                return '?'
            else:
                if self.adjunct:
                    return '<'+self.get_pf()+'>'
                else:
                    return self.get_pf()

        prefix= ''

        if 'null' in self.features:
            if self.adjunct:
                return '<' + prefix + self.left_const.illustrate() + ' ' \
                       + self.right_const.illustrate() + '>'
            else:
                return '['+ prefix + self.left_const.illustrate() + ' ' \
                   + self.right_const.illustrate() + ']'
        else:
            if self.adjunct:
                return f'<' + prefix \
                       + self.left_const.illustrate() + ' ' \
                       + self.right_const.illustrate() + '>'
            else:
                return f'[' + prefix\
                       + self.left_const.illustrate() + ' ' \
                       + self.right_const.illustrate() + ']'

    def illustrate_spellout(self):

        if self.identity != '':
            id_str = ':' + self.identity
        else:
            id_str = ''

        if self.is_primitive():
            if not self.get_pf():
                return '?'
            else:
                if self.adjunct:
                    return '<'+self.get_pf()+'>'
                else:
                    return self.get_pf()

        prefix= ''

        if 'null' in self.features:
            if self.adjunct:
                return '<__>' + id_str
            else:
                return '__' + id_str
        else:
            if self.adjunct:
                return f'<' + prefix \
                       + self.left_const.illustrate_spellout() + ' ' \
                       + self.right_const.illustrate_spellout() + '>' + id_str
            else:
                return f'[' + prefix\
                       + self.left_const.illustrate_spellout() + ' ' \
                       + self.right_const.illustrate_spellout() + ']' + id_str

    #   Standard output function that shows the phrase structure
    def __str__(self):

        # This adds a unique name to the constituent if it has one, so we can trace chains in the output
        if self.identity != '':
            index_str = ':'+self.identity
        else:
            index_str = ''

        # By writing something here you can track which elements are copied in the final solution
        if self.find_me_elsewhere:
            index_str = index_str + ''

        if self.features and 'null' in self.features:
            if self.adjunct:
                return '<'+self.get_cats_string()+'>' + index_str       # Adjuncts are represented as <,>
            else:
                return '(' + self.get_cats_string() + ')' + index_str   # Regular constituents as [,]

        if self.is_primitive():
            if not self.get_pf():
                return '?'
            else:
                if self.adjunct:
                    return '<'+self.get_pf()+'>'
                else:
                    if self.extract_pro():
                        return self.get_pro_type() + '.' + self.get_pf()
                    else:
                        return self.get_pf()
        else:
            if self.adjunct:
                return f'<{self.left_const} {self.right_const}>' + index_str
            else:
                return f'[{self.left_const} {self.right_const}]' + index_str

    # This function returns the type of pro-element depending on the valuation of (uD, up) probe
    # PRO = control pro
    # pro/x = antecedent requiring pro
    # pro = little-pro
    def get_pro_type(self):
        if 'PHI:NUM:_' in self.features and 'PHI:PER:_' in self.features and 'PHI:DET:_' in self.features:
            return 'PRO'
        if 'PHI:NUM:_' not in self.features and 'PHI:PER:_' not in self.features and 'PHI:DET:_' in self.features:
            return 'pro/x'
        return 'phi'

    # More detailed output function
    def __repr__(self):
        if self.is_primitive():
            if not self.get_pf():
                return '?'
            else:
                return self.get_cats_string()
        else:
            return f'[{repr(self.left_const)} {repr(self.right_const)}]'

    def simple_tree(self):
        if self.is_primitive():
            pf_part = self.get_pf() or '?'
            id_part = f':{self.identity}' if self.identity else ''
            if self.adjunct:
                return f'<{pf_part}{id_part}>'
            else:
                return pf_part + id_part
        if self.adjunct:
            opener = '<'
            closer = '>'
        else:
            opener = '['
            closer = ']'
        if self.identity:
            id_part = f'{self.get_head().get_pf()}:{self.identity}'
        else:
            id_part = self.get_head().get_pf()
        return f'{opener}.{id_part} {self.left_const.simple_tree()} {self.right_const.simple_tree()}{closer}'

    # Simpler notation for Merge
    def __add__(self, other):
        return self.merge(other, 'right')

    def rebaptize(self, old_name, new_name):
        if self.identity == old_name:
            if not self.rebaptized:
                self.identity = new_name
                self.rebaptized = True
        if self.left_const:
            self.left_const.rebaptize(old_name, new_name)
        if self.right_const:
            self.right_const.rebaptize(old_name, new_name)
        return

    # This function tidies the names for constituents
    # Chain presentation purposes only
    # This must be reworked later and move to support?
    def tidy_names(self, counter):
        if self.identity != '' and not self.rebaptized:
            self.get_top().rebaptize(self.identity, str(counter))
            counter = counter + 1
        if self.left_const:
            counter = self.left_const.tidy_names(counter)
        if self.right_const:
            counter = self.right_const.tidy_names(counter)
        return counter

