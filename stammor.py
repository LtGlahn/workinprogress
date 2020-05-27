from copy import deepcopy
from datetime import datetime 

import pandas as pd 
import geopandas as gpd 
from shapely import wkt

import STARTHER
import nvdbapiv3

"""
Konseptutvikling, presentasjon av relasjonstrær grøntanlegg (for driftskontrakter). 

Lister ut alle vegobjekter i relasjonstreet under ["Grøntanlegg"](https://datakatalogen.vegdata.no/508-Gr%C3%B8ntanlegg) 
med kobling til grøntanlegg-objektet. 

Funksjoner for å lagre resultatene til geopackage. (Konvertering til excel er triviell og går kjappest med FME)
"""


def familietre( nvdbForekomst, relasjonstre = None  ): 
    """
    Traverserer rekursivt datter-relasjonene til et NVDB objekt og returnerer hele familietreet
    nvdbforekomst kan være ID til objektet, eller dictionary hentet fra JSON-spørringer mot NVDB api
    
    Hvis ikke ID til stammor er oppgitt så antar vi at nvdbforekomsten er stammor. 

    Oppføringene i familietreet er records fra funksjonen nvdbapiv3.egenskaper2records( geometri=True), men med disse tilføyelsene: 
        stammor: dictionary med disse tre elle fire feltene: 
            {   stammor_id       = NVDB.objektId til stammor
                stammor_type     = NVDB.objektTypeId til stammor
                stammor_typenavn = NVDB.objektTypeNavn til stammor 
                stammor_navn     = egenskapverdien "Navn" hvis den har verdi for dette objekttet
                }

    Hvis egenskapen "Navn" finnes på stammor eller mor så føyer vi også til disse egenskapverdiene: 
        stammor_navn = Egenskapverdien "Navn" fra stammor (hvis den finnes)

    """

    if isinstance( nvdbForekomst, int): 
        nvdbForekomst = nvdbapiv3.finnid( nvdbForekomst, kunfagdata=True )

    if not isinstance( nvdbForekomst, dict): 
        print( 'familietre: Ugyldig forekomst, returnerer...')
        return relasjonstre


    typeid = nvdbForekomst['metadata']['type']['id']
    egenskaper = nvdbapiv3.egenskaper2records( nvdbForekomst['egenskaper'], geometri=True )


    if not 'geometri' in nvdbForekomst.keys(): 
        print( 'NVDB-objekt uten geometri (kan trygt ignoreres, hopper videre):', nvdbForekomst['id'], nvdbForekomst['metadata']['type']['id'], nvdbForekomst['metadata']['type']['navn'] )
        return None

    elif not relasjonstre: 
        relasjonstre = {  'stammor' : {     'stammor_id'          : nvdbForekomst['id'],
                                            'stammor_type'        : typeid,
                                            'stammor_typenavn'        : nvdbForekomst['metadata']['type']['navn']
                                }
                        }

        if 'Navn' in egenskaper.keys(): 
            relasjonstre['stammor']['stammor_navn'] = egenskaper['Navn']


        # Tar med vegsystemreferanse
        vegref = ','.join( [ vref['kortform'] for vref in  nvdbForekomst['lokasjon']['vegsystemreferanser']  ]  )
        egenskaper.update( {    'stammor_id'            : nvdbForekomst['id'],
                                'stammor_type'          :  typeid, 
                                'stammor_typenavn'      : nvdbForekomst['metadata']['type']['navn'], 
                                'vegsystemreferanser'   : vegref  }  )

        # Tar med geomtri fra generisk "geometri" - tagg
        geom = nvdbForekomst['geometri']
        geom.pop( 'srid')
        egenskaper.update( geom )        

        relasjonstre['stammor_egenskaper'] = egenskaper

    else: 

        # Sjekker om objekttypeID finnes allerede i relasjonstreet; hvis ikke opprettes den
        if not typeid in relasjonstre.keys(): 
            relasjonstre[typeid] = {   'typenavn' : nvdbForekomst['metadata']['type']['navn'], 
                                        'objekter' : [] }

        # Føyer så til denne forekomsten 
        data = deepcopy( relasjonstre['stammor'] )
        data['nvdbid'] = nvdbForekomst['id']
        data['versjon'] = nvdbForekomst['metadata']['versjon']
        data['startdato'] = nvdbForekomst['metadata']['startdato']
        data['sist_modifisert'] = nvdbForekomst['metadata']['sist_modifisert']
        data['typeid'] = nvdbForekomst['metadata']['type']['id']
        data['typenavn'] = nvdbForekomst['metadata']['type']['navn']
        data.update( egenskaper )

        # Tar med vegsystemreferanse
        vegref = ','.join( [ vref['kortform'] for vref in  nvdbForekomst['lokasjon']['vegsystemreferanser']  ]  )
        data.update( { 'vegsystemreferanser' : vegref }  )

        # Tar med geomtri fra generisk "geometri" - tagg
        geom = nvdbForekomst['geometri']
        data.update( geom )


        relasjonstre[typeid]['objekter'].append( data )

    # Itererer rekursivt over alle "barn"  i relasjonstreet 
    if 'relasjoner' in nvdbForekomst.keys() and 'barn' in nvdbForekomst['relasjoner']: 
        for barnetype in nvdbForekomst['relasjoner']['barn']: 
            for etbarnid in barnetype['vegobjekter']: 
                relasjonstre = familietre( etbarnid, relasjonstre=relasjonstre  )
    
    return relasjonstre 

def familieskog( liste_med_slektstre  ):
    """
    Tar en liste med slektstrær og spleiser dem sammen til dictionary med lister
    """ 
    
    skog = {   }

    for tre in liste_med_slektstre: 
        stammor = deepcopy( tre['stammor'] )
        stammor.update( tre['stammor_egenskaper'])

        if 'stammor' not in skog.keys():
            skog['stammor'] = { 'objekter' : [ stammor ] }
        else: 
            skog['stammor']['objekter'].append( stammor )


        for objtype in tre.keys():

            if 'stammor' in str( objtype ): 
                pass
            else: 

                if objtype not in skog.keys(): 
                    skog[objtype] = deepcopy( tre[objtype] )
                else: 
                    skog[objtype]['objekter'].extend( tre[objtype]['objekter'])


    return skog 


def skog2geopakcage( skog, filnavn ): 
    """
    Tar en familieskog (fra funksjon familieskog) og lagrer til geopackage
    """

    for lag in skog.keys(): 

        if 'stammor' in str( lag) : 
            lagnavn = 'stammor'
        else: 
            lagnavn = 'dattertype' + str( lag )
        
        liste2tabell( skog[lag]['objekter'], filnavn, lagnavn)


def liste2tabell( liste, filnavn, lagnavn ): 
    """
    Lagrer liste med nvdb forekomster til angitt geopackage-tabell. Forutsetter geometri i egenskapen "wkt" 

    Fjerner geometri-kolonner (wkt, "Geometri, punkt|linje|flate" ) før lagring 
    """

    mydf = pd.DataFrame( liste )
    
    # Lager ordentlig geometri av wkt-tekst 
    mydf['geometry'] = mydf['wkt'].apply( wkt.loads )

    # fjerner geometrikolonner
    slettkolonner = [ 'Geometri, punkt', 'Geometri, linje', 'Geometri, flate', 'wkt']
    for slett in slettkolonner: 
        if slett in mydf.columns: 
            mydf.drop( slett, inplace=True, axis=1 )   


    minGdf = gpd.GeoDataFrame( mydf, geometry='geometry', crs='EPSG:25833')
    minGdf.to_file( filnavn, layer=lagnavn, driver="GPKG")

def berikfamilietre( gronnnslekt ):
    """
    Beriker familetrær med egenskaper som teller opp areal etc i hht regelverk
    
    For eksempel areal for grasdekker av type (egenskapId=4129) lik "Grasplen" og "Grasbakke". 
    """ 

    # Variabler som holder på de ulike typene antall og areal som er definert
    grasplen_areal = 0
    grasbakke_areal = 0
    traer_antall = 0
    buskfelt_areal = 0
    blomst_areal = 0 

    # Teller areal grasbakker av typen "Grasplen" og "Grasbakke"
    typeid = 15
    if typeid in gronnnslekt.keys() and 'objekter' in gronnnslekt[typeid].keys():
        for grasdekke in gronnnslekt[typeid]['objekter']: 

            if 'Type' in grasdekke.keys() and 'Areal' in grasdekke.keys(): 

                if grasdekke['Type'] == 'Grasbakke': 
                    grasbakke_areal += grasdekke['Areal']
                elif grasdekke['Type'] == 'Grasplen': 
                    grasplen_areal += grasdekke['Areal']
                else: 
                    print( 'Feil egenskapverdi "Type" for grasdekke', grasdekke['nvdbid'])

    gronnnslekt['stammor_egenskaper']['Grasplen areal m2'] =  grasplen_areal
    gronnnslekt['stammor_egenskaper']['Grasbakke areal m2'] =  grasbakke_areal

    # Teller antall trær
    typeid = 199
    if typeid in gronnnslekt.keys() and 'objekter' in gronnnslekt[typeid].keys():
        for tre in gronnnslekt[typeid]['objekter']: 

            if 'Antall' in tre.keys(): 
                traer_antall += tre['Antall']

    gronnnslekt['stammor_egenskaper']['Trær antall'] =  traer_antall

    # Teller areal for busker av typen buskfelt
    typeid = 511
    if typeid in gronnnslekt.keys() and 'objekter' in gronnnslekt[typeid].keys():
        for busk in gronnnslekt[typeid]['objekter']: 

            if 'Type' in busk.keys() and busk['Type'] == 'Buskfelt' and 'Areal' in busk.keys(): 
                buskfelt_areal += busk['Areal']

    gronnnslekt['stammor_egenskaper']['Buskfelt areal'] =  buskfelt_areal

    # Teller areal for blomsterbeplanting 
    typeid = 274 
    if typeid in gronnnslekt.keys() and 'objekter' in gronnnslekt[typeid].keys():
        for blomst in gronnnslekt[typeid]['objekter']: 

            if 'Areal' in blomst.keys(): 
                blomst_areal += blomst['Areal']

    gronnnslekt['stammor_egenskaper']['Bomsterbeplanting areal m2'] =  blomst_areal

    return gronnnslekt



if __name__ == "__main__":

    mittsok = nvdbapiv3.nvdbFagdata( 508 )
    mittsok.addfilter_geo( { 'vegsystemreferanse' : 'rv706'})

    familier = [ ]

    gront = mittsok.nesteForekomst()
    count = 0
    while gront: 
        count += 1 
        print( 'Lager familietre', count, 'av', mittsok.antall )
        tre = familietre( gront ) 
        if tre: 
            tre = berikfamilietre( tre ) # Beriker med egenskapverdier etter Hanne Mørchs ønske
            familier.append(  tre )  
        else: 
            count -= 1

        gront = mittsok.nesteForekomst()

    skog = familieskog( familier )
