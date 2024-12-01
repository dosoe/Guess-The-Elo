import pandas as pd
import numpy as np
import math

# make mistake bins and mistake labels
mistake_bins = [5, 10, 15, 20, 25, 30, 35, 40, 50, 60, 70, 100]
# start move to count mistakes (counting starts at 0)
move_start=3

mistake_labels=[]
for i in range(len(mistake_bins)-1):
    label = f'({mistake_bins[i]},{mistake_bins[i+1]}]'
    mistake_labels.append(label)

for i in range(0,600,5):

    # read wcl tables
    file='../Cleaned_Analyzed_Games/wcl_train_all_'+str(i)+'-'+str(i+5)+'_by_player.csv'
    print(file)
    df=pd.read_csv(file)

    # initialize mistake columns
    for label in mistake_labels:
        df[label]=0

    for j in range(move_start,(i+5)//2): # look at moves from 0 to the end (could be changed easily)
        
        # get max of wcl and lcl
        df['a']=df[['LCL_'+str(j),'WCL_'+str(j)]].max(axis=1,skipna=False)

        for i_line,line in df.iterrows():
            if math.isnan(line['a']):
                continue

            bin_mis=np.digitize(line['a'],bins=mistake_bins)-1
            if bin_mis<0: # skip if not a mistake
                continue
            # increment corresponding mistake bin
            df.at[i_line, mistake_labels[bin_mis]] = df.iloc[i_line][mistake_labels[bin_mis]]+1
        df.drop(columns=['a'])

    # save output in new file
    df.to_csv('../Cleaned_Analyzed_Games/wcl_and_mistakes_train_all_'+str(i)+'-'+str(i+5)+'_by_player.csv',index=False)
        

