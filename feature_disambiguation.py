from support import set_logging, log, get_number_of_operations, reset_number_of_operations, log_result, illu
from LexicalInterface import LexicalInterface
import phrase_structure

class FeatureProcessing():
    def __init__(self, controlling_parser_process):
        self.controlling_parser_process = controlling_parser_process
        pass

    # Definition for feature inheritance mechanism
    def disambiguate(self, ps):

        # --------------------------- minimal search ---------------------------------------------#
        for node in ps.minimal_search():
            # If there is a primitive head to the left...
            if node.left_const and node.left_const.is_primitive():
                h = node.left_const
                # ...and it has neutralized agreement features, they are first disambiguated...
                if '?ARG' in h.features:
                    log(f'\t\t\t\t\tSolving feature ambiguities for \"{h}\".')
                    self.resolve_neutralized_feature(h)
        # ----------------------------------------------------------------------------------------#

    # Definition for feature inheritance
    def resolve_neutralized_feature(self, h):
        h.features.discard('?ARG')
        if h.selector() and 'SEM:internal' in h.selector().features:
            log(f'\t\t\t\t\t{h} has neutralized PHI-feature, will be resolved into -ARG due to {h.selector()}')
            h.features.add('-ARG')
            h.features.add('-SPEC:*')
            h.features.discard('SPEC:*')
        elif h.selector() and 'SEM:external' in h.selector().features:
            log(f'\t\t\t\t\t{h} has neutralized PHI-feature, will be resolved into +ARG due to {h.selector()}')
            h.features.add('ARG')
            h.features.add('VAL')
            h.features.discard('?VAL')
            h.features.add('!SPEC:*')
        else:
            h.features.add('ARG')
            h.features.add('PHI:NUM:_')
            h.features.add('PHI:PER:_')