from support import log

class FeatureProcessing():
    def __init__(self, controlling_parser_process):
        self.controlling_parser_process = controlling_parser_process
        pass

    # Definition for feature inheritance mechanism
    def disambiguate(self, ps):
        # --------------------------- minimal search ---------------------------------------------#
        for node in ps:
            if node.left_const and node.left_const.is_primitive():
                if '?ARG' in node.left_const.features:
                    log(f'Solving feature ambiguities for \"{node.left_const}\"...')
                    self.resolve_neutralized_feature(node.left_const)
        # ----------------------------------------------------------------------------------------#

    # Definition for feature inheritance
    def resolve_neutralized_feature(self, h):
        h.features.discard('?ARG')
        if self.selected_by_SEM_internal(h):
            log(f'{h} resolved into -ARG due to {h.selector()}...')
            h.features.add('-ARG')
            h.features.add('-SPEC:*')
            h.features.discard('SPEC:*')
        elif self.selected_by_SEM_external(h):
            log(f'{h} resolved into +ARG due to {h.selector()}...')
            h.features.add('ARG')
            if '?VAL' in h.features:
                h.features.add('VAL')
                h.features.discard('?VAL')
            h.features.add('!SPEC:*')
        else:   # Selected by neither
            log(f'{h} resolved to +ARG...')
            h.features.add('ARG')
            h.features.add('PHI:NUM:_')
            h.features.add('PHI:PER:_')
            h.features.add('SPEC:*')
        self.controlling_parser_process.consume_resources("Feature Processing")

    def selected_by_SEM_internal(self, h):
        return h.selector() and 'SEM:internal' in h.selector().features

    def selected_by_SEM_external(self, h):
        return h.selector() and 'SEM:external' in h.selector().features