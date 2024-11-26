import pandas as pd
import numpy as np
import math

def Mistakes_by_player(mv_start,mv_end,mistake_bins,all=False,train=True,move_start=3):

    filename='../Cleaned_Analyzed_Games/wcl_'
    if train:
        filename+='train_'
    else:
        filename+='test_'
    if all:
        filename+='all_'
    if mv_end==None:
        filename+=str(mv_start)
    else:
        filename+=str(mv_start)+'-'+str(mv_end)
    filename+='_by_player.csv'
    print(filename)

    # make mistake tables
    list=[]
    for i in range(len(mistake_bins[:-1])):
        list.append(pd.Interval(mistake_bins[i],mistake_bins[i+1]))
    mistake_labels=pd.IntervalIndex(list)

    # read wcl tables
    df=pd.read_csv(filename)

    # initialize mistake columns
    for label in mistake_labels:
        df[label]=0

    ismove=True
    j=move_start
    while ismove:
    # for j in range(move_start,mv_end//2): # look at moves from 0 to the end (could be changed easily)
        try:
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
            j+=1
        except:
            break

    # save output in new file
    # df.drop(columns=['a'])

    filename_out='../Cleaned_Analyzed_Games/wcl_and_mistakes_'
    if train:
        filename_out+='train_'
    else:
        filename_out+='test_'
    if all:
        filename_out+='all_'
    if mv_end==None:
        filename_out+=str(mv_start)+'-'
    else:
        filename_out+=str(mv_start)+'-'+str(mv_end)
    filename_out+='_by_player.csv'
    df.to_csv(filename_out,index=False)


# make mistake bins and mistake labels
mistake_bins = [5, 10, 15, 20, 25, 30, 35, 40, 50, 60, 70, 100]
# start move to count mistakes (counting starts at 0)
move_start=3

move_bins_for_eval=np.arange(0,150,5)


# # for winchances calculated with binned moves
# for i in range(len(move_bins_for_eval[:-1])):
#     print(move_bins_for_eval[i],move_bins_for_eval[i+1])

#     Mistakes_by_player(move_bins_for_eval[i],move_bins_for_eval[i+1],all=False,train=True,mistake_bins=mistake_bins,move_start=move_start)
    
# Mistakes_by_player(move_bins_for_eval[-1],None,all=False,train=True,mistake_bins=mistake_bins,move_start=move_start)

# for i in range(len(move_bins_for_eval[:-1])):

#     Mistakes_by_player(move_bins_for_eval[i],move_bins_for_eval[i+1],all=False,train=False,mistake_bins=mistake_bins,move_start=move_start)
    
# Mistakes_by_player(move_bins_for_eval[-1],None,all=False,train=False,mistake_bins=mistake_bins,move_start=move_start)

# for winchances calculated with all moves
# for i in range(len(move_bins_for_eval[:-1])):

#     Mistakes_by_player(move_bins_for_eval[i],move_bins_for_eval[i+1],all=True,train=True,mistake_bins=mistake_bins,move_start=move_start)
    
# Mistakes_by_player(move_bins_for_eval[-1],None,all=True,train=True,mistake_bins=mistake_bins,move_start=move_start)

for i in range(len(move_bins_for_eval[:-1])):

    Mistakes_by_player(move_bins_for_eval[i],move_bins_for_eval[i+1],all=True,train=False,mistake_bins=mistake_bins,move_start=move_start)
    
Mistakes_by_player(move_bins_for_eval[-1],None,all=True,train=False,mistake_bins=mistake_bins,move_start=move_start)
