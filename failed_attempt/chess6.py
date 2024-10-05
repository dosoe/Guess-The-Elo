import chess.pgn
import chess.engine
import multiprocessing
import io
import math  # Needed for exponential calculations

def eval_to_score(eval):
    if eval.is_mate():
        mate_in = eval.mate()
        # Assign a large positive or negative value for mate scores
        if mate_in > 0:
            return 100000  # Mate in N moves (winning)
        else:
            return -100000  # Getting mated in N moves (losing)
    else:
        return eval.score()

def winning_chances(cp):
    """
    Convert centipawn evaluation to a value between -1 and 1 representing win chances.
    Positive cp favors White; negative cp favors Black.
    """
    MULTIPLIER = -0.00368208  # Derived from empirical data
    value = 2 / (1 + math.exp(MULTIPLIER * cp)) - 1
    value = max(-1, min(1, value))  # Clamp between -1 and +1
    return value

def win_percent(cp):
    """
    Convert centipawn evaluation to win percentage between 0% and 100%.
    """
    chances = winning_chances(cp)
    win_percentage = 50 + 50 * chances
    win_percentage = max(0, min(100, win_percentage))  # Clamp between 0% and 100%
    return win_percentage

def analyze_single_game(game_data):
    game_text, engine_path = game_data
    print("Analyzing a game...")  # Logging for debugging

    # Parse the game from PGN text
    game = chess.pgn.read_game(io.StringIO(game_text))
    if game is None:
        print("Game is None")
        return None  # Handle empty or invalid games

    board = game.board()

    # Load the chess engine
    try:
        engine = chess.engine.SimpleEngine.popen_uci(engine_path)
    except Exception as e:
        print(f"Engine failed to start: {e}")
        return None
    # Configure the engine
    engine.configure({'Threads': 1, 'Hash': 128})

    # Extract Elo ratings and result
    white_elo = int(game.headers.get("WhiteElo", "0"))
    black_elo = int(game.headers.get("BlackElo", "0"))
    result = game.headers.get("Result", "*")

    move_number = 1
    evaluations = []
    white_cpls = []
    black_cpls = []

    node = game  # Start from the root node

    while not node.is_end():
        try:
            # Get the next move
            next_node = node.variation(0)
            move = next_node.move

            # Get SAN notation before pushing the move
            move_san = board.san(move)

            # Determine whose turn it is
            player_color = board.turn  # True for White, False for Black
            player = 'White' if player_color else 'Black'
            color_factor = 1 if player_color else -1

            # Get the engine's recommended move and its evaluation
            info_best = engine.analyse(board, chess.engine.Limit(depth=12))
            best_move = info_best["pv"][0]
            eval_best = info_best["score"].white()  # Evaluation from White's perspective

            # Apply the best move on a copy of the board
            board_best = board.copy()
            board_best.push(best_move)
            info_after_best = engine.analyse(board_best, chess.engine.Limit(depth=0))
            eval_after_best = info_after_best["score"].white()

            # Apply the player's move to the board
            board.push(move)

            # Get the evaluation after the player's move
            info_after_move = engine.analyse(board, chess.engine.Limit(depth=0))
            eval_after_move = info_after_move["score"].white()

            # Convert evaluations to centipawn scores
            eval_after_best_cp = eval_to_score(eval_after_best)
            eval_after_move_cp = eval_to_score(eval_after_move)

            # Compute CPL = (eval_after_best - eval_after_move) * color_factor
            delta_e = (eval_after_best_cp - eval_after_move_cp) * color_factor

            # If delta_e negative, set to zero
            if delta_e < 0:
                delta_e = 0

            # Adjust eval_after_move_cp for player's perspective
            if player_color:  # White
                eval_after_move_cp_player = eval_after_move_cp
            else:  # Black
                eval_after_move_cp_player = -eval_after_move_cp

            # Compute win percentage after the player's move
            win_percent_player = win_percent(eval_after_move_cp_player)

            # Append delta_e to the appropriate list
            if player_color:
                white_cpls.append(delta_e)
            else:
                black_cpls.append(delta_e)

            # Collect the move, CPL, and win percentage
            evaluations.append({
                'move_number': move_number,
                'move': move_san,
                'cpl': delta_e / 100,  # Convert to pawns
                'win_percent': win_percent_player
            })

            print(f"Move {move_number}: {player} played {move_san}, CPL: {delta_e / 100:.2f} pawns, Win%: {win_percent_player:.2f}%")

            move_number += 1
            node = next_node

        except Exception as e:
            print(f"Error processing move {move_number}: {str(e)}")
            engine.quit()
            return None

    engine.quit()

    # Compute ACPL for each player
    if white_cpls:
        white_acpl = sum(white_cpls) / len(white_cpls) / 100  # Convert to pawns
    else:
        white_acpl = None

    if black_cpls:
        black_acpl = sum(black_cpls) / len(black_cpls) / 100  # Convert to pawns
    else:
        black_acpl = None

    print(f"\nWhite ACPL: {white_acpl:.2f} pawns")
    print(f"Black ACPL: {black_acpl:.2f} pawns")

    return {
        'white_elo': white_elo,
        'black_elo': black_elo,
        'result': result,
        'evaluations': evaluations,
        'white_acpl': white_acpl,
        'black_acpl': black_acpl
    }

def read_games_from_pgn(pgn_file):
    games = []
    with open(pgn_file) as pgn:
        while True:
            game = chess.pgn.read_game(pgn)
            if game is None:
                break
            # Convert the game back to PGN text
            exporter = chess.pgn.StringExporter(headers=True, variations=False, comments=False)
            game_text = game.accept(exporter)
            games.append(game_text)
    return games

def analyze_pgn_file(pgn_file, engine_path):
    # Read all games from the PGN file
    games_text = read_games_from_pgn(pgn_file)
    # Prepare data for multiprocessing
    game_data_list = [(game_text, engine_path) for game_text in games_text]

    if not game_data_list:
        print("No games found in the PGN file.")
        return []

    # Determine the number of processes to use
    cpu_count = multiprocessing.cpu_count()
    num_processes = min(cpu_count, len(game_data_list))

    print(f"Starting analysis with {num_processes} processes...")  # Logging

    # Use multiprocessing to analyze games in parallel
    with multiprocessing.Pool(processes=num_processes) as pool:
        results = pool.map(analyze_single_game, game_data_list)

    return results

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
                print(f"Move {move_eval['move_number']}: {move_eval['move']}, CPL: {move_eval['cpl']:.2f} pawns, Win%: {move_eval['win_percent']:.2f}%")
            print(f"\nWhite ACPL: {first_game['white_acpl']:.2f} pawns")
            print(f"Black ACPL: {first_game['black_acpl']:.2f} pawns")
        else:
            print("First game analysis returned None.")
    else:
        print("No game analysis was performed.")
