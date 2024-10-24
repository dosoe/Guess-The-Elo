import pandas as pd
import numpy as np
import glob, os
import anal_games, functions_anal
import pickle

def get_outcome(game): # convert outcome string into index
    result=game['Result'][0]
    if result == '1-0':
        return 0    # White won
    elif result == '0-1':
        return 2   # White lost
    elif result == '1/2-1/2':
        return 1   # Draw
    else:
        return None     # Exclude other results

# bin moves in blocks of 5
bin_moves=5
file_save='../Analyzed_Games/winning_chances_per_move_'+str(bin_moves)+'.pkl'

# go through all games to get winning chances for each evaluation and move
files=sorted(glob.glob("../Analyzed_Games/twic*_1[56]_analyzed.csv"))

if os.path.isfile(file_save):
    # Open the file in binary mode 
    with open(file_save, 'rb') as file: 
        
        # Call load method to deserialze 
        winchance_array = pickle.load(file) 
    
else:
    # Get maximum number of moves
    df=pd.read_csv('../Analyzed_Games/games_cleaned.csv')
    df['Moves']=df['MovesWhite']+df['MovesBlack']
    max_moves=df['Moves'].max()
    # bin moves in blocks
    max_moves=max_moves//bin_moves

    # make bins for evaluations
    bins=np.arange(-20,20.1,0.1)
    suffix='_winningchance'

    # make array for winning chances
    winchance_array=np.zeros((3,len(bins)+2,int(max_moves)+1)) # +2 to account for values out of bounds, +1 for moves that are bigger than max_moves//5 * 5 
    count_games=np.zeros((len(bins)+2,int(max_moves)+1))

    for file in files:
        data=pd.read_csv(file)
        print(file)
        ind=0
        while ind<len(data):
            ind,game=anal_games.read_game(data,ind,functions=[functions_anal.Cleanup],game_wise=False) # reads a game, rejects it if invalid, outputs a game dictionary
            ind+=1
            if game is None:
                continue
            i_bin=np.digitize(game['Evaluation'],bins=bins)
            winchance_array[get_outcome(game),i_bin,np.arange(len(game['Move']))//5]+=1
            count_games[i_bin,np.arange(len(game['Move']))//5]+=1

    for i in range(3):
        winchance_array[i,:,:]=np.divide(winchance_array[i,:,:],count_games)

    with open(file_save, 'wb') as file: 
        
        # A new file will be created 
        pickle.dump(winchance_array, file) 

def get_winning_chance(game): # make function that gives winning chance for each move using the array created previously
    return {'WinningChance': winchance_array[0,np.digitize(game['Evaluation'],bins=bins),np.arange(len(game['Move']))//bin_moves].tolist()}

# apply get_winning_chance to all games and create new files
anal_games.rewrite_all_files(suffix='_winningchance',filenames=files,functions=[get_winning_chance],skip_if_processed=False,game_wise=False)


