from support import log

class Focus:
    def __init__(self, narrow_semantics):
        self.focus_interpretations = []
        self.narrow_semantics = narrow_semantics

    def reconstruct(self, X):
        self.reset_interpretation()
        if not 'OP' in X.core:  # Ignore scope-markers
            for focus_f in [f for f in X.core.features() if self.focus_feature(f)]:    # Interpret all focus features/elements
                x = X
                while x:

                    # Focus sets for concepts (ignores purely functional items and auxiliaries)

                    if x.core('expresses_concept'):
                        self.focus_interpretations.append(f'Narrow focus on {x.label()} ({focus_f})')
                        log(f'\n\tReconstructed narrow focus for {x.label()} ({focus_f})')

                        # Focus sets for spatiotemporal objects (subtype of "wide focus")

                        if x.core.get_idx_tuple('QND'):
                            idx = x.core.get_idx_tuple('QND')[0]
                            self.narrow_semantics.quantifiers_numerals_denotations.update_discourse_inventory(idx, {'Focus set': f'{{{x.max().illustrate},...}}'})

                        # Focus sets for concepts

                        if x.core.get_idx_tuple('PRE'):
                            idx = x.core.get_idx_tuple('PRE')[0]
                            self.narrow_semantics.predicates_relations_events.update_discourse_inventory(idx, {'Focus set': f'{{{x.core.get_lf()},...}}'})

                    # Focus sets for whole events (a subtype of "wide focus")

                    if x.denotes_event():
                        self.focus_interpretations.append(f'Wide focus on {x.label()}P ({focus_f})')
                        log(f'\n\tReconstructed wide focus for {x.label()}P ({focus_f})')
                        if x.core.get_idx_tuple('PRE'):
                            idx = x.core.get_idx_tuple('PRE')[0]
                            self.narrow_semantics.predicates_relations_events.update_discourse_inventory(idx, {'Focus set': '{{event, no event}}'})

                    # Because the ontology projections are done for the base elements, we must follow the copy-links to find them

                    if x.affix():
                        if x.affix().copied:
                            x = x.affix().copied
                        else:
                            x = x.affix()
                    else:
                        x = None

            return self.focus_interpretations

    def reset_interpretation(self):
        self.focus_interpretations = []

    def focus_feature(self, f):
        return f.startswith('OP:')
