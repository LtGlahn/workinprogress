import pdb

import pandas as pd
import geopandas as gpd
from shapely import wkt, wkb 
from shapely.geometry import LineString 

import lokal_STARTHER
import nvdbapiv3
import nvdbgeotricks 


if __name__ == '__main__': 

    vsok = nvdbapiv3.nvdbVegnett()
    vsok.filter( {'fylke' : 34, 'vegsystemreferanse' : 'Fv'})
    # vsok.filter( {'kommune' : 3435, 'vegsystemreferanse' : 'Fv'})

    resultat = { }
    manglernavn = 'INGEN_KONTRAKT'

    for veg in vsok: 

        if 'kontraktsområder' in veg and len( veg['kontraktsområder']) > 0: 

            for kontrakt in veg['kontraktsområder']: 
                knavn = nvdbapiv3.esriSikkerTekst( kontrakt['navn'] ) 
                if not knavn in resultat: 
                    resultat[knavn] = [ ]

                resultat[knavn].append( veg  )

        else: 
            if not manglernavn in resultat: 
                resultat[manglernavn] = [ ]

            resultat[manglernavn].append( veg  )

    # Etterbehandler og knar: 

    for idx, enkontrakt in enumerate( list( resultat.keys())): 

        if enkontrakt ==  manglernavn: 
            tabellnavn = enkontrakt
        else: 
            tabellnavn = 'kontrakt_' + str( idx + 1 )

        vegDf = pd.DataFrame( resultat[enkontrakt] )
        vegDf['geometry'] = vegDf['geometri'].apply( lambda x : wkt.loads( x['wkt'] ))  
        vegDf.drop( columns=['geometri', 'kontraktsområder', 'riksvegruter'], inplace=True )
        vegDf['feltoversikt'] = vegDf['feltoversikt'].apply( lambda x: '#'.join( x ) if isinstance( x, list) else '')
        vegDf['vegsystemreferanse'] = vegDf['vegsystemreferanse'].apply( lambda x: x['kortform'] if isinstance( x, dict) and 'kortform' in x else '' )

        vegDf['kontraktsområde'] = enkontrakt
        vegGdf = gpd.GeoDataFrame(  vegDf, geometry='geometry', crs=5973  )
        vegGdf.to_file( 'komrader_innlandet.gpkg', layer=tabellnavn, driver='GPKG')

