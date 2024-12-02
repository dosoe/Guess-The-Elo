# Environment

`conda env create -f environment.yml`

# Stockfish_Path

## Steps

1) Install Stockfish (<https://stockfishchess.org/>)
2) Add environment variable `STOCKFISH_PATH`
with the path to the binary file (`.exe` on windows) of stockfish, alternatively provide the path to the binary in the code as     `stockfish_path`.

Run: `python3 main.py`


# Multiprocessing

The code runs in parallel, by default it uses all cores on your system, which might cause performance issues if you use your computer for anything else.
