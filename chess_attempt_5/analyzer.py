# analyzer.py

import chess.pgn
from io import StringIO
import engine  # Import the engine module

def analyze_game_pgn(pgn_string, depth=15):
    """
    Analyzes a single PGN game string and computes evaluations after each move.

    Parameters:
    - pgn_string (str): The PGN string of the game.
    - depth (int): The depth for Stockfish analysis.

    Returns:
    - dict: Analysis results containing evaluations and game information.
    """
    try:
        game = chess.pgn.read_game(StringIO(pgn_string))
        if game is None:
            return None

        # Extract information
        white_name = game.headers.get("White", "Unknown")
        black_name = game.headers.get("Black", "Unknown")
        white_rating = game.headers.get("WhiteElo", "Unknown")
        black_rating = game.headers.get("BlackElo", "Unknown")
        opening = game.headers.get("Opening", "Unknown")
        variation = game.headers.get("Variation", "Unknown")
        date = game.headers.get("Date", "Unknown")
        result_value = game.headers.get("Result", "Unknown")
        # Extract year from date
        if date != "Unknown" and len(date) >= 4:
            year = date[:4]
        else:
            year = "Unknown"

        moves = []

        board = game.board()
        move_number = 1

        for move in game.mainline_moves():
            # Record the move
            san_move = board.san(move)

            # Make the move
            board.push(move)

            # Analyze the position after the move
            if engine.engine is None:
                print("Engine is not initialized.")
                return None

            try:
                # Analyze the position after the move
                info = engine.engine.analyse(board, chess.engine.Limit(depth=depth))
                score = info["score"].pov(chess.WHITE)
            except Exception as e:
                print(f"Error during Stockfish analysis: {e}")
                return None

            # Get evaluation after the move from White's perspective
            if score.is_mate():
                mate_in = score.mate()
                if mate_in > 0:
                    evaluation_after_move = f"M{mate_in}"  # White is mating in mate_in moves
                else:
                    evaluation_after_move = f"-M{abs(mate_in)}"  # Black is mating in abs(mate_in) moves
            else:
                # Convert centipawns to pawns by dividing by 100
                evaluation_after_move = score.score() / 100.0  # Now in pawns

            # Append the move data to the moves list
            moves.append({
                "MoveNumber": move_number,
                "Move": san_move,
                "Evaluation": evaluation_after_move
            })

            move_number += 1

        # Prepare results
        results = {
            "WhiteName": white_name,
            "BlackName": black_name,
            "Year": year,
            "WhiteElo": white_rating,
            "BlackElo": black_rating,
            "Opening": opening,
            "Variation": variation,
            "Result": result_value,
            "Moves": moves
        }

        return results

    except Exception as e:
        print(f"Error analyzing game: {e}")
        return None
