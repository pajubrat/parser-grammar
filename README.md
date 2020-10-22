Linear phase parser
Pauli Brattico
2020

The linear phase parser analyses language by simulating human language comprehension. The program was originally created at IUSS, Pavia, in a research project "ProGraM-PC: A Processing-friendly Grammatical Model for Parsing and predicting on-line Complexity".

To run the program, you must have python installed and configured at your local machine. After cloning the repository, type 'python lpparse' into command prompt inside the folder where the package is installed. This command will process all sentences from a test corpus file. The test corpus file and its path are defined inside config.txt. See /docs for documentation.

To generate phrase structure images, you need the pyglet package at the local machine. To install it, write 'pip install pyglet' in the command prompt or see the pyglet installation instructions. To generate images, use command 'python lpparse /images'.

