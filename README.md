# parser-grammar
I will type here various things I encountered while working with v. 1.01, mainly for myself:

1. Why functions like get_comps() return lists and not sets? They should return sets, unless there was a good reason for this. Once
they return sets, many tests are easier to implement by using set intersection. I think all conditions should be implemented in terms of set operations if possible -- but right now I don't remember if there was some reason to use sets.

2. The way how morphology-lexicon monitors  what are word-internal morphemes is a mess and unintuitive
