from support import log


class LexicalStream:
    def __init__(self, controlling_parsing_process):
        self.controlling_parser_process = controlling_parsing_process

    def stream_into_syntax(self, terminal_lexical_item, lst_branched, inflection, ps, index):

        # Process inflection (store into memory, load from the memory into constituent)
        terminal_lexical_item = self.process_inflection(inflection, terminal_lexical_item)
        log('Done.')
        if inflection:
            # Ask for new element
            if ps:
                self.controlling_parser_process.parse_new_item(ps.copy(), lst_branched, index + 1)
            else:
                self.controlling_parser_process.parse_new_item(None, lst_branched, index + 1)

        # If the next element is a lexical constituent, we prepare it for syntactic attachment
        else:
            self.controlling_parser_process.consume_resources("Item streamed into syntax", f'{terminal_lexical_item}')

            # The element enters active working memory
            terminal_lexical_item.active_in_syntactic_working_memory = True

            # If this was the first element, we have nothing to attach, so we get new element
            if not ps:
                log('No other elements in active working memory, waiting for the next element.\n')
                self.controlling_parser_process.parse_new_item(terminal_lexical_item.copy(), lst_branched, index + 1)
            # If a partial phrase structure exists, we proceed
            else:
                log(f'\n\n\t{self.controlling_parser_process.resources["Item streamed into syntax"]["n"]}. Consume ' + terminal_lexical_item.get_phonological_string())
                # log(f'\t({ps}' + ' + ' + terminal_lexical_item.get_phonological_string() + ')')
                self.controlling_parser_process.resources['Steps']['n'] += 1
                self.controlling_parser_process.local_file_system.simple_log_file.write(
                    f'\n{self.controlling_parser_process.resources["Steps"]["n"]}\t{ps}\n\t{ps} + {terminal_lexical_item.get_phonological_string()}')

            # Send the lexical item into the syntactic component
            return terminal_lexical_item

    def process_inflection(self, inflection, lexical_item):
        """
        Processes inflectional features (if any).

        If the input contains inflectional features, they are stored into a temporary memory buffer.
        If the input does not contain inflectional features, it must be a lexical item. All inflectional
        morphemes are then discharged inside the lexical item.
        """
        if inflection:
            if 'inflectional' in inflection:        # Don't copy inflectional marker itself
                inflection.remove('inflectional')
            self.controlling_parser_process.memory_buffer_inflectional_affixes = self.controlling_parser_process.memory_buffer_inflectional_affixes.union(inflection)
            self.controlling_parser_process.consume_resources("Inflection")
            log(f'Added {sorted(inflection)} into transient memory buffer...')
        else:
            if self.controlling_parser_process.memory_buffer_inflectional_affixes:
                log(f'Adding inflectional features {sorted(self.controlling_parser_process.memory_buffer_inflectional_affixes)} to ' + lexical_item.get_phonological_string() + '...')
                lexical_item.features = lexical_item.features | set(self.controlling_parser_process.memory_buffer_inflectional_affixes)
                self.controlling_parser_process.memory_buffer_inflectional_affixes = set()
        return lexical_item