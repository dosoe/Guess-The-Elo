import chess
import chess.engine
import chess.pgn
from multiprocessing import Pool, cpu_count
from io import StringIO
import os
import csv
from tqdm import tqdm  # Import tqdm for progress bar

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

        cpl_white = []
        cpl_black = []
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

            # **Corrected CPL Assignment:**
            # board.turn represents the player who is about to move.
            # Therefore, the CPL should be assigned to the player who just moved,
            # which is the opposite of board.turn.
            if board.turn == chess.WHITE:
                cpl_black.append(current_cpl)
            else:
                cpl_white.append(current_cpl)

            # Make the move
            board.push(move)
            move_number += 1

        # Compute average CPL per player
        avg_cpl_white = round(sum(cpl_white) / len(cpl_white), 2) if cpl_white else 0
        avg_cpl_black = round(sum(cpl_black) / len(cpl_black), 2) if cpl_black else 0

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
                    "CPL": cpl_white[idx // 2] if (idx % 2 == 1) else cpl_black[idx // 2]
                }
                for idx, move in enumerate(moves)
            ],
            "Average_CPL_White": avg_cpl_white,
            "Average_CPL_Black": avg_cpl_black
        }

        return results

    except Exception as e:
        print(f"Error analyzing game: {e}")
        return None

def analyze_game_pgn_helper(args):
    """
    Helper function to unpack arguments for analyze_game_pgn.
    
    Parameters:
    - args (tuple): Tuple containing (pgn_string, depth)
    
    Returns:
    - dict: Analysis results
    """
    return analyze_game_pgn(*args)

def analyze_pgn_file_parallel(pgn_file_path, stockfish_path, depth=15, output_file="analysis_results.csv"):
    """
    Analyzes multiple PGN games in parallel and computes CPL metrics for each.

    Parameters:
    - pgn_file_path (str): Path to the PGN file containing multiple games.
    - stockfish_path (str): Path to the Stockfish executable.
    - depth (int): The depth for Stockfish analysis.
    - output_file (str): Path to the CSV file where results will be saved.

    Outputs:
    - Writes analysis results to the specified CSV file.
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

        # Use imap_unordered with the helper function and wrap with tqdm for progress bar
        results = pool.imap_unordered(analyze_game_pgn_helper, args)

        # Initialize list to store CSV rows
        csv_rows = []
        current_game_id = 0

        # Iterate through results with tqdm
        for result in tqdm(results, total=len(args), desc="Analyzing Games"):
            if result is None:
                print(f"Game {current_game_id + 1}: Analysis failed.\n-----------------------------\n")
                current_game_id += 1
                continue

            # Increment GameID
            current_game_id += 1

            # Extract ratings
            white_elo = result["WhiteElo"] if result["WhiteElo"] != "Unknown" else ""
            black_elo = result["BlackElo"] if result["BlackElo"] != "Unknown" else ""

            # Opening and Variation
            opening = result["Opening"]
            variation = result["Variation"]

            # Calculate ACPL as the average of white and black ACPLs
            acpl = round((result["Average_CPL_White"] + result["Average_CPL_Black"]) / 2, 2)

            # Iterate through each move and append to CSV rows
            for move in result["Moves"]:
                csv_rows.append([
                    current_game_id,    # GameID
                    white_elo if move["MoveNumber"] == 1 else "",   # WhiteElo
                    black_elo if move["MoveNumber"] == 1 else "",   # BlackElo
                    opening if move["MoveNumber"] == 1 else "",     # Opening
                    variation if move["MoveNumber"] == 1 else "",   # Variation
                    acpl if move["MoveNumber"] == 1 else "",        # ACPL
                    move['MoveNumber'],   # MoveNumber
                    move['Move'],         # Move
                    move['CPL']           # CPL
                ])
                # No need to clear variables since we already set them only for the first move

            # Optional: Add a blank row or separator after each game for clarity
            csv_rows.append([current_game_id + 1, "", "", "", "", "", "", "", ""])  # Adds a blank row

    # Write to CSV after all games are processed
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        # Write header
        csv_writer.writerow(["GameID", "WhiteElo", "BlackElo", "Opening", "Variation", "ACPL", "MoveNumber", "Move", "CPL"])
        # Write all game data
        csv_writer.writerows(csv_rows)

    print(f"Analysis complete. Results saved to {output_file}.")

if __name__ == "__main__":
    # Specify the path to your Stockfish executable
    stockfish_path = r"C:\Users\foivo\Downloads\stockfish-windows-x86-64-avx2\stockfish\stockfish-windows-x86-64-avx2.exe"
    
    # Specify the path to your PGN file
    pgn_file_path = "Games/example3.pgn"
    
    # Specify the desired output CSV file path
    output_csv_path = "Analyzed_Games/test.csv"
    
    # Start the analysis
    analyze_pgn_file_parallel(
        pgn_file_path,
        stockfish_path,
        depth=14,
        output_file=output_csv_path  # Specify your desired output file path
    )
