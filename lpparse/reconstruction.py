from support import log

#
# All reconstruction operations will be taken care by these functions
#

class Reconstruct:
    def __init__(self, controlling_parsing_process):
        self.brain_model = controlling_parsing_process

    def create_chain(self, start_head, reconstructed_object, selection, sustain, legible):
        for head in start_head.search_domain().minimal_search(selection, sustain):
            head.specifier_sister().merge_1(reconstructed_object, 'left')
            if legible(head, reconstructed_object):
                break
            reconstructed_object.remove()
        else:
            head.merge_1(reconstructed_object, 'right')
            if not legible(head, reconstructed_object):
                reconstructed_object.remove()
                start_head.sister().merge_1(reconstructed_object, 'left')

        self.brain_model.consume_resources('Chain', reconstructed_object)
        return reconstructed_object
