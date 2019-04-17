# parser-grammar
I will type here various things I encountered while working with v. 1.01, mainly for myself:

1. Why functions like get_comps() return lists and not sets? They should return sets, unless there was a good reason for this. Once
they return sets, many tests are easier to implement by using set intersection. I think all conditions should be implemented in terms of set operations if possible -- but right now I don't remember if there was some reason to use sets.

3. The way how morphology-lexicon monitors  what are word-internal morphemes is a mess and unintuitive

4. Head movement reconstruction forces me to be more explicit about verb's argument structures, for example, that each intransitive V must have !SPEC:D or !COMP:D, otherwise it will open T{V} as a LF-legible package. The problem is that the  argument structure must be defined by few classes triggering redundancy rules, not listed individually in the lexicon. These verbal classes must be created as features.
