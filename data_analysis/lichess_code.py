
import pandas as pd
import numpy as np


def cp_to_win_percent(cp):
    """
    Convert centipawn evaluation to win percentage using the Lichess formula.

    Parameters:
    cp (float or np.array): Centipawn evaluation(s)

    Returns:
    float or np.array: Win percentage(s)
    """
    # Ensure cp is a NumPy array for vectorized operations
    cp = np.array(cp)
    
    # Apply the Lichess formula
    win_percent = 50 + 50 * (2 / (1 + np.exp(-0.00368208 * cp)) - 1)
    return win_percent

def compute_volatility_weights(df):
    """
    Compute weights based on game volatility for each move in the DataFrame.

    Parameters:
    df (pd.DataFrame): DataFrame containing chess game data with centipawn evaluations.

    Returns:
    pd.DataFrame: DataFrame with an additional 'Weight' column for each move.
    """
    # Ensure the DataFrame is sorted by GameID and MoveNumber
    df = df.sort_values(by=['GameID', 'MoveNumber']).reset_index(drop=True)
    
    # Define minimum and maximum weights
    min_weight = 0.5
    max_weight = 12.0
    
    # List to collect DataFrames for each game
    result = []
    
    # Group the DataFrame by GameID
    for game_id, game_df in df.groupby('GameID'):
        # Reset index for the game DataFrame
        game_df = game_df.reset_index(drop=True)
        
        # Extract centipawn evaluations (assuming the column is named 'CP')
        cps = game_df['CP'].values
        # Convert CP evaluations to WinPercent
        win_percents = cp_to_win_percent(cps)
        # Prepend the initial evaluation
        win_percents = np.insert(win_percents, 0, win_percents[0])
        
        # Determine window size
        total_moves = len(win_percents)
        window_size = max(2, min(8, total_moves // 10))
        
        # Compute weights for each move
        weights = []
        for i in range(1, total_moves):
            # Define the window around the current move
            start_idx = max(0, i - window_size // 2)
            end_idx = min(total_moves, i + window_size // 2)
            window = win_percents[start_idx:end_idx]
            # Compute volatility (standard deviation)
            volatility = np.std(window)
            # Clamp the weight between min_weight and max_weight
            weight = max(min_weight, min(max_weight, volatility))
            weights.append(weight)
        
        # Assign weights to the game DataFrame (excluding the initial prepended move)
        game_df['Volatility_Weight'] = weights
        result.append(game_df)
    
    # Concatenate all game DataFrames
    df_with_weights = pd.concat(result, ignore_index=True)
    return df_with_weights

def compute_move_accuracy(df):
    """
    Compute the accuracy percentage for each move based on win percentages before and after the move,
    adjusted for each player's perspective.
    """
    # Ensure 'CP' exists
    if 'CP' not in df.columns:
        df['CP'] = df['Evaluation'] * 100

    # Compute 'WinPercent' from 'CP'
    df['WinPercent'] = cp_to_win_percent(df['CP'])

    # Ensure 'Player' column exists
    if 'Player' not in df.columns:
        df['Player'] = np.where(df['MoveNumber'] % 2 != 0, 'White', 'Black')

    # Adjust 'WinPercent' to be from player's perspective
    df['WinPercent_Player'] = df['WinPercent']
    df.loc[df['Player'] == 'Black', 'WinPercent_Player'] = 100 - df.loc[df['Player'] == 'Black', 'WinPercent']

    # Compute 'WinPercentBefore' by shifting within each game
    df['WinPercentBefore'] = df.groupby('GameID')['WinPercent'].shift(1)
    df['WinPercentBefore'] = df['WinPercentBefore'].fillna(df['WinPercent'])

    # Adjust 'WinPercentBefore' to be from player's perspective
    df['WinPercentBefore_Player'] = df['WinPercentBefore']
    df.loc[df['Player'] == 'Black', 'WinPercentBefore_Player'] = 100 - df.loc[df['Player'] == 'Black', 'WinPercentBefore']

    # Compute the difference in win percentages from the player's perspective
    delta_win_percent = df['WinPercentBefore_Player'] - df['WinPercent_Player']

    # Compute 'Move_Accuracy' using the given formula
    accuracy_percent = 103.1668 * np.exp(-0.04354 * delta_win_percent) - 3.1669

    # Clamp the accuracy between 0 and 100
    accuracy_percent = np.clip(accuracy_percent, 0, 100)
    df['Move_Accuracy'] = accuracy_percent

    # Compute 'Volatility_Weight' if not already computed
    if 'Volatility_Weight' not in df.columns:
        df = compute_volatility_weights(df)

    return df

def add_total_accuracy(df):
    # Ensure 'Player' column exists
    if 'Player' not in df.columns:
        df['Player'] = np.where(df['MoveNumber'] % 2 != 0, 'White', 'Black')

    # Compute move accuracies
    df = compute_move_accuracy(df)

    # Function to compute Total Accuracy for a player's moves in a game
    def compute_total_accuracy(group):
        A_i = group['Move_Accuracy'].values  # Move accuracies
        w_i = group['Volatility_Weight'].values  # Volatility weights
        n = len(A_i)  # Number of moves

        # Handle zero accuracies to prevent division by zero
        A_i_nonzero = np.where(A_i == 0, 0.1, A_i)

        # Weighted Mean Accuracy
        weighted_mean = np.sum(w_i * A_i) / np.sum(w_i)

        # Harmonic Mean Accuracy
        harmonic_mean = n / np.sum(1 / A_i_nonzero)

        # Total Accuracy
        total_accuracy = (weighted_mean + harmonic_mean) / 2

        return total_accuracy

    # Compute Total Accuracy per game per player
    total_accuracy_df = df.groupby(['GameID', 'Player'], sort=False)[['Move_Accuracy', 'Volatility_Weight']].apply(compute_total_accuracy).reset_index(name='Total_Accuracy')

    # Merge the total accuracies back into the original DataFrame without changing the row order
    df = df.merge(total_accuracy_df, on=['GameID', 'Player'], how='left', sort=False)

    return df


def export_game_to_pgn(df, game_id, output_file="../game1.pgn"):
    import chess
    import chess.pgn

    # Filter the DataFrame for the specified GameID
    game_df = df[df['GameID'] == game_id].sort_values('MoveNumber')

    if game_df.empty:
        print(f"No game found with GameID {game_id}")
        return

    # Create a Game object
    game = chess.pgn.Game()

    # Add headers to the game
    game.headers["Event"] = "Chess Game"
    game.headers["Site"] = "Unknown"
    game.headers["Date"] = game_df['Year'].iloc[0] if 'Year' in game_df.columns else "????.??.??"
    game.headers["Round"] = "?"
    game.headers["White"] = game_df['WhiteName'].iloc[0] if 'WhiteName' in game_df.columns else "White"
    game.headers["Black"] = game_df['BlackName'].iloc[0] if 'BlackName' in game_df.columns else "Black"
    game.headers["Result"] = game_df['Result'].iloc[0] if 'Result' in game_df.columns else "*"
    if 'WhiteElo' in game_df.columns:
        game.headers["WhiteElo"] = str(game_df['WhiteElo'].iloc[0])
    if 'BlackElo' in game_df.columns:
        game.headers["BlackElo"] = str(game_df['BlackElo'].iloc[0])
    if 'Opening' in game_df.columns:
        game.headers["Opening"] = game_df['Opening'].iloc[0]
    if 'Variation' in game_df.columns:
        game.headers["Variation"] = game_df['Variation'].iloc[0]

    # Initialize the board
    board = chess.Board()
    node = game

    # Iterate over the moves
    for _, row in game_df.iterrows():
        move_san = row['Move']
        try:
            # Parse the move in SAN notation
            move = board.parse_san(move_san)
            # Add the move to the game
            node = node.add_variation(move)
            # Make the move on the board
            board.push(move)
        except ValueError:
            print(f"Invalid move '{move_san}' at move number {row['MoveNumber']}")
            return

    # Write the game to a PGN file
    with open(output_file, 'w', encoding='utf-8') as f:
        exporter = chess.pgn.FileExporter(f)
        game.accept(exporter)


def create_summary_table(df):
    # List of columns to remove
    columns_to_remove = ['LineEnd', 'MoveNumber', 'CP', 'WinPercent', 'Move_Accuracy',
                         'Volatility_Weight', 'Move', 'Total_Accuracy']  # Added 'Total_Accuracy' here

    # Drop the specified columns, including 'Total_Accuracy'
    df_reduced = df.drop(columns=columns_to_remove, errors='ignore')

    # Get game-level information (first row per GameID)
    game_info = df_reduced.groupby('GameID', as_index=False).first()

    # Compute TotalMoves per game
    total_moves = df.groupby('GameID')['MoveNumber'].max().reset_index(name='TotalMoves')

    # Merge TotalMoves into game_info
    game_info = pd.merge(game_info, total_moves, on='GameID', how='left')

    # Get Total_Accuracy per GameID and Player
    total_accuracy = df.groupby(['GameID', 'Player'], as_index=False)['Total_Accuracy'].first()

    # Create DataFrames for White and Black players
    # For White
    white_df = game_info.copy()
    white_df['Player'] = 'White'
    white_df['Name'] = white_df['WhiteName']
    white_df['Elo'] = white_df['WhiteElo']
    white_df['FideId'] = white_df['WhiteFideId']

    # For Black
    black_df = game_info.copy()
    black_df['Player'] = 'Black'
    black_df['Name'] = black_df['BlackName']
    black_df['Elo'] = black_df['BlackElo']
    black_df['FideId'] = black_df['BlackFideId']

    # Concatenate the two DataFrames
    summary_table = pd.concat([white_df, black_df], ignore_index=True)

    # Merge Total_Accuracy into summary_table
    summary_table = pd.merge(summary_table, total_accuracy, on=['GameID', 'Player'], how='left')

    # Drop redundant columns
    columns_to_drop = ['WhiteName', 'BlackName', 'WhiteElo', 'BlackElo',
                       'WhiteFideId', 'BlackFideId']
    summary_table = summary_table.drop(columns=columns_to_drop, errors='ignore')

    # Set 'Player' as categorical with specific order
    summary_table['Player'] = pd.Categorical(summary_table['Player'], categories=['White', 'Black'], ordered=True)

    # Sort the summary_table by 'GameID' and 'Player'
    summary_table = summary_table.sort_values(by=['GameID', 'Player']).reset_index(drop=True)

    # Reorder columns if necessary
    cols_order = ['GameID', 'Year', 'Opening', 'Variation', 'Result', 'TotalMoves',
                  'Player', 'Name', 'Elo', 'FideId', 'Total_Accuracy']
    summary_table = summary_table[cols_order]

    return summary_table




