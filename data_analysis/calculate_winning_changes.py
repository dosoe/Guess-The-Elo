import pandas as pd
import numpy as np
import glob, os, sys
import anal_games, functions_anal
import pickle, re
from sklearn.model_selection import train_test_split
import winning_chances_util

# Get the list of filenames matching the patterns
filenames_15 = glob.glob("../Cleaned_Analyzed_Games/twic*_15_processed.csv")
filenames_16 = glob.glob("../Cleaned_Analyzed_Games/twic*_16_processed.csv")

# For dupes, use the bigger depth
filenames_to_process=filenames_16
for file in filenames_15:
    if '_'.join(file.split('_')[:3])+'_16_processed.csv' in filenames_to_process:
        continue
    else:
        filenames_to_process.append(file)

outfile='../Cleaned_Analyzed_Games/all_games_cleaned.csv'

# make list of games 
# anal_games.process_all_files(outfile=outfile,filenames=filenames_to_process,functions=[functions_anal.MovesTotal,functions_anal.Cleanup,functions_anal.MovesBlack,functions_anal.MovesWhite],skip_if_processed=True,game_wise=True)

df=pd.read_csv(outfile)

dupes=df.duplicated(keep=False,subset=['GameID','File'])

dupes=dupes.where(dupes) #
dupes.dropna(how='any',inplace=True)
print(len(dupes))
print(dupes)

sys.exit()

df_train,df_test=train_test_split(df,test_size=0.2,random_state=100) # stratification with number of moves or elos doesn't work, as it needs at least two games for each unique value/combination of values. Binning doesn't help

# save training set 
df_train.to_csv('../Cleaned_Analyzed_Games/all_games_cleaned_train.csv',index=False)
df_test.to_csv('../Cleaned_Analyzed_Games/all_games_cleaned_test.csv',index=False)

# make bins for evaluations
eval_bins=np.arange(-20.05,20.15,0.1)

move_bins=np.arange(0,150,5)

# Compute winning chance tables from training data
df=pd.read_csv('../Cleaned_Analyzed_Games/all_games_cleaned_train.csv')
winning_chances_util.compute_winning_chance_table(df, intervals=eval_bins,movebins=move_bins,outdir='../winning_chances_tables')