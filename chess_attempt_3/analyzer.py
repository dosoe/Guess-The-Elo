# analyzer.py

import chess.pgn
from io import StringIO
import engine  # Import the engine module

def analyze_game_pgn(pgn_string, depth=15):
    """
    Analyzes a single PGN game string and computes CPL metrics.

    Parameters:
    - pgn_string (str): The PGN string of the game.
    - depth (int): The depth for Stockfish analysis.

    Returns:
    - dict: Analysis results containing CPL metrics and game information.
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
            moves.append(san_move)

            # Analyze the position before the move
            if engine.engine is None:
                print("Engine is not initialized.")
                return None

            try:
                best_info = engine.engine.analyse(board, chess.engine.Limit(depth=depth))
                best_move_eval = best_info["score"].pov(board.turn).score(mate_score=100000)

                # Get the evaluation of the move played
                played_info = engine.engine.analyse(board, chess.engine.Limit(depth=depth), root_moves=[move])
                played_eval = played_info["score"].pov(board.turn).score(mate_score=100000)
            except Exception as e:
                print(f"Error during Stockfish analysis: {e}")
                return None

            # Compute centipawn loss
            if best_move_eval is not None and played_eval is not None:
                current_cpl = abs(best_move_eval - played_eval)
            else:
                current_cpl = 0

            # Corrected CPL Assignment:
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
            "WhiteName": white_name,
            "BlackName": black_name,
            "Year": year,
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
