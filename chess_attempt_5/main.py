# main.py

import os
import csv
import chess.pgn  # Ensure chess is imported for PGN processing
import logging
from multiprocessing import Pool, cpu_count
from analyzer import analyze_game_pgn
from engine import init_engine
import glob
from tqdm import tqdm

def setup_logging():
    """
    Sets up logging to file and console.
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Remove all handlers associated with the root logger object
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create handlers
    c_handler = logging.StreamHandler()
    f_handler = logging.FileHandler('analysis.log')

    c_handler.setLevel(logging.INFO)
    f_handler.setLevel(logging.INFO)

    # Create formatter and add it to handlers
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    c_handler.setFormatter(formatter)
    f_handler.setFormatter(formatter)

    # Add handlers to the logger
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)


def analyze_pgn_file_parallel(pgn_file_path, stockfish_path, depth=15, output_file="analysis_results.csv"):
    """
    Analyzes multiple PGN games in parallel and computes evaluations for each move.

    Parameters:
    - pgn_file_path (str): Path to the PGN file containing multiple games.
    - stockfish_path (str): Path to the Stockfish executable.
    - depth (int): The depth for Stockfish analysis.
    - output_file (str): Path to the CSV file where results will be saved.

    Outputs:
    - Writes analysis results to the specified CSV file.
    """
    logging.info(f"Starting analysis for file: {pgn_file_path}")

    # Read all PGN strings first
    pgn_strings = []
    try:
        with open(pgn_file_path, 'r', encoding='utf-8') as pgn_file:
            while True:
                game = chess.pgn.read_game(pgn_file)
                if game is None:
                    break
                # Convert the game back to PGN string
                exporter = chess.pgn.StringExporter(headers=True, variations=True, comments=True)
                pgn_str = game.accept(exporter)
                pgn_strings.append(pgn_str)
    except Exception:
        logging.exception(f"Failed to read PGN file {pgn_file_path}")
        return

    if not pgn_strings:
        logging.warning(f"No games found in the PGN file: {pgn_file_path}")
        return

    # Determine the number of worker processes
    max_workers = 10  # Use the number of CPU cores

    num_workers = min(cpu_count(), len(pgn_strings), max_workers)
    logging.info(f"Using {num_workers} worker(s) for analysis.")

    logging.info(f"Analysing {len(pgn_strings)} games.")

    # Create a pool of worker processes
    try:
        with Pool(processes=num_workers, initializer=init_engine, initargs=(stockfish_path,)) as pool:
            # Prepare arguments for each game
            args = [(pgn_str, depth) for pgn_str in pgn_strings]

            # Use starmap to pass multiple arguments to the worker function
            # results = pool.starmap(analyze_game_pgn, args)

            # result_list_tqdm = []
            # for result in tqdm(pool.imap(func=analyze_game_pgn, iterable=args), total=len(args)):
            #     result_list_tqdm.append(result)

            jobs = [pool.apply_async(func=analyze_game_pgn, args=(*argument,)) if isinstance(argument, tuple) else pool.apply_async(func=analyze_game_pgn, args=(argument,)) for argument in args]
            pool.close()
            result_list_tqdm = []
            for job in tqdm(jobs):
                result_list_tqdm.append(job.get())
    except Exception:
        logging.exception("Error during multiprocessing")
        return

    # Prepare the CSV rows
    csv_rows = []
    current_game_id = 0

    for idx, result in enumerate(result_list_tqdm, start=1):
        if result is None:
            logging.warning(f"Game {idx}: Analysis failed.")
            continue

        # Increment GameID
        current_game_id += 1

        # Extract ratings and names
        white_name = result["WhiteName"] if result["WhiteName"] != "Unknown" else ""
        black_name = result["BlackName"] if result["BlackName"] != "Unknown" else ""
        white_elo = result["WhiteElo"] if result["WhiteElo"] != "Unknown" else ""
        black_elo = result["BlackElo"] if result["BlackElo"] != "Unknown" else ""
        white_fide_id = result.get("WhiteFideId", "")
        black_fide_id = result.get("BlackFideId", "")
        # Opening and Variation
        opening = result["Opening"]
        variation = result["Variation"]

        # Year
        year = result["Year"] if result["Year"] != "Unknown" else ""
        # Result
        result_value = result["Result"] if result["Result"] != "Unknown" else ""

        # Iterate through each move and append to CSV rows
        for move in result["Moves"]:
            csv_rows.append([
                current_game_id,                          # GameID
                white_name if move["MoveNumber"] == 1 else "",   # WhiteName
                white_elo if move["MoveNumber"] == 1 else "",    # WhiteElo
                black_name if move["MoveNumber"] == 1 else "",   # BlackName
                black_elo if move["MoveNumber"] == 1 else "",    # BlackElo
                white_fide_id if move["MoveNumber"] == 1 else "",    # WhiteFideId
                black_fide_id if move["MoveNumber"] == 1 else "",    # BlackFideId
                year if move["MoveNumber"] == 1 else "",         # Year
                opening if move["MoveNumber"] == 1 else "",      # Opening
                variation if move["MoveNumber"] == 1 else "",    # Variation
                result_value if move["MoveNumber"] == 1 else "",     # Result
                move['MoveNumber'],                               # MoveNumber
                move['Move'],                                     # Move
                move['Evaluation']                                # Evaluation
            ])

        # Optional: Add a blank row or separator after each game for clarity
        csv_rows.append([""] * 12)  # Adjusted number of empty fields

        # logging.info(f"Game {current_game_id} analyzed successfully.")

    # Write to CSV
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            csv_writer = csv.writer(csvfile)
            # Write header
            csv_writer.writerow([
                "GameID",
                "WhiteName",
                "WhiteElo",
                "BlackName",
                "BlackElo",
                "WhiteFideId",
                "BlackFideId",
                "Year",
                "Opening",
                "Variation",
                "Result",
                "MoveNumber",
                "Move",
                "Evaluation"
            ])
            # Write all game data
            csv_writer.writerows(csv_rows)
        logging.info(f"Analysis complete for file: {pgn_file_path}. Results saved to {output_file}.")
    except Exception:
        logging.exception(f"Failed to write to CSV file {output_file}")
        return

def process_specific_pgn_files(specific_pgn_files, stockfish_path, depth=15, output_directory="Analyzed_Games/"):
    """
    Processes specified PGN files and analyzes each one, saving results to separate CSV files.
    
    Parameters:
    - specific_pgn_files (list): List of paths to PGN files to analyze.
    - stockfish_path (str): Path to the Stockfish executable.
    - depth (int): Depth for Stockfish analysis.
    - output_directory (str): Directory to save analyzed CSV files.
    """
    # Ensure the output directory exists
    os.makedirs(output_directory, exist_ok=True)

    for pgn_file in specific_pgn_files:
        if not os.path.exists(pgn_file):
            logging.warning(f"PGN file does not exist: {pgn_file}")
            continue

        # Define the output CSV file path based on PGN file name
        output_csv_path = os.path.join(
            output_directory,
            f"{os.path.splitext(os.path.basename(pgn_file))[0]}_{depth}_analyzed.csv"
        )
        if os.path.isfile(output_csv_path):
            logging.info(f"PGN already processed: {pgn_file}")
            continue
        
        logging.info(f"Starting analysis for file: {pgn_file}")
        
        # Start the analysis
        analyze_pgn_file_parallel(
            pgn_file_path=pgn_file,
            stockfish_path=stockfish_path,
            depth=depth,
            output_file=output_csv_path
        )
        
        logging.info(f"Completed analysis for file: {pgn_file}. Results saved to {output_csv_path}.")


if __name__ == "__main__":
    # Set up logging
    setup_logging()

    # Fetch the Stockfish path from environment variable
    stockfish_path = os.getenv('STOCKFISH_PATH') 
    
    if not stockfish_path:
        logging.error("STOCKFISH_PATH environment variable is not set.")
        exit(1)
    
    # Define the list of specific PGN files directly
    specific_pgn_files = [f"utf8_games/twic{num}.pgn" for num in range(1466, 1479 + 1)]
    #specific_pgn_files = ["test2.pgn"]

    # Specify the output directory for analyzed CSV files
    output_directory = "Analyzed_Games"
    
    # Specify the depth for Stockfish analysis
    analysis_depth = 16  # Adjust based on your requirements and system capabilities
    
    # Start processing specific PGN files
    process_specific_pgn_files(
        specific_pgn_files=specific_pgn_files,
        stockfish_path=stockfish_path,
        depth=analysis_depth,  
        output_directory=output_directory
    )
