# Environment: 
Type: conda env create -f environment.yml
# Stockfish_Path:
Steps: 
1) Install Stockfish
2) Edit Environmental variables: On User variables add new: Name: STOCKFISH_PATH 
and then add the path to the .exe file of stockfish
# Multiprocessing
Setting number of workers to be your cpu.count() will make the computer really slow. Use it only at night. During the day you can use number of workers to be 8 or something.
