import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import matplotlib as mpl

# supposes you ran winning_chances.py beforehand with 5 move bins. Else you need to adapt it a little, nothing difficult
datas=[]
for i in range(125):
    datas.append(pd.read_csv('../Analyzed_Games/winning_chances_per_move_5_001_'+str(i)+'.csv'))

moves_max=125
min_games=500
colors = plt.cm.jet(np.linspace(0,1,moves_max//5))
plt.figure(figsize=(15,10))
for i in range(moves_max//5)[10:]:
    plt.plot(datas[i]['bins'][1:-1][datas[i]['TotalGames'][1:-1]>min_games].astype(float),datas[i]['TotalGames'][1:-1][datas[i]['TotalGames'][1:-1]>min_games],label=str(i),color=colors[i])
# plt.legend()
plt.colorbar(mpl.cm.ScalarMappable(norm=mpl.colors.Normalize(vmin=1,vmax=25*5), cmap='jet'),ax=plt.gca(),label='Number of moves played')
plt.xlabel('Evaluation')
plt.ylabel('Number of total moves')
plt.yscale('log')
plt.savefig('move_vs_eval_10.png')

# plt.show()