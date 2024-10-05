# analysis.py

import chess.pgn
import chess.engine
import io
import multiprocessing
import numpy as np  # For standard deviation and harmonic mean
from utils import eval_to_score, win_percent, accuracy_from_win_percents, harmonic_mean  # Import utility functions

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
    # Collect move accuracies and weights
    white_accuracies_weights = []
    black_accuracies_weights = []
    # Collect win percentages and move accuracies
    all_win_percents = [50.0]  # Start with 50% at the beginning
    move_accuracies = []
    move_colors = []  # True for White, False for Black

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
            info_best = engine.analyse(board, chess.engine.Limit(depth=20))
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

            # Append the win percentage
            all_win_percents.append(win_percent_player)

            # Compute accuracy percentage for the move
            prev_win_percent = all_win_percents[-2]
            move_accuracy = accuracy_from_win_percents(prev_win_percent, win_percent_player)

            # Collect move accuracies and colors
            move_accuracies.append(move_accuracy)
            move_colors.append(player_color)  # True for White, False for Black

            # Append delta_e to the appropriate list
            if player_color:
                white_cpls.append(delta_e)
            else:
                black_cpls.append(delta_e)

            # Collect the move, CPL, win percentage, and accuracy
            evaluations.append({
                'move_number': move_number,
                'move': move_san,
                'cpl': delta_e / 100,  # Convert to pawns
                'win_percent': win_percent_player,
                'accuracy': move_accuracy
            })

            print(f"Move {move_number}: {player} played {move_san}, CPL: {delta_e / 100:.2f} pawns, Win%: {win_percent_player:.2f}%, Accuracy: {move_accuracy:.2f}%")

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

    # Compute accuracy percentages using Lichess's method

    # Compute the window size for volatility calculation
    num_moves = len(move_accuracies)
    window_size = max(2, min(8, num_moves // 10))

    # Prepare the list of win percentages for volatility calculation
    win_percent_values = all_win_percents

    # Generate windows of win percentages
    win_percent_windows = []
    for i in range(len(win_percent_values) - 1):
        start_idx = max(0, i - window_size + 1)
        window = win_percent_values[start_idx:i+2]  # Include current and next win percent
        win_percent_windows.append(window)

    # Compute weights based on standard deviation
    move_weights = []
    for window in win_percent_windows:
        std_dev = np.std(window)
        weight = max(0.5, min(12.0, std_dev))
        move_weights.append(weight)

    # Collect accuracies and weights per player
    white_accuracies_weights = []
    black_accuracies_weights = []

    for i in range(len(move_accuracies)):
        accuracy = move_accuracies[i]
        weight = move_weights[i]
        player_color = move_colors[i]
        if player_color:
            white_accuracies_weights.append((accuracy, weight))
        else:
            black_accuracies_weights.append((accuracy, weight))

    # Compute weighted mean and harmonic mean for each player
    def compute_player_accuracy(accuracies_weights):
        if not accuracies_weights:
            return None
        accuracies = [aw[0] for aw in accuracies_weights]
        weights = [aw[1] for aw in accuracies_weights]
        # Weighted mean
        weighted_sum = sum(a * w for a, w in accuracies_weights)
        total_weight = sum(weights)
        weighted_mean = weighted_sum / total_weight if total_weight != 0 else 0
        # Harmonic mean
        harmonic_mean_value = harmonic_mean(accuracies)
        # Final accuracy
        final_accuracy = (weighted_mean + harmonic_mean_value) / 2
        return final_accuracy

    white_accuracy_percent = compute_player_accuracy(white_accuracies_weights)
    black_accuracy_percent = compute_player_accuracy(black_accuracies_weights)

    print(f"\nWhite ACPL: {white_acpl:.2f} pawns, Accuracy: {white_accuracy_percent:.2f}%")
    print(f"Black ACPL: {black_acpl:.2f} pawns, Accuracy: {black_accuracy_percent:.2f}%")

    return {
        'white_elo': white_elo,
        'black_elo': black_elo,
        'result': result,
        'evaluations': evaluations,
        'white_acpl': white_acpl,
        'black_acpl': black_acpl,
        'white_accuracy_percent': white_accuracy_percent,
        'black_accuracy_percent': black_accuracy_percent
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
