from support import log


class LexicalStream:
    def __init__(self, controlling_parsing_process):
        self.controlling_parser_process = controlling_parsing_process
        self.lexicon = self.controlling_parser_process.lexicon
        self.id = 0

    def stream_into_syntax(self, terminal_lexical_item, lst_branched, inflection, ps, index):
        terminal_lexical_item = self.process_inflection(inflection, terminal_lexical_item)
        log('Done.')
        if inflection:
            if ps:
                self.controlling_parser_process.parse_new_item(ps.copy(), lst_branched, index + 1)
            else:
                self.controlling_parser_process.parse_new_item(None, lst_branched, index + 1)
        else:
            self.controlling_parser_process.consume_resources("Item streamed into syntax", f'{terminal_lexical_item}')
            terminal_lexical_item.active_in_syntactic_working_memory = True

            #
            # Add identity feature
            self.add_ID(terminal_lexical_item)

            #
            # Allocate attentional resources
            self.controlling_parser_process.narrow_semantics.pragmatic_pathway.allocate_attention(terminal_lexical_item)
            #

            if not ps:
                log('No other elements in active working memory, waiting for the next element.\n')
                self.controlling_parser_process.parse_new_item(terminal_lexical_item.copy(), lst_branched, index + 1)
            else:
                log(f'\n\n\t{self.controlling_parser_process.resources["Item streamed into syntax"]["n"]}. Consume ' + terminal_lexical_item.get_phonological_string())
                self.controlling_parser_process.resources['Steps']['n'] += 1
                self.controlling_parser_process.local_file_system.simple_log_file.write(
                    f'\n{self.controlling_parser_process.resources["Steps"]["n"]}\t{ps}\n\t{ps} + {terminal_lexical_item.get_phonological_string()}')
            return terminal_lexical_item

    def process_inflection(self, inflection, lexical_item):
        if inflection:
            if 'inflectional' in inflection:        # Don't copy inflectional marker itself
                inflection.remove('inflectional')
            self.controlling_parser_process.memory_buffer_inflectional_affixes = self.controlling_parser_process.memory_buffer_inflectional_affixes.union(inflection)
            self.controlling_parser_process.consume_resources("Inflection")
            log(f'Added {sorted(inflection)} into transient memory buffer...')
        else:
            if self.controlling_parser_process.memory_buffer_inflectional_affixes:
                log(f'Adding inflectional features {sorted(self.controlling_parser_process.memory_buffer_inflectional_affixes)} to ' + lexical_item.get_phonological_string() + '...')
                lexical_item.features = self.lexicon.apply_redundancy_rules(lexical_item.features | set(self.controlling_parser_process.memory_buffer_inflectional_affixes))
                self.controlling_parser_process.memory_buffer_inflectional_affixes = set()
        return lexical_item

    def add_ID(self, lexical_item):
        lexical_item.features.add('#'+str(self.consume_id()))

    def consume_id(self):
        self.id += 1
        return self.id