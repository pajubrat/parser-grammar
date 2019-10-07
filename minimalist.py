# This modular and class defines basic linguistic competence, i.e. phrase structures and operations on phrase structure
from support import log
from LF import LF

major_category = {'N', 'Neg/fin', 'P', 'D', 'C/fin', 'T/fin', 'iWH', 'iR', 'A', 'v', 'V', 'ADV', 'Q', 'NUM', 'T', 'INF'}

# Class phrase structure
class PhraseStructure:

    # Constituent constructor, Merge[A B]
    def __init__(self, left_constituent=None, right_constituent=None):

        # Merge(A,B)
        self.left_const = left_constituent
        self.right_const = right_constituent
        if self.left_const:
            self.left_const.mother = self
        if self.right_const:
            self.right_const.mother = self
        self.mother = None

        # Default feature set
        self.features = set()   # Feature set
        self.morphology = ''
        self.internal = False   # Tells if the constituent is word-internal
        self.adjunct = False    # Marks the constituent as an adjunct

        # This tells if the constituent has been re-merged into another position
        # When False, the constituent should in its canonical first-Merge position
        # This feature will be replaced in a fully modular architecture
        self.find_me_elsewhere = False

        # This name is used to identify chains for output, it has not other function
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

    # Returns the index of 'site' inside 'self'
    # The index 0 = top note
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

        new_ps = None               # The resulting new complex constituent
        left = False
        right = False

        if self.mother:             # Determines whether 'self' is left or right
            if self.is_left():
                left = True
            else:
                right = True

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

    # Defines the multiplication operation which merges a head inside another head
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

    # Reductive definition for EPP
    def EPP(self):
        for f in self.features:
            if f == 'SPEC:*' or f == '!SPEC:*':
                return True
        return False

    # Copies a constituent and does all other operations required for reconstruction
    def transfer(self, babtize='1'):

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
        remove_tail_features(self)         # Remove tail-features from the original

        return self_copy

    # Removes an element from the phrase structure
    def remove(self):
        mother = self.mother
        sister = self.geometrical_sister()
        grandparent = self.mother.mother

        # Sealing the leftover hole
        sister.mother = sister.mother.mother
        if mother.is_right():
            grandparent.right_const = sister
            self.mother = None
        elif mother.is_left():
            grandparent.left_const = sister
            self.mother = None

    # Return a list of affixes inside a grammatical head
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

    # Returns the phrase structure containing 'self'
    def get_top(self):
        result = self
        while result.mother:
            result = result.mother
        return result

    # Labeling (this is redundant but is here for readability)
    def get_labels(self):
        return self.get_head().get_cats()

    # Recursive definition for head (also label) of a phrase structure
    def get_head(self):

        if self.is_primitive():
            return self

        # Case 1. [H XP] returns H
        if not self.is_primitive():
            if self.left_const.is_primitive():
                return self.left_const

        # Case2. {XP H] returns H
        if not self.is_primitive():
            if self.right_const.is_primitive():
                return self.right_const

        # Case 3. [XP, YP] = look into YP if it is not an adjunct, otherwise look into XP
        if not self.is_primitive():
            if not self.left_const.is_primitive() and not self.right_const.is_primitive():
                if self.right_const.adjunct:
                    return self.left_const.get_head()
                return self.right_const.get_head()

    # Returns a set of unvalued phi-features
    def get_unvalued_features(self):
        unvalued_phi_set = set()
        for f in self.features:
            if f[:4] == 'PHI:' and f[-1] == '_':
                unvalued_phi_set.add(f)
        return unvalued_phi_set

    # Definition for the relation of SISTER
    # [Y <X>], <X> has no sister
    # [X <Y>], X has no sister, looks mother next
    # [X Y], [Y, X], both sisters to each other
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

    # Definition for the relation of LOCAL SPECIFIER
    # (Should be simplified, unified)
    def get_local_specifier(self):

        # Case 1. Definition for SPEC for a primitive left head
        if self.is_primitive() and \
                self.is_left() and \
                self.mother.sister() and \
                not self.mother.adjunct and \
                self.mother.sister().is_left() and \
                not self.mother.sister().is_primitive():
            # Checks that the head projects, not the left branch (in which case the head is inside right adjunct)
            if self.mother.mother.get_head() == self.get_head():
                return self.mother.sister()

        # Case 2. Definition for SPEC for a primitive right head
        elif self.is_primitive() and self.is_right() and self.sister() and not self.sister().is_primitive():
            return self.sister()

        # Case 3. Definition for pro-specifier (if no phrasal specifier exists)
        else:
            if self.extract_pro():
                return self.extract_pro()
            else:
                return None

    # Counts the number of specifiers
    # (Is used when reconstructing elements, will be eliminated)
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

    # Returns a list of c-commanding complex left phrases up to the next head
    # (Is used only when creating adjuncts, this must be replaced and/or reduced)
    def get_generalized_specifiers(self):
        if not self.is_primitive():
            return None

        if self.is_right():
            ps_ = self
        else:
            ps_ = self.mother

        # Specifiers will be collected into this list
        list = []

        while ps_ and ps_.sister() and (ps_.sister().is_left() and not ps_.sister().is_primitive()):
            list.append(ps_.sister())
            ps_ = ps_.walk_upstream()

        if not list:
            if self.extract_pro():
                list.append(self.extract_pro())

        return list

    # Definition for phi-feature conflict
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

    # This extracts a pro-element from a primitive head
    def extract_pro(self):
        phi_set = set()

        # Only phi-active head can contain a pro-element
        if 'ARG' in self.features:
            # Collect phi-features
            for f in self.features:
                if f[:4] == 'PHI:':
                    phi_set.add(f)
            # Construct a pronominal phi-set
            if phi_set:
                # Assumption 1. Pro-element is a constituent
                pro = PhraseStructure()

                # Assumption 2. Pro-element has the phi-features from the host
                pro.features = pro.features | phi_set

                # Assumption 3. Pro-element has label D
                pro.features.add('CAT:D')

                # Assumption 4. Pro-element is printed out as 'pro'
                pro.features.add('PF:pro')

                # Assumption 5. Pro-element is phonologically covert
                pro.silence_phonologically()

                # Assumption 6. Pro-element is a copy
                pro.find_me_elsewhere = True

                # Assumption 7. Pro-element can be created only from a consistent phi-set
                if not pro.phi_conflict():
                    return pro
            return None

    # Definition for complement
    def complement(self):
        # A complement is a right sister (notice that there is a separate definition for sister())
        if self.sister() and self.sister().is_right():
            return self.sister()
        return None

    # Definition for geometrical sister
    def geometrical_sister(self):
        if self.mother:
            if self.is_left():
                return self.mother.right_const
            if self.is_right():
                return self.mother.left_const
        return None

    # Definition for selector
    def get_selector(self):
        # Get the feature vector
        feature_vector = self.get_feature_vector()
        # If there are no c-commanding heads, we return no selector
        if len(feature_vector) == 1:
            return None
        else:
            # Return the local c-commanding head
            return feature_vector[1]

    # Definition of LEFT
    def is_left(self):
        if self.mother and self.mother.left_const == self:
            return True
        else:
            return False

    # Definition of RIGHT
    def is_right(self):
        if self.mother and self.mother.right_const == self:
            return True
        else:
            return False

    # Definition of PRIMITIVE
    def is_primitive(self):
        if self.right_const and self.left_const:
            return False

        else:
            return True

    # Definition for affix
    # (Used in connection with complex heads and head movement reconstruction)
    def has_affix(self):
        if self.right_const and not self.left_const:
            return True
        else:
            return False

    # Definition for the concept of word internal
    def is_word_internal(self):
        return self.internal

    # Definition for adjoinable phrase
    def is_adjoinable(self):
        adjoinable_categories = {'ADV', 'R', 'D', 'P', 'TO/inf'}

        # Adjuncts are automatically adjoinable
        if self.adjunct:
            return True

        # A constituent with adjoinable label is adjoinable
        if adjoinable_categories.intersection(self.get_labels()):
            return True
        else:
            return False

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

    # Transforms a constituent into an adjunct
    # The nontrivial part is how much surrounding structure to eat inside the adjunct
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
                if '!SPEC:*' in head.features and head.mother.mother and self.get_generalized_specifiers():
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
                if self.get_generalized_specifiers() and not '-SPEC:*' in head.features and \
                        not set(head.get_not_specs()).intersection(set(self.get_generalized_specifiers()[0].get_labels())) and \
                        not self.get_generalized_specifiers()[0].is_primitive():
                    if head.mother.mother:
                        log(f'{head}: {head.get_generalized_specifiers()}')
                        make_adjunct(head.mother.mother)
                    return self.mother.mother
                else:
                    # Do not eat a primitive selector
                    if head.get_selector() and not head.get_selector().is_primitive():
                        make_adjunct(head.mother)
                    else:
                        make_adjunct(head)
                    return self.mother
        else:
            make_adjunct(self)

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

    # Probe-goal function
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
                if ps_.left_const.get_head().features and goal_feature in ps_.left_const.get_head().features:
                    return ps_.left_const

                # Check left constituent for a criterial feature
                elif goal_feature[:4] == 'TAIL' and goal_feature[5:] in ps_.left_const.get_criterial_features():
                    return ps_.left_const

                # Walk downstream
                else:
                    # Intervention breaks the search (this has not been studied in detail)
                    if ps_.left_const.is_primitive() and ps_.left_const.features and probe_label.issubset(ps_.left_const.features):
                        return None
                    else:
                        ps_ = ps_.walk_downstream()

    # Definition for the notion of feature vector (Salo, 2003)
    def get_feature_vector(self):
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

            # We don't use upstream walk function because we don't want to ignore adjuncts
            if _ps_iterator.mother:
                _ps_iterator = _ps_iterator.mother
            else:
                _ps_iterator = None

        return feature_vector

    # Definition for finiteness (trivial)
    def is_finite(self):
        head = self.get_head()
        if 'CAT:FIN' in head.features:
            return True
        else:
            return False

    # Definition for the external tail head test
    def external_tail_head_test(self):
        def get_max(ps):
            ps_ = ps
            while ps_.mother and ps_.mother.get_head() == self.get_head():
                if ps_.mother:
                    ps_ = ps_.walk_upstream()
                else:
                    break
            return ps_

        # --- Main function begins here ---#

        # Each tail head condition is based on a set, here we collect them all first into a set of sets
        tail_sets = self.get_tail_sets()
        if not tail_sets:
            return True

        feature_vector = self.get_feature_vector()

        for tail_set in tail_sets:

            # Condition i.
            # First check if the constituent is already inside the checking projection (Spec-Head checking)
            if get_max(self) and get_max(self).mother and get_max(self).mother.get_head().check_features(tail_set):
                if self.mysterious_property():
                    return True

            # Condition ii.
            # Check if goal's tail features can be matched in the feature vector
            # Comment: In the current system, adverbs cannot satisfy ii.
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

            # External tail head test returns false if the tail-head features cannot be matched
            return False

    # This involves empirical issues that I don't fully understand
    def mysterious_property(self):
        if 'CAT:D' in self.features and not 'TAIL:CAT:INF,A/HEAD' in self.features:
            return False
        else:
            return True

    # Definition for the well-formed phi-set
    def get_phi_set(self):
        head_ = self.get_head()
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
        constituent_ = self.get_head()

        for f in constituent_.features:
            if f[:4] == 'TAIL':
                tail_features.add(frozenset((f[5:].split(','))))

        if tail_features:
            return tail_features
        else:
            return None

    # Definition for internal tail head test
    # Internal tail head test is more lenient than the external version, returns false only if there is partial match
    def internal_tail_head_test(self):

        # Collect all tail head sets for testing
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

        # If there there were no overlapping features, this test is accepted
        return True

    # Definition of bottom node
    def get_bottom(self):
        ps_ = self

        while not ps_.is_primitive():
            ps_ = ps_.right_const

        return ps_

    # Recusrive definition for criterial features (type ABAR:_) inside phrase
    def get_criterial_features(self):
        set_ = set()

        # Condition 1. Left branch is searched if it has not been moved
        if self.left_const and not self.left_const.find_me_elsewhere:
            set_ = set_.union(self.left_const.get_criterial_features())

        # Condition 2. Right branch is searched if it is not adjunct and its label is not T/fin
        if self.right_const and not self.right_const.adjunct and not 'T/fin' in self.right_const.get_labels():
            set_ = set_.union(self.right_const.get_criterial_features())

        # Condition 3. Primitive constituents are examined for criterial features
        if self.is_primitive():
            for f in self.features:
                if f[:5] == 'ABAR:':
                    set_.add(f[5:])
        return set_

    # Definition for feature check: can head H check all features in 'feature_set'
    def check_features(self, feature_set):
        return (feature_set & self.features) == feature_set

    # Recursive definition for contains-feature-F for a phrase
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

    # Definition for walking downwards (search) on the right edge
    def walk_downstream(self):

        if self.is_primitive():
            return None

        # Dodge right adjuncts
        if self.left_const.is_primitive():
            if not self.right_const.adjunct:
                return self.right_const
            else:
                return self.left_const

        # [XP YP]: follow selection
        # Condition 1. Check right branch
        if self.get_head() == self.right_const.get_head():
            return self.right_const

        # Condition 2. Check left branch
        if self.get_head() == self.left_const.get_head():
            return self.left_const

        return None

    # Definition for geometrical upstream walk (trivial)
    def walk_upstream_geometrically(self):

        if self.mother:
            return self.mother
        else:
            return None

    # Definition for upstream walk
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

    # Definition for phase (controversial)
    def is_phase(self):
        if 'CAT:v' in self.features or 'CAT:C' in self.features or 'CAT:FORCE' in self.features or 'CAT:COPULA' in self.features:
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

    # Definition for label
    def get_cats(self):
        return {f[4:] for f in self.features if f[:3] == 'CAT'}

    # Definition for positive specifier selection
    def get_specs(self):
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

    # Definition of features that are used at LF-interface (only obligatory selection counts)
    def for_LF_interface(self, features):
        set_of_features = set()
        for f in features:
            if f[0] == '!' or f[0] == '-':
                set_of_features.add(f)
        return set_of_features

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

