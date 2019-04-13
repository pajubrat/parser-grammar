# parser-grammar
I will type here various things I encountered while working with v. 1.01, mainly for myself:

1. Why functions like get_comps() return lists and not sets? They should return sets, unless there was a good reason for this. Once
they return sets, many tests are easier to implement by using set intersection. I think all conditions should be implemented in terms of set operations if possible -- but right now I don't remember if there was some reason to use sets.

The drop (movement reconstruction) is such a mess, it has to be refractored in some way. It should not be part of parser class,
because the functions are cognitive reflexes and do not open up parsing space. I will create a class 'reconstruction' that will take care of these operations. 
