from copy import deepcopy 
import pdb 
from datetime import datetime

from shapely import wkt 
import pandas as pd 
import geopandas as gpd 
import numpy as np 

import STARTHER
import nvdbapiv3
# import fiksBK_feilvegkat

def dato2int( datotekst  ): 
    """
    Konverterer ISO datostreng til heltall, '19861123' => 19860123 

    Ideelt skulle vi brukt en skikkelig datetime eller dato-type og 
    manipulert den... meeeeeeeeeen støtten for dette er litt variabel og 
    tildels dårlig i ulike verktøy. Å filtrere på heltall, f.eks. startdato >= 19860123, 
    fungerer i alle verktøy. (Hvis ikke bør du bytte verktøy)

    Vi bruker heltallet 99991231 for å antyde åpen sluttdato, dvs "uendelig" langt fram i tid

    ARGUMENTS: 
        datotekst - ISO dato streng

    KEYWORDS
        N/A
    
    RETURNS
        Integer 
    """

    result = 99991231
    if isinstance( datotekst, str ) and '-' in datotekst: 
        result = int( datotekst.replace('-', '') )
    
    return result



if __name__ == '__main__': 

    t0 = datetime.now( )
    idagfilter = { 'kartutsnitt' : '-53074.72,6507486.16,-13880.70,6570928.63', 'vegsystemreferanse' : 'Rv,Ev' }    

    ## kode for kun å hente dagens vegnett
    # idag = nvdbapiv3.nvdbVegnett(  )
    # idag.filter( idagfilter )
    # 
    # mindf = pd.DataFrame( idag.to_records( ) ) 
    # mindf['geometry'] = mindf['geometri'].apply( wkt.loads )
    # mindf.drop( columns=[ 'href', 'geometri'], inplace=True)
    # minGdf = gpd.GeoDataFrame( mindf, geometry='geometry', crs=5973  )
    # minGdf.to_file( 'dagens_riksveger.gpkg', layer='europa_og_riksveg', driver="GPKG")  

    # Henter all historikk, all tid
    hist = nvdbapiv3.nvdbVegnett( )
    histfilter = deepcopy( idagfilter) 
    histfilter['historisk'] = True
    hist.filter( histfilter )

    histdf = pd.DataFrame(  hist.to_records() )
    histdf['geometry'] = histdf['geometri'].apply( wkt.loads )
    histdf.drop( columns=[ 'href', 'geometri'], inplace=True)
    histGdf = gpd.GeoDataFrame( histdf, geometry='geometry', crs=5973  )

    # Fra dato som tekst til heltall '1986-01-23' => 19860123
    histGdf['startdato_num'] = histGdf['startdato'].apply( lambda x: dato2int(x ))
    histGdf['sluttdato_num'] = histGdf['sluttdato'].apply( lambda x: dato2int(x ))

    # Fjerner en del kolonner som strengt tatt er helt overflødige
    slettekolonner = [  'veglenkenummer', 'segmentnummer', 'startnode', 'sluttnode',
                        'referanse', 'typeVeg_sosi', 'vegsystemreferanse', 'strekning', 
                        'delstrekning', 'ankerpunktmeter', 'sideanleggsdel', 'fra_meter', 'til_meter',
                         'kryssdel']    

    histGdf.drop( columns=slettekolonner, inplace=True )
    
    # Lager en fornuftig vegnumer-kolonne 
    histGdf['vegnummer'] = histGdf['vref'].apply( lambda x : x.split()[0] )

    # Dagens vegnett er alt vegnett med sluttdato > i dag. 
    dagens = histGdf[ histGdf['sluttdato_num'] >  int( datetime.now().strftime( '%Y%m%d' ) ) ]

    dagens.to_file(  'riksveger.gpkg', layer='dagens_e_r', driver="GPKG")  
    histGdf.to_file( 'riksveger.gpkg', layer='historisk_e_r', driver="GPKG")  


    tidsbruk = datetime.now( ) - t0 
    print( "tidsbruk:", tidsbruk.total_seconds( ), "sekunder")