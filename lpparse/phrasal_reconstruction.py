from support import log
from lexical_interface import LexicalInterface

class PhrasalMovement:
    def __init__(self, controlling_parser_process):
        self.brain_model = controlling_parser_process
        self.brain_model.name_provider_index = 1
        self.lexical_access = LexicalInterface(self.brain_model)

    def reconstruct(self, ps):
        for head in ps.minimal_search(lambda x: x.EF()):
            for i, spec in enumerate([spec for spec in head.edge() if not spec.find_me_elsewhere]):
                spec_copy = spec.copy_for_chain(self.brain_model.babtize())
                if self.scan_operator(spec):
                    self.process_criterial_features(head, spec, i > 0)
                    self.brain_model.reconstruct.create_chain(head, spec_copy, lambda x: x.A_bar_chain_selection(), lambda x: x.A_bar_chain_sustain(), lambda x, y: x.A_bar_chain_legibility(spec))
                else:
                    if spec.A_reconstructing():
                        self.brain_model.reconstruct.create_chain(head, spec_copy, lambda x: x.A_chain_selection(), lambda x: x.A_chain_sustain(), lambda x, y: x.A_chain_legibility())

    def scan_operator(self, spec):
        return self.brain_model.narrow_semantics.operator_variable_module.scan_criterial_features(spec)

    def process_criterial_features(self, head, spec, multi):
        if multi and self.multi_specifier_needs_head_support(spec):
            head = spec.sister().merge_1(self.lexical_access.PhraseStructure(), 'left').left
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
