# This modular and class defines basic linguistic competence, i.e. phrase structures and operations on phrase structure
from support import log
from LF import LF

major_category = {'N', 'Neg/fin', 'P', 'D', 'C/fin', 'T/fin', 'iWH', 'iR', 'A', 'v', 'V', 'ADV', 'Q', 'NUM', 'T'}

class PhraseStructure:

    # Constituent constructor
    def __init__(self, left_constituent=None, right_constituent=None):
        """"
        Creates a new constituent by Merge or by out of the blue generation

        A new complex constituent is created by Merge(A, B) = [A,B].
        If no constituents are given, an empty primitive constituent is generated.
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

        This operation merges a constituent into an existing phrase structure. It uses the primitive Merge
        function (__init__) but is able to merge items (countercyclically) inside the phrase structure, as
        required by the Phillips architecture. It is also used by operations implementing Move and its
        reverse version drop.
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

        This provides a reductive definition for Chomsky's (2000) generalized EPP as it is realized in the
        present theory: it is a combination of three things:

        i) SPEC:* feature,
        ii) !SPEC:* feature,
        iii) +PHI marking.

        The relevance of (iii) is currently open.
        """

        for f in self.features:
            if f == 'SPEC:*' or f == '!SPEC:*' or f == '+PHI':
                return True
        return False

    # This function copies a constituent and does all other operations required for dropping
    # Babtize will be the name (index) given to the original and its copy,
    # and is used for chain identification in output only
    def transfer(self, babtize='1'):
        """
        Prepares an altered copy of a phrase for internal merge

        Transfer prepares an altered copy a constituent for the purposes of copying it into another location.
        The operation relies on a more primitive operation Copy. The following alterations are made to the original constituent:

        i) the original is silenced phonologically, which is determined by a dedicated feature,
        ii) the original is tagged as being copied, so that it will be excluded from certain later operations,
        iii) tail features are removed from the original.

        (i) is applies more generally, to null pronouns/elliptic structures for example. It seems that language
        allows constituents, both simple and complex, to be marked as "irrelevant for PF".
        (ii-iii) could be reduce to one feature if tail features are always ignored for moved constituents.
        In this version they are kept separate.
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
        self_copy.silence_phonologically()  # Silence the new constituent phonologically
        self.find_me_elsewhere = True       # Mark that the constituent has been copied

        # neutralize the original
        remove_tail_features(self)         # Remove tail-features from the original

        return self_copy

    # Removes an element from the phrase structure
    def remove(self):
        """
        Removes a constituent countercyclically from the phrase structure.

        The constituent is removed from the phrase structure, and the leftover hole is repaired. The operation
        is triggered when the parser tries various merge solutions and determines that they did not work, hence it
        must cancel the merge operation. An alternative is to use non-tampering operation for testing the legibility
        of outputs, but this seems simpler and more intuitive way. It is also clear that the parser has the ability
        to remove constituents.
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

        The operation finds the head of the phrase and returns its labels.
        """
        return self.get_head().get_cats()

    # Labeling algorithm
    # Looks for the closest primitive head, ignores right adjuncts
    def get_head(self):
        """
        Returns the head of a phrase (critical part of the labeling algorithm).

        The following head selection algorithm is used:
        i) The head of a primitive constituent is the constituent itself,
        ii) if the phrase is complex, but contains primitive constituents (one or two),
        the head is one of these primitive constituents so that left head is prioritized over right head,
        iii) if both constituents are complex, then they are searched recursively for heads,
        so that right constituent is prioritized over left, unless the right-constituent is an adjunct and not
        searched at all.

        The following properties are noteworthy of this solution. Because merge is asymmetric, we can use
        this asymmetry in labeling. This makes the asymmetry extremely important. It is a fundamental assumption
        underlying this theory. The asymmetry is used in an intuitively clear way. The algorithm first looks for
        primitive heads by going from left to right, and if nothing is found, it examines complex phrases and
        sweeps back from right to left.
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

    # Returns the sister of the constituent X, right adjuncts are invisible
    # [Y <X>], <X> has no sister
    # [X <Y>], X has no sister, looks mother next
    # [X Y], [Y, X], both sisters to each other
    def sister(self):
        """
        Finds and returns the (first non-right adjunct) sister of a constituent in a phrase structure.

        The operation uses the following principles:
        i) if the constituent is a right-adjunct itself, it has no sister (returns None)
        ii) if the constituent is merged with a right adjunct, it tries to find a sister of the mother (recursively).
        iii) if there are no right adjuncts, the sister is returned.

        The operation therefore looks the phrase structure as if all right-adjuncts were invisible. It is assumed that
        right-adjuncts are located in a separate working space ("syntactic dimension"). This property means that
        this sister relation should be used in connection with selection.
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

        Only primitive heads H can have specifiers. The intuition we pursue here is that specifiers are
        non-projecting complex phrases to the left of the head. Thus, we have two cases:
        i) If we have [XP H], then XP is the SPEC of H, i.e. its left complex phrase,
        ii) If we have [H X(P)], then the SPEC of H is the complex left sister of [H X(P)], i.e. YP in [YP [H X(P)]], and
        H must project, so that label(H) = label([YP [H XP]]). The latter condition is relevant e.g. if H happens to
        be inside a right adjunct [YP <H XP>].

        As a consequence, right head has no specifier if its sister is a head too, i.e in [X, H], H has no SPEC,
        instead H is the complement of X.

        In configuration [XP H], XP will be both COMP (sister) and SPEC of H, so the case is ambiguous.
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
        else:
            return None

    def count_specifiers(self):

        ps_ = self.mother
        count = 0

        while ps_ and ps_.sister() and (ps_.sister().is_left() and not ps_.sister().is_primitive()):
            count = count + 1
            ps_ = ps_.walk_upstream()
        return count






    # Returns the complement of head ('self') if available, otherwise returns None
    # Complement = right sister
    def complement(self):
        """
        Returns the complement of a head.

        Complement is defined as the sister of the head, and sister is defined so that it ignores
        right adjuncts. See the sister() function. The idea is that most selection relations
        follow the contours of the sister relation.
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

        In [X(P), Y(P)], XP is the geometrical sister of YP, and YP is the geometrical sister of XP.
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

        Adjoinable categories have several properties that non-adjoinable categories do not have. This function
        forces the distinction enumeratively, because the underlying reason for the property is still unclear. Currently,
        adjoinable categories are adverb, relative clause, determiner and preposition (adposition). Adjectives will be
        added later. The distinction has to do with LF, in that these categories (and only these) are interpretable
        at LF as adjuncts via the tail-head relation.
        """

        adjoinable_categories = {'ADV', 'R', 'D', 'P'}
        if self.adjunct:
            return True
        if adjoinable_categories.intersection(self.get_labels()):
            return True
        else:
            return False

    def copy(self):
        """
        Copies a constituent and returns the newly created copy.

        This creates an identical token of a constituent. All features and constituents are copied, and the
        function is applied recursively if the constituents are itself complex.
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

    def LF_legibility_test(self):
        """
        Checks if the phrase structure, as a detached item, is interpretable at the LF-level

        The construction is send off to LF interface (a separate class/object) for checking. The function that
        performs checking is lf.test(), lf being an object of the class LF().
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

        If an operation wants to examine a constituent in isolation from its context, then it can be detached from
        the phrase structure (often temporarily). There are several operations of this type. The reason for their
        existence is that often we want to limit the applicability of an operation to certain node so that higher
        nodes are examined, for example, when we drop constituents inside left branches. We don't want to let them
        move outside of the left branch, so we detach the phrase structure before the operation is applied.
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

        Probe-goal operation checks that a feature (goal_feature) can be found from within probe's sister,
        i.e. c-command domain. The element carrying the feature is called "goal". The operation descends the right edge of
        the phrase structure and examines each left constituent (complex or primitive) for the existence
        of the relevant feature, and returns the containing constituent if match is found.

        Criterial features are searched from the whole left constituent whereas all other features are only looked
        from the head only. The former search is deeper than the latter. It is not clear at present if this feature
        is truly essential.

        Probing stops if
        i) we have reached the bottom of the phrase structure (at the right edge), or
        ii) we encounter a primitive left head that has a designated probe_label feature which is normally the probe's
        label set. That is, a probe with label C does not look past C, probe with label T does not look past another T.
        This is based on the relativized minimality system of Rizzi (1990).

        The probe-goal operation is called if a head has feature [PROBE:F], where F is the goal feature. In
        the standard minimalist theory, F would be an uninterpretable feature. A more general interpretation is used here.
        It is possible for a lexical head to use this feature to check for the existence of a non-local feature/label,
        for example, that T/fin exists in the C-command domain of C/fin. This is required because in Finnish Neg can occur
        between them. Here, then, the probe-goal is equivalent to "nonlocal selection". These checks are performed
        at the LF-interface. Intuitively: [probe:F, XP] = make sure that feature/label F is inside XP.

        The operation is not currently used in the Chomsky's sense, to match uninterpretable features with
        interpretable ones. This is due to the fact that agreement is not fully implemented, and because the notion of
        uninterpretable feature is not defined (it will be later when binding is included).
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

        Feature vector is an ordered list of c-commanding primitive constituents,
        beginning from the original constituent itself, such that the order follows their locality. The notion
        comes from Salo (2004). Under the current implementation, the vector contains the primitive heads themselves,
        not just their labels. The operation is called during the tail-head tests. This connects it also with
        morphosyntax (structural case), as assumed in the original source. The relation is independently needed
        in order to account for the Finnish long-distance Case assignment.
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

            # Here we don't use upstream walk because we don't wanto to ignore adjuncts
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

        Finiteness will be assumed to originate from an independent feature [finite], but in this implementation
        it is part of certain labels, such as T/fin, C/fin and also FORCE. The single-feature theory is not used
        here because some of the empirical details are still unclear.
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

        The external tail-head test checks that a constituent can be "linked" with an appropriate head at LF.
        If it cannot be, this operation returns false and crashes.

        If H has no tail features, then the test is vacuous and the operations returns true. If it has
        tail features, then the operation returns true if and only if the features are matched. That is, unchecked
        tail features results in a crash. Tail features of H are matched if either i) or ii):

        i) The tail features are found from the head X whose projection contains HP, and HP is not DP (see * below),
        ii) The tail features are found from a (c-commanding) head X that is in H's feature vector.

        Search is terminated if and only if the feature vector is exhausted or if there is partial feature match;
        both will lead into crash.

        Condition i) means that HP must be inside a projection from head X that has the relevant features. For example,
        VP-adverbs can be inside the VP in this sense. The tail-feature is [TAIL:CAT:V]. It can be adjunct, spec or
        comp. Condition ii) means that the critical feature is found by using feature vectors/c-command. Both i-ii
        are understood as requirements that are interpreted at LF, by a semantic mechanisms, so they are
        checked by the parser. The semantic mechanism "links" the phrase to a head.

        DP is excluded from mechanism (i). This is because the grammatical subject must occur at Spec,VP to link with
        T/fin and not Spec,T/Fin, which would be possible by (i). The reason is because Spec,vP is the position in which
        it will be associated its thematic role at LF. Adverbials are allowed under (i) in addition to (ii). What this
        means is that arguments and adjuncts do not behave identically with respect to tailing. This is a flaw in the
        current theory (Brattico 2016, 2018) which assumes that they should.
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
                if self.mysterious_property(): # This matter involves things that I don't understand
                    return True

            # Condition ii)
            # Check if goal's tail features can be matched in the feature vector
            for const in feature_vector:
                # Ignore the first element which is the goal itself
                if const is not self:
                    # If ALL goal's features are matched, the test is accepted
                    if const.check_features(tail_set):
                        return True
                    # If there is PARTIAL match, it is left unchecked
                    elif tail_set & const.features:
                        return False

            return False

    def mysterious_property(self):
        if 'CAT:D' in self.features and 'TAIL:PHI:0,A/HEAD' not in self.features:
            return False
        else:
            return True

    # Not needed yet, but added this for future (if it will be needed)
    def phi_feature_match(self, ps):

        phi_list_1 = [str(item).split(':') for item in list(self.get_head().get_phi_set())]
        phi_list_2 = [str(item).split(':') for item in list(ps.get_head().get_phi_set())]

        for (type1, value1) in phi_list_1:
            for (type2,value2) in phi_list_2:
                if type1 == type2 and not value1 == value2:
                    return False

        return True

    def get_phi_set(self):

        # NUM = number: sg, pl
        # PER = person: 1, 2, 3
        # GEN = gender: m, f, n
        # SEN = Sentiency: human, nonhuman, inanimate
        # HON = Honority: honorofic, nonhonorific
        phi_labels = {'NUM', 'PER', 'GEN', 'SEN', 'HON'}

        phi_feature_set = set()
        constituent_ = self.get_head()

        for f in constituent_.features:
            if f[:3] in phi_labels:
                phi_feature_set.add(str(f))

        return phi_feature_set

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

        Internal tail-head test checks that a constituent H is not c-commanded by a head X that is not allowed in
        virtue of its tail-features (e.g. *towards he). It uses feature vectors (Salo, 2004) for the purposes of finding
        possible violations. This operation returns true if there are no violations: it does not require that a link
        exists between a tail feature and its head. It only detects the existence of wrong combinations.
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

        The operation searches the constituent recursively, ignoring right adjuncts, and adds all criterial
        features to a set and returns the set. Criterial features are of the type [ABAR:F], F being the feature
        and ABAR designating it as criterial. It is a simple scanning function.
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

        Searches for feature F recursively from within a constituent, and returns true is found. False otherwise.
        Features are checked only from primitive heads.
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

        This function walks downward on the right edge, one constituent at a time. "Right edge" refers to
        the sequence of right constituents (excluding right adjuncts). Right edge plays a fundamental role in
        the Phillips-style parser/grammar, because new constituents are merged to the right edge.
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

    # Walk upstream and ignore right-adjuncts
    def walk_upstream(self):
        """
        Returns the next constituent at the right edge in upward direction.

        Right edge refers to the chain of right constituents, given some starting point, but ignoring right
        adjuncts. A left constituent cannot be part of a right edge made up of higher nodes, only lower nodes.
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

    def get_comps(self):
        set_ = set()
        for f in self.features:
            if f[:4] == 'COMP':
                set_.add(f[5:])
            if f[:5] == '!COMP':
                set_.add(f[6:])
        return set_

    def get_not_comps(self):
        set_ = set()
        for f in self.features:
            if f[:5] == '-COMP':
                set_.add(f[6:])
        return set_

    # Return the set of POS categories
    def get_cats(self):
        set_ = set()
        if self.features:
            for f in self.features:
                if f[:3] == 'CAT':
                    set_.add(f[4:])
        return set_

    def get_specs(self):
        set_ = set()
        for f in self.features:
            if f[:4] == 'SPEC':
                set_.add(f[5:])
            if f[:5] == '!SPEC':
                set_.add(f[6:])
        return set_

    def get_not_specs(self):
        set_ = set()
        for f in self.features:
            if f[:5] == '-SPEC':
                set_.add(f[6:])
        return set_

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

        Constituents can be silenced phonologically for several reasons and/or ways. Here they are all captured by
        assuming that constituents can be marked directly as phonologically invisible. This concerns copies, null
        pronouns, elliptic structures, null objects, and such. Phonologically null elements are visible at LF.
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
                    return self.get_pf()
        else:
            if self.adjunct:
                return f'<{self.left_const} {self.right_const}>' + index_str
            else:
                return f'[{self.left_const} {self.right_const}]' + index_str

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

