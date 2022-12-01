from support import log

class A_reconstruction:
    def __init__(self, controlling_parser_process):
        self.brain_model = controlling_parser_process

    def reconstruct(self, head, spec):
        if spec.A_reconstructing():
            for node in spec.sister().minimal_search(lambda x: x.has_vacant_phrasal_position() or x.referential()):
                head.merge_to_right(node, spec, self.brain_model.babtize())
                self.brain_model.consume_resources('A-Chain')
                break
