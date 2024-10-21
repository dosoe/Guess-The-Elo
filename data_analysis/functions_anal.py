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
game['Variation']
game['Result']
game['Moves']
game["Evaluations"]
I believe these are self-explanatory. 

Output of functions needs to be a dictionary. Each key of the dictionary will create a new row in the output DataFrame, so it needs to be compatible with it (for example, no lists)
"""

def WhiteAvgEvaluation(game):
    evals=game['Evaluations']
    ev_sum=0
    mv=0
    for i in range(len(game['Moves'])):
        if i%2==0:
            mv+=1.
            ev_sum+=evals[i]
    if mv==0:
        return {'WhiteAvgEvaluation':-100,'MovesWhite':0}
    else:
        return {'WhiteAvgEvaluation':ev_sum/mv,'MovesWhite':mv} # functions can have more than one output

def BlackAvgEvaluation(game):
    evals=game['Evaluations']
    ev_sum=0
    mv=0
    for i in range(len(game['Moves'])):
        if i%2==1:
            mv+=1.
            ev_sum+=evals[i]
    if mv==0:
        return {'BlackAvgEvaluation':-100}
    else:
        return {'BlackAvgEvaluation':ev_sum/mv}

def MovesBlack(game):
    mv=0
    for i in range(len(game['Moves'])):
        if i%2==1:
            mv+=1.
    return {'MovesBlack':mv}