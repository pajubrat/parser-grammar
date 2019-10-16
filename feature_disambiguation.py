from support import set_logging, log, get_number_of_operations, reset_number_of_operations, log_result, illu
from LexicalInterface import LexicalInterface
import phase_structure

class FeatureProcessing():
    def __init__(self):
        pass

    def disambiguate(self, ps):
        ps_ = ps
        while ps_:
            # If there is a primitive head to the left...
            if ps_.left_const and ps_.left_const.is_primitive():
                h = ps_.left_const
                # ...and it has neutralized agreement features, they are first disambiguated...
                if '?ARG' in h.features:
                    self.resolve_neutralized_feature(h)
            ps_ = ps_.walk_downstream()

    def resolve_neutralized_feature(self, h):
        h.features.discard('?ARG')
        if h.get_selector() and 'SEM:internal' in h.get_selector().features:
            log(f'\t\t\t\t\t{h} has neutralized PHI-feature, will be resolved into -ARG due to {h.get_selector()}')
            h.features.add('-ARG')
            h.features.add('CAT:-ARG')
            h.features.add('-SPEC:*')
        elif h.get_selector() and 'SEM:external' in h.get_selector().features:
            log(f'\t\t\t\t\t{h} has neutralized PHI-feature, will be resolved into +ARG due to {h.get_selector()}')
            h.features.add('ARG')
            h.features.add('CAT:ARG')
            h.features.add('VAL')
            h.features.discard('?VAL')
            h.features.add('!SPEC:*')
        else:
            h.features.add('ARG')
            h.features.add('CAT:ARG')

