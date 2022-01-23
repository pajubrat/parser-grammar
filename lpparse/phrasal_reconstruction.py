from support import log
from lexical_interface import LexicalInterface
from adjunct_constructor import AdjunctConstructor

class PhrasalMovement:
    def __init__(self, controlling_parser_process):
        self.brain_model = controlling_parser_process
        self.brain_model.name_provider_index = 1
        self.brain_model.syntactic_working_memory = []
        self.context = controlling_parser_process
        self.lexical_access = LexicalInterface(self.brain_model)
        self.lexical_access.load_lexicon(self.brain_model)
        self.adjunct_constructor = AdjunctConstructor(self.brain_model)

    def reconstruct(self, ps):
        self.brain_model.syntactic_working_memory = []
        # ------------------------------ minimal search -----------------------------------------------#
        for node in ps.minimal_search():
            if self.get_local_head(node) and self.get_local_head(node).EPP():
                self.pull_into_working_memory(self.get_local_head(node))
            if self.get_local_head(node):
                self.brain_model.LF.try_LFmerge(self.get_local_head(node))
            if self.intervention(node):
                break
        # ---------------------------------------------------------------------------------------------#

    def intervention(self, node):
        if node.left_const and \
                node.left_const.is_primitive() and \
                'φ' in node.left_const.features and \
                self.brain_model.syntactic_working_memory:
                    return True

    def pull_into_working_memory(self, head):
        for i, spec in enumerate([const for const in head.working_memory_edge()]):
            if not spec.find_me_elsewhere:
                if self.Abar_movable(spec, head):
                    self.brain_model.syntactic_working_memory = self.brain_model.syntactic_working_memory + [spec]
                else:
                    self.A_reconstruct(spec)
                self.process_criterial_features(i, spec, head)

    def process_criterial_features(self, i, spec, head):
        def consider_externalization(head):
            if head.get_tail_sets():
                self.adjunct_constructor.externalize_structure(head)

        if i == 0:
            if not spec.find_me_elsewhere and self.brain_model.narrow_semantics.operator_variable_module.scan_criterial_features(spec):
                head.features |= self.get_features_for_criterial_head(spec, head)
                consider_externalization(head)
        else:
            if self.specifier_phrase_must_have_supporting_head(spec, head):
                new_h = self.engineer_head_from_specifier(head, spec)
                spec.sister().merge_1(new_h, 'left')
                consider_externalization(new_h)

    def engineer_head_from_specifier(self, head, spec):
        log(f'New head was spawned at {head.get_cats_string()}P...')
        new_h = self.lexical_access.PhraseStructure()
        new_h.features |= self.get_features_for_criterial_head(spec, head)
        if 'FIN' in head.features:
            new_h.features |= {'C', 'PF:C'}
        return new_h

    def get_features_for_criterial_head(self, spec, head):
        criterial_features = self.brain_model.narrow_semantics.operator_variable_module.scan_criterial_features(spec)
        if criterial_features:
            feature_set = criterial_features
            feature_set |= {'FIN', 'OP:_'}
            return self.lexical_access.apply_parameters(self.lexical_access.apply_redundancy_rules(feature_set))
        else:
            return {'?'}

    def A_reconstruct(self, spec):
        def candidate_for_A_reconstruction(spec):
            return spec.is_complex() and \
                   spec == spec.container_head().licensed_phrasal_specifier() and \
                   'φ' in spec.head().features and \
                   spec.sister() and \
                   spec.is_left() and \
                   not spec.is_primitive()

        def target_location_for_A_reconstruction(node):
            # Two cases: (a) [XP1 [Y [__1 [Z WP]] or (b) [XP1 X [__1 Y]]]
            return (node.left_const and
                    node.left_const.is_primitive() and
                    node.sister().is_primitive()) or \
                   node.is_primitive()

        def ad_hoc_genitive_filter(node, moved_constituent):
            node.merge_1(moved_constituent, 'left')
            if 'GEN' in moved_constituent.head().features and not moved_constituent.external_tail_head_test():
                value = False
            else:
                value = True
            moved_constituent.remove()
            return value

        if candidate_for_A_reconstruction(spec):
            # Special case: [DP H] => [__ [H DP]]
            if spec.sister().is_primitive():
                spec.sister().merge_1(spec.copy_from_memory_buffer(self.brain_model.babtize()), 'right')
                return

            #-----------------minimal search---------------------------------------------------------------------------#
            for node in spec.sister().minimal_search()[1:]:
                if target_location_for_A_reconstruction(node) and ad_hoc_genitive_filter(node, spec.copy()):
                    node.merge_1(spec.copy_from_memory_buffer(self.brain_model.babtize()), 'left')
                    self.brain_model.consume_resources('A-Move Phrase')
                    self.brain_model.consume_resources('Move Phrase')
                    break
            #-----------------------------------------------------------------------------------------------------------#

    @staticmethod
    def get_local_head(node):
        if node.is_primitive():
            return node
        if node.left_const.is_primitive():
            return node.left_const

    def Abar_movable(self, spec, head):
        if self.brain_model.narrow_semantics.operator_variable_module.scan_criterial_features(spec) or 'A/inf' in spec.head().features:
            return True

    def specifier_phrase_must_have_supporting_head(self, spec, head):
        if spec.is_primitive():
            return False
        if self.brain_model.narrow_semantics.operator_variable_module.scan_criterial_features(spec):
            return True
        if spec.max().adjunct:
            return False
        if spec.max() != spec.max().container_head().licensed_phrasal_specifier():
            return True

    @staticmethod
    def get_phrasal_left_sister(h):
        if h.sister() and not h.sister().is_primitive() and h.sister().is_left():
            return h.sister()