from support import log

#
# All reconstruction operations will be taken care by these functions
#

class Reconstruct:
    def __init__(self, controlling_parsing_process):
        self.brain_model = controlling_parsing_process

    def create_chain(self, start_head, reconstructed_object, selection, sustain, legible):

        # Rule 1. There is no right sister
        if not start_head.right_sister():
            start_head.merge_around(reconstructed_object)

        # Rule 2. Create chain inside the right sister
        else:

            # Rule 2.1. Chain formation
            for head in start_head.sister().minimal_search(selection, sustain):
                head.specifier_sister().merge_1(reconstructed_object, 'left')
                if legible(reconstructed_object):
                    break
                reconstructed_object.remove()

            # Rule 2.4 Last resort reconstruction
            else:
                start_head.sister().merge_1(reconstructed_object)

        # Rule 3. Return the original object
        return reconstructed_object
