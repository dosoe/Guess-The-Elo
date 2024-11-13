import anal_games
import functions_anal
import numpy as np
import glob

moves=np.arange(0,700,10)
lmoves=len(moves)-1

for i in range(lmoves)[30:]:
    additional_inputs={}
    additional_inputs['mv_min']=moves[i]
    additional_inputs['mv_max']=moves[i+1]

    print(moves[i])

    filenames = sorted(glob.glob("../Cleaned_Analyzed_Games/*.csv"))
    
    outfile='WCL_'+str(moves[i])+'_'+str(moves[i+1])+'.csv'

    anal_games.process_all_files(outfile=outfile,filenames=filenames,functions=[(functions_anal.WinChanceIncrease,additional_inputs)],skip_if_processed=True,game_wise=True)
