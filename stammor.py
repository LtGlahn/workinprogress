"""
Konseptutvikling, presentasjon av relasjonstrær grøntanlegg (for driftskontrakter). 

Lister ut alle vegobjekter i relasjonstreet under ["Grøntanlegg"](https://datakatalogen.vegdata.no/508-Gr%C3%B8ntanlegg) 
med kobling til grøntanlegg-objektet. 

Funksjoner for å lagre resultatene til geopackage. (Konvertering til excel er triviell og går kjappest med FME)

Installasjon: Må ha dataFrames og GeoDataframes-bibliotekene pandas og geopandas. Shapely er inkludert i geopandas. 

Dette er konseptutvikling og eksperimentering, og ikke optimalisert på noen som helst måte! F.eks. henter vi ett og ett 
datterobjekt, og det går jo unødvendig tregt. Vi bruker ca 45 minutter på å hente data for grøntanlegg i Trøndelag 
(655 grøntanlegg, 11810 objekter totalt i relasjonstrærne)
"""

from copy import deepcopy
from datetime import datetime 
import re

import pandas as pd 
import geopandas as gpd 
from shapely import wkt

import STARTHER
import nvdbapiv3




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

    NB! Dette er konseptutvikling / eksperimentering / demonstrator! 

    Nedlasting av store datamengder er ekstremt ineffektivt: Vi henter ett og ett objekt i relasjonstreet
    fra angitt rot og nedover. Greit nok for å eksperimenter / demonstrere, men her er det MYE som bør optimaliseres
    i produksjon. 
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

        # kontraktsområder
        k_omr = ','.join( [ kOmr['navn'] for kOmr in  nvdbForekomst['lokasjon']['kontraktsområder']  ]  )


        # Tar med vegsystemreferanse
        vegref = ','.join( [ vref['kortform'] for vref in  nvdbForekomst['lokasjon']['vegsystemreferanser']  ]  )
        vegref = pyntvegref( vegref )
        egenskaper.update( {    'stammor_id'            : nvdbForekomst['id'],
                                'stammor_type'          :  typeid, 
                                'stammor_typenavn'      : nvdbForekomst['metadata']['type']['navn'], 
                                'vegsystemreferanser'   : vegref, 
                                'kontraktsområder'      : k_omr  }  )

        

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

        # kontraktsområder
        k_omr = ','.join( [ kOmr['navn'] for kOmr in  nvdbForekomst['lokasjon']['kontraktsområder']  ]  )
        data.update( { 'kontraktsområder' : k_omr })

        # Tar med vegsystemreferanse
        vegref = ','.join( [ vref['kortform'] for vref in  nvdbForekomst['lokasjon']['vegsystemreferanser']  ]  )
        vegref = pyntvegref( vegref )
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


def skog2geopakcage( skog, filnavn, kontraktsomrader=True ): 
    """
    Tar en familieskog (fra funksjon familieskog) og lagrer til geopackage
    """

    for lag in skog.keys(): 

        if 'stammor' in str( lag) : 
            lagnavn = 'stammor'
        else: 
            lagnavn = 'dattertype' + str( lag )
        
        liste2tabell( skog[lag]['objekter'], filnavn, lagnavn, kontraktsomrader=kontraktsomrader)


def liste2tabell( liste, filnavn, lagnavn, kontraktsomrader=True ): 
    """
    Lagrer liste med nvdb forekomster til angitt geopackage-tabell. Forutsetter geometri i egenskapen "wkt" 

    Fjerner geometri-kolonner (wkt, "Geometri, punkt|linje|flate" ) før lagring 
    """

    mydf = pd.DataFrame( liste )
    
    # Lager ordentlig geometri av wkt-tekst 
    mydf['geometry'] = mydf['wkt'].apply( wkt.loads )

    # fjerner geometrikolonner
    slettkolonner = [ 'Geometri, punkt', 'Geometri, linje', 'Geometri, flate', 'wkt']
    if not kontraktsomrader: 
        slettkolonner.append( 'kontraktsområder')

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

    # Spesialvarianter som summerer basert på om det finnes tekst med "Klippes 2 ganger" i egenskapen "tilleggsinformasjon"
    grasbakke_areal_2x = 0
    grasplen_areal_2x = 0

    # Spesialvarianter som summerer basert på om det finnes tekst med "Klippes 4 ganger" i egenskapen "tilleggsinformasjon"
    grasbakke_areal_4x = 0
    grasplen_areal_4x = 0


    # Teller areal grasbakker av typen "Grasplen" og "Grasbakke"
    typeid = 15
    if typeid in gronnnslekt.keys() and 'objekter' in gronnnslekt[typeid].keys():
        for grasdekke in gronnnslekt[typeid]['objekter']: 

            klippetekst = 'tomtekst'
            if 'Tilleggsinformasjon' in grasdekke.keys(): 
                klippetekst = re.sub(r'\s+', '',  grasdekke['Tilleggsinformasjon'].lower() )  

            if 'Type' in grasdekke.keys() and 'Areal' in grasdekke.keys(): 

                if grasdekke['Type'] == 'Grasbakke': 
                    grasbakke_areal += grasdekke['Areal']

                    if 'klippes2ganger' in klippetekst: 
                        grasbakke_areal_2x += grasdekke['Areal']
                    elif 'klippes4ganger' in klippetekst: 
                        grasbakke_areal_4x += grasdekke['Areal']

                elif grasdekke['Type'] == 'Grasplen': 
                    grasplen_areal += grasdekke['Areal']

                    if 'klippes2ganger' in klippetekst: 
                        grasplen_areal_2x += grasdekke['Areal']
                    elif 'klippes4ganger' in klippetekst: 
                        grasplen_areal_4x += grasdekke['Areal']


                else: 
                    print( 'Feil egenskapverdi "Type" for grasdekke', grasdekke['nvdbid'])

    gronnnslekt['stammor_egenskaper']['Grasplen areal m2'] =  grasplen_areal
    gronnnslekt['stammor_egenskaper']['Grasbakke areal m2'] =  grasbakke_areal

    gronnnslekt['stammor_egenskaper']['Grasbakke 2x areal'] =  grasbakke_areal_2x
    gronnnslekt['stammor_egenskaper']['Grasbakke 4x areal'] =  grasbakke_areal_4x
    gronnnslekt['stammor_egenskaper']['Grasplen 2x areal'] =  grasplen_areal_2x
    gronnnslekt['stammor_egenskaper']['Grasplen 4x areal'] =  grasplen_areal_4x

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

def pyntvegref( vegref):
    """
    Forenkler kommaseparert liste med vegsystemreferanser. Tilgrensende meterverdier slås sammen. 

    For eksempel 'RV706 S1D1 m5846-5869,RV706 S1D1 m5869-5885' => 'RV706 S1D1 m5846-5885'
    """

    data = [ ]
    resultat = [ ]
    liste = vegref.split( ',')

    # Trivielt tilfelle: Kun en forekomst
    if len( liste ) <= 1: 
        return vegref 

    for segment in liste: 

        
        temp = segment.split( ) # Meterverdier = siste ord i vegsystemreferanse-teksten
        temp2 = temp[-1].split( '-') # Splitter meterverdier. Merk at den første forekomsten har forstavelsen m
        data.append( { 'anker' :  ' '.join( temp[:-1]), 'fra' : int( temp2[0][1:]), 'til' : int( temp2[1])  })

    # Lagrer som dataframe, sorterer på ankerpunkt og fra-meter
    mydf = pd.DataFrame(  data )
    mydf.sort_values( [ 'anker', 'fra'], inplace=True )  


    # Finner meterverdi og differanse for raden nedefor 
    mydf['neste_fra'] = mydf['fra'].shift(-1)     
    mydf['meterdiff'] = mydf['neste_fra'] - mydf['til']   

    # Itererer over alle radene, samler opp inntil enten "anker"-verdien endres eller meterdiff > 0
    # først må vi initialisere med data fra den første raden. 

    anker = mydf.iloc[0, 0]
    fra   = mydf.iloc[0, 1] 
    til   = mydf.iloc[0, 2] 

    for ix, row in mydf.iterrows():   
        # Sjekker om betingelsene er tilstede for å slå sammen denne strekningen med foregående
        # I så fall justerer vi til-meterverdien 
        if row['meterdiff'] == 0 and row['anker'] == anker:  
            til = row['til'] 
        else: 
            # Må legge fra oss det vi har slått sammen og gå videre med ny, ettersom vi har brudd i meterverdi og/eller ankerverdi
            # Komponerer vegsystemreferanse med anker + den første fra-meterverdien og akkumulert til-meterverdi  
            resultat.append( anker + ' m' + str( int(fra) ) + '-' + str( int( til)) ) 
            # Starter med ny oppføring 
            anker = row['anker'] 
            fra = row['fra'] 
            til = row['til'] 

    return ','.join( resultat )


if __name__ == "__main__":

    mittsok = nvdbapiv3.nvdbFagdata( 508 )
    # mittsok.addfilter_geo( { 'vegsystemreferanse' : 'rv706'})
    # mittsok.addfilter_geo( { 'fylke' : '50'})
    # mittsok.addfilter_geo( { 'kartutsnitt' : '227416.128,6951595,227631.4,6951816.951'})

    k_omr = [ '9302 Haugesund 2020-2025', '9304 Bergen', '9305 Sunnfjord' ]

    mittsok.addfilter_geo( { 'kontraktsomrade' : k_omr})

    familier = [ ]

    t0 = datetime.now()

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

    dt = datetime.now( ) - t0 
    print( 'Kjøretid', dt.total_seconds(), 'sekunder' )