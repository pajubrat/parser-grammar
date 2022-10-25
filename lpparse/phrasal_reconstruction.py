from support import log
from lexical_interface import LexicalInterface
from adjunct_constructor import AdjunctConstructor
from A_reconstruction import A_reconstruction


class PhrasalMovement:
    def __init__(self, controlling_parser_process):
        self.brain_model = controlling_parser_process
        self.brain_model.name_provider_index = 1
        self.brain_model.syntactic_working_memory = []
        self.lexical_access = LexicalInterface(self.brain_model)
        self.lexical_access.load_lexicon(self.brain_model)
        self.adjunct_constructor = AdjunctConstructor(self.brain_model)
        self.A = A_reconstruction(self.brain_model)

    def reconstruct(self, ps):
        self.brain_model.syntactic_working_memory = []
        pull_point = None
        # ------------------------------ minimal search -----------------------------------------------#
        for node in [const for const in ps]:
            if self.get_local_head(node) and self.get_local_head(node).EF():
                self.pull_spec_phrases_into_working_memory(self.get_local_head(node))
                pull_point = node
            if self.get_local_head(node):
                self.brain_model.LF.try_LFmerge(self.get_local_head(node))
            if self.intervention(node, pull_point):
                log(f'Ā-chain was intervened by feature (this effect is offline). ')
        # ---------------------------------------------------------------------------------------------#

    def pull_spec_phrases_into_working_memory(self, head):
        for i, spec in enumerate(head.edge_specifiers()):
            if not spec.find_me_elsewhere:
                if self.scan_operator(spec):
                    self.brain_model.syntactic_working_memory.append(spec)
                    self.process_criterial_features(i, head, spec)
                else:
                    self.A.reconstruct(spec)

    def scan_operator(self, phrase):
        return self.brain_model.narrow_semantics.operator_variable_module.scan_criterial_features(phrase)

    def process_criterial_features(self, i, head, spec):
        if self.specifier_phrase_must_have_supporting_head(i, spec):
            head = spec.sister().merge_1(self.lexical_access.PhraseStructure(), 'left').left_const
        head.features |= self.transfer_features(head, spec)

    def transfer_features(self, head, spec):
        features = {'OP:_'} | self.scan_operator(self.checking_domain(spec)) | self.add_scope_information(head)
        return self.lexical_access.apply_parameters(self.lexical_access.apply_redundancy_rules(features))

    @staticmethod
    def add_scope_information(head):
        if not {'Inf', 'P', 'D', 'φ'} & head.features:
            return {'Fin', 'C', 'PF:C'}
        return set()

    def checking_domain(self, spec):
        if 'OP*' in self.scan_operator(spec):
            return spec.head()
        return spec

    @staticmethod
    def get_local_head(node):
        if node.is_primitive():
            return node
        if node.left_const.is_primitive():
            return node.left_const

    def specifier_phrase_must_have_supporting_head(self, i, spec):
        if spec.is_primitive():
            return False
        if i == 0:
            return False
        if self.brain_model.narrow_semantics.operator_variable_module.scan_criterial_features(spec):
            return True
        if spec.max().adjunct:
            return False
        if spec.max().container() and spec.max() != spec.max().container().licensed_phrasal_specifier():
            return True

    def intervention(self, node, pull_point):
        return ((pull_point and pull_point.head() != node.head() and
                node.left_const and 'φ' in node.left_const.features and
                self.brain_model.syntactic_working_memory) or node.find_me_elsewhere)
