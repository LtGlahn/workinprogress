import json 

import pandas as pd 
import geopandas as gpd
from shapely import wkt 

import STARTHER
import nvdbapiv3 

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

if __name__ == '__main__': 
    forb = nvdbapiv3.apiforbindelse 

    forb = nvdbapiv3.apiforbindelse( miljo='prodles')
    riksvegruter = forb.les( 'https://nvdbapiles-v3.atlas.vegvesen.no/omrader/riksvegruter' ).json()

    # Ser først på rute5A E134 Drammen - Haugesund  
    # riksvegruter = [ x for x in riksvegruter if x['navn'] == 'RUTE5A' ]

    alledata = None 


    for rute in riksvegruter: 


        if rute['navn'] in [ 'RUTE 7' ]: 
            print( f"##############\n\nHopper over rute {rute['navn']} {rute['beskrivelse']} {rute['periode']} \n" )
            print( json.dumps( rute, indent=4) )

        else: 

            print(f"Henter riksvegrute {rute['navn']} {rute['beskrivelse']} {rute['periode']} " )

            v = nvdbapiv3.nvdbVegnett( )
            v.filter( { 'riksvegrute' : rute['navn']})

            mindf = pd.DataFrame( v.to_records( ))
            mindf['Riksvegrute navn'] = rute['navn']
            mindf['Riksvegrute beskrivelse'] = rute['beskrivelse']
            mindf['Riksvegrute periode'] = rute['periode']

            mindf['geometry'] = mindf['geometri'].apply( wkt.loads )
            veg = gpd.GeoDataFrame( mindf, geometry='geometry', crs=5973 )
            veg.to_file( 'riksvegruter.gpkg', layer=rute['navn'], driver="GPKG")  


            if not isinstance( alledata, pd.DataFrame): 
                alledata = mindf.copy()
            else: 
                alledata = pd.concat( [ alledata, mindf], ignore_index=True   )

    alledata['geometry'] = alledata['geometri'].apply( wkt.loads )
    minGdf = gpd.GeoDataFrame( alledata, geometry='geometry', crs=5973)
    minGdf.to_file(  'riksvegruter.gpkg', layer='alleruter', driver='GPKG' )


    sok = nvdbapiv3.nvdbFagdata( 704 )
    ruteDf = pd.DataFrame( sok.to_records( vegsegmenter=False ) )
    col = [ 'nvdbId', 'Nummer', 'Navn', 'Beskrivelse', 'Periode', 'vegsystemreferanser' ]
    # ruteDf[col]
    ruteDf[ ruteDf['Nummer'] == '7'][col]
    ruteDf['Nummer'].value_counts()
    ruteDf['Navn'].value_counts()

