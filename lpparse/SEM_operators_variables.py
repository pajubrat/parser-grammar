
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
                                         'OP:DE/EM': 'De-emphatic ',
                                         'OP:FAM': 'Familiarity ',
                                         'OP:FOC': 'Contrastive focus ',
                                         'OP:EM': 'Emphatic ',
                                         'OP:Q': 'Yes/no interrogative ',
                                         'OP:REL': 'Relativization ',
                                         'OP:C/OP': 'Generic '}

    def bind_operator(self, X):

        # Binding configuration outputs, which are strings, are stored into a list

        self.bindings = []

        # Scope markers do not themselves have scopes

        if not X('scope_marker') and X('operator'):

            # Find all operator features

            for Opf in X('operator'):

                # Determine the scope for the operator and, if not found, determine covert scope

                self.interpret_results(self.get_covert_scope(self.get_overt_scope(X, Opf)))

        return self.bindings

    @staticmethod
    def get_overt_scope(X, Opf):

        # Scope information is returned in the form of a dictionary
        # If scope-markers are not found, a default is generated

        return next(({'Head': X, 'Scope': Y, 'Overt': True, 'Feature': Opf} for Y in X.EXT(acquire='all') if
                     {'OP', 'Fin', Opf} in Y.core), {'Head': X, 'Scope': None, 'Overt': False, 'Feature': Opf})

    @staticmethod
    def get_covert_scope(binding_dict):

        # Determine covert scope if no scope exists and in situ is licensed

        if not binding_dict['Scope'] and '-insitu' not in binding_dict['Head'].core.bundle_for_feature(binding_dict['Feature']):

            # Covert scope markers are elements of the finite left periphery, if not found, return Scope: None

            return next(({'Head': binding_dict['Head'], 'Scope': X, 'Overt': False, 'Feature': binding_dict['Feature']}
                         for X in binding_dict['Head'].EXT(acquire='all', self=True) if
                         X('finite_left_periphery')),
                        {'Head': binding_dict['Head'], 'Scope': None, 'Overt': False, 'Feature': binding_dict['Feature']})

        return binding_dict

    def interpret_results(self, binding):
        Opf = binding['Feature']
        if binding['Scope']:
            if binding['Overt']:
                self.bindings.append(f'{binding["Head"].label()}({Opf}, {self.operator_interpretation[Opf]}) bound by {binding["Scope"].illustrate()}')
                log(f'\n\t{binding["Head"].label()}({Opf}, {self.operator_interpretation[Opf]}) bound by {binding["Scope"].illustrate()}')
                if '-insitu' in binding["Head"].core.bundle_for_feature(Opf):
                    binding["Scope"].core.remove_features({Opf})                        # Feature checking = remove Opf from the scope-marker so that it can only check one operator
                    binding["Scope"].core.add_features({'_checked(' + Opf + ')'})       # Mark the checked feature for clarity in the output, not part of the theory
            else:
                self.bindings.append(f'{binding["Head"].label()}({Opf}, {self.operator_interpretation[Opf]}) bound by {binding["Scope"].illustrate()} by default rule. ')
        else:
            log(f'\n\t{binding["Head"].illustrate()} with {Opf} is not bound by scope-marker. ')
            self.interpretation_failed = True

