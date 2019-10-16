from support import set_logging, log, get_number_of_operations, reset_number_of_operations, log_result, illu
from LexicalInterface import LexicalInterface
import phase_structure


class Reconstruction():
    def __init__(self, context):
        self.name_provider_index = 0
        self.memory_buffer = []
        self.context = context
        self.number_of_Moves = 0

        # Access to the lexicon
        self.lexical_access = LexicalInterface(context.redundancy_rules_file)
        self.lexical_access.load_lexicon(context.lexicon_file, context.language)
        self.lexical_access.load_lexicon(context.ug_morpheme_file, context.language, combine=True)

