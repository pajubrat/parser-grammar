from support import log

class Focus:
    def __init__(self, narrow_semantics):
        self.focus_interpretations = []
        self.narrow_semantics = narrow_semantics

    def reconstruct(self, X):
        self.focus_interpretations = []

        # Ignore scope-markers

        if not 'OP' in X.core:

            # Check if X has focus feature(s) and, if so, examine each

            for focus_f in sorted(list(X('operator'))):

                # Examine the constituent having the operator and, if it is complex, all other heads that it contains
                # x = used in the loop

                x = X

                while x:

                    # Focus sets for concepts (ignores purely functional items and auxiliaries)

                    if x.core('expresses_concept'):
                        self.focus_interpretations.append(f'Narrow focus on {x.label()} ({focus_f})')
                        log(f'\n\tReconstructed narrow focus for {x.label()} ({focus_f})')

                        # Focus sets for spatiotemporal objects

                        if x.core.get_idx_tuple('QND'):
                            idx = x.core.get_idx_tuple('QND')[0]
                            self.narrow_semantics.quantifiers_numerals_denotations.update_discourse_inventory(idx, {'Focus set': f'{{{x.EXT(max=True, collect=False).illustrate},...}}'})

                        # Focus sets for concepts (PRE = predicates, relations and events)

                        if x.core.get_idx_tuple('PRE'):
                            idx = x.core.get_idx_tuple('PRE')[0]
                            self.narrow_semantics.predicates_relations_events.update_discourse_inventory(idx, {'Focus set': f'{{{x.core.get_lf()},...}}'})

                    if x.core('polarity'):
                        self.focus_interpretations.append(f'Wide polarity focus on {x.label()} ({focus_f})')
                        log(f'\n\tReconstructed wide polarity focus for {x.label()} ({focus_f})')

                    # Focus sets for whole events (a subtype of "wide focus")
                    # Events are denoted by functional heads specifically marked for doing so by feature π (e.g., T)

                    if x.INT('event'):
                        self.focus_interpretations.append(f'Wide focus on event {x.label()}P ({focus_f})')
                        log(f'\n\tReconstructed wide focus for event {x.label()}P ({focus_f})')
                        if x.core.get_idx_tuple('PRE'):
                            idx = x.core.get_idx_tuple('PRE')[0]
                            self.narrow_semantics.predicates_relations_events.update_discourse_inventory(idx, {'Focus set': '{event, no event}'})

                    # Because the ontology projections are done for the base elements, we must follow the copy-links to find them

                    if x.affix():
                        if x.affix().copied:
                            x = x.affix().copied
                        else:
                            x = x.affix()
                    else:
                        x = None    # This will terminate the focus set generation for X

            return self.focus_interpretations

