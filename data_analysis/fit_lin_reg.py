import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import root_mean_squared_error

moves=np.arange(60,80,10)
lmoves=len(moves)-1

# skip first 5 moves for each player

for i_moves in range(lmoves):

    if os.path.isfile('WCL_'+str(moves[i_moves])+'_'+str(moves[i_moves+1])+'.csv'):
        data=pd.read_csv('WCL_'+str(moves[i_moves])+'_'+str(moves[i_moves+1])+'.csv')
    else:
        continue
    print(moves[i_moves])

    data[["WhiteElo", "BlackElo"]] = data[["WhiteElo", "BlackElo"]].apply(pd.to_numeric)

    data.dropna(subset=["WhiteElo", "BlackElo"],how='any',inplace=True)

    print(data.describe())

    data_train,data_test=train_test_split(data,test_size=0.2)

    features_white=[]
    for i in range(1,(moves[i_moves])//2):
        features_white.append('white_WCL_'+str(i))
    
    lr_white=LinearRegression()
    
    lr_white.fit(data_train[features_white],data_train['WhiteElo'].astype(float))

    print('White Coeffs',lr_white.coef_)
    print('White Intercept',lr_white.intercept_)

    elo_pred_white=lr_white.predict(data_test[features_white])
    residuals_white=data_test['WhiteElo']-elo_pred_white
    print('RMS White ', root_mean_squared_error(data_test['WhiteElo'], elo_pred_white))


    lr_black=LinearRegression()

    features_black=[]
    for i in range(moves[i_moves]//2):
        features_black.append('black_LCL_'+str(i))
    
    lr_black.fit(data_train[features_black],data_train['BlackElo'])

    print('Black Coeffs',lr_black.coef_)
    print('Black Intercept',lr_black.intercept_)

    elo_pred_black=lr_black.predict(data_test[features_black])
    residuals_black=data_test['BlackElo']-elo_pred_black
    print('RMS Black ', root_mean_squared_error(data_test['BlackElo'], elo_pred_black))

    player_games=  data_test[(data_test['BlackElo'] >= 1400) & (data_test['BlackElo'] <= 1500)]

    player_games = player_games.head(20)

    out=lr_black.predict(player_games[features_black])

    print(out)

    plt.figure()
    plt.scatter(elo_pred_white,residuals_white,label='White',s=.1)
    plt.scatter(elo_pred_black,residuals_black,label='Black',s=.1)
    plt.legend()
    plt.xlim([1750,2500])
    plt.savefig('Residuals_vs_predicted_'+str(moves[i_moves])+'_'+str(moves[i_moves+1])+'.png')

    plt.figure()
    plt.scatter(elo_pred_white,data_test['WhiteElo'],label='White',s=.1)
    plt.scatter(elo_pred_black,data_test['BlackElo'],label='Black',s=.1)
    plt.plot([1000,3000],[1000,3000])
    plt.legend()
    plt.xlim([1750,2500])
    plt.savefig('true_vs_predicted_'+str(moves[i_moves])+'_'+str(moves[i_moves+1])+'.png')
    # plt.show()