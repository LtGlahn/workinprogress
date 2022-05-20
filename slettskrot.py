from copy import deepcopy 
import pdb 

from shapely import wkt 
from shapely.ops import unary_union
import pandas as pd 
import geopandas as gpd 
from datetime import datetime
import json 

import STARTHER
import nvdbapiv3
import skrivnvdb


def sjekksletting( vegobjektid, kunUtenRelasjoner=True, kunUtenStedfesting=True ):
    """
    Sjekker at et objekt i slettemanus er skrotobjekt uten vegnettstilknytning 
    (gitt nøkkelord kunUtenStedfesting=True )

    Hvis nøkkelord kunUtenRelasjoner=True så hopper vi over de objektene som har relasjoner til andre objekter 
    (kan godt hende de skal slettes de og, men det må du finne ut av først)

    For objekter som passerer kontrollen (mangler stedfesting veg, uten  datteobjekter)
    så returnerer vi dictionary med data rett fra NVDB API. Der står jo NVDB ID og versjon, 
    som du trenger for å lukke objektet. Eller hva du nå har tenkt å gjøre... 

    Returnerer None om kontrollen feiler, men skriver en melding til konsollet    

    """

    forb = nvdbapiv3.apiforbindelse()
    r = forb.les( '/vegobjekt', params={ 'id' : vegobjektid })
    if r.ok: 
        data = r.json( )
        if data['relasjoner'] and kunUtenRelasjoner: 
            print( 'Ignorerer objektID', vegobjektid, 'pga relasjoner:', json.dumps( data['relasjoner'], indent=4))
        elif data['lokasjon']['stedfestinger'] and kunUtenStedfesting:
            print( 'Ignorerer objektID', vegobjektid, 'pga gyldig stedfesting'  )

        elif 'sluttdato' in data['metadata']: 
            print( 'Siste gyldige versjon av', vegobjektid, 'er allerede lukket', data['metadata']['sluttdato'] )
        else: 
            return data

    else: 
        print( 'FEILER - feilkode', r.status_code, 'for spørring', r.url )

    return None 

if __name__ == '__main__': 

    # filnavn = 'objekt_uten_vegreferanse.xls'
    filnavn = 'Duplikater NVDB.xlsx'
    slettemanus = pd.read_excel( filnavn )
    slettemanus.rename( columns={'FID' : 'VEGOBJEKT-ID'}, inplace=True)
    # slettemanus = pd.DataFrame( { 'VEGOBJEKT-ID' : [83142283, 89322382, 89322384, 89322383, 89339669, 131977370, 420762716 ] } )
    # slettemanus = pd.DataFrame( { 'VEGOBJEKT-ID' : [83142283, 89322384, 89339669, 131977370, 420762716 ] } )

    # slettemanus = pd.DataFrame( { 'VEGOBJEKT-ID' : [83142283, 89322382, 89339669, 131977370, 420762716 ] } )


    slettobjekter = []


    for ix, row in slettemanus.iterrows():

        if ix < 10: 
            slett = sjekksletting( row['VEGOBJEKT-ID'], kunUtenRelasjoner=False, kunUtenStedfesting=False   )
            if slett: 

                slettobjekter.append( slett )           

    endringssett = skrivnvdb.fagdata2skrivemal( slettobjekter, operasjon='lukk' ) 

    # snakkmedskriv = skrivnvdb.endringssett( endringssett )               # Objekt som håndterer kommunikasjon med SKRIV 
    # snakkmedskriv.forbindelse.login( miljo='testskriv', username='****' )  # Logger inn i SKRIV TESTPROD
    # snakkmedskriv.forbindelse.login( miljo='prodskriv', username='****' )  # Logger inn i SKRIV PRODUKSJON 
                                                                              # Passord oppgis interaktivt, eller bruk nøkkelord pw='***********' 
    # snakkmedskriv.registrer( dryrun=True )                               # Registrer endringssett
    # snakkmedskriv.startskriving( )