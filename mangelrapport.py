from copy import deepcopy 
import pdb 
from datetime import datetime
import string
import requests

from shapely import wkt 
from shapely.geometry import LineString, MultiLineString
# from shapely.ops import unary_union
import pandas as pd 
import geopandas as gpd 
import xlsxwriter

import STARTHER 
import nvdbapiv3


def lesLoggfil( filnavn:string  ): 
    """
    Minimalistisk (forkortet) utgave av funksjon "lesmangel" der vi ikke gjor NOEN gjettinger
    på hva som finnes av data i mottatt loggfil. Vi gjør heller ingen oppslag på stedfesting etc. 

    Se dokumentasjon for lesmangel

    ARGUMENTS
        filnavn : Tekst med filnavn 

    KEYWORDS
        N/A

    RETURNS
        Liste med json, der nøkkelordene er kolonneoverskriftet plukket fra rad 11 (rad 10 med null-basert tellemåte)
    """
    lines = []
    data =  []
    with open( filnavn, errors='ignore' ) as f: 
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

    # Kolonnenavn og posisjon. Her er det dynamisk (ta det du finner), i motsetning til lesmangelrapport+finnkolonnepos, 
    # som er avhengig av at gitte kolonnenavn finnes 
    temp = [ x.strip() for x in lines[10]  if len( x.strip() ) > 0]
    kolonneposisjoner =  { x : count for count, x in enumerate( temp ) }

    # Iterer over alle linjer i fila
    count = 0
    for ll in lines: 
        cc = lesmangelrad_generisk( ll, kolonneposisjoner )
        if cc:
            cc['sqldump_miljo']       = miljo 
            cc['sqldump_dato']        = dato
            cc['sqldump_klokke']      = klokke
            cc['sqldump_beskrivelse'] = beskrivelse
            cc['sqldump_datarad']     = count 
            cc['sqldump_datauttak']   = datauttak
            cc['sqldump_parametre']   = parametre
            cc['filnavn']             = filnavn 

            count += 1  

            data.append( cc )

    return data

# Leser mangelrapport 
def lesmangel( filnavn:string ): 
    """
    Leser mangelrapport (sql-dump) inn som rader 

    ARGUMENTS
        filnavn : Text string, filnavn med loggfil-data som vist nedenfor

    KEYWORDS
        N/A
    
    RETURNS Liste med dictionary 

    EKSEMPEL 

    |       NID      MSLOC      MELOC     LENGTH VREF
    |---------- ---------- ---------- ---------- ----------------------------------------
    |     21765  .36944962  .41532587    357.843 4221 PV98455 S1D1 seq=1000 (K)
    |     21802  .82250887  .82254903       .153 FV403 S2D1 seq=19000 (K)


    Sukk...  nytt format som ser slik ut, må tolke kolonnenavn dynamisk

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

    minstelengde = 3 # Biter kortere enn dette blir LINESTRING( start_wkt, slutt_wkt )
    lines = []
    data = [ ]
    with open( filnavn, errors='ignore' ) as f: 
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

    # Finner linjen som inneholder kolonnenavn. Dette pleide være linje 10, men varierer
    kolonneNavnLinje = lines[10]
    for temp1 in lines[0:20]: 
        temp2 = ';'.join( temp1 ).lower()
        if 'vref' in temp2 and 'netelemid' in temp2: 
            kolonneNavnLinje = temp1

    # from IPython import embed; embed() # For debugging 

    # Rekkefølgen på kolonner varierer, så vi må finne ut hvilke kolonner som er hva 
    kolonneposisjoner = finnkolonnepos( kolonneNavnLinje  )

    count = 0 
    # for ll in lines[0:100]:  # Debugvariant, kun ta de første N linjene
    for ll in lines:          # Hele datasettet
        cc = lesmangelrad( ll, posisjoner=kolonneposisjoner )
        if cc:
            cc['sqldump_miljo']       = miljo 
            cc['sqldump_dato']        = dato
            cc['sqldump_klokke']      = klokke
            cc['sqldump_beskrivelse'] = beskrivelse
            cc['sqldump_datarad']     = count 
            cc['sqldump_datauttak']   = datauttak
            cc['sqldump_parametre']   = parametre
            cc['filnavn']             = filnavn 

            # Henter data for start- og sluttpunkt 
            p1 = nvdbapiv3.veglenkepunkt( str( cc['sqldump_frapos'] ) + '@' + str( cc['sqldump_vlenkid'] ), retur = 'komplett'   )
            if p1: 
                cc['start_wkt']     = p1['geometri']['wkt']
                if 'kortform' in p1['vegsystemreferanse']: 
                    cc['start_vref']    = p1['vegsystemreferanse']['kortform']

            else: 
                print( 'Fikk ikke gyldige data for geometrispørring startpunkt', str( cc['sqldump_tilpos'] ) + '@' + str( cc['sqldump_vlenkid'] )   )

            p2 = nvdbapiv3.veglenkepunkt( str( cc['sqldump_tilpos'] ) + '@' + str( cc['sqldump_vlenkid'] ), retur = 'komplett'   )
            if p2: 
                cc['slutt_wkt']     = p2['geometri']['wkt']
                if 'kortform' in p2['vegsystemreferanse']:
                    cc['slutt_vref']    = p2['vegsystemreferanse']['kortform']
            else: 
                print( 'Fikk ikke gyldige data for geometrispørring sluttpunkt', str( cc['sqldump_tilpos'] ) + '@' + str( cc['sqldump_vlenkid'] )   )

            # Henter rute for segmenter > 3m (minstelengde)
            suksess = False 
            rutefeil = False
            if cc['sqldump_length'] > minstelengde: 
                rute = nvdbapiv3.hentrute( str( cc['sqldump_frapos'] ) + '@' + str( cc['sqldump_vlenkid'] ), 
                                        str( cc['sqldump_tilpos'] ) + '@' + str( cc['sqldump_vlenkid'] )  )

                temp_rute = []
                for segment in rute: 
                    seg = { **segment, **cc }

                    # Sjekker at vi er på samme veglenkesekvens. I noen tilfeller vil vi velge ei anna rute fra A til B hvis det er kortere enn å følge veglenkesekvensen 
                    if seg['veglenkesekvensid'] == seg['sqldump_vlenkid']: 
                        seg['stedfesting'] = 'RUTE'
                        temp_rute.append( seg  )
                        suksess = True 
                    else: 
                        rutefeil = True 

                # Forkaster forslaget hvis det er kommet rutefeil 
                if rutefeil: 
                    suksess = False 
                elif suksess: 
                    data.extend( temp_rute )

                # Prøver å hente data fra NVDB api segmentert vegnett hvis rute-spørring feiler
                if not suksess and cc['sqldump_length'] > minstelengde: 
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
 
            # Fallback hvis lengde < minstelengde, eller ingenting av det andre funker 
            if not suksess: 
                if cc['sqldump_length'] > minstelengde: 
                    cc['stedfesting'] = 'FEILER, kun start-sluttpunkt'
                else:
                    cc['stedfesting'] = 'Kort bit, geometri ut fra start=>sluttpunkt'

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
                    cc['stedfesting'] = 'FEILER, lager fiktiv linje uti Norskehavet'
                    cc['geometri'] =  'LineString (101237.70285620921640657 7128534.10969377029687166, 225651.72560383414383978 7241528.48784137237817049)'

                data.append( cc )

            count += 1 

            if count == 1 or count == 10 or count % 50 == 0: 
                print( f'Prosesserte rad {count} av {len(lines)} for fil {filnavn} ')

            # if cc['sqldump_length'] < minstelengde:
            #     from IPython import embed; embed() # For debugging 

    return data 

def finnkolonnepos( kolonnerad ): 
    """
    Finner rekkefølge på kolonne i dagens SQL-dump 
    """

    # Slik kolonnene var organisert 20.12.2021
    posisjoner={ 'vlenkid' : 0, 'frapos' : 1, 'tilpos' : 2,  'vref' : 3, 'length' : 4  }

    # Oversettelse mellom de begrepene vi bruker og de kryptiske navnene i SQL-dumpen
    oversettelse={ 'vlenkid' : 'netelemid', 
                    'frapos' : 'nstartpos', 'tilpos' : 'nendpos', 
                    'vref' : 'roadsysref', 
                    'length' : 'length'  
                    }

    kolonner = [ x.strip().lower() for x in kolonnerad ]

    for myKey in posisjoner: 
        nypos = __finnListeIndex(  kolonner, oversettelse[ myKey  ]  )
        if nypos: 
            posisjoner[myKey] = nypos 

    return posisjoner

def __finnListeIndex( minliste, mintekst ): 
    """
    Hjelpefunksjon som finner indeks til det første elementet i minListe som matcher mintekst 
    Som er mer kronglete enn det burde vært, ref   https://stackoverflow.com/a/45808300
    """
    try:
        return minliste.index(mintekst)
    except ValueError:
        return None


def lesmangelrad_generisk( enkeltrad, kolonneposisjoner:dict ): 
    """
    Parser en enkelt rad fra mangelrapport
    
    Leser mangelrapport og returnerer dictionary med datavedier for veglenkeid, posisjon fra og til og VREF

    Vil prøve å konvertere dataverdi til flyttall

    ARGUMENTS  
        enkeltrad: Liste med data for en enkelt rad

        posisjoner : dictionary som angir hvilke kolonner som er hva, på stuktur { 'kolonnenavn1' : 0 }, 


    RETURNS 
        dictionary med struktur { 'kolonnenavn1' : dataverd1 }
    """
    returdata = None 

    # Klipper vekk linjeskift hvis det finnes
    if enkeltrad[-1] == '\n': 
        enkeltrad = enkeltrad[0:-1]

    # Har vil linje kun med skilletegn --- ? 
    if len( [ x for x in enkeltrad if '---' in x ] ) > 5:
        return None  


    if len( enkeltrad ) != len( kolonneposisjoner ): 
        return None 
        # print( f"lesmangelrad_generisk: {len(enkeltrad)} kolonner i datasett, forventer {len(kolonneposisjoner)} ")

    returdata = {}
    for key, posisjon in kolonneposisjoner.items():
        if len( enkeltrad ) > posisjon: 
            returdata[key] =  lesdataverdi( enkeltrad[posisjon] )

    # Så en sjekk om vi har lest linja med kolonnedefinisjoner
    # I så fall er returdata['kolonnenavn'] == kolonnenavn
    if len( [ x for x in returdata.keys() if x == returdata[x] ] ) > 0: 
        return None 

    return returdata

def lesdataverdi( dataverdi:str ): 
    """
    Leser dataverdi og prøver å omsette til rett datatype: None (kun mellomrom), float, int eller str
    """

    retur = dataverdi
    utenBlank = dataverdi.strip()
    if len( utenBlank ) == 0: 
        return None  

    # Prøver å konvertere 
    try: 
        heltall = int( utenBlank )
        flyttall = float( utenBlank )
    except ValueError: 
        return utenBlank # Returnerer tekst
    else: 
        if heltall == flyttall: 
            return heltall 
        else: 
            return flyttall 

    return utenBlank # Overflødig, men føles riktig å ha den med

def lesmangelrad( enkeltrad, posisjoner={ 'vlenkid' : 0, 'frapos' : 1, 'tilpos' : 2, 'vref' : 3, 'length' : 4  } ): 
    """
    Parser en enkelt rad fra mangelrapport
    
    Leser mangelrapport og returnerer dictionary med datavedier for veglenkeid, posisjon fra og til og VREF

    nøkkelord posisjoner=dictionary angir hvilke kolonner som er hva
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
            returdata['sqldump_vlenkid'] =      int( mylist[ posisjoner['vlenkid'] ])
            returdata['sqldump_frapos']  =    float( mylist[ posisjoner['frapos']  ])
            returdata['sqldump_tilpos']  =    float( mylist[ posisjoner['tilpos']  ])
            returdata['sqldump_vref']    =           mylist[ posisjoner['vref']  ].strip() 
            returdata['sqldump_length']  =    float( mylist[ posisjoner['length']]  )

        except ValueError: 
            return None 

        else: 
            if returdata['sqldump_vref'] in kjente_feil: 
                print( 'Ignorerer kjent feil', enkeltrad )
                return None 

    return returdata 


def sortervegkategori( vegkategori ):
    """
    Sorterer på vegkategori i rekkefølgen E-R-F-K-P-S 
    """
    minsort = { 'E' : 1, 'R' : 2, 'F' : 3, 'K' : 4, 'P' : 5, 'S' : 6}
    if vegkategori in minsort:
        return minsort[vegkategori]
    return 7

def finnMeter( vref, returnerTilmeter=False  ): 
    """
    Finner frameter eller tilmeter basert på vegreferanse
    """
    fraMeter = ''
    tilMeter = ''

    if vref and isinstance( vref, str) and len( vref ) > 5: 
        splitt1 = vref.split( 'm')
        if len( splitt1 ) > 1: 
            s2 = splitt1[-1]
            if '-' in s2: 
                splitt2 = s2.split('-')
                fraMeter = splitt2[0]
                if len( splitt2 ) > 1: 
                    tilMeter = splitt2[1]

    if returnerTilmeter: 
        return tilMeter
    else: 
        return fraMeter 


def lagmangel( FILNAVN, gpkg_fil, excelwriter ):

    tx = datetime.now()

    dd = lesmangel(  FILNAVN )

    mindf = pd.DataFrame( dd  ) 
    mindf['filnavn'] = FILNAVN

    # from IPython import embed; embed() # For debugging 
    mineFanenavn = {  '900' : 'Hull Tømmer off', 
                      '901' : 'Hull Tømmer UOFF',
                      '902' : 'Hull Spesial off',
                      '903' : 'Hull Spesial UOFF',
                      '904' : 'Hull Bk Normal off',
                      '905' : 'Hull Bk Normal UOFF'
                    }


    if len( mindf ) > 0: 

        # Finner objekttype
        objekttype = mindf.iloc[0]['sqldump_parametre'].split('=')[1].split()[0]
        fanenavn = mineFanenavn[ objekttype ]

        if 'gate' in mindf.columns: 
            mindf['gate'] = mindf['gate'].apply( lambda x : x['navn'] if isinstance(x, dict)  and 'navn' in x else ''  )

        # Legger på vegkategori
        # mindf['vegkategori'] = mindf['vref'].apply( lambda x: getFirstChar(x) )
        mindf['vegnr'] = mindf['vref'].apply( lambda x: x.split()[0] if isinstance(x, str) and len(x) > 0 else ' ' )

        # Legger på kommunenavn 
        komm = requests.get( 'https://nvdbapiles-v3.atlas.vegvesen.no/omrader/kommuner.json').json()
        kommunenavn = { x['nummer'] : x['navn'] for x in komm }
        mindf['kommunenavn'] = mindf['kommune'].map( kommunenavn ).fillna('')

        col = [ 'vegkategori', 'vegnr', 'vref', 'lengde', 'trafikantgruppe', 'fylke', 'kommune', 'kommunenavn', 'gate',  'stedfesting', 
                'vegkategori', 'sqldump_vlenkid', 'sqldump_frapos', 'sqldump_tilpos', 
                'sqldump_length', 'sqldump_vref', 'sqldump_miljo', 'sqldump_dato', 
                'sqldump_klokke', 'sqldump_beskrivelse', 'sqldump_datarad', 
                'sqldump_datauttak', 'sqldump_parametre', 
                'kortform', 'type',  'typeVeg', 'geometri', 'filnavn' ]

        slettecol = list( set( mindf.columns ) - set(col) )
        mindf.drop( columns=slettecol, inplace=True )
        mindf['vegnr'].fillna(  ' ', inplace=True )
        mindf['vegkategori'].fillna( ' ', inplace=True )
        mindf['sortering'] = mindf['vegkategori'].apply( lambda x : sortervegkategori( x ))


        mindf.sort_values( by=['sortering', 'kommune', 'lengde', ],
                ascending=[     True,        True,      True ], inplace=True )
        
        mindf['geometry'] = mindf['geometri'].apply( wkt.loads )
        minGdf = gpd.GeoDataFrame( mindf, geometry='geometry', crs=25833 )
        minGdf.drop( columns='geometri', inplace=True )
        minGdf.to_file( gpkg_fil, layer='debug_' + fanenavn, driver="GPKG")  

        mindf.drop( columns=['geometri', 'geometry'], inplace=True )
        # mindf.to_excel( 'mangelrapport.xlsx', sheet_name=fanenavn, index=False  )

        # Føyer på fra- og tilmeter 
        mindf['Fra m'] = mindf['vref'].apply( lambda x : finnMeter(x) )
        mindf['Til m'] = mindf['vref'].apply( lambda x : finnMeter(x, returnerTilmeter=True) )

        # Vil ha en feature per vegnummer og kommune i orginaldatasettet - aggregerer geometri m.m. 
        # Ignorerer dem som mangler vegnr, vegkategori m.m. 
        temp = minGdf.dropna( subset=['vegkategori']  )
        temp['trafikantgruppe'].fillna( ' ', inplace=True )

        aggGdf = temp[ (temp['sqldump_length'] >= 1) & (temp['lengde'] >= 1)  ].dissolve( by=[ 'vegnr', 'kommune', 'kommunenavn'], aggfunc={ 'lengde' : 'sum',
                 'fylke' : 'first',  'sqldump_length' : 'first' , 'vegkategori' : 'unique', 'trafikantgruppe' : 'unique'}, as_index=False )
                
        aggGdf['vegkategori'] = aggGdf['vegkategori'].apply(         lambda x :  ','.join( list(x) ) )  
        aggGdf['trafikantgruppe'] = aggGdf['trafikantgruppe'].apply( lambda x :  ','.join( list(x) ) ) 
        aggGdf['geometry'] = aggGdf['geometry'].apply( lambda x : MultiLineString( [x] ) if x.type == 'LineString' else x )

        aggGdf.sort_values( by=['trafikantgruppe', 'vegnr', 'lengde'], ascending=[ False, True, False ], inplace=True   )

        # aggGdf.to_file( gpkg_fil, layer=fanenavn + '_filtrert', driver='GPKG')
        aggGdf[ (aggGdf['vegkategori'].str.contains('E')) | (aggGdf['vegkategori'].str.contains('R')) ].to_file( gpkg_fil, layer=fanenavn + '_ER', driver='GPKG')
        aggGdf[ aggGdf['vegkategori'].str.contains('F') ].to_file( gpkg_fil, layer=fanenavn + '_F', driver='GPKG')
        aggGdf[ aggGdf['vegkategori'].str.contains('K')].to_file( gpkg_fil, layer=fanenavn + '_K', driver='GPKG')
        # print( "Har kommentert ut skriving til gpkg")

        tidsbruk = datetime.now() - tx
        print( F"tidsbruk Bk{objekttype}: {tidsbruk.total_seconds()} sekunder")

        # Summerer statistikk per vegkategori og per kommune: 
        aggGdf['antall'] = 1 
        statistikk = aggGdf.groupby( ['vegkategori', 'trafikantgruppe']  ).agg({ 'antall' : 'count', 'lengde' : 'sum' } )
        statistikk_perkommune = aggGdf.groupby( ['vegkategori', 'kommune', 'kommunenavn', 'trafikantgruppe']  ).agg( {'antall' : 'count', 'lengde' : 'sum'}  )
        metadata = metadata = pd.DataFrame( { 'verdi' : [ str(t0), FILNAVN, fanenavn ] }, index=['Dato', 'Filnavn', 'Type' ] )

        # Skriver til excel: 
        # excelwriter = pd.ExcelWriter( EXCELFIL, engine='xlsxwriter')

        # Døper om kolonner så de matcher brukerønskene 
        mindf.rename( columns={ 'vref' :  'Vegreferanse', 'lengde' : 'Lengde hull', 'kommune' : 'Kommune',  'gate' : 'Gate', 'vegkategori' : 'Vegkategori'   }, inplace=True)
        col2 = [ 'Vegkategori', 'Vegreferanse', 'Fra m', 'Til m', 'Lengde hull', 'Kommune', 'kommunenavn', 'Gate', 'typeVeg', 'fylke']
        mindf[ mindf['Lengde hull'] >= 1][col2].to_excel( excelwriter, sheet_name= fanenavn, index=False )
        excelwriter.sheets[fanenavn].set_column( 0, 9, 20 )
        excelwriter.sheets[fanenavn].set_column( 1, 1, 60 )
        excelwriter.sheets[fanenavn].set_column( 6, 6, 40 )

        # statistikk.to_excel( excelwriter, sheet_name='Statistikk ' + fanenavn, index=True )
        # aggGdf[['vegnr', 'vegkategori',  'fylke', 'kommune', 'kommunenavn', 'lengde', 'trafikantgruppe']].to_excel( excelwriter, sheet_name='Annen visning '+fanenavn, index=False  )
        # metadata.to_excel( excelwriter, sheet_name='Metadata' + fanenavn, index=True  )
        # statistikk_perkommune.to_excel( excelwriter, sheet_name='Statistikk per kommune' + fanenavn, index=True ) # 
        # TODO: Må korte inn navnet på fanen, men tror den er overflødig

        # excelwriter.save()

    else: 
        print( f'Fikk ikke lest inn gyldige data fra {FILNAVN}')

###################################################
## 
## Scriptet starter her
##
#######################################################
if __name__ == '__main__': 

    #####################################################
    ## 
    ## Last ned ny LOGG-fil fra https://nvdb-datakontroll.atlas.vegvesen.no/ for objekttype 901, 903 og 905 
    ## Legg fila i samme mappe som dette scriptet, og editer inn filnavnet her: 

    mangeldato = '20221024'

    loggfiler = [ f'checkCoverage 900_{mangeldato}.LOG', f'checkCoverage 901_{mangeldato}.LOG', f'checkCoverage 902_{mangeldato}.LOG', 
                  f'checkCoverage 903_{mangeldato}.LOG', f'checkCoverage 904_{mangeldato}.LOG', f'checkCoverage 905_{mangeldato}.LOG' ]

    # loggfiler = [ f'checkCoverage 905_{mangeldato}.LOG' ]

    mindato = datetime.now().strftime( "%Y-%m-%d")

    # gpkg_fil = 'mangelrapportDEBUG.gpkg'
    gpkg_fil = 'mangelrapport-Bruksklasser' + mindato + '.gpkg'

    # Skriver til excel:
    excel_fil = 'mangelrapport-Bruksklasser' + mindato + '.xlsx' 
    excelwriter = pd.ExcelWriter( excel_fil, engine='xlsxwriter')
    

    print( 'Mangelrapport 3.4 - Nytt og enklere loggfil-format')
    t0 = datetime.now()

    for FILNAVN in loggfiler: 

        lagmangel( FILNAVN, gpkg_fil, excelwriter )


    excelwriter.save()
    tidsbruk = datetime.now() - t0 
    print( F"tidsbruk alle objekttyper: {tidsbruk.total_seconds()} sekunder")
