import pandas as pd
import numpy as np
import glob, os
import anal_games, functions_anal
from sklearn.model_selection import train_test_split


def get_outcome(result):
    if result == '1-0':
        return 'Win'    # White won
    elif result == '0-1':
        return 'Loss'   # White lost
    elif result == '1/2-1/2':
        return 'Draw'   # Draw
    else:
        return None     # Exclude other results
    
def get_outcome_num(result):
    if result == '1-0':
        return 0    # White won
    elif result == '0-1':
        return 1   # White lost
    elif result == '1/2-1/2':
        return 2   # Draw
    else:
        return None     # Exclude other results

def smooth_lines(winchance_array,count_games,bins):

    nonzerolines=np.where((count_games[1:-2]>100))
    # print(nonzerolines)
    zerolines=np.where((count_games[1:-2]<=100))
    
    # print(zerolines)
    # print(bins[zerolines])
    if len(zerolines[0])>0 and len(nonzerolines[0])>0:
        for j in range(3):
            # print(len(zerolines), len(nonzerolines))
            # print(bins[1:][nonzerolines],winchance_array[j,1:-2,i][nonzerolines])
            # print(bins[1:])
            winchance_array[j,1:-2]=np.interp(bins[1:],bins[1:][nonzerolines],winchance_array[j,1:-2][nonzerolines]) 
        winchance_array[:,0]=winchance_array[:,1]
        winchance_array[:,-1]=winchance_array[:,-2]
    
    if len(nonzerolines[0])==0:
        winchance_array[:,:]=1./3.
    
    return winchance_array
    
def get_winning_chance(game,inputs): # make function that gives winning chance for each move using the array created previously
    winchance_array=inputs['winchance_array']
    bins=inputs['bins']
    bin_moves=inputs['bin_moves']
    return {'WinningChance': winchance_array[0,np.digitize(game['Evaluation'],bins=bins),np.arange(len(game['Move']))//bin_moves].tolist()}
   
def convert_evaluation(row):
    """
    Convert the evaluation M to a numeric value.

    Parameters:
    row (pd.Series): A row from a DataFrame containing the 'Evaluation' column.

    Returns:
    float: The numeric evaluation value. Returns 0.0 for mate in 0 moves, 20.0 if White can mate, -20.0 if Black can mate, 
           the numeric evaluation if it can be parsed, or NaN if the evaluation cannot be parsed.
    """
    eval_str = row['Evaluation']
    
    if eval_str in ['+M0', '-M0', 'M0']:
        return 0.0  # Mate in 0 moves
    elif eval_str.startswith('+M') or (eval_str.startswith('M') and not eval_str.startswith('-M')):
        return 20.0  # White can mate
    elif eval_str.startswith('-M'):
        return -20.0  # Black can mate
    else:
        # Try to convert the evaluation to a float
        try:
            eval_float = float(eval_str)
            return eval_float  # Numeric evaluation remains the same
        except ValueError:
            return np.nan  # Unable to parse evaluation
           
def calculate_chances(df, lower_eval, upper_eval):
    """
    Calculate the chances of winning, drawing, and losing for positions within a specified evaluation range.

    Parameters:
    df (pd.DataFrame): DataFrame containing chess game data with columns 'GameID', 'Evaluations', 'Result', etc.
    lower_eval (float): The lower bound of the evaluation range.
    upper_eval (float): The upper bound of the evaluation range.

    Returns:
    list: A list containing the winning chance, drawing chance, losing chance, total number of valid games, and outcome counts.
    """
    # Filter positions where 'New_evaluations' is between lower_eval and upper_eval
    positions_in_range = df[(df['Evaluation'] >= lower_eval) & (df['Evaluation'] <= upper_eval)].copy()
    
    # Get unique GameIDs where this occurs
    games_in_range = positions_in_range['GameID'].unique()
    
    # Get the results of these games
    game_results = df[df['GameID'].isin(games_in_range)][['GameID', 'Result']].drop_duplicates()
    
    # Apply the mapping
    game_results['Outcome'] = game_results['Result'].apply(get_outcome)
    
    # Exclude games with 'Other' outcomes
    valid_results = game_results.dropna(subset=['Outcome'])
    
    # Total number of valid games
    total_valid_games = valid_results.shape[0]
    outcome_counts=None
    if total_valid_games == 0:
        winning_chance = drawing_chance = losing_chance = 0.0
    else:
        # Count the number of games in each category
        outcome_counts = valid_results['Outcome'].value_counts()
        
        # Calculate percentages
        winning_chance = (outcome_counts.get('Win', 0) / total_valid_games) * 100
        drawing_chance = (outcome_counts.get('Draw', 0) / total_valid_games) * 100
        losing_chance = (outcome_counts.get('Loss', 0) / total_valid_games) * 100
    
    return [winning_chance, drawing_chance, losing_chance, total_valid_games,outcome_counts]

def compute_winning_chance_table(df, intervals=np.arange(-13, 13.2, 0.2)):
    """
    Compute winning, drawing, and losing chances over specified evaluation intervals.

    Parameters:
    df (pd.DataFrame): DataFrame containing chess game data, including 'Evaluation' and 'MoveNumber' columns.
    calculate_chances_func (function): Function to calculate chances, should accept parameters (df, lower_eval, upper_eval).
    intervals (np.array, optional): Array of evaluation interval edges. Default is np.arange(-13, 13.2, 0.2).

    Returns:
    pd.DataFrame: DataFrame containing winning chances for each evaluation interval.
    """
    # Ensure intervals are rounded to one decimal place
    intervals = np.round(intervals, decimals=1)
    edges = [-np.inf] + list(intervals) + [np.inf]

    # Create bin labels
    bin_labels = []
    for i in range(len(edges) - 1):
        lower = edges[i]
        upper = edges[i + 1]
        if np.isneginf(lower):
            label = f"(-∞, {upper}]"
        elif np.isposinf(upper):
            label = f"({lower}, ∞)"
        else:
            label = f"({lower}, {upper}]"
        bin_labels.append(label)

    # Prepare a list to hold the results
    results = []

    # Loop over evaluation intervals
    for i in range(len(edges) - 1):
        lower_eval = edges[i]
        upper_eval = edges[i + 1]

        # Call the calculate_chances function
        winning_chance, drawing_chance, losing_chance, total_valid_games, _ = calculate_chances(
            df, lower_eval, upper_eval
        )

        # Store the results
        results.append({
            'Interval': bin_labels[i],
            'WinningChance': winning_chance,
            'DrawingChance': drawing_chance,
            'LosingChance': losing_chance,
            'TotalGames': total_valid_games,
        })

    # Create a DataFrame from the results
    winning_chance_table = pd.DataFrame(results)

    return winning_chance_table

def process_chess_data(df, winning_chance_table=pd.read_csv('winning_chances_all_moves.csv'), intervals=np.arange(-13, 13.2, 0.2)):
    """
    Processes chess data by binning evaluation values, merging with winning chances,
    and computing WCL, LCL, Player, and 'a' columns.

    Parameters:
    df (pd.DataFrame): DataFrame containing chess game data with 'Evaluation', 'GameID', and 'MoveNumber' columns.
    winning_chance_table (pd.DataFrame): DataFrame containing winning chances with 'Interval', 'WinningChance', 'LosingChance', and 'TotalGames' columns.
    intervals (np.array): Numpy array of interval edges used for binning evaluations.

    Returns:
    pd.DataFrame: Modified DataFrame with additional columns added.
    """

    # Ensure intervals are rounded to one decimal place
    intervals = np.round(intervals, decimals=1)
    edges = [-np.inf] + list(intervals) + [np.inf]

    # Create bin labels
    bin_labels = []
    for i in range(len(edges) - 1):
        lower = edges[i]
        upper = edges[i + 1]
        if np.isneginf(lower):
            label = f"(-infty, {upper}]"
        elif np.isposinf(upper):
            label = f"({lower}, infty)"
        else:
            label = f"({lower}, {upper}]"
        bin_labels.append(label)

    # Ensure that the bin labels in 'winning_chance_table' match the ones we're creating
    # This is important for a correct merge
    winning_chance_table['Interval'] = winning_chance_table['Interval'].astype(str)
    bin_labels = [str(label) for label in bin_labels]

    # Bin the 'Evaluation' values in 'df' to create an 'Interval' column
    df['Interval'] = pd.cut(
        df['Evaluation'],
        bins=edges,
        labels=bin_labels,
        right=True,
        include_lowest=True,
    )

    # Ensure 'Interval' in 'df' is of type string
    df['Interval'] = df['Interval'].astype(str)

    # Select the columns to merge
    columns_to_merge = ['Interval', 'WinningChance', 'LosingChance', 'TotalGames']

    # Merge 'df' with 'winning_chance_table' on 'Interval'
    df = df.merge(
        winning_chance_table[columns_to_merge],
        on='Interval',
        how='left'
    )

    # Compute 'WCL' and 'LCL' differences per game
    df['WCL'] = df.groupby('GameID')['WinningChance'].diff().abs()
    df['LCL'] = df.groupby('GameID')['LosingChance'].diff().abs()

    # Assign 'Player' based on move number
    df['Player'] = np.where(df['MoveNumber'] % 2 != 0, 'White', 'Black')

    # Compute 'a' = max(|WCL|, |LCL|) for each move
    df['a'] = df[['WCL', 'LCL']].abs().max(axis=1)

    return df
  
def create_summary_table(df, mistake_bins= [5, 10, 15, 20, 25, 30, 35, 40, 50, 60, 70, 100], winning_chance_table=None, intervals=None):
    """
    Processes the chess DataFrame to create a summary table of mistakes per interval per player per game.

    Parameters:
    df (pd.DataFrame): DataFrame containing chess game data.
    mistake_bins (list): List of bin edges for mistake intervals.
    winning_chance_table (pd.DataFrame, optional): DataFrame containing winning chances.
                                            Default is loaded from 'winning_chances_all_moves.csv'.
    intervals (np.array, optional): Numpy array of interval edges used for binning evaluations.
                                    Default is np.arange(-13, 13.2, 0.2).

    Returns:
    pd.DataFrame: Summary table with mistakes per interval per player per game.
    """


    # If 'WCL' does not exist, apply the 'process_chess_data' function
    if 'WCL' not in df.columns or 'a' not in df.columns:
        if winning_chance_table is None:
            winning_chance_table = pd.read_csv('winning_chances_all_moves.csv')
        if intervals is None:
            intervals = np.arange(-13, 13.2, 0.2)
        df = process_chess_data(df, winning_chance_table, intervals)

    # Step 1: Define mistake labels based on mistake_bins
    mistake_labels = []
    for i in range(len(mistake_bins)-1):
        label = f'({mistake_bins[i]},{mistake_bins[i+1]}]'
        mistake_labels.append(label)

    # Step 2: Assign each 'a' to a mistake interval
    df['MistakeInterval'] = pd.cut(
        df['a'],
        bins=mistake_bins,
        labels=mistake_labels,
        right=True,
        include_lowest=True
    )

    # Step 3: Identify the player making the move if 'Player' column doesn't exist
    if 'Player' not in df.columns:
        df['Player'] = np.where(df['MoveNumber'] % 2 != 0, 'White', 'Black')

    # Step 4: Group and count the number of mistakes per interval, per player, per game
    mistake_moves = df.dropna(subset=['MistakeInterval']).copy()
    mistake_moves['MistakeInterval'] = mistake_moves['MistakeInterval'].astype(str)
    mistake_counts = mistake_moves.groupby(['GameID', 'Player', 'MistakeInterval']).size().reset_index(name='MistakeCount')
    average_a = df.groupby(['GameID', 'Player'])['a'].mean().reset_index(name='AWCL')
    
    # Step 5: Pivot the data to get a summary table per game and player
    summary_table = mistake_counts.pivot_table(
        index=['GameID', 'Player'],
        columns='MistakeInterval',
        values='MistakeCount',
        fill_value=0
    ).reset_index()
    summary_table = summary_table.merge(average_a, on=['GameID', 'Player'], how='left')
    # Flatten the column MultiIndex if necessary
    summary_table.columns.name = None
    summary_table.columns = [col if isinstance(col, str) else col for col in summary_table.columns]

    # Step 6: Compute Total Moves per game
    total_moves = df.groupby('GameID')['MoveNumber'].max().reset_index(name='TotalMoves')

    # Step 7: Extract game-level metadata: Opening, Variation, Result
    game_metadata = df.groupby('GameID').agg({
        'Opening': 'first',
        'Variation': 'first',
        'Result': 'first'
    }).reset_index()

    # Merge TotalMoves into game_metadata
    game_metadata = game_metadata.merge(total_moves, on='GameID', how='left')

    # Step 8: Extract player-level metadata
    player_metadata = df.groupby('GameID').agg({
        'WhiteName': 'first',
        'WhiteElo': 'first',
        'WhiteFideId': 'first',
        'BlackName': 'first',
        'BlackElo': 'first',
        'BlackFideId': 'first'
    }).reset_index()

    # Prepare player metadata for merging
    # For White players
    white_players = player_metadata[['GameID', 'WhiteName', 'WhiteElo', 'WhiteFideId']].copy()
    white_players['Player'] = 'White'
    white_players = white_players.rename(columns={
        'WhiteName': 'Name',
        'WhiteElo': 'Elo',
        'WhiteFideId': 'FideId'
    })

    # For Black players
    black_players = player_metadata[['GameID', 'BlackName', 'BlackElo', 'BlackFideId']].copy()
    black_players['Player'] = 'Black'
    black_players = black_players.rename(columns={
        'BlackName': 'Name',
        'BlackElo': 'Elo',
        'BlackFideId': 'FideId'
    })

    # Concatenate player metadata
    player_metadata_long = pd.concat([white_players, black_players], ignore_index=True)

    # Step 9: Merge player metadata with the summary table
    summary_table = summary_table.merge(player_metadata_long, on=['GameID', 'Player'], how='left')

    # Step 10: Merge game metadata with the summary table
    summary_table = summary_table.merge(game_metadata, on='GameID', how='left')
    total_moves_bins = [0, 30, 40, 50, 60, 70, 80, 90, 100, 120, np.inf]
    total_moves_labels = [
        '(0,30]', '(30,40]', '(40,50]', '(50,60]', '(60,70]',
        '(70,80]', '(80,90]', '(90,100]', '(100,120]', '(120,∞)'
    ]

    # Step 2: Assign each game to a TotalMovesInterval
    summary_table['TotalMovesInterval'] = pd.cut(
        summary_table['TotalMoves'],
        bins=total_moves_bins,
        labels=total_moves_labels,
        right=True,
        include_lowest=True
    )
    # Rearranging columns for better readability
    cols = ['GameID', 'Player', 'Name', 'Elo', 'FideId', 'Opening', 'Variation', 'Result',
        'TotalMoves', 'TotalMovesInterval', 'AWCL'] + mistake_labels
    summary_table = summary_table[cols]

    return summary_table

def calculate_mistake_percentage(summary_table, interval_label):
    """
    Calculates the percentage of games that have at least one mistake in the specified interval.

    Parameters:
    summary_table (pd.DataFrame): The DataFrame containing game summaries.
    interval_label (str): The label of the mistake interval to analyze (e.g., '(25,30]').

    Returns:
    float: The percentage of games with at least one mistake in the specified interval.
    """
    # Check if the interval column exists in the summary table
    if interval_label not in summary_table.columns:
        raise ValueError(f"The interval '{interval_label}' does not exist in the summary table columns.")

    # Total number of games
    total_games = len(summary_table)

    # Number of games with at least one mistake in the specified interval
    games_with_mistake = summary_table[summary_table[interval_label] > 0]
    number_with_mistake = len(games_with_mistake)

    # Compute the percentage
    percentage = (number_with_mistake / total_games) * 100
    print(f"Percentage of games with at least one mistake in {interval_label} interval: {percentage:.2f}%")
    return percentage
