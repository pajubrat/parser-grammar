from support import log
from lexical_interface import LexicalInterface
from adjunct_constructor import AdjunctConstructor
from A_reconstruction import A_reconstruction


class PhrasalMovement:
    def __init__(self, controlling_parser_process):
        self.brain_model = controlling_parser_process
        self.brain_model.name_provider_index = 1
        self.lexical_access = LexicalInterface(self.brain_model)
        self.A = A_reconstruction(self.brain_model)

    def reconstruct(self, ps):
        # ------------------- minimal search -------------------------#
        for head in ps.minimal_search():
            if head.EF():
                for i, spec in enumerate(head.edge_specifiers()):
                    if not spec.find_me_elsewhere:
                        self.create_phrasal_chain(head, spec, i > 0)
        # ------------------------------------------------------------#

    def create_phrasal_chain(self, head, spec, multi):
        if self.scan_operator(spec):
            self.create_A_bar_chain(head, spec, multi)
        else:
            self.create_A_chain(spec)

    def create_A_bar_chain(self, head, spec, multi):
        self.process_criterial_features(head, spec, multi)
        self.find_gap(head, spec)

    def find_gap(self, head, spec):
        for head in head.mother.minimal_search():
            if self.brain_model.LF.try_LFmerge(head, spec):
                break

    def create_A_chain(self, spec):
        self.A.reconstruct(spec)

    def scan_operator(self, spec):
        return self.brain_model.narrow_semantics.operator_variable_module.scan_criterial_features(spec)

    def process_criterial_features(self, head, spec, multi):
        if multi and self.multi_specifier_needs_head_support(spec):
            head = spec.sister().merge_1(self.lexical_access.PhraseStructure(), 'left').left_const
        head.features |= self.transfer_features(head, spec)

    def transfer_features(self, head, spec):
        features = {'OP:_'} | self.scan_operator(self.checking_domain(spec)) | head.add_scope_information()
        return self.lexical_access.apply_parameters(self.lexical_access.apply_redundancy_rules(features))

    # Strong and weak operators
    def checking_domain(self, spec):
        if 'OP*' in self.scan_operator(spec):
            return spec.head()
        return spec

    def multi_specifier_needs_head_support(self, spec):
        return self.scan_operator(spec) or \
               (not spec.adjunct and spec.container() and spec != spec.container().licensed_phrasal_specifier())
