from support import log

class Discourse:
    def __init__(self, narrow_semantics):
        self.narrow_semantics = narrow_semantics            # This provides access to semantic bookkeeping

    def is_discourse_feature(self, feature):
        return feature[:2] == 'D:'

    def get_discourse_features(self, features):
        return {feature for feature in features if feature[:2] == 'D:'}

    def reconstruct_discourse(self, ps):
        if 'FIN' in ps.features:
            return True
        d_features = self.get_discourse_features(ps.features)
        if not d_features:
            return True
        log('Interpreting D-feature ')
        for f in d_features:
            result = self.interpret_discourse_feature(f, ps)
            if not result:
                return False
        return True

    def interpret_discourse_feature(self, f, ps):
        log(f'[{f}] at {ps.max().illustrate()}: ')
        idx = self.narrow_semantics.get_semantic_wiring(ps)
        if not idx:
            log(f'{ps.max().illustrate()} not wired semantically. ')
            return None
        if idx not in self.narrow_semantics.semantic_bookkeeping:
            log(f'No idea what {ps.max().illustrate()} refers to. ')
            return None
        if 'Bound by' not in self.narrow_semantics.semantic_bookkeeping[idx]:
            log(f'{ps.max().illustrate()} not bound by propositional scope operator. ')
            return None
        idx = self.narrow_semantics.get_semantic_wiring(self.narrow_semantics.semantic_bookkeeping[idx]['Bound by'][0])
        if not idx:
            log('The relevant proposition not available in SEM. ')
            return None
        log(f'Interpreted with semantic object [{idx}].')
        return idx


