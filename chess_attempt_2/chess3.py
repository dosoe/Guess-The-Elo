import chess
import chess.engine
import chess.pgn
from multiprocessing import Pool, cpu_count
from io import StringIO
import os

# Global variable for the engine in each worker
engine = None

def init_engine(stockfish_path):
    """
    Initializer for each worker process. Starts the Stockfish engine.
    """
    global engine
    if not os.path.exists(stockfish_path):
        raise FileNotFoundError(f"Stockfish executable not found at {stockfish_path}")
    engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)

def analyze_game_pgn(pgn_string, depth=15):
    """
    Analyzes a single PGN game string and computes CPL metrics.

    Parameters:
    - pgn_string (str): The PGN string of the game.
    - depth (int): The depth for Stockfish analysis.

    Returns:
    - dict: Analysis results containing CPL metrics and game information.
    """
    global engine
    try:
        game = chess.pgn.read_game(StringIO(pgn_string))
        if game is None:
            return None

        # Extract information
        white_rating = game.headers.get("WhiteElo", "Unknown")
        black_rating = game.headers.get("BlackElo", "Unknown")
        opening = game.headers.get("Opening", "Unknown")
        variation = game.headers.get("Variation", "Unknown")

        cpl_white = []
        cpl_black = []

        board = game.board()

        for move in game.mainline_moves():
            # Analyze the position before the move
            best_info = engine.analyse(board, chess.engine.Limit(depth=depth))
            best_move_eval = best_info["score"].pov(board.turn).score(mate_score=100000)

            # Get the evaluation of the move played
            played_info = engine.analyse(board, chess.engine.Limit(depth=depth), root_moves=[move])
            played_eval = played_info["score"].pov(board.turn).score(mate_score=100000)

            # Compute centipawn loss
            if best_move_eval is not None and played_eval is not None:
                cpl = abs(best_move_eval - played_eval)
            else:
                cpl = 0

            # Assign CPL to the player who made the move
            if board.turn == chess.WHITE:
                cpl_white.append(cpl)
            else:
                cpl_black.append(cpl)

            # Make the move
            board.push(move)

        # Compute average CPL per player
        avg_cpl_white = sum(cpl_white) / len(cpl_white) if cpl_white else 0
        avg_cpl_black = sum(cpl_black) / len(cpl_black) if cpl_black else 0

        # Prepare results
        results = {
            "WhiteElo": white_rating,
            "BlackElo": black_rating,
            "Opening": opening,
            "Variation": variation,
            "CPL_White": cpl_white,
            "CPL_Black": cpl_black,
            "Average_CPL_White": avg_cpl_white,
            "Average_CPL_Black": avg_cpl_black
        }

        return results

    except Exception as e:
        print(f"Error analyzing game: {e}")
        return None

def analyze_pgn_file_parallel(pgn_file_path, stockfish_path, depth=15, show_move_cpl=False):
    """
    Analyzes multiple PGN games in parallel and computes CPL metrics for each.

    Parameters:
    - pgn_file_path (str): Path to the PGN file containing multiple games.
    - stockfish_path (str): Path to the Stockfish executable.
    - depth (int): The depth for Stockfish analysis.
    - show_move_cpl (bool): Whether to display CPL per move.

    Outputs:
    - Prints analysis results for each game.
    """
    # Read all PGN strings first
    with open(pgn_file_path, 'r', encoding='utf-8') as pgn_file:
        pgn_strings = []
        while True:
            game = chess.pgn.read_game(pgn_file)
            if game is None:
                break
            # Convert the game back to PGN string
            exporter = chess.pgn.StringExporter(headers=True, variations=True, comments=True)
            pgn_str = game.accept(exporter)
            pgn_strings.append(pgn_str)

    # Determine the number of worker processes
    num_workers = min(cpu_count(), len(pgn_strings))
    print(f"Starting analysis with {num_workers} worker(s)...")

    # Create a pool of worker processes
    with Pool(processes=num_workers, initializer=init_engine, initargs=(stockfish_path,)) as pool:
        # Prepare arguments for each game
        args = [(pgn_str, depth) for pgn_str in pgn_strings]

        # Use starmap to pass multiple arguments to the worker function
        results = pool.starmap(analyze_game_pgn, args)

    # Output the results
    for idx, result in enumerate(results, start=1):
        if result is None:
            print(f"Game {idx}: Analysis failed.\n-----------------------------\n")
            continue
        print(f"Game {idx}:")
        print("White rating:", result["WhiteElo"])
        print("Black rating:", result["BlackElo"])
        print("Opening:", result["Opening"])
        print("Variation:", result["Variation"])

        if show_move_cpl:
            print("CPL per move:")
            move_number = 1
            for i in range(max(len(result["CPL_White"]), len(result["CPL_Black"]))):
                if i < len(result["CPL_White"]):
                    print(f"Move {move_number} (White): {result['CPL_White'][i]}")
                    move_number += 1
                if i < len(result["CPL_Black"]):
                    print(f"Move {move_number} (Black): {result['CPL_Black'][i]}")
                    move_number += 1

        print("Average CPL for White:", result["Average_CPL_White"])
        print("Average CPL for Black:", result["Average_CPL_Black"])
        print("\n-----------------------------\n")

    print("Analysis complete.")

if __name__ == "__main__":
    stockfish_path = r"C:\Users\foivo\Downloads\stockfish-windows-x86-64-avx2\stockfish\stockfish-windows-x86-64-avx2.exe"
    pgn_file_path = "Games/example3.pgn"
    analyze_pgn_file_parallel(pgn_file_path, stockfish_path, depth=13, show_move_cpl=False)



