

def WhiteAvgEvaluation(game):
    evals=game['Evaluations']
    ev_sum=0
    mv=0
    for i in range(len(game['Moves'])):
        if i%2==0:
            mv+=1.
            ev_sum+=evals[i]
    if mv==0:
        return -100
    else:
        return ev_sum/mv

def MovesWhite(game):
    mv=0
    for i in range(len(game['Moves'])):
        if i%2==0:
            mv+=1.

    return mv

def BlackAvgEvaluation(game):
    evals=game['Evaluations']
    ev_sum=0
    mv=0
    for i in range(len(game['Moves'])):
        if i%2==1:
            mv+=1.
            ev_sum+=evals[i]
    if mv==0:
        return -100
    else:
        return ev_sum/mv

def MovesBlack(game):
    mv=0
    for i in range(len(game['Moves'])):
        if i%2==1:
            mv+=1.
    return mv