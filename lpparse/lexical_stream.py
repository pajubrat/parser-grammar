from support import log


class LexicalStream:
    def __init__(self, controlling_parsing_process):
        self.controlling_parser_process = controlling_parsing_process
        self.lexicon = self.controlling_parser_process.lexicon
        self.id = 0

    def stream_into_syntax(self, terminal_lexical_item, lst_branched, inflection, ps, index, inflection_buffer):
        terminal_lexical_item, inflection_buffer = self.process_inflection(inflection, terminal_lexical_item, inflection_buffer)
        if inflection:
            log(f'[{lst_branched[index][:-1]}] ')
            if ps:
                self.controlling_parser_process.parse_new_item(ps.copy(), lst_branched, index + 1, inflection_buffer)
            else:
                self.controlling_parser_process.parse_new_item(None, lst_branched, index + 1, inflection_buffer)
        else:

            terminal_lexical_item.active_in_syntactic_working_memory = True
            # Add identity feature
            self.add_ID(terminal_lexical_item)
            # Allocate attentional resources
            self.controlling_parser_process.narrow_semantics.pragmatic_pathway.allocate_attention(terminal_lexical_item)

            if lst_branched[index].endswith('$'):
                stri = lst_branched[index][:-1]
            else:
                stri = lst_branched[index]
            log(f'\n\t\tNext morph [{stri}] ~ {terminal_lexical_item.label()}°')
            if not ps:
                self.controlling_parser_process.parse_new_item(terminal_lexical_item.copy(), lst_branched, index + 1)
            else:
                if self.controlling_parser_process.local_file_system.settings['datatake_full']:
                    self.controlling_parser_process.local_file_system.simple_log_file.write(
                        f'\n\t{ps}\n\t{ps} + {terminal_lexical_item.get_phonological_string()}')
            if self.controlling_parser_process.local_file_system.settings['stop_at_unknown_lexical_item']:
                if '?' in terminal_lexical_item.features:
                    print(f'\nUnrecognized word /{lst_branched[index]}/ terminated the derivation. ')
                    self.controlling_parser_process.exit = True
            return terminal_lexical_item

    def process_inflection(self, inflection, lexical_item, inflection_buffer):
        if inflection:
            if 'inflectional' in inflection:        # Don't copy inflectional marker itself
                inflection.remove('inflectional')
                if inflection_buffer:
                    inflection_buffer = inflection_buffer.union(inflection)
                else:
                    inflection_buffer = set()
                    inflection_buffer = inflection_buffer.union(inflection)
        else:
            if inflection_buffer:
                log(f'=> next morph({lexical_item}) ')
                lexical_item.features = self.lexicon.apply_redundancy_rules(lexical_item.features | inflection_buffer)
                inflection_buffer = None
        return lexical_item, inflection_buffer

    def add_ID(self, lexical_item):
        lexical_item.features.add('#'+str(self.consume_id()))

    def consume_id(self):
        self.id += 1
        return self.id