import anal_games
import pandas as pd
import winning_chances_util
import numpy as np

df=pd.read_csv('../Cleaned_Analyzed_Games/all_games_cleaned_train.csv')

process_by_move=False


if process_by_move:
    movebins=np.arange(0,700,5)

    # read winning chance tables
    wc_tables=winning_chances_util.read_winning_tables(dir='../winning_chances_tables/',movebins=movebins)
    for i in range(0,600,5):

        # bin moves
        wc_tables['mv_min']=i
        wc_tables['mv_max']=i+5

        print(list(df))

        # only process games with moves in bin
        df_moves=df.where(df['MovesAll']>=i)
        df_moves=df_moves.where(df['MovesAll']<i+5)
        df_moves.dropna(how='any',inplace=True)

        # get win chance loss table
        anal_games.process_game_list('../Cleaned_Analyzed_Games/wcl_train_'+str(i)+'-'+str(i+5)+'.csv',df_moves,functions=[(winning_chances_util.WinChanceIncrease,wc_tables)],skip_if_processed=True,game_wise=True)

        print('../Cleaned_Analyzed_Games/wcl_train_'+str(i)+'-'+str(i+5)+'.csv')

        try:
            df_out=pd.read_csv('../Cleaned_Analyzed_Games/wcl_train_'+str(i)+'-'+str(i+5)+'.csv')
        except:
            continue

        # get data for white player
        data_white=df_out.filter(regex='White*',axis='columns')
        for feature in ['Opening','Variation','Result','GameID','LineStart','File']: # Which additional features we want
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
        
        # same for black player
        data_black=df_out.filter(regex='Black*',axis='columns')
        for feature in ['Opening','Variation','Result']:
            data_black[feature]=df_out[feature]
        
        for feature in data_black:
            if feature[:6]=='Black_':
                data_black[feature[6:]]=data_black[feature]
                data_black.drop(feature,axis=1,inplace=True)
            elif feature[:5]=='Black':
                data_black[feature[5:]]=data_black[feature]
                data_black.drop(feature,axis=1,inplace=True)
        data_black['Player']='Black'

        # merge and save black and white tables
        data=pd.concat([data_white, data_black], ignore_index=True)
        data.to_csv('../Cleaned_Analyzed_Games/wcl_train_'+str(i)+'-'+str(i+5)+'_by_player.csv',index=False)

if not process_by_move: # same for global winning chance tables (winning chances not calculated by move)
    movebins='all'

    # read winning chance tables
    wc_tables=winning_chances_util.read_winning_tables(dir='../winning_chances_tables/',movebins=movebins)

    for i in range(0,600,5):

        wc_tables['mv_min']=i
        wc_tables['mv_max']=i+5
        print(list(df))

        df_moves=df.where(df['MovesAll']>=i)
        df_moves=df_moves.where(df['MovesAll']<i+5)
        df_moves.dropna(how='any',inplace=True)
        anal_games.process_game_list('../Cleaned_Analyzed_Games/wcl_train_all_'+str(i)+'-'+str(i+5)+'.csv',df_moves,functions=[(winning_chances_util.WinChanceIncrease,wc_tables)],skip_if_processed=True,game_wise=True)

        print('../Cleaned_Analyzed_Games/wcl_train_all_'+str(i)+'-'+str(i+5)+'.csv')

        try:

            df_out=pd.read_csv('../Cleaned_Analyzed_Games/wcl_train_all_'+str(i)+'-'+str(i+5)+'.csv')
        except:
            continue
        
        data_white=df_out.filter(regex='White*',axis='columns') 
        for feature in ['Opening','Variation','Result','GameID','LineStart','File']:
            data_white[feature]=df_out[feature]
        for feature in data_white:
            if feature[:6]=='White_':
                data_white[feature[6:]]=data_white[feature]
                data_white.drop(feature,axis=1,inplace=True)
            elif feature[:5]=='White':
                data_white[feature[5:]]=data_white[feature]
                data_white.drop(feature,axis=1,inplace=True)

        data_white['Player']='White'
        
        data_black=df_out.filter(regex='Black*',axis='columns') 
        for feature in ['Opening','Variation','Result']:
            data_black[feature]=df_out[feature]
        
        for feature in data_black:
            if feature[:6]=='Black_':
                data_black[feature[6:]]=data_black[feature]
                data_black.drop(feature,axis=1,inplace=True)
            elif feature[:5]=='Black':
                data_black[feature[5:]]=data_black[feature]
                data_black.drop(feature,axis=1,inplace=True)
        data_black['Player']='Black'

        data=pd.concat([data_white, data_black], ignore_index=True)
        data.to_csv('../Cleaned_Analyzed_Games/wcl_train_all_'+str(i)+'-'+str(i+5)+'_by_player.csv',index=False)
