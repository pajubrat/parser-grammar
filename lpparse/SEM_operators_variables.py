
from support import log
from collections import namedtuple

BindingDependency = namedtuple('BindingDependency', ['OperatorHead', 'ScopeMarker', 'Overt'])


class OperatorVariableModule:
    def __init__(self, speaker_model):
        self.interpretation_failed = False
        self.speaker_model = speaker_model
        self.bindings = []
        self.operator_interpretation = {'OP:WH': 'Wh-',
                                         'OP:TOP': 'Topic ',
                                         'OP:DE/EM': 'De-emphasis ',
                                         'OP:FAM': 'Familiarity ',
                                         'OP:FOC': 'Contrastive focus ',
                                         'OP:POL': 'Polarity ',
                                         'OP:Q': 'Yes/no interrogative ',
                                         'OP:REL': 'Relativization ',
                                         'OP:C/OP': 'Generic '}

    def bind_operator(self, X):
        self.bindings = []

        # Scope markers do not themselves have scopes

        if not X('scope_marker'):

            # Find all operator features

            for Opf in (f for f in X.core.features() if self.is_operator_feature(f)):

                # Determine the scope for the operator and, if not found, determine covert scope

                binding = self.interpret_covert_scope(self.find_overt_scope(X, Opf), Opf)

                # Produce output

                self.interpret_results(binding, Opf)

        return self.bindings

    @staticmethod
    def find_overt_scope(X, Opf):

        # Scope information is returned in the form of a dictionary

        return next(({'Head': X, 'Scope': Y, 'Overt': True} for Y in X.EXT(acquire='all') if
                     {'OP', 'Fin', Opf} in Y.core), {'Head': X, 'Scope': None, 'Overt': False})

    @staticmethod
    def interpret_covert_scope(binding_dict, Opf):

        # Determine covert scope if no scope exists and in situ is licensed

        if not binding_dict['Scope'] and '-insitu' not in binding_dict['Head'].core.bundle_features(Opf):

            # Covert scope markers are elements of the finite left periphery, if not found, return Scope: None

            return next(({'Head': binding_dict['Head'], 'Scope': X, 'Overt': False}
                         for X in binding_dict['Head'].EXT(acquire='all', self=True) if
                         X('finite_left_periphery')),
                        {'Head': binding_dict['Head'], 'Scope': None, 'Overt': False})

        return binding_dict

    def interpret_results(self, binding, Opf):
        if binding['Scope']:
            if binding['Overt']:
                self.bindings.append(f'{binding["Head"].label()}({Opf}, {self.operator_interpretation[Opf]}) bound by {binding["Scope"].illustrate()}')
                log(f'\n\t{binding["Head"].label()}({Opf}, {self.operator_interpretation[Opf]}) bound by {binding["Scope"].illustrate()}')
                if '-insitu' in binding["Head"].core.bundle_features(Opf):
                    binding["Scope"].core.remove_features({Opf})                        # Feature checking = remove Opf from the scope-marker so that it can only check one operator
                    binding["Scope"].core.add_features({'_checked(' + Opf + ')'})       # Mark the checked feature for clarity in the output
            else:
                self.bindings.append(f'{binding["Head"].label()}({Opf}, {self.operator_interpretation[Opf]}) bound by {binding["Scope"].illustrate()} by default rule. ')
        else:
            log(f'\n\t{binding["Head"].illustrate()} with {Opf} is not bound by scope-marker. ')
            self.interpretation_failed = True

    def is_operator(self, head):
        return {f for f in head.core.features() if self.is_operator_feature(f)}

    @staticmethod
    def is_operator_feature(f):
        return f.startswith('OP:')
