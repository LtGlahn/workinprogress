from copy import deepcopy 
import pdb 

from shapely import wkt 
from shapely.geometry import LineString 
# from shapely.ops import unary_union
import pandas as pd 
import geopandas as gpd 
from datetime import datetime

import STARTHER 
import nvdbapiv3

# Leser mangelrapport 
def lesmangel( filnavn ): 
    """
    Leser mangelrapport (sql-dump) inn som rader 


    |       NID      MSLOC      MELOC     LENGTH VREF
    |---------- ---------- ---------- ---------- ----------------------------------------
    |     21765  .36944962  .41532587    357.843 4221 PV98455 S1D1 seq=1000 (K)
    |     21802  .82250887  .82254903       .153 FV403 S2D1 seq=19000 (K)


    """

    lines = []
    data = [ ]
    with open( filnavn ) as f: 
        for line in f: 
            mylist = line.split()
            if len( mylist ) > 4: 
                lines.append( mylist )
        

    # De to første radene har verdifulle metadata, så kommer dataverdiene iblandet litt tull og tøys
    miljo = lines[0][2]
    dato  = lines[0][3]
    klokke = lines[0][4]
    klokke = klokke.replace( '.', ':')
    beskrivelse = ' '.join( lines[1] )

    count = 0 
    for ll in lines: 
        cc = lesmangelrad( ll )
        if cc:
            cc['sqldump_miljo']       = miljo 
            cc['sqldump_dato']        = dato
            cc['sqldump_klokke']      = klokke
            cc['sqldump_beskrivelse'] = beskrivelse
            cc['sqldump_datarad']     = count 

            # Henter data for start- og sluttpunkt 
            p1 = nvdbapiv3.veglenkepunkt( str( cc['sqldump_frapos'] ) + '@' + str( cc['sqldump_vlenkid'] ), retur = 'komplett'   )
            if p1: 
                cc['start_wkt']     = p1['geometri']['wkt']
                cc['start_vref']    = p1['vegsystemreferanse']['kortform']
            p2 = nvdbapiv3.veglenkepunkt( str( cc['sqldump_tilpos'] ) + '@' + str( cc['sqldump_vlenkid'] ), retur = 'komplett'   )
            if p2: 
                cc['slutt_wkt']     = p2['geometri']['wkt']
                cc['slutt_vref']    = p2['vegsystemreferanse']['kortform']

            # Henter rute 
            rute = nvdbapiv3.hentrute( str( cc['sqldump_frapos'] ) + '@' + str( cc['sqldump_vlenkid'] ), 
                                       str( cc['sqldump_tilpos'] ) + '@' + str( cc['sqldump_vlenkid'] )  )

            suksess = False 
            for segment in rute: 
                seg = { **segment, **cc }
                seg['stedfesting'] = 'RUTE'

                data.append( seg  )
                suksess = True 

            # Prøver å hente data fra NVDB api segmentert vegnett hvis rute-spørring feiler
            if len( rute ) == 0: 
                if cc['sqldump_length'] > 1: 
                    forb = nvdbapiv3.apiforbindelse()
                    r = forb.les( '/vegnett/veglenkesekvenser/segmentert/' + str( cc['sqldump_vlenkid'] ))
                    if r.ok: 
                        segmentdata = r.json()
                        if isinstance( segmentdata, list):
                            for segment in segmentdata: 
                                seg = nvdbapiv3.flatutvegnettsegment( segment )
                                if seg['startposisjon'] < cc['sqldump_tilpos'] and seg['sluttposisjon'] > cc['sqldump_frapos']:
                                    seg['stedfesting'] = 'Per veglenkesekvens ID' 
                                    nyttseg = { **seg, **cc }
                                    data.append( nyttseg )
                                    suksess = True 
 
            # Fallback hvis ingenting av det andre funker 
            if not suksess: 
                cc['rute_stedfesting'] = 'FEILER, kun start-sluttpunkt'
                p1 = wkt.loads( cc['start_wkt'] )
                p2 = wkt.loads( cc['slutt_wkt'] )
                myLine = LineString([p1, p2] )
                if cc['sqldump_length'] == 0: 
                    cc['geometri'] = p1.wkt
                else:     
                    cc['geometri'] = myLine.wkt 
                data.append( cc )
            count += 1 

            if count == 1 or count == 10 or count % 50 == 0: 
                print( f'Leser rad {count} av {len(lines)}')

    return data 



def lesmangelrad( enkeltrad ): 
    """
    Parser en enkelt rad fra mangelrapport
    
    Leser mangelrapport og returnerer dictionary med datavedier for veglenkeid, posisjon fra og til og VREF
    """
    returdata = None 
    if isinstance(enkeltrad, str): 
        mylist = enkeltrad.split()
    elif isinstance( enkeltrad, list ): 
        mylist = enkeltrad 
    else: 
        raise ValueError( 'Input data til lesmangelrad må være liste eller tekststreng')

    if len( mylist ) > 5: 
        returdata = { }
        try: 
            returdata['sqldump_vlenkid'] =      int( mylist[0]  )
            returdata['sqldump_frapos']  =    float( mylist[1]  )
            returdata['sqldump_tilpos']  =    float( mylist[2]  )
            returdata['sqldump_length']  =    float( mylist[3]  )
            returdata['sqldump_vref']    = ' '.join( mylist[4:] )

        except ValueError: 
            return None 

    return returdata 

if __name__ == '__main__': 

    dd = lesmangel( 'checkCoverage_904_ERF_VT_K_-ferje.log')

    mindf = pd.DataFrame( dd  ) 

    mindf['gate'] = mindf['gate'].apply( lambda x : x['navn'] if isinstance(x, dict)  and 'navn' in x else ''  )

    col = [ 'vref', 'lengde', 'trafikantgruppe', 'fylke', 'kommune', 'gate',  'stedfesting', 
            'vegkategori', 'sqldump_vlenkid', 'sqldump_frapos', 'sqldump_tilpos', 
            'sqldump_length', 'sqldump_vref', 'sqldump_miljo', 'sqldump_dato', 
            'sqldump_klokke', 'sqldump_beskrivelse', 'sqldump_datarad', 
            'start_wkt', 'start_vref', 'slutt_wkt', 'slutt_vref', 
            'kortform', 'type',  'typeVeg', 'geometri' ]

    mindf = mindf[col].copy()

    mindf.sort_values( by=['trafikantgruppe',  'sqldump_length', 'sqldump_datarad', 'sqldump_frapos' ], ascending=[False, False, True, True], inplace=True )
    
    mindf['geometry'] = mindf['geometri'].apply( wkt.loads )
    minGdf = gpd.GeoDataFrame( mindf, geometry='geometry', crs=25833 )
    minGdf.drop( columns='geometri', inplace=True )
    minGdf.to_file( 'mangelrapport.gpkg', layer='mangelrapport-ufiltrert', driver="GPKG")  

    mindf.drop( columns=['geometri', 'geometry'], inplace=True )
    mindf.to_excel( 'mangelrapport.xlsx', index=False  )

    # tidsbruk = datetime.now( ) - t0 
    # print( "tidsbruk:", tidsbruk.total_seconds( ), "sekunder")



