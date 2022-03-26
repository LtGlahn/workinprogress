"""
Lapper små hull (og evt større?) i bruksklasse basert på tilstøtende BK-objekter

Regler: 
   - Tilstøtende objekter med ulike BK-verdier: Må gi opp hvis det er tre stykker (innafor toleranse), dvs at vi har et kryss
     og er usikker på om vi er på den ene eller andre siden av krysset (krever litt mer raffinert logikk å finne hvilket objekt som skal 
     forlenges inn mot, men ikke gjennom krysset - IKKE noe vi fintenker ut nå. Manuell vurdering?)

   - To tilstøtende objekter med ulike BK-verdier: Plukk en - vilkårlig hvilken og forleng den gjennom hullet (delvis oppdater av stedfesting)
        - NB! Sjekk at hull og BK-objekt som forlenges er innafor samme kommune, plukk den andre hvis ikke. 

    - Må ha logikk for å forenkle stedfesting, dvs hvis hullet er et hull i et objekts (multiple) stedfesting så forenkler vi slik at hullet lukkes
        eks: Et objekt stedfestet på 0-0.4999998 og 0.5-1 skal ha stedfesting 0-1 når hullet er lukket, ikke multippel med 0-0.5 og 0.5-1 (joda, skriv 
        og NVDB-databasen har en viss logikk for å lukke slike tøysehull, men vi bør ta det ansvaret sjøl. 

    

"""
from copy import deepcopy
import pdb
from datetime import datetime

import pandas as pd
import geopandas as gpd 
import fiona

import warnings # Ignorerer den irriterende meldingen fra geopandas.from_file(), og litt anna støy 
warnings.filterwarnings("ignore", message="Sequential read of iterator was interrupted. Resetting iterator. This can negatively impact the performance.")
warnings.filterwarnings("ignore", message="The spaces in these column names will not be changed. In pandas versions < 0.14, spaces were converted to underscores.")

import STARTHER
import skrivnvdb 
from nvdbapiv3 import  nvdbFagdata, apiforbindelse 
from nvdbgeotricks import finnoverlapp 

def leshull( filnavn ): 
    layerlist = fiona.listlayers( filnavn )
    mittlag = [ x for x in layerlist if '904' in x and 'debug' in x ][0]

    bkhull = gpd.read_file( filnavn, layer=mittlag )
    retthull = bkhull[ bkhull['sqldump_length'] <= 2 ].copy()
    retthull.sort_values( by='sqldump_length', inplace=True)
    retthull.reset_index( inplace=True )
    return retthull 

if __name__ == '__main__': 

    retthull = leshull( 'mangelrapport.gpkg')