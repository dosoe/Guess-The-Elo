# analyzer.py

import chess.pgn
from io import StringIO
import engine  # Import the engine module

def analyze_game_pgn(pgn_string, depth=15):
    """
    Analyzes a single PGN game string and computes CPL metrics and evaluations.

    Parameters:
    - pgn_string (str): The PGN string of the game.
    - depth (int): The depth for Stockfish analysis.

    Returns:
    - dict: Analysis results containing CPL metrics, evaluations, and game information.
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

        # Extract year from date
        if date != "Unknown" and len(date) >= 4:
            year = date[:4]
        else:
            year = "Unknown"

        cpl_white = []
        cpl_black = []
        moves = []

        board = game.board()
        move_number = 1

        for move in game.mainline_moves():
            # Record the move
            san_move = board.san(move)

            # Keep track of the player who is about to move
            current_player = board.turn

            # Analyze the position before the move
            if engine.engine is None:
                print("Engine is not initialized.")
                return None

            try:
                # Best move evaluation for CPL calculation
                best_info = engine.engine.analyse(board, chess.engine.Limit(depth=depth))
                best_score = best_info["score"].pov(current_player)

                # Played move evaluation for CPL calculation
                played_info = engine.engine.analyse(board, chess.engine.Limit(depth=depth), root_moves=[move])
                played_score = played_info["score"].pov(current_player)
            except Exception as e:
                print(f"Error during Stockfish analysis: {e}")
                return None

            # Compute centipawn loss (CPL)
            if best_score.is_mate() or played_score.is_mate():
                current_cpl = 0  # Handle mate cases separately if needed
            else:
                best_move_eval = best_score.score()
                played_eval = played_score.score()
                current_cpl = abs(best_move_eval - played_eval)

            # Assign CPL to the player who just moved
            if current_player == chess.WHITE:
                cpl_white.append(current_cpl)
            else:
                cpl_black.append(current_cpl)

            # Get evaluation after the move from White's perspective
            # Use the evaluation from the 'played_info' after the move is made
            # Since 'played_info' is the evaluation after the move, we can get it directly
            evaluation_score = played_info["score"].pov(chess.WHITE)
            if evaluation_score.is_mate():
                mate_in = evaluation_score.mate()
                if mate_in > 0:
                    evaluation_after_move = f"M{mate_in}"  # White is mating in mate_in moves
                else:
                    evaluation_after_move = f"-M{abs(mate_in)}"  # Black is mating in abs(mate_in) moves
            else:
                # Convert centipawns to pawns by dividing by 100
                evaluation_after_move = evaluation_score.score() / 100.0  # Now in pawns

            # Append the move data to the moves list
            moves.append({
                "MoveNumber": move_number,
                "Move": san_move,
                "CPL": current_cpl,
                "Evaluation": evaluation_after_move
            })

            # Make the move
            board.push(move)
            move_number += 1

        # Compute average CPL per player
        avg_cpl_white = round(sum(cpl_white) / len(cpl_white), 2) if cpl_white else 0
        avg_cpl_black = round(sum(cpl_black) / len(cpl_black), 2) if cpl_black else 0

        # Prepare results
        results = {
            "WhiteName": white_name,
            "BlackName": black_name,
            "Year": year,
            "WhiteElo": white_rating,
            "BlackElo": black_rating,
            "Opening": opening,
            "Variation": variation,
            "Moves": moves,
            "Average_CPL_White": avg_cpl_white,
            "Average_CPL_Black": avg_cpl_black
        }

        return results

    except Exception as e:
        print(f"Error analyzing game: {e}")
        return None
