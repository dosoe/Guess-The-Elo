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

def smooth_lines(count_games,bins):

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

if __name__ == "__main__":
    # bin moves in blocks of 5
    bin_moves=5
    file_prefix='../Analyzed_Games/winning_chances_per_move_'+str(bin_moves)+'_001_'
    file_suffix='.csv'
    # make bins for evaluations
    bins=np.arange(-20.005,20.015,0.01)

    # go through all games to get winning chances for each evaluation and move
    files=sorted(glob.glob("../Analyzed_Games/twic*_1[56]_analyzed.csv"))
    # files=['../Analyzed_Games/twic1260_15_analyzed.csv']

    # Get maximum number of moves
    df=pd.read_csv('../Analyzed_Games/games_cleaned.csv')
    df['Moves']=df['MovesWhite']+df['MovesBlack']
    max_moves=df['Moves'].max()
    # bin moves in blocks
    max_moves=max_moves//bin_moves


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
            if game is None or get_outcome(game) is None:
                continue
            for j in range(len(game['Move'])):
                i_bin=np.digitize(game['Evaluation'][j],bins=bins)
                # print(i_bin)
                # print(game['Evaluation'],bins,i_bin)
                # print(get_outcome(game))
                winchance_array[get_outcome(game),i_bin,j//5]+=1
                count_games[i_bin,j//5]+=1
            
            # i_bin=np.digitize(game['Evaluation'],bins=bins)
            # # print(game['Evaluation'],bins,i_bin)
            # # print(get_outcome(game))
            # winchance_array[get_outcome(game),i_bin,np.arange(len(game['Move']))//5]+=1
            # count_games[i_bin,np.arange(len(game['Move']))//5]+=1

    for i in range(3):
        winchance_array[i,:,:]=np.divide(winchance_array[i,:,:],count_games)
    
    for i in range(int(max_moves)+1):

        out_line=winchance_array[:,:,i]
        # out_line=smooth_lines(winchance_array[:,:,i],bins)
        
        bins_new=bins.tolist()
        bins_new.insert(0,'-20-')
        bins_new.append('20+')
        data=pd.DataFrame({'bins':bins_new,'WinningChance':out_line[0,:],
                            'DrawChance':out_line[1,:],
                            'LosingChance':out_line[2,:],
                            'TotalGames':count_games[:,i]})
        data=data[['bins','WinningChance','DrawChance','LosingChance','TotalGames']]
        data.to_csv(file_prefix+str(i)+file_suffix,index=False)


    # # apply get_winning_chance to all games and create new files
    # anal_games.rewrite_all_files(suffix='_winningchance',filenames=files,functions=[(get_winning_chance,{'winchance_array':winchance_array,
    #                                                                                                     'bins':bins,
    #                                                                                                     'bin_moves':bin_moves})],
    #                                                                                                     skip_if_processed=False,game_wise=False)


    # code that creates csv tables for each range of moves
    # fill out missing values in increasing order, impose winning increase, losing decrease
    # code that assemples csvs to numpy array and applies it to all games