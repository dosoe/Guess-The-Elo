import numpy as np
import pandas as pd
import os

# Function to convert 'Evaluation' to 'New_evaluations'
def convert_evaluation(eval_str):
    """
    Converts evaluations from string to float, including near-mate evaluations

    Parameters: 
    - eval_str (str): Evaluation string

    Returns: 
    - float : Evaluation float
    """
    
    try:
        return float(eval_str)
    except:
        pass
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
            return None  # Unable to parse evaluation

def read_game(data, ind, functions=[], game_wise=True):
    """
    Reads a game from a pandas.DataFrame as a dictionary, applies a list of functions to it, outputs the result

    Parameters: 
    - df (pandas.DataFrame): Contains games
    - ind (str): starting line for the game to be processed
    - functions (list): a list of functions to be applied on the game. If the function has arguments other 
      than the game, the corresponding element of the list should be a tuple with the function and a dictionary of 
      additional arguments
    - game_wise (bool): If True, the output is a dictionary with single values, else each value is a list as long 
      as the number of moves. To be adapted to the function, some functions apply game-wise, some move-wise. 

    Returns:
    - ind (str): The index of the line of the game
    - None if the game is not valid. This happens
      either because one of the players doesn't have a fide id (it's a bot), because the game has no moves or 
      because one or more of the functions returns None
    else:
    - ind (str): The index of the line of the game
    - game (dict): a dictionary of the game properties, including the result of the functions
    

    Examples of functions can be found in functions_anal.py

    Function outputs are stored in 
    game[function_name] (fetched with function.__name__)
    """
    game = {}
    gameid = data.loc[ind, "GameID"]
    game_used = True
    try:  # reject games with no Fide ID for black or white
        if np.isnan(float(data.loc[ind, "WhiteFideId"])) or np.isnan(float(data.loc[ind, "BlackFideId"])):
            game_used = False
    except ValueError:  # reject games where the file does not have FideIDs
        game_used = False
    if game_used:  # read game metadata
        game['GameID'] = data.loc[ind, "GameID"]
        game['WhiteName'] = data.loc[ind, "WhiteName"]
        game['BlackName'] = data.loc[ind, "BlackName"]
        game['WhiteElo'] = data.loc[ind, "WhiteElo"]
        game['BlackElo'] = data.loc[ind, "BlackElo"]
        game['LineStart'] = ind
        try:
            game['WhiteFideId'] = int(data.loc[ind, "WhiteFideId"])
            game['BlackFideId'] = int(data.loc[ind, "BlackFideId"])
        except: # if no FideId game is rejected
            game_used = False
        game['Year'] = data.loc[ind, "Year"]
        game['Opening'] = data.loc[ind, "Opening"]
        game['Variation'] = data.loc[ind, "Variation"]
        game['Result'] = data.loc[ind, "Result"]
        if game['Result'] == '*': # if unclear result game is rejected
            game_used = False
        game_moves = []
        game_evals_original = []
        game_evals_converted = []

    while ind < len(data) and data.loc[ind, "GameID"] == gameid:  # read game moves, convert to numeric
        if game_used:
            game_moves.append(data.loc[ind, "Move"])
            eval_orig = data.loc[ind, "Evaluation"]
            game_evals_original.append(eval_orig)
            new_eval = convert_evaluation(eval_orig)
            game_evals_converted.append(new_eval)
            if new_eval is None:
                game_used = False

        ind += 1

    if game_used and len(game_moves)==0: # if no moves, reject game
        game_used=False

    if game_used:
        game['Move'] = game_moves
        game['Old_Evaluation'] = game_evals_original
        game['Evaluation'] = game_evals_converted  # New evaluations are now in 'Evaluation'
        for function in functions:  # apply functions to games
            if callable(function):  # If function does not take additional arguments
                out_tmp = function(game)
            else:  # function is a tuple containing the function and a dictionary containing additional inputs
                out_tmp = function[0](game, function[1])
            if out_tmp is None:  # if output is None, game is rejected
                game_used = False
                continue
            for key in out_tmp:  # put outputs of functions to games
                game[key] = out_tmp[key]
        if game_wise: # if game_wise, don't keep move-specific information
            del game['Move']
            del game['Evaluation']
            del game['Old_Evaluation']

        game['LineEnd'] = ind # Last line of the game
    if game_used:
        if game_wise:
            return ind, game
        else: # if move-wise, make lists out of every tag
            out = {}
            for key in game:
                if key in ['WhiteName', 'BlackName', 'WhiteElo', 'BlackElo', 'WhiteFideId', 'BlackFideId', 'Year', 'Opening', 'Variation', 'Result', 'LineStart', 'LineEnd']:
                    out[key] = [game[key]] + (len(game['Move']) - 1) * ['']
                else:
                    out[key] = game[key]
            out['GameID'] = (len(game['Move'])) * [game['GameID']]
            out['MoveNumber'] = list(range(1, len(game['Move']) + 1))

            return ind, out
    else:
        return ind, None

def process_one_file(filename,functions=[],game_wise=True):
    """
    Processes one file

    Parameters:
    - filename (str): name of the file to process
    - functions (list): list of functions to apply to each game, see read_game
    - game_wise (bool): If True, the output has one line per game, else the output has one line per move
      and 
    
    Returns:
    - games (pandas.DataFrame): DataFrame containing the game properties as well as function outputs
    """

    data=pd.read_csv(filename)
    if not 'WhiteFideId' in data:
        print(filename,'has no fide ids')
        return
    ind=0

    output=pd.DataFrame()
    while ind<len(data):
        # reads game and returns index of last line of the game (empty line)
        ind,game=read_game(data,ind,functions=functions,game_wise=game_wise)
        ind+=1
        if game:
            if game_wise:
                game['File']=filename
                game_df=pd.DataFrame([game])
                output = pd.concat([output, game_df], ignore_index=True)
            else:
                for key in game:
                    game[key].append('') # every game ends with an empty line
                game_df=pd.DataFrame.from_dict(game)
                output = pd.concat([output, game_df], ignore_index=True)
    return output

def process_all_files(outfile,filenames=[],functions=[],skip_if_processed=True,game_wise=True):
    """
    Processes all files, saves results in outfile as csv

    Parameters:
    - outfile (str): name of the file to store all the outputs
    - filenames (list): List of files to process
    - functions (list): List of functions to apply to the games, see read_game
    - skip_if_processed (bool): if True and outfile already exists, skips a file if already processed
    - game_wise (bool): If True, the output has one line per game, else the output has one line per move

    outputs: 
    - None
    """
    found=False
    if os.path.isfile(outfile) and skip_if_processed:
        found=True
        df=pd.read_csv(outfile)
    else:
        df=pd.DataFrame()
    
    for i,file in enumerate(filenames):
        if found and file in df['File'].values and skip_if_processed:
            continue
        else:
            print(file)
            df_new=process_one_file(file,functions,game_wise=game_wise)

            if found:
                df=pd.concat([df, df_new])
            else:
                df=df_new
                found=True
            if i%20==0:
                df.to_csv(outfile,index=False)
                
    df.to_csv(outfile,index=False)
    
    return

def process_game_list(outfile,df_in,functions=[],skip_if_processed=True,game_wise=True):
    """
    Processes all games in a list, saves results in outfile as csv
    Good to process files game-wise and concatenate all outputs into one big file

    Parameters:
    - outfile (str): name of the file to store all the outputs
    - df_in (pandas.DataFrame): dataframe of games to process
    - functions (list): List of functions to apply to the games, see read_game
    - skip_if_processed (bool): if True and outfile already exists, skips a file if already processed
    - game_wise (bool): If True, the output has one line per game, else the output has one line per move

    
    Returns: 
    - None
    """

    if os.path.isfile(outfile) and skip_if_processed:
        found=True
        output=pd.read_csv(outfile)
    else:
        found=False
        output=pd.DataFrame()
    i_file=0
    for file in df_in['File'].unique(): # loop over files
        if found and file in output['File'].values and skip_if_processed:
            continue
        print(file)
        data=pd.read_csv(file)
        df_file=df_in.where(df_in['File']==file) # check which training games are in that file
        df_file.dropna(how='any',inplace=True)
        for line in df_file.iterrows(): # loop over games in training set from that file
            data_line=line[1]
            file=data_line['File']
            ind=data_line['LineStart'] # starting line for the game
            assert data.loc[ind, "GameID"]==data_line['GameID'] # sanity checks
            assert not np.isnan(data.loc[ind, "WhiteElo"]) # sanity checks
            ind,game=read_game(data,ind,functions=functions,game_wise=game_wise) # reads a game, rejects it if invalid, outputs a game dictionary
            if game:
                if game_wise:
                    game['File']=file
                    game_df=pd.DataFrame([game])
                    output = pd.concat([output, game_df], ignore_index=True)
                else:
                    for key in game:
                        game[key].append('')
                        # print(game[key])
                    game_df=pd.DataFrame.from_dict(game)
                    output = pd.concat([output, game_df], ignore_index=True)

        if i_file%20==0 and output.shape[0]>0:
            output.to_csv(outfile,index=False)
        i_file+=1
                
    if output.shape[0]>0:
        output.to_csv(outfile,index=False)
    
    return

def rewrite_all_files(suffix,filenames=[],functions=[],skip_if_processed=True,game_wise=False):
    """
    Re-writes each filename, applying a function and adding it a suffix
    Identical to process_all_files, but doesn't concatenate the outputs into one file 
    but makes a new file for each input file in filenames
    Good to process games move-wise

    Parameters:
    - suffix (str): suffix to be appended to the end of each file
    - filenames (list): List of files to process
    - functions (list): List of functions to apply to the games, see read_game
    - skip_if_processed (bool): if True and outfile already exists, skips a file if already processed
    - game_wise (bool): If True, the output has one line per game, else the output has one line per move

    outputs: 
    - None
    """
    
    for file in filenames:
        print(file)
        outfile=os.path.splitext(file)[0]+suffix+'.csv'
        if os.path.isfile(outfile) and skip_if_processed:
            continue
        
        df_new=process_one_file(file,functions,game_wise=game_wise)
        if df_new is None:
            continue
        df_new.to_csv(outfile,index=False)
    
    return