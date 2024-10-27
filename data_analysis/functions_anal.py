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

# remove games with no fide ids for one or other player
# games where result is *
# games with less than 15 moves which are draws (?)