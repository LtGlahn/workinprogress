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

        elif 'sluttdato' in data['metadata']: 
            print( 'Siste gyldige versjon av', vegobjektid, 'er allerede lukket', data['metadata']['sluttdato'] )
        else: 
            return data

    else: 
        print( 'FEILER - feilkode', r.status_code, 'for spørring', r.url )

    return None 

if __name__ == '__main__': 

    filnavn = 'objekt_uten_vegreferanse.xls'
    slettemanus = pd.read_excel( filnavn )
    slettobjekter = []

    for ix, row in slettemanus.iterrows():

        slett = sjekksletting( row['VEGOBJEKT-ID'] )
        if slett: 

            slettobjekter.append( slett )                

    endringssett = skrivnvdb.fagdata2skrivemal( slettobjekter, operasjon='lukk' ) 

    # snakkmedskriv = skrivnvdb.endringssett( endringssett )               # Objekt som håndterer kommunikasjon med SKRIV 
    # snakkmedskriv.forbindelse.login( miljo='testskriv', username='****' )  # Logger inn i SKRIV TESTPROD
    # snakkmedskriv.forbindelse.login( miljo='prodskriv', username='****' )  # Logger inn i SKRIV PRODUKSJON 
                                                                              # Passord oppgis interaktivt, eller bruk nøkkelord pw='***********' 
    # snakkmedskriv.registrer( dryrun=True )                               # Registrer endringssett
    # snakkmedskriv.startskriving( )