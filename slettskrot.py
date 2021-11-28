from copy import deepcopy 
import pdb 

from shapely import wkt 
from shapely.ops import unary_union
import pandas as pd 
import geopandas as gpd 
from datetime import datetime

import STARTHER
import nvdbapiv3
import skrivnvdb

def sjekksletting( vegobjektid ):
    """
    Sjekker at et objekt i slettemanus er skrotobjekt uten vegnettstilknytning

    Sjekker også om objektet evt har datterobjekter (kan godt hende de skal 
    slettes de og, men det er verdt å undersøke)

    For objekter som passerer kontrollen (mangler stedfesting veg, uten  datteobjekter)
    så returnerer vi dictionary med data rett fra NVDB API. Der står jo NVDB ID og versjon, 
    som du trenger for å lukke objektet. Eller hva du nå har tenkt å gjøre... 

    Returnerer None om kontrollen feiler, men skriver en melding til konsollet

    """

    r = forb.les( '/vegobjekt', params={ 'id' : vegobjektid })
    if r.ok: 
        data = r.json( )
        if data['relasjoner']: 
            print( 'Ignorerer objektID', vegobjektid, 'pga relasjoner:', data['relasjoner'])
        elif data['lokasjon']['stedfestinger']:
            print( 'Ignorerer objektID', vegobjektid, 'pga gyldig stedfesting'  )
        else: 
            return data


    else: 
        print( 'FEILER - feilkode', r.status_code, 'for spørring', r.url )

    return None 

if __name__ == '__main__': 


    forb = nvdbapiv3.apiforbindelse()


    # tm = nvdbapiv3.nvdbFagdata(540 )
    # tm.filter( { 'tidspunkt' : '2019-12-31' })
    # tm.filter( minefilter)
    filnavn = 'objekt_uten_vegreferanse.xls'
    slettemanus = pd.read_excel( filnavn )

    for ix, row in slettemanus.iterrows():

        if ix < 3: 
            slett = sjekksletting( row['VEGOBJEKT-ID'])
            if slett: 
                print( 'Ikke ferdig')
                


    # mindf = pd.DataFrame( tm.to_records( ) ) 

    # mindf['geometry'] = mindf['geometri'].apply( wkt.loads )
    # minGdf = gpd.GeoDataFrame( mindf, geometry='geometry', crs=25833 )
    # minGdf.to_file( 'trafikkmengde.gpkg', layer='trafikkmengde2019-12-31', driver="GPKG")  

    # tidsbruk = datetime.now( ) - t0 
    # print( "tidsbruk:", tidsbruk.total_seconds( ), "sekunder")