"""
Script som viser hvordan du kan hente historiske data fra NVDB api og analysere dem. 

SCriptet forutsetter at disse bibliotekene finnes på søkestien: 
  - geopandas https://geopandas.org/ 
  - nvdbapiv3 https://github.com/ltglahn/nvdbapi-v3 

Hvis du må installere python så anbefaler vi anaconda-distribusjonen https://anaconda.org/ 
"""

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

def vegstatus2kortform( vegstatus ): 
    """
    Konverterer 532 - egenskapen "vegstatus" til sin forkortelse, f.eks. "Eksisterende veg" => "V" 
    """

    oversett =  {   'Eksisterende veg' :  					'V' , 
                    'Midlertidig veg' :                      'W' , 
                    'Midlertidig status bilveg' :            'T' , 
                    'Eksisterende ferjestrekning' :          'S' , 
                    'Gang-/sykkelveg' :                      'G' , 
                    'Midlertidig status gang-/sykkelveg' :   'U' , 
                    'Beredskapsveg' :                        'B' , 
                    'Serviceveg' :                           'M' , 
                    'Rømningstunnel' :                       'X' , 
                    'Anleggsveg' :                           'A' , 
                    'Gang-/sykkelveg anlegg' :               'H' , 
                    'Vedtatt veg' :                          'P' , 
                    'Vedtatt ferjestrekning' :               'E' , 
                    'Vedtatt gang-/sykkelveg' :              'Q'  
                    } 

    retval = ''
    if vegstatus in oversett: 
        retval = oversett[vegstatus]


    return retval 

def finntrafikantgruppe( vegstatus ): 
    """
    Konverter vegstatus på 532 - objektet til trafikantgruppe 

    Vi oversetter de 4 som er varianter av gang/sykkelveg til trafikantgruppe = 'G', resten til 'K'


    Se datakatalog-definisjonen på vegstatus https://datakatalogen.vegdata.no/532-Vegreferanse
    Eventuelt https://api.vegdata.no/verdi/vegreferanse.html

    """

    if vegstatus in [ 'Gang-/sykkelveg', 'Midlertidig status gang-/sykkelveg', 
                    'Gang-/sykkelveg anlegg', 'Vedtatt gang-/sykkelveg' ]: 

        return 'G'
    else: 
        return 'K'

if __name__ == '__main__': 

    t0 = datetime.now( )
 
    ##################################################################################
    ## DEMO 3
    ## 
    ## For data eldre enn november 2019 så er vegnettsdata litt mangelfulle: Du mangler for 
    ## eksempel data for trafikantgruppe. Løsningen er å hente historikk for objekttypen 532 vegreferanse
    ##
    ## For å få et mer komplett eksempel henter vi data for både E, R og F - veger
    ## ID'ene som er brukt i egenskapsfilteret er hentet fra datakatalogen, sjølsagt
    ## https://datakatalogen.vegdata.no/532-Vegreferanse

    vegrefFilter = { 'kartutsnitt' : '-53074.72,6507486.16,-13880.70,6570928.63' } 
    # Egenskapverdi for 4566 Vegkategori = E, R eller F 
    vegrefFilter['egenskap'] = '4566=5492 OR 4566=5493 OR 4566=5494'

    # For vegnett har vi brukt 'historisk' - parameteren. Denne finnes ikke for vegobjekter
    # Workaround: Vi laster ned data for hvert år og spleiser dem sammen. Vi går dermed glipp av endringer 
    # som kun gjaldt et par måneder midt i året, for eksempel hvis vegen ble endret både i mars og september 
    # så ser vi ikke det som var gyldig mars-september, kun det som var gyldig ved nyttår før og etter. 
    # Hvis du er engstelig for å gå glipp av vesentlige vegnettsendringer (lite sannsynlig) kan du øke 


    # Liste som holder alle data 
    vegrefdata = [] 

    # Henter objekter gyldige i dag

    vegrefsok = nvdbapiv3.nvdbFagdata(532)
    vegrefsok.filter( vegrefFilter )
    vegrefdata.extend( vegrefsok.to_records())

    # Henter for alle år fom 2004 - til i dag 
    for year in range( 2004, int( datetime.now().strftime('%Y'))+1):
        print( 'Henter 532 Vegreferanse for', year)
        vegrefsok = nvdbapiv3.nvdbFagdata(532)
        vegrefFilter['tidspunkt'] = str(year) + '-01-01'
        vegrefsok.filter( vegrefFilter )
        vegrefdata.extend( vegrefsok.to_records())        

    # Henter data nyttårsaften 2009 pga alle endringene 1.1.2010 
    print( 'henter 532 Vegreferanse fra nyttårsaften 2009 (før forvaltningsreform 2010')
    vegrefsok = nvdbapiv3.nvdbFagdata(532)
    vegrefFilter['tidspunkt'] = '2009-12-31'
    vegrefsok.filter( vegrefFilter )
    vegrefdata.extend( vegrefsok.to_records())

    raaDf   = pd.DataFrame( vegrefdata )

    # Filtrer vekk duplikater (Dvs objekter som er uendret gjennom flere år => som gir 
    #                           dubletter fordi vi henter data for hvert år)
    vrefDF = raaDf.drop_duplicates( subset=['nvdbId', 'versjon', 
                        'veglenkesekvensid', 'startposisjon', 'sluttposisjon' ] ).copy()

    # Døper om kolonner der vi har navnekollisjon 
    nyenavn = { 'vegkategori'      : 'vegsystem_vegkategori', 
                'fase'             : 'vegsystem_fase', 
                'vegnummer'        : 'vegsystem_vegnummer', 
                'trafikantgruppe' : 'vegsystem_trafikantgruppe' }
    vrefDF.rename( columns=nyenavn, inplace=True )


    # Lager en fornuftig vegnumer-kolonne. Bruker egenskapsverdiene fra 
    vrefDF['kortvegstatus'] = vrefDF['Vegstatus'].apply( lambda x : vegstatus2kortform( x ) )
    vrefDF['kortvegkat'] = vrefDF['Vegkategori'].apply( lambda x : x[0] )
    vrefDF['kortvegnr'] = vrefDF['kortvegkat'] + vrefDF['kortvegstatus'] + vrefDF['Vegnummer'].astype( str )

    # Fra dato som tekst til heltall '1986-01-23' => 19860123
    vrefDF['startdato_num'] = vrefDF['startdato'].apply( lambda x: dato2int(x ))
    vrefDF['sluttdato_num'] = vrefDF['sluttdato'].apply( lambda x: dato2int(x ))

    # Lager trafikantgruppe ut fra 532 Vegferferanse sin egenskapverdi vegstatus
    vrefDF['trafikantgruppe'] = vrefDF['Vegstatus'].apply( lambda x : finntrafikantgruppe( x ) ) 

    # Lager geodataframe
    vrefDF['geometry'] = vrefDF['geometri'].apply( wkt.loads )
    vrefDF.drop( columns=[ 'geometri'], inplace=True)
    vrefGDF  = gpd.GeoDataFrame( vrefDF, geometry='geometry', crs=5973  )
    vrefGDF.to_file( 'vr532analyse.gpkg', layer='vegreferanse', driver='GPKG' )

    tidsbruk = datetime.now( ) - t0 
    print( "tidsbruk:", tidsbruk.total_seconds( ), "sekunder")