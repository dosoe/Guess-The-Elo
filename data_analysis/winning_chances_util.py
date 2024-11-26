import pandas as pd
import numpy as np
import glob, os
import anal_games, functions_anal
import pickle, re
from sklearn.model_selection import train_test_split


def get_outcome(result):
    if isinstance(result, str):
        result_tmp=result
    else:
        result_tmp=result[0]
    if result_tmp == '1-0':
        return 'Win'    # White won
    elif result_tmp == '0-1':
        return 'Loss'   # White lost
    elif result_tmp == '1/2-1/2':
        return 'Draw'   # Draw
    else:
        return None     # Exclude other results

def get_outcome_num(result):
    """
    Returns 0 if win, 1 if draw and 2 if loss
    """

    if isinstance(result, str):
        result_tmp=result
    else:
        result_tmp=result[0]
    if result_tmp == '1-0':
        return 0    # White won
    elif result_tmp == '0-1':
        return 2   # White lost
    elif result_tmp == '1/2-1/2':
        return 1   # Draw
    else:
        return None     # Exclude other results

def smooth_lines(winchance_array,count_games,bins):
    """
    Smoothes the winchance arrays, attributing values for bins with less than 100 games by linearly interpolating other bins
    If edge bins don't have enough games, winchance is 95, draw is 5 and lose is 0 at one end and opposite at the other

    Inputs:
    winchance_array: np.array of dimensions (3, number of eval bins) containing win,draw,lose chances for each bin
    count_games: np.array of dimensions (number of eval bins) containing the number of games in each eval bin

    outputs: 
    winchance_array: smoothed array, modifies winchance_array in place and returns it
    """

    nmin=100

    bins_copy=bins.tolist()

    count_games_copy=count_games
    if count_games_copy[0]<=nmin:
        count_games_copy[0]=nmin+1
        winchance_array[0,0]=0.
        winchance_array[1,0]=5
        winchance_array[2,0]=95
    if count_games_copy[-1]<=nmin:
        count_games_copy[-1]=nmin+1
        winchance_array[0,-1]=95
        winchance_array[1,-1]=5
        winchance_array[2,-1]=0.0
    nonzerolines=np.where((count_games_copy>nmin))

    bins_copy.insert(0,bins[0])
    bins_copy=np.array(bins_copy)

    zerolines=np.where((count_games_copy<=nmin))
    
    if len(zerolines[0])>0 and len(nonzerolines[0])>0:
        for j in range(3):
            winchance_array[j,:]=np.interp(bins_copy,bins_copy[nonzerolines],winchance_array[j,:][nonzerolines]) 
    
    if len(nonzerolines[0])==0:
        for i,eval in enumerate(bins):
            if eval>0:
                winchance_array[0,i]=95
                winchance_array[1,i]=5
                winchance_array[2,i]=0.
            else:
                winchance_array[0,i]=0.
                winchance_array[1,i]=5
                winchance_array[2,i]=95
    
    return winchance_array

if __name__ == "__main__":

    # Get the list of filenames matching the patterns
    filenames_15 = glob.glob("../Cleaned_Analyzed_Games/twic*_15_processed.csv")
    filenames_16 = glob.glob("../Cleaned_Analyzed_Games/twic*_16_processed.csv")

    # For dupes, use the bigger depth
    filenames_to_process=filenames_16
    for file in filenames_15:
        if '_'.join(file.split('_')[:3])+'_16_processed.csv' in filenames_to_process:
            continue
        else:
            filenames_to_process.append(file)
    
    outfile='../Cleaned_Analyzed_Games/all_games_cleaned.csv'

    # make list of games 
    anal_games.process_all_files(outfile=outfile,filenames=filenames_to_process,functions=[functions_anal.MovesTotal,functions_anal.Cleanup,functions_anal.MovesBlack,functions_anal.MovesWhite],skip_if_processed=True,game_wise=True)

    df=pd.read_csv(outfile)

    bin_moves=5

    df_train,df_test=train_test_split(df,test_size=0.2,random_state=100) # stratification with number of moves or elos doesn't work, as it needs at least two games for each unique value/combination of values. Binning doesn't help

    # save training set 
    df_train.to_csv('../Cleaned_Analyzed_Games/all_games_cleaned_train.csv',index=False)
    df_test.to_csv('../Cleaned_Analyzed_Games/all_games_cleaned_test.csv',index=False)
    
    # output files for winning chances
    file_prefix='../Cleaned_Analyzed_Games/winning_chances_per_move_'+str(bin_moves)+'_001_'
    file_suffix='.csv'
    # make bins for evaluations
    bins=np.arange(-20.05,20.15,0.1)

    # Get maximum number of moves
    df=pd.read_csv('../Cleaned_Analyzed_Games/all_games_cleaned_train.csv')
    max_moves=df['MovesAll'].max()
    # bin moves in blocks
    max_moves=max_moves//bin_moves


    # make array for winning chances
    winchance_array=np.zeros((3,len(bins)+2,int(max_moves)+1)) # +2 to account for values out of bounds, +1 for moves that are bigger than max_moves//5 * 5 
    count_games=np.zeros((len(bins)+2,int(max_moves)+1))

    for file in df_train['File'].unique(): # loop over files
        print(file)
        data=pd.read_csv(file)
        df_file=df_train.where(df_train['File']==file) # check which training games are in that file
        df_file.dropna(how='any',inplace=True)
        for line in df_file.iterrows(): # loop over games in training set from that file
            data_line=line[1]
            file=data_line['File']
            ind=data_line['LineStart'] # starting line for the game
            assert data.loc[ind, "GameID"]==data_line['GameID'] # sanity checks
            assert not np.isnan(data.loc[ind, "WhiteElo"]) # sanity checks
            ind,game=anal_games.read_game(data,ind,functions=[],game_wise=False) # reads a game, rejects it if invalid, outputs a game dictionary

            if game is None or get_outcome_num(game) is None: # sanity check, should be taken care of earlier
                continue

            for j in range(len(game['Move'])): # bin output and move evaluation
                i_bin=np.digitize(game['Evaluation'][j],bins=bins,right=True)
                winchance_array[get_outcome_num(game),i_bin,j//5]+=1
                count_games[i_bin,j//5]+=1

    for i in range(3): # normalize win chance array
        winchance_array[i,:,:]=np.divide(winchance_array[i,:,:],count_games)
    
    for i in range(int(max_moves)+1): # store win chance array

        out_line=winchance_array[:,:,i]
        out_line=smooth_lines(winchance_array[:,:,i],count_games[:,i],bins) # smooth win chance array to give values to evaluations where we don't have games
        
        # transform output into DataFrame and save
        bins_new=bins.tolist()
        bins_new.insert(0,'-20-')
        bins_new.append('20+')
        print(i,np.shape(bins_new),np.shape(winchance_array),np.shape(winchance_array[:,:,i]),np.shape(smooth_lines(winchance_array[:,:,i],count_games[:,i],bins)),np.shape(out_line),np.shape(out_line[0,:]),np.shape(out_line[1,:]),np.shape(out_line[2,:]),np.shape(count_games[:,i]))
        data=pd.DataFrame({'bins':bins_new,'WinningChance':out_line[0,:],
                            'DrawChance':out_line[1,:],
                            'LosingChance':out_line[2,:],
                            'TotalGames':count_games[:,i]})
        data=data[['bins','WinningChance','DrawChance','LosingChance','TotalGames']]
        data.to_csv(file_prefix+str(i)+file_suffix,index=False)

def compute_winning_chance_table(game_list, intervals=np.arange(-13, 13.2, 0.2),movebins=np.arange(0,700,5),outdir='./',smooth=True):
    """
    Compute winning, drawing, and losing chances over specified evaluation intervals.

    Parameters:
    df (pd.DataFrame): DataFrame containing chess game data, including 'Evaluation' and 'MoveNumber' columns.
    intervals (np.array, optional): Array of evaluation interval edges. Default is np.arange(-13, 13.2, 0.2).
    movebins (np.array, optional): 'all' or array of bins to bin the move number. If 'all', moves are not binned
    outdir (str): directory to store the tables of win/lose/draw chances

    Returns:
    list of pd.DataFrame: list for each move bin of DataFrame containing winning chances for each evaluation interval
    """
    # Ensure intervals are rounded to one decimal place
    intervals = np.round(intervals, decimals=2)
    edges = [-np.inf] + list(intervals) + [np.inf]

    allbins=type(movebins)==str and movebins=='all'

    if allbins:
        len_movebins=1
    else:
        len_movebins=len(movebins)+1

    winchance_array=np.zeros((3,len(intervals)+1,len_movebins))
    count_games=np.zeros((len(intervals)+1,len_movebins))

    for file in game_list['File'].unique(): # loop over files
        print(file)
        data=pd.read_csv(file)
        df_file=game_list.where(game_list['File']==file) # check which training games are in that file
        df_file.dropna(how='any',inplace=True)
        for line in df_file.iterrows(): # loop over games in training set from that file
            data_line=line[1]
            file=data_line['File']
            ind=data_line['LineStart'] # starting line for the game
            assert data.loc[ind, "GameID"]==data_line['GameID'] # sanity checks
            assert not np.isnan(data.loc[ind, "WhiteElo"]) # sanity checks
            ind,game=anal_games.read_game(data,ind,functions=[],game_wise=False) # reads a game, rejects it if invalid, outputs a game dictionary
            if game is None or get_outcome_num(game['Result']) is None: # sanity check, should be taken care of earlier
                continue

            for j in range(len(game['Move'])): # bin move and move
                i_bin=np.digitize(game['Evaluation'][j],bins=intervals,right=True)
                if allbins:
                    move_bin=0
                else:
                    move_bin=np.digitize(j,bins=movebins)-1 # no negative moves
                
                # increment winchance, counter
                winchance_array[get_outcome_num(game['Result']),i_bin,move_bin]+=1
                count_games[i_bin,move_bin]+=1
    
    for i in range(3): # normalize win chance array, in percent
        print(np.shape(winchance_array[i,:,:]),np.shape(count_games))
        winchance_array[i,:,:]=np.divide(winchance_array[i,:,:],count_games,where=count_games>0)*100.
    
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

    results=[]
    # for each move bin, create a dataframe and save it
    if allbins: # if only one move bin
        out_line=winchance_array[:,:,0]
        if smooth:
            out_line=smooth_lines(winchance_array[:,:,0],count_games[:,0],intervals) # smooth win chance array to give values to evaluations where we don't have enough games
        
        # transform output into DataFrame and save
        data=pd.DataFrame({'Interval':bin_labels,'WinningChance':out_line[0,:],
                            'DrawingChance':out_line[1,:],
                            'LosingChance':out_line[2,:],
                            'TotalGames':count_games[:,0]})
        results.append(data)

        data.to_csv(os.path.join(outdir,'winning_chances_all.csv'),index=False)

    else: # if several move bins
        for i in range(len(movebins)): # store win chance array

            out_line=winchance_array[:,:,i]
            if smooth:
                out_line=smooth_lines(winchance_array[:,:,i],count_games[:,i],intervals) # smooth win chance array to give values to evaluations where we don't have enough games
            
            # transform output into DataFrame and save
            data=pd.DataFrame({'Interval':bin_labels,'WinningChance':out_line[0,:],
                                'DrawingChance':out_line[1,:],
                                'LosingChance':out_line[2,:],
                                'TotalGames':count_games[:,i]})
            results.append(data)

            if i <len(movebins)-1:
                data.to_csv(os.path.join(outdir,'winning_chances_'+str(movebins[i])+'-'+str(movebins[i+1])+'.csv'),index=False)
            else:
                data.to_csv(os.path.join(outdir,'winning_chances_'+str(movebins[i])+'-.csv'),index=False)

    return results

def read_winning_tables(dir,movebins):
    """ 
    Reads tables as created by compute_winning_chance_table
    Inputs: 
    dir: directory containing the win tables
    movebins: bins of moves, either numpy array or 'all' if no move bins

    Outputs: 
    additional_inputs: dictionary that can be used by WinCHanceIncrease
    """

    winchances={}
    bins_moves=[]
    winchances=[]
    losechances=[]
    drawchances=[]
    bins_eval=[]
    files=[]

    # read winning chance files
    # if movebins is 'all', then just one bin with very large size
    if type(movebins)==str and movebins=='all':
        files.append(os.path.join(dir,'winning_chances_all.csv'))
        bins_moves=[0,100000]
    else: 
        for i in range(len(movebins)-1):
            files.append(os.path.join(dir,'winning_chances_'+str(movebins[i])+'-'+str(movebins[i+1])+'.csv'))
        files.append(os.path.join(dir,'winning_chances_'+str(movebins[-1])+'-.csv')) #more moves than the max bin
    
    
    for i,file in enumerate(files):
        filename=file.split('/')[-1].split('.')[0]

        # recover bins from filenames, should be same as input
        if type(movebins)==str and movebins=='all':
            num_moves_start=0
        else:
            num_moves_start=int(filename.split('_')[-1].split('-')[0])
        bins_moves.append(num_moves_start)
        data=pd.read_csv(file)
        if i==0:

            # read eval bins from files
            intervals=data['Interval']
            for interval in intervals[:-1]:
                top=interval.split(',')[1]
                bins_eval.append(float(top[:-1]))
        # reassemble numpy array
        winchances.append(data['WinningChance'].to_numpy(dtype=float))
        losechances.append(data['LosingChance'].to_numpy(dtype=float))
        drawchances.append(data['DrawingChance'].to_numpy(dtype=float))

    # order numpy arrays by move bins
    bins_moves, winchances, losechances, drawchances=(list(t) for t in zip(*sorted(zip(bins_moves, winchances, losechances, drawchances))))

    bins_moves=np.array(bins_moves)
    winchances=np.array(winchances)
    losechances=np.array(losechances)
    drawchances=np.array(drawchances)

    additional_inputs={}
    additional_inputs['bins_moves']=bins_moves
    additional_inputs['bins_eval']=bins_eval
    additional_inputs['winchances']=winchances
    additional_inputs['drawchances']=drawchances
    additional_inputs['losechances']=losechances

    return additional_inputs

def WinChanceIncrease(game,additional_inputs):
    """
    Takes a game dictionary and win chance tables, outputs dict containing WCL and LCL for each black and white move for anal_games functions
    """

    mv_min=additional_inputs['mv_min']
    mv_max=additional_inputs['mv_max']
    bins_moves=additional_inputs['bins_moves']
    bins_eval=additional_inputs['bins_eval']
    winchances=additional_inputs['winchances']
    drawchances=additional_inputs['drawchances']
    losechances=additional_inputs['losechances']

    one_bin=np.shape(winchances)[0]==1

    num_moves=len(game['Move'])

    if num_moves<mv_min or num_moves>=mv_max:
        return None
        
    winchance=np.zeros((num_moves))
    losechance=np.zeros((num_moves))
    for i in range(num_moves):
        i_eval=np.digitize(game['Evaluation'][i],bins=bins_eval,right=True) # bin evaluation
        if one_bin: # bin move
            i_move=0
        else:
            i_move=np.digitize(i,bins=bins_moves)-1 # annoying shift by 1 because moves start at 0
        
        winchance[i]=winchances[i_move,i_eval]
        losechance[i]=losechances[i_move,i_eval]

    # get difference in win/lose chance
    windiff=winchance[1:]-winchance[:-1]
    losediff=losechance[1:]-losechance[:-1]

    # get WCL, LCL for white and black
    out={}
    # first move has not increase
    out['White_WCL_'+str(0)]=0.
    out['White_LCL_'+str(0)]=0.
    for i in range(1,num_moves): # we want to shift it by one because the first move has a wcl=0.
        if i%2==0:
            if i==0:
                continue
            out['White_WCL_'+str(i//2)]=windiff[i-1]
            out['White_LCL_'+str(i//2)]=losediff[i-1]
        else:
            out['Black_LCL_'+str(i//2)]=losediff[i-1]
            out['Black_WCL_'+str(i//2)]=windiff[i-1]
    
    return out

def process_chess_data(df, winning_chance_table=pd.read_csv('winning_chances_all_moves.csv')):
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

    # Step 5: Pivot the data to get a summary table per game and player
    summary_table = mistake_counts.pivot_table(
        index=['GameID', 'Player'],
        columns='MistakeInterval',
        values='MistakeCount',
        fill_value=0
    ).reset_index()

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
    cols = ['GameID', 'Player', 'Name', 'Elo', 'FideId', 'Opening', 'Variation', 'Result', 'TotalMoves', 'TotalMovesInterval'] + mistake_labels
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


        # data.to_csv(file_prefix+str(i*bin_moves)+'_'+str((i+1)*bin_moves)+file_suffix,index=False)