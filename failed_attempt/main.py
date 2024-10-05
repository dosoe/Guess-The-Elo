# main.py

import multiprocessing
from analysis import analyze_pgn_file
import sys

if __name__ == '__main__':
    multiprocessing.set_start_method('spawn')  # Important for Windows

    # Paths to the Stockfish engine and PGN file
    stockfish_path = r"C:\Users\foivo\Downloads\stockfish-windows-x86-64-avx2\stockfish\stockfish-windows-x86-64-avx2.exe"
    pgn_file = "example2.pgn"

    # Analyze the PGN file
    games_analysis = analyze_pgn_file(pgn_file, stockfish_path)

    # Example: Print the analysis of the first game
    if games_analysis:
        first_game = games_analysis[0]
        if first_game is not None:
            print(f"\nWhite Elo: {first_game['white_elo']}, Black Elo: {first_game['black_elo']}, Result: {first_game['result']}")
            for move_eval in first_game['evaluations']:
                print(f"Move {move_eval['move_number']}: {move_eval['move']}, CPL: {move_eval['cpl']:.2f} pawns, Win%: {move_eval['win_percent']:.2f}%, Accuracy: {move_eval['accuracy']:.2f}%")
            print(f"\nWhite ACPL: {first_game['white_acpl']:.2f} pawns, Accuracy: {first_game['white_accuracy_percent']:.2f}%")
            print(f"Black ACPL: {first_game['black_acpl']:.2f} pawns, Accuracy: {first_game['black_accuracy_percent']:.2f}%")
        else:
            print("First game analysis returned None.")
    else:
        print("No game analysis was performed.")


