import pandas as pd
import numpy as np

# Grab this repos: https://github.com/LtGlahn/nvdbapi-V3
# File structure: /nvdbapi-V3/ (some helper .py functions here) 
# 				  /nvdbapi-V3/nvdbapiv3/nvdbapiv3.py 
# you should point your path to: 
# 				  /nvdbapi-V3/ 
# 
# Then you need to to something like this 
# import sys 
# sys.path.append( 'c:/mycomputer/folder/where/you/have/nvdbapi-V3/' ) 

import pandas as pd

import STARTHER
import nvdbapiv3 

def findParent( relasjon, objektType=True ): 
    """
    Finds "parents" (foreldre) from the "relasjoner" dictionary 

    We are interested in two pieces of information:
        - The typeid of the mother
        - the NVDB id of the mother

    Example: From this dictionary: 
        {'foreldre': [{'listeid': 222185,
                        'id': 202185,
                        'type': {'id': 5, 'navn': 'Rekkverk'},
                        'vegobjekter': [78775800]}]}

    we want typeid = 5 from foreldre[0]['type']['id'] 
    and nvdbId = 78775800 foreldre[0]['vegobjekter'][0]

    And although this dictionary may contain more than one parent that would 
    in fact be a data error! Objects in NVDB should only have one single parent. 

    For ease of use with the pandas.DataFrame.apply - function 
    we use the keyword objektType = True | False to determine which of these 
    two data points this function returns. That way you can do 

    myDf['parent_typeId'] = myDf['relasjoner'].apply( lambda x : findParent( x ))
    myDf['parent_nvdbId'] = myDf['relasjoner'].apply( lambda x : findParent( x, objektType=False  ))
    
    """

    if isinstance( relasjon, dict):

        try: 
            if objektType == True: 
                return relasjon['foreldre'][0]['type']['id']
            elif objektType == True: 
                return relasjon['foreldre'][0]['vegobjekter'][0]

        except KeyError: 
            return np.nan 

    else: 
        return np.nan 

if __name__ == '__main__': 

    # nvdbFagdata is an object that handles all complexity to grab data from 
    # NVDB api (pagination, filters etc)
    search_rekkverk = nvdbapiv3.nvdbFagdata( 5 )
    myfilter = { 'kontraktsomrade' : '9305 Sunnfjord 2021-2026', 'srid' : 4326 }
    search_rekkverk.filter( myfilter )
    df_rekkverk = pd.DataFrame( search_rekkverk.to_records( ) )

    # Dealing with relationships is a bit more convoluted. I've 
    # choosen just to deal with "mother" - relationships from the 
    # three tilstand/skade objects. See the definition of findParent

    # First Tilstand/skade, rekkverk, typeId = 284 
    search_tilstand284 = nvdbapiv3.nvdbFagdata( 284 )
    search_tilstand284.filter( myfilter )
    df_tilstand284 = pd.DataFrame( search_tilstand284.to_records( relasjoner=True ) )
    df_tilstand284['parent_objektTypeId'] = df_tilstand284['relasjoner'].apply( lambda x : findParent( x ))
    df_tilstand284['parent_nvdbId'] = df_tilstand284['relasjoner'].apply( lambda x : findParent( x, objektType=False  ))

    # Then Tilstand/skade FU, strekning 507
    search_tilstand507 = nvdbapiv3.nvdbFagdata( 507 )
    search_tilstand507.filter( myfilter )
    df_tilstand507 = pd.DataFrame( search_tilstand507.to_records( relasjoner=True ) )
    df_tilstand507['parent_objektTypeId'] = df_tilstand507['relasjoner'].apply( lambda x : findParent( x ))
    df_tilstand507['parent_nvdbId'] = df_tilstand507['relasjoner'].apply( lambda x : findParent( x, objektType=False  ))

    # Tilstand/skade Fu, strekning is a generic object used by lots of different objekt types. 
    # We filter out just those relevant for objekttype 5 Rekkverk 
    df_tilstand507 = df_tilstand507[ df_tilstand507['parent_objektTypeId'] == 5 ]

    # Finally  Tilstandsgrad, rekkverk 947
    search_tilstand947 = nvdbapiv3.nvdbFagdata( 947 )
    search_tilstand947.filter( myfilter )
    df_tilstand947 = pd.DataFrame( search_tilstand947.to_records( relasjoner=True ) )
    df_tilstand947['parent_objektTypeId'] = df_tilstand947['relasjoner'].apply( lambda x : findParent( x ))
    df_tilstand947['parent_nvdbId'] = df_tilstand947['relasjoner'].apply( lambda x : findParent( x, objektType=False  ))


# now you have 4 dataframes: df_rekkverk, df_tilstand284, df_tilstand507 and df_tilstand947  


