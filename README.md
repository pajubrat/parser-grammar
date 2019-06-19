# Parser-grammar v. 1.9x 

2019

This project is a computational implementation of a Phillips' (1996) style minimalist top-down/left-right parser-grammar, 
intended to be used as a tool for scientific, linguistic analysis. 

Full documentation can be found from Documentation` folder.

The program is used to test theoretical linguistic hypotheses by means of simulation. In a typical scenario, you will feed the 
algorithm with a (typically large) linguistic corpus which it parses/analyses, and which you would then compare with some 
"gold standard" analysis. In this way, theoretical ideas can be tested and compared with each other rigorously on a very large 
set of expressions.

The parser-grammar is based on a theory originally proposed by Phillips (1996), which derives phrase structures in top-down/left-right 
order, thus in a way that is consistent with how humans must comprehend/parse language. The program adds to this the algorithm that 
performs the actual parsing. It guides the core computational operations of the human language faculty (e.g. Merge, Move) by reading 
a list of words from the PF-interface. The model has been developed within the framework of the minimalist grammar (Chomsky, 1995, 2000, 2008).

## Authors

The program was created in connection with a research project led by Prof. Cristiano Chesi (IUSS, Pavia). This version was designed 
and programmed by Pauli Brattico with some code contributed by Jukka Purma.

## Requirements

Parser-grammar requires Python 3.6 or later. In following, it is assumed that python-interpreter is run with command `python3`. Depending on your environment, it may be `py3` (Windows) or just `python` or `py` (if there are no python 2.x frameworkds present). 

The parser itself could be easily converted to run with older versions of Python, 3.6 is required because it allows easier creation of logging strings with f-strings. 

## Running

To run an example parse set, cd to this directory and:

    python3 run_example.py
    
This will run the parser with sentences from `test_set.txt` at the `example`-directory and write the output into the same directory.

In same manner you can run...

    python3 run_study1.py
    
 ...to recreate the study1 result files. It is recommended to have your study sets in their own directories and to make a new copy of `run_study1.py for each study. If a study requires a specific lexicon, those should be added into study-folder and referred by name in run_study-script.
 `
 You can also run parser directly with specific test set file or default example set with `parse.py`.
 
    python3 parse.py
    
 Will run the same test set as run_example and
 
    python3 parse.py myfile.txt
    
  ... will run sentences from `myfile.txt`. See any of example or study sets for format for test set files. Modify `parse.py` and run directly from it if you need more control on environment where the parser is running, but remember that changing it may affect the reproducibility of other studies.
  
  ## Preparing larger study sets
  
  There are two utility scripts:
  
  * `scramble.py` for creating all permutations of word orders for a set of sentences
  * `sample.py` for sampling a smaller random set of sentences from possibly huge set of scrambled permutations

See script files for instructions on running them.
   
 