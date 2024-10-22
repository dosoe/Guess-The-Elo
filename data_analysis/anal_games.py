import numpy as np
import pandas as pd
import glob,os
import functions_anal

def read_game(data,ind,functions=[],game_wise=True):
    """
    df: csv that contains the games
    ind: the line we are in right now
    functions: a list of functions to be applied on the game
    return:
    ind: The index of the line we ended on
    game: a dictionary of the game preperties, including the result of functions
    None if the game is not valid. This happens
    either because one of the players doesn't have a fide id (it's a bot)
    or because the game has no moves
    game_wise: are the outputs game-wise, i e one value per game, or move-wise i e one value per move

    Takes functions as input, these will be applied to each game if game_wise=True 
    or to each move if game_wise=False

    Examples can be found in functions_anal.py
    Function outputs are stored in 
    game[function_name] (fetched with function.__name__)
    """
    game={}
    gameid=data.loc[ind,"GameID"]
    game_used=True
    try: # reject games with no Fide ID for black or white
        if np.isnan(float(data.loc[ind,"WhiteFideId"])) or np.isnan(float(data.loc[ind,"BlackFideId"])):
            game_used=False
    except ValueError: # reject games where the file does not have FideIDs
        game_used=False
    if game_used: # read game metadata
        game['GameID']=data.loc[ind,"GameID"]
        game['WhiteName']=data.loc[ind,"WhiteName"]
        game['BlackName']=data.loc[ind,"BlackName"]
        game['WhiteElo']=data.loc[ind,"WhiteElo"]
        game['BlackElo']=data.loc[ind,"BlackElo"]
        game['LineStart']=ind
        try:
            game['WhiteFideId']=int(data.loc[ind,"WhiteFideId"])
            game['BlackFideId']=int(data.loc[ind,"BlackFideId"])
        except:
            game_used=False
        game['Year']=data.loc[ind,"Year"]
        game['Opening']=data.loc[ind,"Opening"]
        game['Variation']=data.loc[ind,"Variation"]
        game['Result']=data.loc[ind,"Result"]
        if game['Result']=='*':
            game_used=False
        game_moves=[]
        game_evals=[]

    while ind<len(data) and data.loc[ind,"GameID"]==gameid: # read game moves      
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
        game['Move']=game_moves
        game["Evaluation"]=game_evals
        for function in functions: # apply functions to games
            if callable(function): # function is actually a function
                out_tmp=function(game)
            else: # function is a tuple containing the function and a dictionary containing additional inputs
                out_tmp=function[0](game,function[1])
            if out_tmp is None: # if output is None, game is rejected
                game_used=False
                continue
            for key in out_tmp: # put outputs of functions to games
                game[key]=out_tmp[key]
        if game_wise:
            del game['Move']
            del game['Evaluation']
        
        game['LineEnd']=ind
    if game_used:
        if game_wise:
            return ind,game
        else:
            out={}
            for key in ['WhiteName','BlackName','WhiteElo','BlackElo','WhiteFideId','BlackFideId','Year','Opening','Variation','Result']:
                out[key]=[game[key]]+(len(game['Move'])-1)*['']
                out['Move']=game['Move']
                out['Evaluation']=game['Evaluation']
                out['GameID']=(len(game['Move']))*[game['GameID']]
                out['MoveNumber']=list(range(1,len(game['Move'])+1))
            return ind,out
    else:
        return ind,None

def process_one_file(filename,functions=[],game_wise=True):
    """
    Processes one file
    inputs:
    filename: name of the file to process
    functions: list of functions to apply to each game
    game_wise: functions applied game-wise or move-wise?
    
    outputs:
    games: DataFrame containing the outputs
    """

    games={}
    if game_wise:
        games['File']=[]

    data=pd.read_csv(filename)
    if not 'WhiteFideId' in data:
        print(filename,'has no fide ids')
        return
    ind=0
    while ind<len(data):
        # reads game and returns index of last line of the game (empty line)
        ind,game=read_game(data,ind,functions=functions,game_wise=game_wise)
        ind+=1
        # puts output of read_game in a dictionary that will be converted into csv at the end
        if game:
            if game_wise:
                games['File'].append(filename)
            for key in game:
                if key in games:
                    if game_wise:
                        games[key].append(game[key])
                    else:
                        games[key].extend(game[key])
                        games[key].append('')
                else:
                    if game_wise:
                        games[key]=[game[key]]
                    else: 
                        games[key]=game[key]
                        games[key].append('')
    return pd.DataFrame(games)

def process_all_files(outfile,filenames=[],functions=[],skip_if_processed=True,game_wise=True):
    """
    Processes all files, saves results in outfile as csv
    inputs:
    outfile: name of the file to store all the outputs
    filenames: List of files to process
    functions: List of functions to apply to the games
    skip_if_processed: if True and outfile already exists, skips a file if already processed

    good to process files game-wise and concatenate all outputs into one big file
    outputs: 
    None
    """
    found=False
    if os.path.isfile(outfile):
        found=True
        df=pd.read_csv(outfile)
    
    for i,file in enumerate(filenames):
        if found and file in df['File'].values and skip_if_processed:
            continue
        else:
            df_new=process_one_file(file,functions,game_wise=game_wise)

            if found:
                df=pd.concat([df, df_new])
            else:
                df=df_new
                found=True
            if i%20==0:
                df.to_csv(outfile)
    df.to_csv(outfile)
    
    return

def rewrite_all_files(suffix,filenames=[],functions=[],skip_if_processed=True,game_wise=False):
    """
    Re-writes each filename adding it a suffix
    else identical to process_all_files, just doesn't concatenate the outputs but makes a new file for each input file in filenames
    Good to process games move-wise
    """
    
    for file in filenames:
        print(file)
        outfile=os.path.splitext(file)[0]+suffix+'.csv'
        if os.path.isfile(outfile) and skip_if_processed:
            continue
        
        df_new=process_one_file(file,functions,game_wise=game_wise)
        
        df_new.to_csv(outfile)
    
    return


if __name__ == "__main__":

    filenames = sorted(glob.glob("../Analyzed_Games/twic*analyzed.csv"))
    
    outfile='../Analyzed_Games/games_cleaned.csv'

    process_all_files(outfile,filenames,[functions_anal.Cleanup],skip_if_processed=True,game_wise=True)

    # filenames = sorted(glob.glob("../Analyzed_Games/twic*analyzed.csv"))[:10]
    print(filenames)

    rewrite_all_files('_cleaned',filenames=filenames,functions=[functions_anal.Cleanup],skip_if_processed=True,game_wise=False)

    # functions=[functions_anal.MovesBlack,
    #            functions_anal.WhiteAvgEvaluation,
    #            functions_anal.BlackAvgEvaluation]
    
    # outfile='../Analyzed_Games/avgeval_example.csv'

    # process_all_files(outfile,filenames,functions,skip_if_processed=True)

    # functions=[functions_anal.Cleanup]
    
    # outfile='../Analyzed_Games/cleanup_example.csv'

    # process_all_files(outfile,filenames,functions,skip_if_processed=True)

    # functions=[(functions_anal.NmoveMove,{'movenum':5})]
    
    # outfile='../Analyzed_Games/additional_inputs_example.csv'

    # process_all_files(outfile,filenames,functions,skip_if_processed=True)