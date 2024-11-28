import anal_games
import pandas as pd
import winning_chances_util
import numpy as np
from multiprocessing import Pool
import copy
import sys
import concurrent.futures
import functions_anal

def WCL_by_player(mv_start,mv_end,all=False,train=True):
    filename='../Cleaned_Analyzed_Games/wcl_'
    if train:
        filename+='train_'
    else:
        filename+='test_'
    if all:
        filename+='all_'
    if mv_end==None:
        filename+=str(mv_start)+'-'
    else:
        filename+=str(mv_start)+'-'+str(mv_end)
    filename+='.csv'
    print(filename)
    try:
        df_out=pd.read_csv(filename)
    except:
        print('Error in WCL_by_player: File ' ,filename, ' does not exist')

    # get data for white player
    data_white=df_out.filter(regex='White*',axis='columns')
    print(list(df_out))
    for feature in ['Opening','Variation','Result','GameID','LineStart','File','MovesWhite']: # Which additional features we want
        data_white[feature]=df_out[feature]
    # rename white player features
    for feature in data_white:
        if feature[:6]=='White_':
            data_white[feature[6:]]=data_white[feature]
            data_white.drop(feature,axis=1,inplace=True)
        elif feature[:5]=='White':
            data_white[feature[5:]]=data_white[feature]
            data_white.drop(feature,axis=1,inplace=True)

    data_white['Player']='White'
    data_white['Moves']='MovesWhite'
    data_white.drop('MovesWhite',axis=1,inplace=True)
    
    # same for black player
    data_black=df_out.filter(regex='Black*',axis='columns')
    for feature in ['Opening','Variation','Result','GameID','LineStart','File','MovesBlack']:
        data_black[feature]=df_out[feature]
    
    for feature in data_black:
        if feature[:6]=='Black_':
            data_black[feature[6:]]=data_black[feature]
            data_black.drop(feature,axis=1,inplace=True)
        elif feature[:5]=='Black':
            data_black[feature[5:]]=data_black[feature]
            data_black.drop(feature,axis=1,inplace=True)
    data_black['Player']='Black'
    data_black['Moves']='MovesBlack'
    data_black.drop('MovesBlack',axis=1,inplace=True)

    # merge and save black and white tables
    data=pd.concat([data_white, data_black], ignore_index=True)

    filename_out='../Cleaned_Analyzed_Games/wcl_'
    print(train)
    if train:
        filename_out+='train_'
    else:
        filename_out+='test_'
    if all:
        filename_out+='all_'
    if mv_end==None:
        filename_out+=str(mv_start)
    else:
        filename_out+=str(mv_start)+'-'+str(mv_end)
    filename_out+='_by_player.csv'

    print(filename_out)
    data.to_csv(filename_out,index=False)

    return


df_train=pd.read_csv('../Cleaned_Analyzed_Games/all_games_cleaned_train.csv')

df_test=pd.read_csv('../Cleaned_Analyzed_Games/all_games_cleaned_test.csv')

process_by_move=False # do we want to have one winning table, or one for each move bracket?

num_workers=15

move_bins=np.arange(0,150,5)

# if process_by_move:

movebins=move_bins
wc_tables=winning_chances_util.read_winning_tables(dir='../winning_chances_tables/',movebins=movebins)
args = []
i_process=0

for i in range(len(move_bins)-1):

    
    wc_tables_new=copy.deepcopy(wc_tables)

    # bin moves
    wc_tables_new['mv_min']=move_bins[i]
    wc_tables_new['mv_max']=move_bins[i+1]

    # only process games with moves in bin
    df_moves=df_train.where(df_train['MovesAll']>=move_bins[i])
    df_moves=df_moves.where(df_moves['MovesAll']<move_bins[i+1])
    df_moves.dropna(how='any',inplace=True)

    if df_moves.shape[0]==0:
        continue

    args.append(('../Cleaned_Analyzed_Games/wcl_train_'+str(move_bins[i])+'-'+str(move_bins[i+1])+'.csv',df_moves,[(winning_chances_util.WinChanceIncrease,wc_tables_new),functions_anal.MovesWhite,functions_anal.MovesBlack],True,True))
    i_process+=1

wc_tables_new=copy.deepcopy(wc_tables)
wc_tables_new['mv_min']=move_bins[-1]
wc_tables_new['mv_max']=100000
# only process games with moves in bin
df_moves=df_train.where(df_train['MovesAll']>=move_bins[-1])
df_moves=df_moves.where(df_train['MovesAll']<100000)
df_moves.dropna(how='any',inplace=True)
args.append(('../Cleaned_Analyzed_Games/wcl_train_'+str(move_bins[-1])+'-.csv',df_moves,[(winning_chances_util.WinChanceIncrease,wc_tables_new),functions_anal.MovesWhite,functions_anal.MovesBlack],False,True))
i_process+=1

for i in range(len(move_bins)-1):

    
    wc_tables_new=copy.deepcopy(wc_tables)

    # bin moves
    wc_tables_new['mv_min']=move_bins[i]
    wc_tables_new['mv_max']=move_bins[i+1]

    # only process games with moves in bin
    df_moves=df_test.where(df_test['MovesAll']>=move_bins[i])
    df_moves=df_moves.where(df_moves['MovesAll']<move_bins[i+1])
    df_moves.dropna(how='any',inplace=True)

    if df_moves.shape[0]==0:
        continue

    args.append(('../Cleaned_Analyzed_Games/wcl_test_'+str(move_bins[i])+'-'+str(move_bins[i+1])+'.csv',df_moves,[(winning_chances_util.WinChanceIncrease,wc_tables_new),functions_anal.MovesWhite,functions_anal.MovesBlack],True,True))
    i_process+=1

wc_tables_new=copy.deepcopy(wc_tables)
wc_tables_new['mv_min']=move_bins[-1]
wc_tables_new['mv_max']=100000
# only process games with moves in bin
df_moves=df_test.where(df_test['MovesAll']>=move_bins[-1])
df_moves=df_moves.where(df_test['MovesAll']<100000)
df_moves.dropna(how='any',inplace=True)
args.append(('../Cleaned_Analyzed_Games/wcl_test_'+str(move_bins[-1])+'-.csv',df_moves,[(winning_chances_util.WinChanceIncrease,wc_tables_new),functions_anal.MovesWhite,functions_anal.MovesBlack],True,True))
i_process+=1

with concurrent.futures.ProcessPoolExecutor(max_workers=num_workers) as executor:
    tasks = []
    for argument in args:
        tasks.append(executor.submit(anal_games.process_game_list, argument[0],argument[1],argument[2],argument[3],argument[4]))


for i in range(len(move_bins[:-1])):

    WCL_by_player(move_bins[i],move_bins[i+1],all=False,train=True)

WCL_by_player(move_bins[-1],None,all=False,train=True)

for i in range(len(move_bins[:-1])):

    WCL_by_player(move_bins[i],move_bins[i+1],all=False,train=False)

WCL_by_player(move_bins[-1],None,all=False,train=False)

# if not process_by_move: # same for global winning chance tables (winning chances not calculated by move)
movebins='all'

wc_tables=winning_chances_util.read_winning_tables(dir='../winning_chances_tables/',movebins=movebins)
args = []
i_process=0

for i in range(len(move_bins)-1):

    
    wc_tables_new=copy.deepcopy(wc_tables)

    # bin moves
    wc_tables_new['mv_min']=move_bins[i]
    wc_tables_new['mv_max']=move_bins[i+1]

    # only process games with moves in bin
    df_moves=df_train.where(df_train['MovesAll']>=move_bins[i])
    df_moves=df_moves.where(df_moves['MovesAll']<move_bins[i+1])
    df_moves.dropna(how='any',inplace=True)

    if df_moves.shape[0]==0:
        continue

    args.append(('../Cleaned_Analyzed_Games/wcl_train_all_'+str(move_bins[i])+'-'+str(move_bins[i+1])+'.csv',df_moves,[(winning_chances_util.WinChanceIncrease,wc_tables_new),functions_anal.MovesWhite,functions_anal.MovesBlack],True,True))
    i_process+=1

wc_tables_new=copy.deepcopy(wc_tables)
wc_tables_new['mv_min']=move_bins[-1]
wc_tables_new['mv_max']=100000
# only process games with moves in bin
df_moves=df_train.where(df_train['MovesAll']>=move_bins[-1])
df_moves=df_moves.where(df_train['MovesAll']<100000)
df_moves.dropna(how='any',inplace=True)
args.append(('../Cleaned_Analyzed_Games/wcl_train_all_'+str(move_bins[-1])+'-.csv',df_moves,[(winning_chances_util.WinChanceIncrease,wc_tables_new),functions_anal.MovesWhite,functions_anal.MovesBlack],True,True))
i_process+=1

for i in range(len(move_bins)-1):

    
    wc_tables_new=copy.deepcopy(wc_tables)

    # bin moves
    wc_tables_new['mv_min']=move_bins[i]
    wc_tables_new['mv_max']=move_bins[i+1]

    # only process games with moves in bin
    df_moves=df_test.where(df_test['MovesAll']>=move_bins[i])
    df_moves=df_moves.where(df_moves['MovesAll']<move_bins[i+1])
    df_moves.dropna(how='any',inplace=True)

    if df_moves.shape[0]==0:
        continue

    args.append(('../Cleaned_Analyzed_Games/wcl_test_all_'+str(move_bins[i])+'-'+str(move_bins[i+1])+'.csv',df_moves,[(winning_chances_util.WinChanceIncrease,wc_tables_new),functions_anal.MovesWhite,functions_anal.MovesBlack],True,True))
    i_process+=1

wc_tables_new=copy.deepcopy(wc_tables)
wc_tables_new['mv_min']=move_bins[-1]
wc_tables_new['mv_max']=100000
# only process games with moves in bin
df_moves=df_test.where(df_test['MovesAll']>=move_bins[-1])
df_moves=df_moves.where(df_test['MovesAll']<100000)
df_moves.dropna(how='any',inplace=True)
args.append(('../Cleaned_Analyzed_Games/wcl_test_all_'+str(move_bins[-1])+'-.csv',df_moves,[(winning_chances_util.WinChanceIncrease,wc_tables_new),functions_anal.MovesWhite,functions_anal.MovesBlack],True,True))
i_process+=1

with concurrent.futures.ProcessPoolExecutor(max_workers=num_workers) as executor:
    tasks = []
    for argument in args:
        tasks.append(executor.submit(anal_games.process_game_list, argument[0],argument[1],argument[2],argument[3],argument[4]))

for i in range(len(move_bins[:-1])):

    WCL_by_player(move_bins[i],move_bins[i+1],all=True,train=True)

WCL_by_player(move_bins[-1],None,all=True,train=True)

for i in range(len(move_bins[:-1])):

    WCL_by_player(move_bins[i],move_bins[i+1],all=True,train=False)

WCL_by_player(move_bins[-1],None,all=True,train=False)