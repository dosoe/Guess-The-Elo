import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import matplotlib as mpl

# supposes you ran winning_chances.py beforehand with 5 move bins. Else you need to adapt it a little, nothing difficult
datas=[]
for i in range(125):
    datas.append(pd.read_csv('../Analyzed_Games/winning_chances_per_move_5_001_'+str(i)+'.csv'))

num_games=[]
for i in range(125):
    num_games.append(datas[i]['TotalGames'].sum())
plt.figure()
plt.plot(np.arange(125)*5,num_games)
plt.xlabel('Number of moves')
plt.ylabel('cumulative number of games')
plt.savefig('moves_num.png')

moves_max=125
min_games=500
colors = plt.cm.jet(np.linspace(0,1,moves_max//5))
plt.figure()
for i in range(moves_max//5):
    plt.plot(datas[i]['bins'][1:-1][datas[i]['TotalGames'][1:-1]>min_games].astype(float),datas[i]['WinningChance'][1:-1][datas[i]['TotalGames'][1:-1]>min_games],label=str(i),color=colors[i])
# plt.legend()
plt.colorbar(mpl.cm.ScalarMappable(norm=mpl.colors.Normalize(vmin=1,vmax=25*5), cmap='jet'),ax=plt.gca(),label='Number of moves played')
plt.xlabel('Evaluation')
plt.ylabel('Chance to win')
plt.savefig('winningchances.png')

plt.figure()
for i in range(moves_max//5):
    plt.plot(datas[i]['bins'][1:-1][datas[i]['TotalGames'][1:-1]>min_games].astype(float),datas[i]['DrawChance'][1:-1][datas[i]['TotalGames'][1:-1]>min_games],label=str(i),color=colors[i])
# plt.legend()
plt.colorbar(mpl.cm.ScalarMappable(norm=mpl.colors.Normalize(vmin=1,vmax=25*5), cmap='jet'),ax=plt.gca(),label='Number of moves played')
plt.xlabel('Evaluation')
plt.ylabel('Chance to draw')
plt.savefig('drawingchances.png')


plt.figure()
for i in range(moves_max//5):
    plt.plot(datas[i]['bins'][1:-1][datas[i]['TotalGames'][1:-1]>min_games].astype(float),datas[i]['LosingChance'][1:-1][datas[i]['TotalGames'][1:-1]>min_games],label=str(i),color=colors[i])
# plt.legend()
plt.colorbar(mpl.cm.ScalarMappable(norm=mpl.colors.Normalize(vmin=1,vmax=25*5), cmap='jet'),ax=plt.gca(),label='Number of moves played')
plt.xlabel('Evaluation')
plt.ylabel('Chance to lose')
plt.savefig('losingchances.png')

plt.show()