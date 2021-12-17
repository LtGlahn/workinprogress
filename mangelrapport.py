from copy import deepcopy 
import pdb 
from datetime import datetime

from shapely import wkt 
from shapely.geometry import LineString, MultiLineString
# from shapely.ops import unary_union
import pandas as pd 
import geopandas as gpd 

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


    Sukk...  nytt format som ser slik ut: 

    Detaljer - checkCoverage 904

    Nasjonal vegdatabank- PRODUKSJON          2021-12-15 11.06

    Manglende Bruksklasse normal
    Kjørt:  15.12.2021 - 06:57 - 06:59
    Antall feil: 8939
    Parametere: ftid=904 categories=ERFK phases=VT trafficTypes=K roadTypes=-ferje 

    ----------|----------|--------|------------|--------------------------|--------|-----------------------------------|
    NetElemId| NStartPos| NEndPos|municipality|                roadSysRef|  length|                               vref|
    ----------|----------|--------|------------|--------------------------|--------|-----------------------------------|
        929|     0,613|   0,626|        4203|           KV55132 S3D1 m8|  13.067|     4203 KV55132 S3D1 seq=1000 (K)|
        1569|     0,574|   0,640|        4212|          KV1041 S1D1 m352|  38.194|      4212 KV1041 S1D1 seq=5000 (K)|


    """

    lines = []
    data = [ ]
    with open( filnavn ) as f: 
        for linjenr, line in enumerate(f):
            if linjenr < 10: 
                lines.append( line )
            else: 
                eiLinje = line.replace( ',', '.') # Ugrei blanding av desimalskilletegn, både , og .
                mylist = eiLinje.split( '|' )
                if len( mylist ) > 4: 
                    lines.append( mylist )

    # De  første radene har verdifulle metadata, så kommer dataverdiene iblandet litt tull og tøys
    miljo = lines[2].split()[2]
    dato  = lines[2].split()[3]
    klokke = lines[2].split()[4]
    klokke = klokke.replace( '.', ':')
    beskrivelse = lines[4].strip()
    datauttak = lines[5].strip()
    parametre = lines[7].strip()

    count = 0 
    for ll in lines[0:50]: 
        cc = lesmangelrad( ll )
        if cc:
            cc['sqldump_miljo']       = miljo 
            cc['sqldump_dato']        = dato
            cc['sqldump_klokke']      = klokke
            cc['sqldump_beskrivelse'] = beskrivelse
            cc['sqldump_datarad']     = count 
            cc['sqldump_datauttak']   = datauttak
            cc['sqldump_parametre']   = parametre


            # Henter data for start- og sluttpunkt 
            p1 = nvdbapiv3.veglenkepunkt( str( cc['sqldump_frapos'] ) + '@' + str( cc['sqldump_vlenkid'] ), retur = 'komplett'   )
            if p1: 
                cc['start_wkt']     = p1['geometri']['wkt']
                cc['start_vref']    = p1['vegsystemreferanse']['kortform']

            else: 
                print( 'Fikk ikke gyldige data for geometrispørring startpunkt', str( cc['sqldump_tilpos'] ) + '@' + str( cc['sqldump_vlenkid'] )   )

            p2 = nvdbapiv3.veglenkepunkt( str( cc['sqldump_tilpos'] ) + '@' + str( cc['sqldump_vlenkid'] ), retur = 'komplett'   )
            if p2: 
                cc['slutt_wkt']     = p2['geometri']['wkt']
                cc['slutt_vref']    = p2['vegsystemreferanse']['kortform']
            else: 
                print( 'Fikk ikke gyldige data for geometrispørring sluttpunkt', str( cc['sqldump_tilpos'] ) + '@' + str( cc['sqldump_vlenkid'] )   )

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

                try: 
                    p1 = wkt.loads( cc['start_wkt'] )
                    p2 = wkt.loads( cc['slutt_wkt'] )
                    if cc['sqldump_length'] == 0: 
                        cc['geometri'] = p1.wkt
                    else:     
                        myLine = LineString([p1, p2] )
                        cc['geometri'] = myLine.wkt 


                except KeyError as ERR: 
                    print( 'Backup-metode for stedfesting feiler', cc['sqldump_vref'], ERR )
                    cc['rute_stedfesting'] = 'FEILER, lager fiktiv linje uti Norskehavet'
                    cc['geometri'] =  'LineString (101237.70285620921640657 7128534.10969377029687166, 225651.72560383414383978 7241528.48784137237817049)'

                data.append( cc )

            count += 1 

            if count == 1 or count == 10 or count % 50 == 0: 
                print( f'Prosesserte rad {count} av {len(lines)}')

    return data 



def lesmangelrad( enkeltrad ): 
    """
    Parser en enkelt rad fra mangelrapport
    
    Leser mangelrapport og returnerer dictionary med datavedier for veglenkeid, posisjon fra og til og VREF
    """

    returdata = None 
    kjente_feil = [ 'EV6 S185D10 seq=9000 (K)', 'asdf', 
                    'enda en feil' ]


    if isinstance(enkeltrad, str): 
        enkeltrad = enkeltrad.replace( ',', '.')
        mylist = enkeltrad.split('|')
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
            returdata['sqldump_kommune']  =   int(   mylist[-4]  )
            returdata['sqldump_vref']    =           mylist[-3].strip() 
            returdata['sqldump_length']  =    float( mylist[-2]  )

        except ValueError: 
            return None 

        else: 
            if returdata['sqldump_vref'] in kjente_feil: 
                print( 'Ignorerer kjent feil', enkeltrad )
                return None 

    return returdata 


###################################################
## 
## Scriptet starter her
##
#######################################################
if __name__ == '__main__': 
    print( 'Mangelrapport 2.2 - Legger på ny kolonne for vegkategori ')
    t0 = datetime.now()

    #####################################################
    ## 
    ## Last ned ny LOGG-fil fra https://nvdb-datakontroll.atlas.vegvesen.no/
    ## Legg fila i samme mappe som dette scriptet, og editer inn filnavnet her: 
    FILNAVN = 'checkCoverage 904_20211216 (2).LOG'
    dd = lesmangel(  FILNAVN )

    mindf = pd.DataFrame( dd  ) 

    # Finner objekttype
    objekttype = mindf.iloc[0]['sqldump_parametre'].split('=')[1].split()[0]
    fanenavn = 'hullBk' + objekttype

    if len( mindf ) > 0: 

        if 'gate' in mindf.columns: 
            mindf['gate'] = mindf['gate'].apply( lambda x : x['navn'] if isinstance(x, dict)  and 'navn' in x else ''  )

        # Legger på vegkategori
        # mindf['vegkategori'] = mindf['vref'].apply( lambda x: getFirstChar(x) )
        mindf['vegnr'] = mindf['vref'].apply( lambda x: x.split()[0] if isinstance(x, str) and len(x) > 0 else '' )

        col = [ 'vegkategori', 'vegnr', 'vref', 'lengde', 'trafikantgruppe', 'fylke', 'kommune', 'gate',  'stedfesting', 
                'vegkategori', 'sqldump_vlenkid', 'sqldump_frapos', 'sqldump_tilpos', 
                'sqldump_length', 'sqldump_vref', 'sqldump_miljo', 'sqldump_dato', 
                'sqldump_klokke', 'sqldump_beskrivelse', 'sqldump_datarad', 
                'sqldump_datauttak', 'sqldump_parametre', 
                'kortform', 'type',  'typeVeg', 'geometri' ]

        slettecol = list( set( mindf.columns ) - set(col) )
        mindf.drop( columns=slettecol, inplace=True )

        mindf.sort_values( by=['trafikantgruppe',  'sqldump_length', 'sqldump_datarad', 'sqldump_frapos' ],
                ascending=[     False,              False,           True,               True], inplace=True )
        
        mindf['geometry'] = mindf['geometri'].apply( wkt.loads )
        minGdf = gpd.GeoDataFrame( mindf, geometry='geometry', crs=25833 )
        minGdf.drop( columns='geometri', inplace=True )
        minGdf.to_file( 'mangelrapport.gpkg', layer=fanenavn + '_alt' + objekttype + 'alle', driver="GPKG")  

        mindf.drop( columns=['geometri', 'geometry'], inplace=True )
        mindf.to_excel( 'mangelrapport.xlsx', sheet_name=fanenavn, index=False  )

        # Vil ha en feature per rad i orginaldatasettet - aggregerer geometri m.m. 
        aggGdf = minGdf[ minGdf['sqldump_length'] >= 1  ].dissolve( by=[ 'sqldump_datarad'], aggfunc={ 'lengde' : 'sum', 
            'vegnr' : 'unique', 'fylke' : 'first', 'kommune' : 'first',  'sqldump_length' : 'first' , 
            'vegkategori' : 'unique', 'trafikantgruppe' : 'unique'}, as_index=False )
        aggGdf['vegnr'] = aggGdf['vegkategori'].apply( lambda x :  ','.join( x ) )  
        aggGdf['vegkategori'] = aggGdf['vegkategori'].apply( lambda x :  ','.join( x ) )  
        aggGdf['trafikantgruppe'] = aggGdf['trafikantgruppe'].apply( lambda x :  ','.join( x ) ) 
        aggGdf['geometry'] = aggGdf['geometry'].apply( lambda x : MultiLineString( [x] ) if x.type == 'LineString' else x )

        aggGdf.sort_values( by=['trafikantgruppe', 'lengde'], ascending=[ False, False ], inplace=True   )

        aggGdf.to_file( 'mangelrapport.gpkg', layer=fanenavn + '_filtrert', driver='GPKG')



        tidsbruk = datetime.now() - t0 
        print( "tidsbruk:", tidsbruk.total_seconds(), "sekunder")

    else: 
        print( f'Fikk ikke lest inn gyldige data fra {FILNAVN}')

