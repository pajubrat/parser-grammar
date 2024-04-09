
from collections import defaultdict


class LanguageGuesser:
    def __init__(self, settings):
        self.lang_map = defaultdict(list)
        self.languages = set()
        for lexicon_file in [file.strip() for file in settings.retrieve('file_lexicons', set()).split(';')]:
            for line in open(settings.folders['lexicon'] / lexicon_file, 'r', encoding='utf-8'):
                if not line or '::' not in line or line.startswith('#'):
                    continue
                line = line.strip()
                key, feats = line.split('::')
                key = key.strip()
                feats = [f.strip() for f in feats.split()]
                for feat in feats:
                    if feat.startswith('LANG:'):
                        self.lang_map[key].append(feat)
                        self.languages.add(feat)

    def guess_language(self, sentence):
        counter = {}
        for word in sentence:
            for lang in self.lang_map[word]:
                if lang not in counter.keys():
                    counter[lang] = 1
                else:
                    counter[lang] += 1
        selection = 0
        selected_language = ''
        if counter:
            for key in counter.keys():
                if counter[key] > selection:
                    selected_language = key
                    selection = counter[key]
            return selected_language
        return 'LANG:FI'    # default language assumption for unknown language


