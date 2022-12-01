from support import log

class FeatureProcessing():
    def __init__(self, controlling_parser_process):
        self.controlling_parser_process = controlling_parser_process

    def disambiguate(self, ps):
        # --------------------------- minimal search ---------------------------------------------#
        for node in ps:
            if node.check({'?ARG'}):
                self.resolve_neutralized_feature(node)
        # ----------------------------------------------------------------------------------------#

    # Definition for feature inheritance
    def resolve_neutralized_feature(self, h):
        h.features.discard('?ARG')
        if h.selected_by_SEM_internal_predicate():
            log(f'{h} resolved into -ARG due to {h.selector()}...')
            h.features.add('-EF:φ')
            h.features.discard('EF:φ')
            h.features.add('-ARG')
        else:
            log(f'{h} resolved into +ARG...')
            h.features.add('ARG')
            h.features.add('!EF:φ')
            h.features.add('EF:φ')
            h.features.add('PHI:NUM:_')
            h.features.add('PHI:PER:_')