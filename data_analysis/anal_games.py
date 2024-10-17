import numpy as np
import pandas as pd
import glob
import functions_anal

def read_game(data,ind,functions=[]):
    """
    df: csv that contains the games
    ind: the line we are in right now
    return:
    None if the game is not valid. This happens
    either because one of the players doesn't have a fide id (it's a bot)
    or because the game has no moves
    """
    game={}
    gameid=data.loc[ind,"GameID"]
    game_used=True
    if np.isnan(data.loc[ind,"WhiteFideId"]) or np.isnan(data.loc[ind,"BlackFideId"]):
        game_used=False
    if game_used:
        game['File']=filename
        game['GameID']=data.loc[ind,"GameID"]
        game['WhiteName']=data.loc[ind,"WhiteName"]
        game['BlackName']=data.loc[ind,"BlackName"]
        game['WhiteElo']=data.loc[ind,"WhiteElo"]
        game['BlackElo']=data.loc[ind,"BlackElo"]
        game['LineStart']=ind
        try:
            game['WhiteFideId']=data.loc[ind,"WhiteFideId"]
            game['BlackFideId']=data.loc[ind,"BlackFideId"]
        except:
            game['WhiteFideId']=0
            game['BlackFideId']=0
            pass
        game['Year']=data.loc[ind,"Year"]
        game['Opening']=data.loc[ind,"Opening"]
        game['Variation']=data.loc[ind,"Variation"]
        game['Result']=data.loc[ind,"Result"]
        game_moves=[]
        game_evals=[]

    while ind<len(data) and data.loc[ind,"GameID"]==gameid:            
        if game_used:
            game_moves.append(data.loc[ind,"Move"])
            try:
                game_evals.append(float(data.loc[ind,"Evaluation"]))
            except:
                if data.loc[ind,"Evaluation"][0]=='-':
                    game_evals.append(-7)
                elif data.loc[ind,"Evaluation"][0]=='M':
                    game_evals.append(7)
        ind+=1
    
    if game_used:
        game['Moves']=game_moves
        game["Evaluations"]=game_evals
        for function in functions:
            game[function.__name__]=function(game)
        
        game['LineEnd']=ind-1
    if game_used:
        return ind,game
    else:
        return ind,None

if __name__ == "__main__":

    games={}
    games['File']=[]
    games['GameID']=[]
    games['WhiteName']=[]
    games['BlackName']=[]
    games['WhiteElo']=[]
    games['BlackElo']=[]
    games['WhiteFideId']=[]
    games['BlackFideId']=[]
    games['Year']=[]
    games['Opening']=[]
    games['Variation']=[]
    games['Result']=[]
    games['WhiteAvgEvaluation']=[]
    games['BlackAvgEvaluation']=[]
    games['MovesWhite']=[]
    games['MovesBlack']=[]
    games['LineStart']=[]
    games['LineEnd']=[]

    game_ended=True
    game_used=True
    game=0
    for filename in glob.glob("../Analyzed_Games/*"):
        print(filename)
        data=pd.read_csv(filename)
        if not 'WhiteFideId' in data:
            print(filename,'has no fide ids')
            continue
        ind=0
        while ind<len(data):
            ind,game=read_game(data,ind,functions=[functions_anal.MovesWhite,
                                                functions_anal.MovesBlack,
                                                functions_anal.WhiteAvgEvaluation,
                                                functions_anal.BlackAvgEvaluation])
            ind+=1
            if game:
                games['File'].append(game['File'])
                games['GameID'].append(game['GameID'])
                games['WhiteName'].append(game['WhiteName'])
                games['BlackName'].append(game['BlackName'])
                games['WhiteElo'].append(game['WhiteElo'])
                games['BlackElo'].append(game['BlackElo'])
                games['WhiteFideId'].append(game['WhiteFideId'])
                games['BlackFideId'].append(game['BlackFideId'])
                games['Year'].append(game['Year'])
                games['Opening'].append(game['Opening'])
                games['Variation'].append(game['Variation'])
                games['Result'].append(game['Result'])
                games['WhiteAvgEvaluation'].append(game['WhiteAvgEvaluation'])
                games['BlackAvgEvaluation'].append(game['BlackAvgEvaluation'])
                games['MovesWhite'].append(game['MovesWhite'])
                games['MovesBlack'].append(game['MovesBlack'])
                games['LineStart'].append(game['LineStart'])
                games['LineEnd'].append(game['LineEnd'])

        
    for key in games:
        print(key,len(games[key]))
    games_df=pd.DataFrame(games)
    games_df.to_csv('../Analyzed_Games/games.csv')