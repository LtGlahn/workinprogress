"""
Hvilke kontraktsområder finnes hvor på vegnettet? Er det deler av vegnettet som ikke er tilknyttet et kontraktsområde? 

Dette scriptet svarer på slike spørsmål. Vi laster ned segmentert vegnett fra NVDB api og ser hvilke kontraktsområder 
som finnes. Vi lagrer resultatene som ett kartlag per kontraktsområde. Ettersom disse kontraktsområdene har ganske lange 
og kronglete navn må vi navngi dem med løpenummer (kontrakt_1, kontrakt_2 osv). I tillegg kommer et kartlag for INGEN_KONTRAKT, 
hvis vi finner noen slike. For Innlandet har vi f.eks. 1.1km med gang/sykkelveg der det ikke finnes noen kontrakt. 

Filformatet er OGC Geopackage (.gpkg), et moderne filformat som leses av de fleste kartsystemer. 
"""

import pandas as pd
import geopandas as gpd
from shapely import wkt

import lokal_STARTHER # Sørger for at biblioteket med nvdbapiv3 blir tilgjengelig på søkestien 
import nvdbapiv3      # https://github.com/LtGlahn/nvdbapi-V3 


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

    # Etterbehandler, knar og lagrer til fil, ett kartlag per kontraktsområde: 
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

