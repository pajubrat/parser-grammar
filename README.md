Parser-grammar v. 1.9x

2019

This project is a computational implementation of a Phillips' (1996) style minimalist top-down/left-right parser-grammar, 
intended to be used as a tool for scientific, linguistic analysis. 

Full documentation can be found from /Documentation folder, together with a bibliography of published articles.

The program is used to test theoretical linguistic hypotheses by means of simulation. In a typical scenario, you will feed the 
algorithm with a (typically large) linguistic corpus which it parses/analyses, and which you would then compare with some 
"gold standard" analysis. In this way, theoretical ideas can be tested and compared with each other rigorously on a very large 
set of expressions.

The parser-grammar is based on a theory originally proposed by Phillips (1996), which derives phrase structures in top-down/left-right 
order, thus in a way that is consistent with how humans must comprehend/parse language. The program adds to this the algorithm and required modifications that performs the actual parsing. It guides the core computational operations of the human language faculty (e.g. Merge, Move) by reading a list of words from the PF-interface. The model has been developed within the framework of the minimalist grammar (Chomsky, 1995, 2000, 2008).

The program was created in connection with a research project ProGraM-PC: A Processing-friendly Grammatical Model for Parsing and predicting on-line Complexity)" led by Prof. Cristiano Chesi (IUSS, Pavia). This version was designed and programmed by Pauli Brattico with some code contributed by Jukka Purma.
