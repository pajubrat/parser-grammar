# This class defines basic linguistic competence, i.e. phrase structures and operations on phrase structure
from support import log
from LF import LF

major_category = {'N', 'Neg', 'Neg/fin', 'P', 'D', 'C', 'A', 'v', 'V', 'ADV', 'Q', 'NUM', 'T', 'TO/inf', 'A/inf', 'FORCE', '0', 'a', 'b', 'c', 'd', 'x', 'y', 'z'}

# Definitions and methods for phrase structure
class PhraseStructure:

    # Constituent constructor, Merge[A B]
    # Definition for cyclic Merge
    def __init__(self, left_constituent=None, right_constituent=None):

        # Merge(A,B)
        # Definition for simple Merge(A, B) that extents the structure
        # A = left constituent, B = right constituent
        #
        # Property 1. Constituents
        #
        self.left_const = left_constituent
        self.right_const = right_constituent
        #
        # Property 2. Mother-of relations
        #
        if self.left_const:
            self.left_const.mother = self
        if self.right_const:
            self.right_const.mother = self
        self.mother = None

        # Feature are stored as a set of grammatical objects.
        self.features = set()
        self.morphology = ''
        self.internal = False   # Tells if the constituent is word-internal; a more intuitive implementation is required
        self.adjunct = False    # Whether the constituent is stored in the secondary working space (i.e. is an adjunct)
        self.incorporated = False  # Tells if the constituent was incorporated

        # This feature is set if the constituent is copied into another location.
        # A better implementation would be one in which this property is derived from the modular architecture
        self.find_me_elsewhere = False

        # This name is used to identify chains for output purposes.
        self.identity = ''      # A unique handler/name for the constituent
        self.rebaptized = False  # Support variable used in the creation of chain numbering

        # Parameters for 2d visualization
        self.x = 0
        self.y = 0

    #
    #
    # BLock 1. Other structure building operations
    #
    #
    # Definition for countercyclic merge with substitution
    # Merges 'ps' to 'self' at 'direction, i.e. H.merge(G, 'right'') = [H G]
    def merge(self, ps, direction='right'):

        # Define new complex constituent that will result in the operation
        new_ps = None
        left = False
        right = False

        # Determines if 'self' is left or right
        if self.mother:
            if self.is_left():
                left = True
            else:
                right = True

        # Store link between mother and self
        old_mother = self.mother

        #
        # Condition 1. Create new constituent
        #
        if direction == 'left':
            new_ps = PhraseStructure(ps, self)          # An elementary Merge operation
        if direction == 'right':
            new_ps = PhraseStructure(self, ps)          # An elementary Merge operation

            if self.adjunct and self.is_primitive():    # Percolation adjuncthood from head to phrase
                new_ps.adjunct = True
                self.adjunct = False

        #
        # Condition 2. Put the new constituent counter-cyclically into the tree into the position of original 'self'
        #
        if right:
            old_mother.right_const = new_ps
        if left:
            old_mother.left_const = new_ps
        new_ps.mother = old_mother

        return new_ps.top()

    # Simpler notation for Merge
    def __add__(self, other):
        return self.merge(other, 'right')

    # Definition for an operation that removes an element from the phrase structure
    # Removes the element and seals the hole left behind.
    def remove(self):
        mother = self.mother
        sister = self.geometrical_sister()
        grandparent = self.mother.mother

        # Seals the leftover hole
        sister.mother = sister.mother.mother
        if mother.is_right():
            grandparent.right_const = sister
            self.mother = None
        elif mother.is_left():
            grandparent.left_const = sister
            self.mother = None

    def sink(self, ps):

        def get_bottom(site):
            ps_ = site
            while ps_.right_const:
                ps_ = ps_.right_const
            return ps_

        bottom = get_bottom(self)

        bottom.right_const = ps
        ps.mother = bottom
        bottom.left_const = None

        return self.top()

    #
    #
    # Block 2. Definitions for basic grammatical relations
    #
    #

    # Recursive definition for head (also label) of a phrase structure
    # Locates the most dominant head from XP when left is prioritized over right
    def head(self):

        # Case 1. H is primitive, then return H
        if self.is_primitive():
            return self

        # Case 2. H is not primitive
        else:
            # Case 2.A [H XP] returns H
            if self.left_const.is_primitive():
                return self.left_const

            # Case 2.B [XP H] returns H
            if self.right_const.is_primitive():
                return self.right_const

            # Case 2.C [XP, YP] = look into YP if it is not an adjunct, otherwise look into XP
            if not self.left_const.is_primitive() and not self.right_const.is_primitive():
                if self.right_const.adjunct:
                    return self.left_const.head()
                return self.right_const.head()

    # Definition for sisterhood
    # [Y <X>], <X> has no sister
    # [X <Y>], X has no sister, looks mother next
    # [X Y], [Y, X], X and Y sisters to each other
    def sister(self):
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

    # Definition for complex constituent
    def is_complex(self):
        return not self.is_primitive()

    # Definition for the relation of local specifier or local edge
    # XP is a local specifier for head H if and only if
    # Condition 1. They are in configuration [XP [H YP]], i.e.
    #   a) H is primitive
    #   b) H is left
    #   c) XP is complex
    #   d) [H YP] is not an adjunct
    #   e) H projects
    #       OR
    # Condition 2. They are in the configuration [XP H]
    #   a) H is primitive
    #   b) XP is complex
    #   c) H is right, XP is left
    #       OR
    # Condition 3. XP is a pro inside H.
    def local_edge(self):

        # Condition 1. Configuration [XP [H YP]]
        #   a) H is primitive
        #   b) H is left
        #   c) There is XP, [XP [H XP]], XP complex and left
        #   d) [H XP] is not adjunct
        #   e) H projects
        if self.is_primitive() and \
                self.is_left() and \
                self.mother.sister() and \
                not self.mother.adjunct and \
                self.mother.sister().is_left() and \
                self.mother.sister().is_complex():
            if self.mother.mother.head() == self.head():
                return self.mother.sister()

        # Case 2(a-c) Definition for specifier for a primitive right head
        elif self.is_primitive() and self.is_right() and self.sister() and self.sister().is_complex():
            return self.sister()

        # Case 3. Definition for pro-specifier (if no phrasal specifier exists)
        else:
            if self.extract_pro():
                return self.extract_pro()
            else:
                return None

    # Definition for the notion of edge (also generalized specifier)
    # A list of element inside the edge of head H, H = head
    # Condition 1. Collect all complex left sister phrases reached by upstream path from H until the left sister is not complex
    # Condition 2. If nothing is found, return pro-element if any
    def edge(self):

        # Presupposition 1. H is not complex
        if self.is_complex():
            return None

        if self.is_right():
            ps_ = self
        else:
            ps_ = self.mother

        # Specifiers will be collected into this list
        list = []

        # Condition 1. Collect all complex left sisters for which there exists an upstream path from H
        while ps_ and ps_.sister() and (ps_.sister().is_left() and ps_.sister().is_complex()):
            list.append(ps_.sister())
            ps_ = ps_.walk_upstream()

        # Condition 2. If nothing is found, try to extract the pro-element
        if not list:
            if self.extract_pro():
                list.append(self.extract_pro())

        return list

    # Definition for complement
    def complement(self):

        # A complement is a right sister (notice that there is a separate definition for sister())
        if self.sister() and self.sister().is_right():
            return self.sister()
        else:
            return None

    # Definition for geometrical sister
    def geometrical_sister(self):
        if self.mother:
            if self.is_left():
                return self.mother.right_const
            if self.is_right():
                return self.mother.left_const
        return None

    def Abar_movable(self):
        if self.scan_criterial_features():
            return True
        elif 'A/inf' in self.head().features:
            return True
        else:
            return False

    def must_have_head(self):
        if self.adjunct and not self.scan_criterial_features():
            return False
        else:
            return True

    def get_iterator(self):
        if self.is_left():
            return self.mother
        else:
            return self

    def get_phrasal_left_sister(self):
        if self.sister() and not self.sister().is_primitive() and self.sister().is_left():
            return self.sister()
        else:
            return None


    # Definition for selector
    # X is the selector of H if and only if
    # Condition 1. X is the  element in H's feature vector with index 1
    def selector(self):

        # Get the feature vector
        feature_vector = self.feature_vector()

        # If there are no c-commanding heads, we return no selector
        if len(feature_vector) == 1:
            return None
        else:
            # Condition 1. Return the local c-commanding head
            return feature_vector[1]

    # Definition for property X has a theta assigner P
    # X is assigned theta role by P if and only if
    # Condition 1. X has a primitive sister P OR,
    # Condition 2. X is at the edge of P.
    #
    # Returns P, if any
    def get_theta_assigner(self):
        # Condition 1. X has a primitive sister
        if self.sister() and self.sister().is_primitive():
            return self.sister
        # Condition 2. X is at the edge
        if self.container_head() and self in self.container_head().edge():
            return self.container_head()

    # Definition of max
    # XP is the maximum projection from head X if and only if
    # XP is the highest/last element (by upstream walk) whose head is H
    def max(self):
        ps_ = self
        last = self
        while ps_ and ps_.head() == self.head():
            last = ps_
            ps_ = ps_.walk_upstream()
        return last

    # Definition of left
    # X is the left constituent if and only if
    # Condition 1. X has mother M
    # Condition 2. X is the left constituent of M.
    def is_left(self):
        if self.mother and self.mother.left_const == self:
            return True
        else:
            return False

    # Definition of right
    # X is the right constituent if and only if
    # Condition 1. X has mother M
    # Condition 2. X is the right constituent of M.
    def is_right(self):
        if self.mother and self.mother.right_const == self:
            return True
        else:
            return False

    # Definition of primitive constituent
    # X is a primitive constituent if and only if
    # X does not have both the left and right constituents
    def is_primitive(self):
        if self.right_const and self.left_const:
            return False
        else:
            return True

    # Definition of bottom node
    # X is a bottom node of structure XP if and only if
    # Condition 1. X can be reached from XP by moving through its right constituents
    # Condition 2. X is primitive
    def bottom(self):
        ps_ = self

        while not ps_.is_primitive():
            ps_ = ps_.right_const

        return ps_

    # Definition for walking downwards (search) on the right edge
    # Condition 1. A primitive constituent has no downstream path
    # Condition 2. In [L, XP], L = intervening feature, downstream path terminates
    # Condition 3. In [XP, YP], YP not an adjunct, downward path is XP; YP otherwise
    # Condition 3'. In [XP, YP], downward path is that constituent whose head/label is the same as [XP, YP]
    #
    def walk_downstream(self, intervention_feature=None):

        # Condition 1. Primitive constituents cannot be searched further
        if self.is_primitive():
            return None

        # Condition 2. If [L, XP], L = intervening feature, search cannot go further
        if intervention_feature and self.left_const.is_primitive() and intervention_feature in self.left_const.features:
            log(f'\t\t\t\t\t({intervention_feature} intervenes search)')
            return None

        # Condition 3. In [X, YP], YP not an adjunct, downward path is XP; YP otherwise
        if self.left_const.is_primitive():
            if not self.right_const.adjunct:
                return self.right_const
            else:
                return self.left_const

        # Condition 3'. [XP YP]: follow selection
        if self.head() == self.right_const.head():
            return self.right_const
        if self.head() == self.left_const.head():
            return self.left_const

        return None

    def walk_downstream_geometrically(self):
        if self.is_complex() and self.right_const:
            return self.right_const
        else:
            return None

    def causes_intervention(self, feature, phrase_structure):
        if self != phrase_structure.minimal_search()[0]:                    # Ignore the first node
            if feature in self.sister().features:
                log(f'\t\t\t\t\tFeature {feature} causes HM intervention.')
                return True
            else:
                return False

    def detect(self, property=''):
        if property == 'complex head':
            complex_head = None
            if self.is_primitive() and self.has_affix():
                complex_head = self
            elif self.left_const and self.left_const.is_primitive() and self.left_const.has_affix():
                complex_head = self.left_const
            return complex_head
        return None

    def minimal_search(self):
        return [node for node in self]

    def is_primitive_head(self):
        if self.is_primitive() and not self.has_affix():
            return True
        else:
            return False

    def is_complex_head(self):
        if self.is_primitive() and self.has_affix():
            return True
        else:
            return False

    # Definition for geometrical upstream walk
    # XP can be reached from H by geometrical upstream walk if and only if
    # XP is the mother of H
    def walk_upstream_geometrically(self):
        if self.mother:
            return self.mother
        else:
            return None

    # Definition for upstream walk
    # XP is reached from H by upstream walk if and only if
    # XP is the first mother (of mother..) of H whose sister is not right adjunct
    def walk_upstream(self):
        if self.mother:
            ps_ = self.mother

            # Dodge right adjuncts
            while ps_.right_const.adjunct:
                if ps_.mother:
                    ps_ = ps_.mother
                else:
                    return ps_
            return ps_
        else:
            return None

    # Definition for the top of XP
    # T is the top of XP if and only if
    # Condition 1. T can be reached from XP by following mother path
    # Condition 2. T does not have mother.
    def top(self):
        result = self
        while result.mother:
            result = result.mother
        return result

    def node_at(self, position):
        ps_ = self.top()
        for pos in range(0, position):
                ps_ = ps_.right_const
        return ps_

    def get_position_on_geometric_right_edge(self):
        ps_ = self.top()
        position = 0
        while ps_:
            if ps_ == self:
                return position
            if ps_.right_const:
                position = position + 1
                ps_ = ps_.right_const
            else:
                return None

    # Copies a phrase structure
    def copy(self):
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

    #
    #
    # Block 3. Nonlocal dependencies and operations
    #
    #
    # Definition for nonlocal selection, i.e. the probe-goal dependency
    # Probe P establishes a probe-goal relation in relation to feature F with goal G (returned by the function) if and only if
    # Condition 1. The goal, or its head, has feature F,
    # Condition 2. There is an downstream path from P to G,
    # Condition 3. G is left constituent,
    # Condition 4. No intervention occurs.
    def probe(self, probe_label, goal_feature):

        if self.is_primitive() and self.is_right():
            return None

        ps_ = self.sister()

        # Search downward for goals
        while ps_:

            # Case 1. If we reach the bottom, we check and return from the function
            if ps_.is_primitive():
                if goal_feature in ps_.features:
                    return ps_
                else:
                    return None

            # Case 2. If we haven't reached the bottom, we try to match with the constituent at left
            else:
                # Check left constituent head for goal feature
                if ps_.left_const.head().features and goal_feature in ps_.left_const.head().features:
                    return ps_.left_const

                # Check left constituent for a criterial feature
                elif goal_feature[:4] == 'TAIL' and goal_feature[5:] in ps_.left_const.scan_criterial_features():
                    return ps_.left_const

                # Walk downstream
                else:
                    # Intervention breaks the search (this has not been studied in detail)
                    if ps_.left_const.is_primitive() and ps_.left_const.features and probe_label.issubset(ps_.left_const.features):
                        return None
                    else:
                        ps_ = ps_.walk_downstream()

    # Definition for the notion of feature vector (from my thesis work)
    # [H1...Hn] constitutes a feature vector for head X if and only if
    # Condition 1. each H is a primitive head,
    # Condition 2. each H is left,
    # Condition 3. H is not complement to X,
    # Condition 4. H can be reached from X by upstream walk but not ignoring adjuncts,
    # Condition 5. [H1...Hn] is ordered by locality, with local elements first,
    # Condition 6. H1 = X (with index 0)
    def feature_vector(self):

        # Condition 6.
        feature_vector = [self]

        # Starting point
        _ps_iterator = self

        # Upstream path (with adjuncts)
        while _ps_iterator and _ps_iterator.mother:
            # Conditions 1-3
            if _ps_iterator.geometrical_sister() and \
                    _ps_iterator.geometrical_sister().is_primitive() and \
                    _ps_iterator.geometrical_sister().is_left() and not \
                    _ps_iterator.geometrical_sister() == self.complement():
                feature_vector.append(_ps_iterator.geometrical_sister())

            # Condition 4. H can be reached from X by upstream walk but not ignoring adjuncts
            if _ps_iterator.mother:
                _ps_iterator = _ps_iterator.mother
            else:
                _ps_iterator = None

        return feature_vector

    # Definition for the external tail head test
    # A head H satisfies its tail-feature TAIL:F1...Fn if and only if
    #   Condition 1. H can establish a tail-head configuration with head K such that
    #       a)    HP is either inside a projection KP, or
    #       b)    K occurs in H's feature vector and is the closest that checks at least
    #             one tail-feature from H,
    #   AND
    #   Condition 2. K checks all tail-features from H and none of the negative features
    #
    #   Note:  Condition 1.1.a is applied to adverbials, condition 1.1.b to everything else.
    def external_tail_head_test(self):

        # Internal function
        def get_max(ps):
            ps_ = ps
            while ps_.mother and ps_.mother.head() == self.head():
                if ps_.mother:
                    ps_ = ps_.walk_upstream()
                else:
                    break
            return ps_

        # Internal function
        # Definition for negative tail set
        # Tail set T is negative if and only if it contains a feature that is negative
        def negative(tail_set):
            for f in tail_set:
                if f.startswith('*'):
                    return True
            return False

        #
        # --- Main function begins here ---#
        #
        # Each tail head condition is based on a set, here we collect them all first into a set of sets
        tail_sets = self.get_tail_sets()
        if not tail_sets:
            return True

        feature_vector = self.feature_vector()
        tests_checked = set()

        # Examine all tail sets
        for tail_set in tail_sets:

            exit = False

            # Condition 1.a) Tail features are checked by a head that contains XP
            # Applied to everything except non-genitive DPs.
            if get_max(self) and get_max(self).mother and get_max(self).mother.head().match_features(tail_set) == 'complete match':
                # mysterious property = option 1.a. is not applied to non-genitive DPs
                # (It is mysterious because I don't understand it fully, but it is required empirically.)
                if self.mysterious_property():
                    tests_checked.add(tail_set)

            # Condition 1.b) Tail features can be matched in the feature vector
            # Applied to everything besides (right) adverbs
            if 'ADV' not in self.features:
                for const in feature_vector:

                    if exit:
                        break

                    # Ignore the first element which is the goal itself
                    if const is not self:

                        # If ALL goal's features are matched, the test is accepted
                        # Notice that we check also internal affixes
                        for m in const.get_affix_list():

                            test = m.match_features(tail_set)

                            # Complete match is accepted and stored
                            # No further, nonlocal heads are examined (exit = True)
                            if test == 'complete match':
                                tests_checked.add(tail_set)
                                # If complete match is found, we do not test nonlocal heads
                                exit = True

                            # Partial match is not accepted, search is terminated immediately
                            elif test == 'partial match':
                                return False

                            # Negative match is not accepted, search is terminated immediately
                            elif test == 'negative match':
                                return False

                # If negative tail_set was not matched, it will be checked
                if negative(tail_set):
                    tests_checked.add(tail_set)

        # If all tests have been checked, the tail-head test succeeds
        if tests_checked & tail_sets == tail_sets:
            return True
        else:
            return False

    # Definition for internal tail head test
    # Internal tail head test is more lenient than the external version, returns false only if there is partial match
    def internal_tail_head_test(self):

        # Collect all tail head sets for testing
        tail_sets = self.get_tail_sets()
        if not tail_sets:
            return True

        feature_vector = self.feature_vector()

        for tail_set in tail_sets:

            # Check if goal's tail features can be matched in the feature vector
            for const in feature_vector:

                # Ignore the first element which is the goal itself
                if const is not self:

                    test = const.match_features(tail_set)

                    # Complete match is accepted and no further, nonlocal heads are examined
                    if test == 'complete match':
                        break

                    # Partial match (some, not all, features are matched) is not accepted, search is terminated immediately
                    if test == 'partial match':
                        return False

                    elif test == 'negative match':
                        return False

        # If there there were no overlapping features, this test is accepted
        return True

    # Definition for feature match
    # Head H checks features in set F if and only F
    # Condition 1. No negative features of F are matched with features in H, and
    # Condition 2a. All positive features of F are matched with features in H, which is COMPLETE MATCH, or
    # Condition 2b. Some positive features of F ar matched with features in H, which is PARTIAL MATCH, or
    # Condition 2c. A negative feature is matched, which is NEGATIVE MATCH.
    def match_features(self, features_to_check):

        # Partition the set of features into positive and negative features
        positive_features = {feature for feature in features_to_check if feature[0] != '*'}
        negative_features = {feature[1:] for feature in features_to_check if feature[0] == '*'}

        if negative_features & self.features:                           # Condition 2c
            return 'negative match'
        else:
            if positive_features & self.features == positive_features:  # Condition 2a
                return 'complete match'
            elif positive_features & self.features:                      # Condition 2b
                return 'partial match'

    # Recursive definition for contains-feature-F for a phrase
    # XP contains feature F if and only if
    # XP contains a head that has F.
    def contains_feature(self, feature):
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

    #
    #
    # Block 4. Functions which return properties from inside a head
    #
    #
    # Reductive definition for the (weak and strong) EPP
    def EPP(self):
        if 'SPEC:*' in self.features or '!SPEC:*' in self.features:
            return True
        else:
            return False

    def finite(self):
        if 'FIN' in self.features or 'T/fin' in self.features or 'Neg/fin' in self.features:
            return True
        else:
            return False

    # Returns the union of features of head and all its affixes
    def get_all_features_of_complex_word(self):

        # Target a head of the phrase if complex
        if self.is_complex():
            head = self.head()
        else:
            head = self

        # Add the features of the highest lexical item
        complex_word_features = head.features

        # Construct the union of the features of all lexical elements (affixes) inside the complex word
        for affix in head.get_affix_list():
            complex_word_features = complex_word_features | affix.features
        return complex_word_features

    # Return a list of affixes inside a grammatical head (including the head itself)
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

    # Returns the highest affix (if available)
    # Affix is A in [0, A]
    def get_affix(self):
        if not self.left_const and self.is_primitive():
            return self.right_const
        else:
            return None

    # Returns a set of unvalued phi-features
    # P is an unvalued phi-feature if and only if
    # Condition 1. It begins with "PHI"
    # Condition 2. It ends with "_"
    def get_unvalued_features(self):
        return {f for f in self.features if f[:4] == 'PHI:' and f[-1] == '_'}

    # Definition for pro-extraction
    # H has a pro-element if and only if
    # Condition 1. H is phi-active (+ARG)
    # Condition 2. H has consistent phi-set.
    #
    # P is a pro-element if and only if
    # Assumption 1. P is a constituent
    # Assumption 2. P has the phi-features from the host
    # Assumption 3. P has label D
    # Assumption 4. P has PF-feature 'PF:pro'
    # Assumption 5. P is phonologically covert
    # Assumption 6. P has consistent phi-set (Condition 2).
    def extract_pro(self):

        phi_set = set()
        # Condition 1. Only phi-active head can contain a pro-element
        if 'ARG' in self.features:

            # Condition 2. H has consistent phi-set
            # Collect the phi-set (features with PHI:)
            # Heads which require valuation can only construct pro from valued features
            if 'VAL' in self.features:
                phi_set = {f for f in self.features if f[:4] == 'PHI:' and f[-1] != '_'}
            else:
                # Heads marked for -val can generate PRO from unvalued features
                phi_set = {f for f in self.features if f[:4] == 'PHI:'}

            # Construct a pronominal phi-set
            if phi_set:

                # Assumption 1. Pro-element is a constituent
                pro = PhraseStructure()

                # Assumption 2. Pro-element has the phi-features from the host
                pro.features = pro.features | phi_set

                # Assumption 3. Pro-element has label D
                pro.features.add('D')

                # Assumption 4. Pro-element is printed out as 'pro'
                pro.features.add('PF:pro')

                # This is just to make its origin clear, not relevant theoretically
                pro.features.add('pro')

                # Assumption 5. Pro-element is phonologically covert
                pro.silence_phonologically()

                # Assumption 6/Condition 2. Pro-element can be created only from a consistent phi-set
                if not pro.phi_conflict():
                    return pro

            return None
        else:
            return None

    # Definition for affix
    # X has an affix if and only if X has a right constituent but not left constituent
    #
    # Note: the right constituent is the affix
    def has_affix(self):
        if self.right_const and not self.left_const:
            return True
        else:
            return False

    # Definition for the concept of word internal
    # X is word-internal if and only if it is marked for being internal
    def is_word_internal(self):
        return self.internal

    # Definition for adjoinable phrase
    # XP is an adjoinable phrase if and only if
    #
    # Condition 1. It is an adjunct
    # Condition 2. it belongs to one of the adjoinable categories OR
    def is_adjoinable(self):
        # Condition 1. Adjuncts are automatically adjoinable
        if self.adjunct:
            return True

        # Condition 2. A constituent with 'SEM:adjoinable' is adjoinable
        if 'adjoinable' in self.head().features:
            return True
        else:
            return False

    # This involves empirical issues that I don't fully understand
    def mysterious_property(self):
        if 'D' in self.features and not 'TAIL:INF,A/HEAD' in self.features:
            return False
        else:
            return True

    # Definition for well-formed phi-set
    # {P1...Pn} is a well-formed phi-set if and only if
    # Condition 1. It contains features with the form 'PHI:T:V'
    def get_phi_set(self):
        head_ = self.head()
        return {f for f in head_.features if f[:4] == 'PHI:' and len(f.split(':')) == 3}

    # Definition of bottom affix
    def get_bottom_affix(self):
        if not self.is_primitive:
            return None

        ps_ = self
        while ps_.right_const:
            ps_ = ps_.right_const

        return ps_

    # Definition for tail sets
    def get_tail_sets(self):

        tail_features = set()
        constituent_ = self.head()

        for f in constituent_.features:
            if f[:4] == 'TAIL':
                tail_features.add(frozenset((f[5:].split(','))))

        if tail_features:
            return tail_features
        else:
            return None

    # Definition for scope-operator that can bind a variable at LF
    # X is a scope-operator if and only if
    # Condition 1. X has an operator feature
    # Condition 2. X is finite (has feature FIN)
    def is_scope_operator(self):
        operator_features = {feature for feature in self.features if feature[:2] == 'OP'}
        if 'FIN' in self.features and operator_features:
            return True
        else:
            return False

    # Returns all operator features from the head H as a set of [OP, VAL] lists
    def operator_features(self):
        return {feature for feature in self.features if feature[:3] == 'OP'}

    def has_op_feature(self):
        return {feature for feature in self.features if feature[:3] == 'OP'}

    # Recursive definition for criterial features (type ABAR:_) inside phrase
    def scan_criterial_features(self):

        set_ = set()

        # Condition 1. Left branch is searched if it has not been moved
        if self.left_const and not self.left_const.find_me_elsewhere:
            set_ = set_ | self.left_const.scan_criterial_features()

        # Condition 2. Right branch is searched if it is not adjunct and its label is not T/fin
        if self.right_const and not self.right_const.adjunct and not 'T/fin' in self.right_const.head().features:
            set_ = set_ | self.right_const.scan_criterial_features()

        # Condition 3. Primitive constituents are examined for criterial features
        if self.is_primitive():
            set_ |= {feature for feature in self.features if feature[:3] == 'OP:'}
        return set_

    # Definition for phase (used by Agree-1)
    def is_phase(self):
        if 'v' in self.features or 'C' in self.features or 'FORCE' in self.features or 'COPULA' in self.features:
            return True
        else:
            return False

    # Definition for mandatory complement selection
    def get_mandatory_comps(self):
        return  {f[6:] for f in self.features if f[:5] == '!COMP' and f != '!COMP:*'}

    # Definition for complement selection
    def get_comps(self):
        return {f[5:] for f in self.features if f[:4] == 'COMP'} | {f[6:] for f in self.features if f[:5] == '!COMP'}

    # Definition for complements selection for a complex head
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

    # Definition for negative complement selection
    def get_not_comps(self):
        return {f[6:] for f in self.features if f[:5] == '-COMP'}

    # Definition for positive specifier selection
    def specs(self):
        return {f[5:] for f in self.features if f[:4] == 'SPEC'} | {f[6:] for f in self.features if f[:5] == '!SPEC'}

    # Definition for negative specifier selection
    def get_not_specs(self):
        return {f[6:] for f in self.features if f[:5] == '-SPEC'}

    # Definition for rate specifier selection (not used)
    def get_rare_specs(self):
        return {f[6:] for f in self.features if f[:5] == '%SPEC'}

    # Returns features without !
    def for_parsing(self, features):
        return {f[1:] if f.startswith('!') else f for f in features}

    # Return the phonological form of the constituent if any
    # Does some additional formatting
    def get_pf(self):

        # We return phonological features but not inflectional features
        pfs = [f[3:] for f in self.features if f[:2] == 'PF' and f[3:] not in ['NOM', 'ACC', 'PAR', '3sg', 'FOC',
                                                                               'TOP']]
        if self.has_affix():
            affix_str = self.show_affix()
            return '.'.join(sorted(pfs)) + '(' + affix_str + ')'
        else:
            return '.'.join(sorted(pfs))

    # Definition for semantic features (access keys to concepts)
    def get_lf(self):
        lfs = [f[3:] for f in self.features if f[:2] == 'LF']
        return '.'.join(sorted(lfs))

    #
    #
    # Block 5. Unclassified functions
    #
    #
    # Returns the node 'item' at the right edge
    # E.g. ps[3] = 3rd node at the right edge
    def __getitem__(self, position):

        iterator_ = 0
        ps_ = self

        while ps_:
            if iterator_ == position:
                return ps_

            # No more constituents to travel
            if ps_.is_primitive():
                raise IndexError

            # ps_ = [X(P) Y(P)], selection must be made
            else:
                # Take Y if labelling takes Y (ignore left specifiers, adjuncts)
                if ps_.head() == ps_.right_const.head():
                     ps_ = ps_.right_const
                # Labelling picks X in [X Y]
                else:
                    # If X is complex, pick it
                    if ps_.left_const.is_complex():
                        ps_ = ps_.left_const
                    else:
                        # If X is primitive, take Y if it is not adjunct
                        if ps_.right_const.adjunct:
                            ps_ = ps_.left_const
                        # If y is primitive and Y is selected sister, continue with Y
                        else:
                            ps_ = ps_.right_const

            iterator_ = iterator_ + 1

    # Copies a constituent and does all other operations required for reconstruction
    def copy_from_memory_buffer(self, babtize='1'):

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

        # Copy
        self_copy = self.copy()              # Copy the constituent
        self_copy.find_me_elsewhere = False  # Copy is marked for being where it is
        self_copy.silence_phonologically()   # Silence the new constituent phonologically
        self.find_me_elsewhere = True        # Mark that the constituent has been copied
                                             # Neutralize the original
        remove_tail_features(self)           # Remove tail-features from the original

        return self_copy

    # Counts the number of (in situ non-adjunct) specifiers
    def count_specifiers(self):
        ps_ = self.mother
        count = 0
        # ---------------- while loop begins ----------------------#
        while ps_ and ps_.sister() and \
                (ps_.sister().is_left() and \
                not ps_.sister().is_primitive()) and \
                not ps_.sister().find_me_elsewhere and \
                not ps_.sister().adjunct:
            count = count + 1
            ps_ = ps_.walk_upstream()
        # ---------------- while loop ends --------------------------#
        return count

    def container_head(self):
        if self.mother:
            return self.mother.head()
        else:
            return self.head()

    # Definition for phi-feature conflict
    # Element H involves a phi-feature conflict if and only if
    # Condition 1. H has two phi-features with the same type but different value
    def phi_conflict(self):
        for f in self.features:
            if f[:4] == 'PHI:' and f[-1] != '_':  # Check only valued phi-features
                for g in self.features:
                    if g[:4] == 'PHI:' and g[-1] != '_':  # Check only valued phi-features
                        f_type = f.split(':')[1]
                        g_type = g.split(':')[1]
                        f_value = f.split(':')[2]
                        g_value = g.split(':')[2]
                        # If there is a feature type T with two difference values, we have feature conflict
                        if f_type == g_type and f_value != g_value:
                            return True
        return False

    # Definition for LF-legibility
    def LF_legibility_test(self):

        def detached(ps):
            ps.mother = None
            return ps

        lf = LF()
        lf.test(detached(self.copy()))
        return lf

    # Separate phrase structure from its host and return the mother (for later reattachment)
    def detach(self):

        if self.mother:
            original_mother = self.mother
            self.mother = None
        else:
            original_mother = None

        return original_mother

    # Definition for finiteness (trivial)
    def is_finite(self):
        head = self.head()
        if 'FIN' in head.features:
            return True
        else:
            return False

    # Definition of features that are used at LF-interface (only obligatory selection counts)
    def for_LF_interface(self, features):
        set_of_features = set()
        for f in features:
            if f[0] == '!' or f[0] == '-':
                set_of_features.add(f)
        return set_of_features

    # Definition for selection match, i.e. whether self (label) selects for head (label)
    # This duplicates functionality in the LF class, all this must be unified
    def selects(self, selectee):
        selector = self
        if selector.has_affix():
            selector = selector.get_bottom_affix()

        # Search positive selection feature
        if selectee.features & selector.get_comps():
            return True
        else:
            return False

    # Recursive definition for phonological silencing
    def silence_phonologically(self):

        # Add feature [null]
        if not self.features:
            self.features = {'null'}
        else:
            self.features.add('null')

        # Silence also constituents
        if self.left_const:
            self.left_const.silence_phonologically()
        if self.right_const:
            self.right_const.silence_phonologically()

    #
    #
    # Block 6. Support functions
    #
    #
    def get_valued_phi_set(self):

        phi_set = set()

        if self.is_complex():
            if self.left_const:
                phi_set = self.left_const.get_valued_phi_set()
            if self.right_const:
                phi_set = phi_set | self.right_const.get_valued_phi_set()
        else:
            if 'PHI:NUM:SG' in self.features and 'PHI:PER:1' in self.features:
                phi_set.add(f'{self}.1sg')
            elif 'PHI:NUM:SG' in self.features and 'PHI:PER:2' in self.features:
                phi_set.add(f'{self}.2sg')
            elif 'PHI:NUM:SG' in self.features and 'PHI:PER:3' in self.features:
                phi_set.add(f'{self}.3sg')
            elif 'PHI:NUM:PL' in self.features and 'PHI:PER:1' in self.features:
                phi_set.add(f'{self}.1pl')
            elif 'PHI:NUM:PL' in self.features and 'PHI:PER:2' in self.features:
                phi_set.add(f'{self}.2pl')
            elif 'PHI:NUM:PL' in self.features and 'PHI:PER:3' in self.features:
                phi_set.add(f'{self}.3pl')

        if 'PHI:DET:GEN' in self.features:
            phi_set.add(f'{self}.generic')

        return phi_set

    def show_affix(self):
        i = ''
        if self.is_primitive() and self.right_const:
            i = self.right_const.get_cats_string()
            if self.right_const.right_const:
                i = i + ',' + self.right_const.show_affix()
        else:
            i = ''
        return i

    def show_primitive_constituents(self):
        reply = ''
        if not self.is_primitive():
            reply += self.left_const.show_primitive_constituents()
            reply += self.right_const.show_primitive_constituents()
        else:
            reply += f'{self.get_pf():<10} {sorted(self.features)}\n'
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
            pf = pf + self.get_lf()

        return pf

    def show_all_vectors(self):
        if not self.is_primitive():
            return self.left_const.show_all_vectors() + self.right_const.show_all_vectors()
        return f'{self}: {self.feature_vector()};  '

    # This function tries to create "informative" representation of the categories of the constituent ps
    def get_cats_string(self):
        major_cats = ''.join(sorted([feature for feature in self.head().features if feature in major_category]))
        if major_cats == 'Neg/fin':
            major_cats = 'Neg'
        if self.is_complex():
            suffix = 'P'
        else:
            suffix = ''
        if not major_cats:
            major_cats = 'X'
        return major_cats + suffix

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
                return '<__>' + index_str       # Adjuncts are represented as <,>
            else:
                return '__' + index_str
                # return '(' + self.get_cats_string() + ')' + index_str   # Regular constituents as [,]

        if self.is_primitive():
            if not self.get_pf():
                return '?'
            else:
                if self.adjunct:
                    return '<'+self.get_pf()+'>'
                else:
                    if self.extract_pro():
                        return self.get_pf()
                        # return self.get_pro_type() + '.' + self.get_pf()
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
            return '\N{GREEK CAPITAL LETTER PHI}'
        if 'PHI:NUM:_' not in self.features and 'PHI:PER:_' not in self.features and 'PHI:DET:_' in self.features:
            return '\N{GREEK SMALL LETTER PHI}/x'
        return '\N{GREEK SMALL LETTER PHI}'

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
            id_part = f'{self.head().get_pf()}:{self.identity}'
        else:
            id_part = self.head().get_pf()
        return f'{opener}.{id_part} {self.left_const.simple_tree()} {self.right_const.simple_tree()}{closer}'

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
            self.top().rebaptize(self.identity, str(counter))
            counter = counter + 1
        if self.left_const:
            counter = self.left_const.tidy_names(counter)
        if self.right_const:
            counter = self.right_const.tidy_names(counter)
        return counter