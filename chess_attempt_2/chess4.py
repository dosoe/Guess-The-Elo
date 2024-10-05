import chess
import chess.engine
import chess.pgn
from multiprocessing import Pool, cpu_count
from io import StringIO
import os
import json

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
    # Optionally, set engine options here
    engine.configure({"Threads": 1, "Hash": 128})  # Example configuration

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

        cpl = []
        moves = []

        board = game.board()
        move_number = 1

        for move in game.mainline_moves():
            # Record the move
            san_move = board.san(move)
            moves.append(san_move)

            # Analyze the position before the move
            best_info = engine.analyse(board, chess.engine.Limit(depth=depth))
            best_move_eval = best_info["score"].pov(board.turn).score(mate_score=100000)

            # Get the evaluation of the move played
            played_info = engine.analyse(board, chess.engine.Limit(depth=depth), root_moves=[move])
            played_eval = played_info["score"].pov(board.turn).score(mate_score=100000)

            # Compute centipawn loss
            if best_move_eval is not None and played_eval is not None:
                current_cpl = abs(best_move_eval - played_eval)
            else:
                current_cpl = 0

            cpl.append(current_cpl)

            # Make the move
            board.push(move)
            move_number += 1

        # Compute average CPL per player
        # Assuming even-indexed moves are White and odd-indexed are Black
        cpl_white = cpl[::2]  # White moves: indices 0,2,4,...
        cpl_black = cpl[1::2]  # Black moves: indices 1,3,5,...

        avg_cpl_white = sum(cpl_white) / len(cpl_white) if cpl_white else 0
        avg_cpl_black = sum(cpl_black) / len(cpl_black) if cpl_black else 0

        # Prepare results
        results = {
            "WhiteElo": white_rating,
            "BlackElo": black_rating,
            "Opening": opening,
            "Variation": variation,
            "Moves": [
                {
                    "MoveNumber": idx + 1,
                    "Move": move,
                    "CPL": cpl_value
                }
                for idx, (move, cpl_value) in enumerate(zip(moves, cpl))
            ],
            "Average_CPL_White": avg_cpl_white,
            "Average_CPL_Black": avg_cpl_black
        }

        return results

    except Exception as e:
        print(f"Error analyzing game: {e}")
        return None

def analyze_pgn_file_parallel(pgn_file_path, stockfish_path, depth=15, show_move_cpl=False, output_file="analysis_results.json"):
    """
    Analyzes multiple PGN games in parallel and computes CPL metrics for each.

    Parameters:
    - pgn_file_path (str): Path to the PGN file containing multiple games.
    - stockfish_path (str): Path to the Stockfish executable.
    - depth (int): The depth for Stockfish analysis.
    - show_move_cpl (bool): Whether to include CPL per move in the output.
    - output_file (str): Path to the JSON file where results will be saved.

    Outputs:
    - Writes analysis results to the specified JSON file.
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

    if not pgn_strings:
        print("No games found in the PGN file.")
        return

    # Determine the number of worker processes
    num_workers = min(cpu_count(), len(pgn_strings))
    print(f"Starting analysis with {num_workers} worker(s)...")

    # Create a pool of worker processes
    with Pool(processes=num_workers, initializer=init_engine, initargs=(stockfish_path,)) as pool:
        # Prepare arguments for each game
        args = [(pgn_str, depth) for pgn_str in pgn_strings]

        # Use starmap to pass multiple arguments to the worker function
        results = pool.starmap(analyze_game_pgn, args)

    # Prepare the final output data
    output_data = []
    for idx, result in enumerate(results, start=1):
        if result is None:
            print(f"Game {idx}: Analysis failed.\n-----------------------------\n")
            continue
        game_data = {
            "GameNumber": idx,
            "WhiteElo": result["WhiteElo"],
            "BlackElo": result["BlackElo"],
            "Opening": result["Opening"],
            "Variation": result["Variation"],
            "Moves": result["Moves"],
            "Average_CPL_White": result["Average_CPL_White"],
            "Average_CPL_Black": result["Average_CPL_Black"]
        }

        # Append move CPLs regardless of player
        # If you want to hide CPL per move when show_move_cpl is False, you can skip this
        if show_move_cpl:
            game_data["MoveCPL"] = [
                {
                    "MoveNumber": move["MoveNumber"],
                    "Move": move["Move"],
                    "CPL": move["CPL"]
                }
                for move in result["Moves"]
            ]

        # To simplify, you can exclude the 'Moves' list and only include 'MoveCPL'
        # But keeping both for flexibility

        # Alternatively, restructure 'MoveCPL' to match the desired output
        # e.g., list of strings like "1: c4 - 20"

        # Here's how to adjust it:
        simplified_moves = [
            f"{move['MoveNumber']}: {move['Move']} - {move['CPL']}"
            for move in result["Moves"]
        ]
        game_data["SimplifiedMoves"] = simplified_moves

        output_data.append(game_data)

    # Write the output data to a JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=4)

    print(f"Analysis complete. Results saved to {output_file}.")

if __name__ == "__main__":
    stockfish_path = r"C:\Users\foivo\Downloads\stockfish-windows-x86-64-avx2\stockfish\stockfish-windows-x86-64-avx2.exe"
    pgn_file_path = "Games/twic1560.pgn"
    analyze_pgn_file_parallel(
        pgn_file_path,
        stockfish_path,
        depth=13,
        show_move_cpl=False,  # Set to True if you want detailed CPL per move
        output_file="analyzed_twic1560.json"  # Specify your desired output file path
    )
