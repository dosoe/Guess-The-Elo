
import requests
import pandas as pd
import numpy as np
import sys,os
try: 
    from BeautifulSoup import BeautifulSoup
except ImportError:
    from bs4 import BeautifulSoup

def get_player_info(fide_id):
    response = requests.get(url="https://ratings.fide.com/profile/"+str(fide_id))
    if response.status_code==200:
        pass
    else:
        print(response.status_code) 
        return
    parsed_html = BeautifulSoup(response.text, "html.parser")

    try:
        first_check=parsed_html.body.find(string="No record found please check ID number")
        if first_check: # no player with that Fide ID found
            print(first_check,fide_id)
            return None
    except AttributeError:
        return None

    out={}
    out['Name']=parsed_html.body.find('div', attrs={'class':'col-lg-8 profile-top-title'}).text
    for parsed in parsed_html.body.find_all('div', attrs={'class':'profile-top-info__block'}):
        for row in parsed.find_all('div', attrs={'class':'profile-top-info__block__row'}):
            header=row.find('div', attrs={'class':'profile-top-info__block__row__header'})
            if header:
                data=row.find('div', attrs={'class':'profile-top-info__block__row__data'})
                out[header.text]=data.text
    return out

if __name__ == "__main__":
    data=pd.read_csv('../Analyzed_Games/games.csv')
    allfideids=np.append(data['WhiteFideId'].to_numpy(dtype=int),data['BlackFideId'].to_numpy(dtype=int))

    print(len(np.unique(allfideids)))

    found=False
    if os.path.isfile('../Analyzed_Games/players.csv'):
        found=True
        df=pd.read_csv('../Analyzed_Games/players.csv')

    if not found:
        players={}
        name=[]
        # rank=[] # not always defined if I understand correctly, also inconsistent in the parsing of the fide website
        fed=[]
        fide=[]
        B_Year=[]
        sex=[]
        title=[]
    
    tags=['Name','Federation','FideID','B_Year','Sex','Title']

    for i,fideid in enumerate(np.unique(allfideids)):

        if found and fideid in df['FideID'].values:
            continue
        
        print(fideid)
        out=get_player_info(fideid)

        if out:

            if found:
                df_new_row = pd.DataFrame({ 'Name': [out['Name']], 
                                            'Federation': [out['Federation:']],
                                            'FideID': [out['FIDE ID:']],
                                            'B_Year': [out['B-Year:']],
                                            'Sex': [out['Sex:']],
                                            'Title': [out['FIDE title:']]
                                            })
                df = pd.concat([df[tags], df_new_row[tags]])
            if not found:
                name.append(out['Name'])
                # rank.append(out[''])
                fed.append(out['Federation:'])
                fide.append(out['FIDE ID:'])
                B_Year.append(out['B-Year:'])
                sex.append(out['Sex:'])
                title.append(out['FIDE title:'])
            

        if not found and i%100==0:
            players['Name']=name
            players['Federation']=fed
            players['FideID']=fide
            players['B_Year']=B_Year
            players['Sex']=sex
            players['Title']=title
            df=pd.DataFrame(players)
            df.to_csv('../Analyzed_Games/players.csv',index=False)
            found=True
        elif i%100==0:
            df.to_csv('../Analyzed_Games/players.csv',index=False)
    df.to_csv('../Analyzed_Games/players.csv',index=False)


