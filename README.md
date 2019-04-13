# parser-grammar
I will type here various things I encountered while working with v. 1.01, mainly for myself:

WHy functions like get_comps() returns lists and not sets? They should return sets, unless there was a good reason for this. Once
they return sets, many tests are easier to implement by using set intersection.
