from support import set_logging, log, get_number_of_operations, reset_number_of_operations, log_result, illu
from LexicalInterface import LexicalInterface
import phrase_structure

class FeatureProcessing():
    def __init__(self, controlling_parser_process):
        self.controlling_parser_process = controlling_parser_process
        pass

    # Definition for feature inheritance mechanism
    # Condition 1. Examine primitive heads to left
    # Condition 2. Examine only ambiguous features ?F
    # Output. Resolve ambiguous feature ?F
    def disambiguate(self, ps):
        ps_ = ps
        while ps_:
            # If there is a primitive head to the left...
            if ps_.left_const and ps_.left_const.is_primitive():
                h = ps_.left_const
                # ...and it has neutralized agreement features, they are first disambiguated...
                if '?ARG' in h.features:
                    log(f'\t\t\t\t\tSolving feature ambiguities for \"{h}\".')
                    self.resolve_neutralized_feature(h)
            ps_ = ps_.walk_downstream()

    # Definition for feature inheritance
    # Only applies for features ?F that need resolution
    def resolve_neutralized_feature(self, h):

        # We are replacing ?ARG so we discard it
        h.features.discard('?ARG')

        # Condition 1. H selected by head with SEM:internal => -ARG
        if h.selector() and 'SEM:internal' in h.selector().features:
            log(f'\t\t\t\t\t{h} has neutralized PHI-feature, will be resolved into -ARG due to {h.selector()}')
            h.features.add('-ARG')
            h.features.add('CAT:-ARG')
            h.features.add('-SPEC:*')
            h.features.discard('SPEC:*')

        # Condition 2. H selected by head with SEM:external => ARG + !SPEC:* (EPP)
        elif h.selector() and 'SEM:external' in h.selector().features:
            log(f'\t\t\t\t\t{h} has neutralized PHI-feature, will be resolved into +ARG due to {h.selector()}')
            h.features.add('ARG')
            h.features.add('CAT:ARG')
            h.features.add('VAL')
            h.features.discard('?VAL')
            h.features.add('!SPEC:*')

        # Condition 3. If H is selected by neither internal nor external, we assume ARG
        else:
            h.features.add('ARG')
            h.features.add('CAT:ARG')
            h.features.add('PHI:NUM:_')
            h.features.add('PHI:PER:_')

