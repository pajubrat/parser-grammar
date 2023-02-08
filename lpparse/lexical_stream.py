from support import log
import time
from feature_processing import phi_feature

class LexicalStream:
    def __init__(self, brain_model):
        self.brain_model = brain_model
        self.lexicon = self.brain_model.lexicon
        self.id = 0

    def stream_into_syntax(self, lexical_item, lst_branched, ps, index, inflection_buffer):
        if '#' in lexical_item.morphology:
            return
        lexical_item, inflection_buffer, inflection = self.process_inflection(lexical_item, inflection_buffer, lst_branched[index])
        if inflection:
            log(f'\n\tNext affix [{lst_branched[index][:-1]}] ')
            if ps:
                self.brain_model.parse_new_item(ps.copy(), lst_branched, index + 1, inflection_buffer)
            else:
                self.brain_model.parse_new_item(None, lst_branched, index + 1, inflection_buffer)
        else:
            lexical_item.active_in_syntactic_working_memory = True
            self.brain_model.narrow_semantics.pragmatic_pathway.allocate_attention(lexical_item)

            if lst_branched[index].endswith('$'):
                stri = lst_branched[index][:-1]
            else:
                stri = lst_branched[index]
            log(f'\n\tNext morph [{stri}] ~ {lexical_item.label()}°\n')
            if not ps:
                self.brain_model.parse_new_item(lexical_item.copy(), lst_branched, index + 1)
            else:
                if self.brain_model.local_file_system.settings['datatake_full']:
                    self.brain_model.local_file_system.simple_log_file.write(
                        f'\n\t{ps}\n\t{ps} + {lexical_item.get_phonological_string()}')
            if self.brain_model.local_file_system.settings['stop_at_unknown_lexical_item']:
                if '?' in lexical_item.features:
                    print(f'\nUnrecognized feature in /{lst_branched[index]}/. ')
                    self.brain_model.exit = True

    def process_inflection(self, lexical_item, inflection_buffer, phonological_word):
        inflection = self.get_inflection_features(lexical_item, phonological_word)
        if inflection:
            if inflection_buffer:
                for feature in inflection:
                    if (phi_feature(feature) and feature in inflection_buffer) or (feature == 'default' and 'PHI/PF' in inflection_buffer):
                        inflection_buffer.add('?')
                    else:
                        inflection_buffer.add(feature)
            else:
                inflection_buffer = set()
                inflection_buffer = inflection_buffer.union(inflection)
        else:
            if inflection_buffer:
                lexical_item.features = self.lexicon.apply_redundancy_rules(lexical_item.features | inflection_buffer)
                inflection_buffer = None
        return lexical_item, inflection_buffer, inflection

    def get_inflection_features(self, lexical_item, phonological_word):
        if 'inflectional' in lexical_item.features:
            return lexical_item.features - {'inflectional'}

    def add_ID(self, lexical_item):
        lexical_item.features.add('#'+str(self.consume_id()))

    def consume_id(self):
        self.id += 1
        return self.id