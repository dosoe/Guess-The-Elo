import winning_chances
import anal_games
import glob, os
import pandas as pd
import numpy as np

def assemble_csvs_to_numpy(prefix,suffix,bin_moves):
    file_prefix=prefix
    file_suffix=suffix
    i=0
    movlen=len(glob.glob(file_prefix+'*'+file_suffix))
    while os.path.isfile(file_prefix+str(i)+file_suffix):
    # for i in range(bin_moves):
        data=pd.read_csv(file_prefix+str(i)+file_suffix)
        bins=data['bins'][1:-1].to_numpy(dtype=float)
        try:
            output_array[0,:,i]=data['WinningChance'].to_numpy(dtype=float)
            output_array[1,:,i]=data['DrawChance'].to_numpy(dtype=float)
            output_array[2,:,i]=data['LosingChance'].to_numpy(dtype=float)
        except:
            output_array=np.zeros((3,len(bins)+2,movlen))
            output_array[0,:,i]=data['WinningChance'].to_numpy(dtype=float)
            output_array[1,:,i]=data['DrawChance'].to_numpy(dtype=float)
            output_array[2,:,i]=data['LosingChance'].to_numpy(dtype=float)
        i+=1
    return output_array,bins

bin_moves=5
file_prefix='../Analyzed_Games/winning_chances_per_move_'+str(bin_moves)+'_'
file_suffix='.csv'
winchance_array,bins=assemble_csvs_to_numpy(file_prefix,file_suffix,bin_moves)
print(np.shape(winchance_array))

files=sorted(glob.glob("../Analyzed_Games/twic*_1[56]_analyzed.csv"))
# files=['../Analyzed_Games/twic1260_15_analyzed.csv']

# apply get_winning_chance to all games and create new files
anal_games.rewrite_all_files(suffix='_winningchance',filenames=files,functions=[(winning_chances.get_winning_chance,{'winchance_array':winchance_array,
                                                                                                     'bins':bins,
                                                                                                     'bin_moves':bin_moves})],
                                                                                                     skip_if_processed=False,game_wise=False)