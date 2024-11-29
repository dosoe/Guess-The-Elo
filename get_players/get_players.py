
import requests
import pandas as pd
import numpy as np
import sys,os
try: 
    from BeautifulSoup import BeautifulSoup
except ImportError:
    from bs4 import BeautifulSoup

def get_player_info(fide_id):
    """
    Get player information from his FIDE id by calling its profile on the FIDE website
    
    Parameters: 
    - fide_id (int or str): FIDE id of the player

    Outputs: 
    - player (dict): dictionary with keys 
    'Name': Name of the player
    'Federation': Federation the player is affiliated to
    'FIDE ID': FIDE id of the player
    'B_Year': Birth year of the player
    'Sex': Gender of the player
    'FIDE title': FIDE title of the player, not available for all players
    """

    # Fetch page of the player on the FIDE website
    response = requests.get(url="https://ratings.fide.com/profile/"+str(fide_id))
    if response.status_code==200:
        pass
    else:
        print(response.status_code) 
        return
    
    # Parse
    parsed_html = BeautifulSoup(response.text, "html.parser")

    # Check if player exists
    try:
        first_check=parsed_html.body.find(string="No record found please check ID number")
        if first_check: # no player with that Fide ID found
            print(first_check,fide_id)
            return None
    except AttributeError:
        return None

    # read and fill in player information
    player={}
    player['Name']=parsed_html.body.find('div', attrs={'class':'col-lg-8 profile-top-title'}).text
    for parsed in parsed_html.body.find_all('div', attrs={'class':'profile-top-info__block'}):
        for row in parsed.find_all('div', attrs={'class':'profile-top-info__block__row'}):
            header=row.find('div', attrs={'class':'profile-top-info__block__row__header'})
            if header:
                data=row.find('div', attrs={'class':'profile-top-info__block__row__data'})
                player[header.text.split(':')[0]]=data.text
    return player

if __name__ == "__main__":

    input_file='../Analyzed_Games/games.csv'
    output_file='../Analyzed_Games/players.csv'

    # Read list of games
    data=pd.read_csv('../Analyzed_Games/games.csv')

    # Fetch information for each player
    allfideids=np.append(data['WhiteFideId'].to_numpy(dtype=int),data['BlackFideId'].to_numpy(dtype=int))

    # Check if player file already exists
    found=False
    if os.path.isfile(output_file):
        found=True
        df=pd.read_csv(output_file)

    # Loop over players
    for i,fideid in enumerate(np.unique(allfideids)):

        # Check for dupes
        if found and fideid in df['FideID'].values:
            continue
        
        # get player info
        player=get_player_info(fideid)

        if not player:
            continue

        # If table already exists, append to it, else create it
        if found:
            df_new_row = pd.DataFrame({ 'Name': [player['Name']], 
                                        'Federation': [player['Federation']],
                                        'FideID': [player['FIDE ID']],
                                        'B_Year': [player['B-Year']],
                                        'Gender': [player['Sex']],
                                        'Title': [player['FIDE title']]
                                        })
            df = pd.concat([df, df_new_row],ignore_index=True)

        else:
            players={}
            players['Name']=[player['Name']]
            players['Federation']=[player['Federation']]
            players['FideID']=[player['FIDE ID']]
            players['B_Year']=[player['B-Year']]
            players['Gender']=[player['Sex']]
            players['Title']=[player['FIDE title']]
            df=pd.DataFrame(players)
            found=True
            
        # every 100 players, write to file in case of interruptions
        if i%100==0:
            df.to_csv(output_file,index=False)
        
    df.to_csv(output_file,index=False)


