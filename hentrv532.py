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

    vegrefFilter = { 'kartutsnitt' : '-53074.72,6507486.16,-13880.70,6570928.63', 'vegsystemreferanse' : 'Rv,Ev' } 
    # Egenskapverdi for 4566 Vegkategori = E, R eller F 
    vegrefFilter['egenskap'] = '4566=5492 OR 4566=5493 OR 4566=5494'

    # For vegnett har vi brukt 'historisk' - parameteren. Denne finnes ikke for vegobjekter
    # Workaround: Vi laster ned data for hvert år og spleiser dem sammen. Vi går dermed glipp av endringer 
    # som kun gjaldt et par måneder midt i året, for eksempel hvis vegen ble endret både i mars og september 
    # så ser vi ikke det som var gyldig mars-september, kun det som var gyldig ved nyttår før og etter. 
    # Vi går neppe glipp av noe vesentlig. 


    # Liste som holder alle data 
    vegrefdata = [] 

    # Henter objekter gyldige i dag

    vegrefsok = nvdbapiv3.nvdbFagdata(532)
    vegrefsok.filter( vegrefFilter )
    vegrefdata.extend( vegrefsok.to_records())

    debug_2004 = [] 
    debug_2005 = []
    # Henter for alle år fom 2004 - til i dag 
    for year in range( 2004, int( datetime.now().strftime('%Y'))+1):
        print( 'Henter vegreferanse for', year)
        vegrefsok = nvdbapiv3.nvdbFagdata(532)
        vegrefFilter['tidspunkt'] = str(year) + '-01-01'
        vegrefsok.filter( vegrefFilter )
        if year == 2004: 
            debug_2004.extend( vegrefsok.to_records())  
            vegrefdata.extend( debug_2004 )
        elif year == 2005: 
            debug_2005.extend( vegrefsok.to_records())  
        else: 
            vegrefdata.extend( vegrefsok.to_records())        

    # Henter data nyttårsaften 2009 pga alle endringene 1.1.2010 
    print( 'henter data fra nyttårsaften 2009 (før forvaltningsreform 2010')
    vegrefsok = nvdbapiv3.nvdbFagdata(532)
    vegrefFilter['tidspunkt'] = '2009-12-31'
    vegrefsok.filter( vegrefFilter )
    vegrefdata.extend( vegrefsok.to_records())

    vrefDF   = pd.DataFrame( vegrefdata )
    db2004DF = pd.DataFrame( debug_2004 )
    db2005DF = pd.DataFrame( debug_2005 )

    # Lager en fornuftig vegnumer-kolonne 
    vrefDF['vegnummer'] = vrefDF['vref'].apply( lambda x : x.split()[0] )
    db2004DF['vegnummer'] = db2004DF['vref'].apply( lambda x : x.split()[0] )
    db2005DF['vegnummer'] = db2005DF['vref'].apply( lambda x : x.split()[0] )


    # Fra dato som tekst til heltall '1986-01-23' => 19860123
    vrefDF['startdato_num'] = vrefDF['startdato'].apply( lambda x: dato2int(x ))
    vrefDF['sluttdato_num'] = vrefDF['sluttdato'].apply( lambda x: dato2int(x ))

    db2004DF['startdato_num'] = db2004DF['startdato'].apply( lambda x: dato2int(x ))
    db2004DF['sluttdato_num'] = db2004DF['sluttdato'].apply( lambda x: dato2int(x ))
    db2005DF['startdato_num'] = db2005DF['startdato'].apply( lambda x: dato2int(x ))
    db2005DF['sluttdato_num'] = db2005DF['sluttdato'].apply( lambda x: dato2int(x ))

    print( 'Husk å kommenter inn STEG 1 og STEG 2 ')
    tidsbruk = datetime.now( ) - t0 
    print( "tidsbruk:", tidsbruk.total_seconds( ), "sekunder")