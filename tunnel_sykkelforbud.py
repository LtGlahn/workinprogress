import json 

import pandas as pd
import geopandas as gpd
import numpy as np
from shapely import wkt 


import lokal_STARTHER
import nvdbapiv3 

def finnmorobjekt( relasjonstre, morobjektTypeId=581 ): 

    # Tunneller med gammal lukketdato, stedfestet på historisk vegnett, eller anna tøys 
    skitliste = [ 86533356, 86543441, 86992662, 526120355, 526120363, 80564726, 1006205690, 1009929750, 86527444, 86528363, 
              86530670, 86547903, 86526813, 86521839, 84383891, 84383842, 84383798, 84383658, 83661268, 82301104, 82297271, 
              82297239, 82296815, 276992728, 79608889]

    if 'foreldre' in relasjonstre and len( relasjonstre['foreldre'] ) > 0: 
        if len( relasjonstre['foreldre'] ) > 1: 
            print( "Mer enn 1 foreldrerelasjon??", json.dumps( relasjonstre['foreldre'], indent=4))
        
        foreldre = [ x for x in relasjonstre['foreldre'] if 'type' in x and 'id' in x['type'] and x['type']['id'] == morobjektTypeId  ]
        if len( foreldre ) > 0 and 'vegobjekter' in foreldre[0]:
            foreldreliste = [ x for x in foreldre[0]['vegobjekter'] if x not in skitliste ]
            if len( foreldreliste ) != 1: 
                print( f"Finner noe annet enn 1 mor??? {foreldre} " )

            if len( foreldreliste ) > 0: 
                return foreldreliste[0]
        else: 
            print( f"Fant ingen mor-relasjon?? {foreldre} " )

    else: 
        print( "Fant ingen foreldrerelasjoner" )

    return np.nan

if __name__ == '__main__': 

    # Henter tunneller, der sykkelforbud bor 
    tunsok = nvdbapiv3.nvdbFagdata( 581)
    tunnelmor_alle  = pd.DataFrame( tunsok.to_records())
    tunnelmordf = tunnelmor_alle[[ 'nvdbId', 'Sykkelforbud', 'Navn']].copy()
    tunnelmordf.rename( columns={'Navn' : 'tunnelmor_navn', 'nvdbId' : 'tunnelmor_nvdbId'}, inplace=True)

    # Henter tunnelløp som skal arve sykkelforbud-data
    tlopsok = nvdbapiv3.nvdbFagdata( 67)
    tlopdf = pd.DataFrame( tlopsok.to_records(  relasjoner=True ) )
    tlopdf['tunnelmor_nvdbId'] = tlopdf['relasjoner'].apply( lambda x : finnmorobjekt( x ) )  

    resultat = pd.merge( tlopdf, tunnelmordf, on='tunnelmor_nvdbId', how='left')
    resultat = pd.merge( tlopdf, tunnelmordf, on='tunnelmor_nvdbId', how='left')

    resultat['geometry'] = resultat['geometri'].apply( lambda x : wkt.loads( x ))

    resultatGdf = gpd.GeoDataFrame( resultat, geometry='geometry', crs=25833 )  
    resultatGdf.drop( columns=['geometri', 'relasjoner'], inplace=True )
    resultatGdf.to_file( 'tunnelsykkelforbud.gpkg', layer='sykkelforbudlop', driver='GPKG')
