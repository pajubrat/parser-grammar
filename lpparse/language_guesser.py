
from collections import Counter, defaultdict


class LanguageGuesser:
    def __init__(self, lexicon_file):
        self.lang_map = defaultdict(list)
        self.languages = set()
        for line in open(lexicon_file):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            key, feats = line.split('::', 1)
            key = key.strip()
            feats = [f.strip() for f in feats.split()]
            for feat in feats:
                if feat.startswith('LANG:'):
                    self.lang_map[key].append(feat)
                    self.languages.add(feat)

    def guess_language(self, sentence):
        hits = Counter()
        for word in sentence:
            for lang in self.lang_map[word]:
                hits[lang] += 1
        if hits:
            return hits.most_common(1)[0][0]
        return 'LANG:EN'
