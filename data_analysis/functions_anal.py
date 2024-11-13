"""
Functions to apply to games
Functions take as input a 
game: dictionary with the following keys: 
game['GameID']    # gameid of the game in the file
game['WhiteName']
game['BlackName']
game['WhiteElo']
game['BlackElo']
game['LineStart']
game['WhiteFideId']
game['BlackFideId']
game['Year']
game['Opening']
game['Variation']g
game['Result']
game['Move']
game["Evaluation"]
I believe these are self-explanatory. 

Output of functions needs to be a dictionary, or None. Each key of the dictionary will create a new row in the output DataFrame, so it needs to be compatible with it (for example, no lists)
If the output is None, the game is rejected (can be used for cleanup)

Functions can have additional arbuments, they need to be provided in an additional dictionary of arguments
"""

import pandas as pd
import glob, os, re, sys
import numpy as np

def WhiteAvgEvaluation(game):
    evals=game['Evaluation']
    ev_sum=0
    mv=0
    for i in range(len(game['Move'])):
        if i%2==0:
            mv+=1.
            ev_sum+=evals[i]
    if mv==0:
        return {'WhiteAvgEvaluation':-100,'MovesWhite':0}
    else:
        return {'WhiteAvgEvaluation':ev_sum/mv,'MovesWhite':mv} # functions can have more than one output

def BlackAvgEvaluation(game):
    evals=game['Evaluation']
    ev_sum=0
    mv=0
    for i in range(len(game['Move'])):
        if i%2==1:
            mv+=1.
            ev_sum+=evals[i]
    if mv==0:
        return {'BlackAvgEvaluation':-100}
    else:
        return {'BlackAvgEvaluation':ev_sum/mv}

def MovesBlack(game):
    mv=0
    for i in range(len(game['Move'])):
        if i%2==1:
            mv+=1.
    return {'MovesBlack':mv}

def MovesWhite(game):
    mv=0
    for i in range(len(game['Move'])):
        if i%2==0:
            mv+=1.
    return {'MovesWhite':mv}

def NmoveMove(game,additional_inputs):
    """
    Example of function with additional arguments
    takes a game and a dictionary containing the additional inputs
    returns a dictionary
    In this example, returns a dictionary containing the move number n, with n=additional_inputs['movenum']
    and if the game has less than n moves, the game is rejected
    """
    # gives move number n, with n=additional_inputs['movenum']
    movenum=additional_inputs['movenum']
    if len(game['Move'])>=movenum:
        return {'Move_'+str(movenum):game['Moves'][movenum-1]}
    else:
        return None

def Cleanup(game):
    """
    Example of function just for cleaning up
    takes a game
    returns either None if the game is rejected or an empty dictionary
    In this example, we reject games with no known results or games with less than 15 moves
    """
    if game['Result']=='*':
        return None
    if len(game['Move'])<15 and game['Result']=='1/2-1/2':
        return None
    else:
        return {}

dir_win_chances="../winning_chances_tables/"
winchances={}
bins_moves=[]
winchances=[]
losechances=[]
drawchances=[]
bins_eval=[]
for i,file in enumerate(glob.glob(dir_win_chances+"/*")):
    filename=file.split('/')[-1].split('.')[0]
    num_moves_start=int(filename.split('_')[-1].split('-')[0])
    num_moves_end=int(filename.split('_')[-1].split('-')[1])
    bins_moves.append(num_moves_end+1)
    data=pd.read_csv(file)
    if i==0:
        intervals=data['Interval']
        for interval in intervals[:-1]:
            top=interval.split(',')[1]
            bins_eval.append(float(top[:-1]))
    winchances.append(data['WinningChance'].to_numpy(dtype=float))
    losechances.append(data['LosingChance'].to_numpy(dtype=float))
    drawchances.append(data['DrawingChance'].to_numpy(dtype=float))
    # print(file)
    # print(data['WinningChance'])

# print(bins_moves[0],winchances[0])

bins_moves, winchances, losechances, drawchances=(list(t) for t in zip(*sorted(zip(bins_moves, winchances, losechances, drawchances))))

bins_moves.insert(0,0)
assert len(winchances[0])==len(bins_eval)+1

bins_moves=np.array(bins_moves)
winchances=np.array(winchances)
losechances=np.array(losechances)
drawchances=np.array(drawchances)

# print(winchances[1,:])

# sys.exit()

def WinChanceIncrease(game,additional_inputs):

    mv_min=additional_inputs['mv_min']
    mv_max=additional_inputs['mv_max']

    num_moves=len(game['Move'])

    if num_moves<mv_min or num_moves>=mv_max:
        return None
    
    winchance=np.zeros((num_moves))
    losechance=np.zeros((num_moves))
    for i in range(num_moves):
        i_move=np.digitize(i,bins=bins_moves)-1
        # print(i,i_move,bins_moves)
        i_eval=np.digitize(game['Evaluation'][i],bins=bins_eval)
        # print(game['Evaluation'][i],i_eval,bins_eval[i_eval],bins_eval)
        # print(np.shape(winchances))
        # print(i_move,i_eval,winchance[i],winchances[i_move,i_eval])
        winchance[i]=winchances[i_move,i_eval]
        # print(winchances[i_move,:])
        losechance[i]=losechances[i_move,i_eval]

    windiff=winchance[1:]-winchance[:-1]
    losediff=losechance[1:]-losechance[:-1]

    out={}
    out['white_WCL_'+str(0)]=0.
    for i in range(1,num_moves):
        if i%2==0:
            if i==0:
                continue
            out['white_WCL_'+str(i//2)]=windiff[i-1]
        else:
            out['black_LCL_'+str(i//2)]=losediff[i-1]
    
    return out
