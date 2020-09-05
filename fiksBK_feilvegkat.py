import STARTHER
import nvdbapiv3
from copy import deepcopy 
import pdb 

from shapely import wkt 
from shapely.ops import unary_union
import pandas as pd 
import geopandas as gpd 
from datetime import datetime

def utvidbbox( bbox, buffer):
    """
    Utvider en boundingbox

    ARGUMENTS
        bbox : tuple med de eksisterende (xmin, ymin, xmax, ymax) boundingBox-verdier

        buffer: Int eller float, antall koordinat-enheter (meter) som boksen skal utvides med

    KEYWORDS: 
        None

    RETURNS
        bbox : tuple med utvidede (xmin, ymin, xmax, ymax) boundingBox-verdier
    
    """

    return (  bbox[0] - buffer, bbox[1] - buffer, bbox[2] + buffer,  bbox[3] + buffer) 


def joinbbox( bboxA, bboxB): 
    """
    Slår sammen to boundinbboxer til en større bbox som overlapper begge to

    ARGUMENTS
        bboxA : None eller tuple med de eksisterende (xmin, ymin, xmax, ymax) boundingBox-verdier

        bboxB:  tuple med nye (xmin, ymin, xmax, ymax) boundingBox-verdier

    KEYWORDS: 
        None

    RETURNS
        tuple med (xmin, ymin, xmax, ymax) boundingBox-verdier
    """


    if not bboxA: 
        bbox = bboxB
    else: 
        bbox = (  min( bboxA[0], bboxB[0] ), 
                  min( bboxA[1], bboxB[1] ), 
                  max( bboxA[2], bboxB[2] ), 
                  max( bboxA[3], bboxB[3] )
                ) 


    return bbox 

def finntrafikantgruppe( seg): 
    """
    Finner trafikantgruppe for vegsegment tilknyttet vegobjekt (rått fra NVDB api V3)
    """

    trafikantgruppe = 'U'
    if 'kryssystem' in seg['vegsystemreferanse'].keys(): 
        trafikantgruppe = seg['vegsystemreferanse']['kryssystem']['trafikantgruppe']
    elif 'sideanlegg' in seg['vegsystemreferanse'].keys(): 
        trafikantgruppe = seg['vegsystemreferanse']['sideanlegg']['trafikantgruppe']
    elif 'strekning' in seg['vegsystemreferanse'].keys(): 
        trafikantgruppe = seg['vegsystemreferanse']['strekning']['trafikantgruppe']
    else: 
        print( 'MANGLER vegreferansedetaljer', seg['vegsystemreferanse']['kortform'], bk1['href'])


    return trafikantgruppe

def registreringsegenskaper( egenskaper ): 
    """
    Konvererer liste med egenskapverdier (rått fra NVDB api V3) til dictionary med ID : verdi 
    hvor ID = typeId til denne egenskapen ihtt datakatalogen 
    """

    data = { }
    for eg in egenskaper: 

        if 'verdi' in eg.keys():
            data[ eg['id'] ] = eg['verdi']

    return data 

def ignorerliste( ):
    """
    Liste med objektid som av ulike årsaker IKKE skal prosesseres 
    """

    # ignorer = [ 835347602   ]
    ignorer = [  779620154,  1007822938  ]
    return ignorer 

def liste2gpkg( minliste, filnavn, lagnavn, **kwargs):
    """
    Lagrer liste med NVDB-fagdata til geopackage
    ARGUMENTS: 
        minliste - liste med NVDB-objekt
        
        filnavn - navn på .gpkg-fil vi skal skrive til
        lagnavn - navn på tabellen vi skal lagre 
    KEYWORDS: 
        Blir videresendt til nvdbapiv3.nvdbfagdata2records

    RETURNS: 
        Geodataframe (for debugging / inspeksjon, du får den gdf'en vi skrev til fil)

    """

    liste2 = nvdbapiv3.nvdbfagdata2records( minliste, **kwargs )
    if len( liste2 ) > 0: 
        mindf = pd.DataFrame( liste2 )

        if 'vegsegmenter' in mindf.columns: 
            mindf.drop( ['vegsegmenter'], axis=1, inplace=True)

        mindf['geometry'] = mindf['geometri'].apply( wkt.loads )
        minGdf = gpd.GeoDataFrame( mindf, geometry='geometry', crs=25833 )
        minGdf.to_file(filnavn, layer=lagnavn, driver="GPKG")  

        return minGdf
    else: 
        print( 'Ingen forekomster å skrive til lag', lagnavn, 'fil', filnavn)

    return None

def bevartBKverdier( gammelbk, nybk ): 
    """
    Sammenligner dictionary med nytt forslag BK-verdier med det gamle 

    Vil ignorere strekningsbeskrivelse og en del andre mindre viktige ting... 

    ARGUMENTS
        gammelbk, nybk : string eller dictionary på formen { "egenskapTypeId" : "verdi" }

    KEYWORDS
        None

    RETURNS 
        True eller False 
    """

    # 905 BK uoff 
    # [{10902: 'Bruksklasse'},
    # {10908: 'Bruksklasse vinter'},
    # {10914: 'Maks vogntoglengde'},
    # {10920: 'Strekningsbeskrivelse'}, IGNORER 
    # {10927: 'Maks totalvekt kjøretøy, skiltet'}, IGNORER
    # {10928: 'Maks totalvekt vogntog, skiltet'}, IGNORER 
    # {11010: 'Merknad'}]

    # Har vi fått tomme data? 
    if not gammelbk or not nybk: 
        return False 

    ignorer = [ 10920, 10927, 10928, # 905 BK normal, uoff
                10916, 10918 # Strekningsbeskrivelser 901 tømmer og 903 spesial 
                 ] 

    s_ignorer = set( ignorer )

    gmlKey = set( gammelbk.keys())  - s_ignorer
    nyKey  = set( nybk.keys())      - s_ignorer

    if gmlKey != nyKey: 
        return False 
    
    else: 
        for akey in gmlKey: 
            if gammelbk[akey] != nybk[akey]:
                return False 

    return True 




if __name__ == '__main__': 

    t0 = datetime.now( )
    vegkategori = 'F'
    vegobjekttype = 901
    # minefilter = { 'kartutsnitt' : '-30363,6634094,-30176,6634265', 'vegsystemreferanse' :  vegkategori + 'v'}   # Ev134 vestpå rundkjøring-eksempel for 904
    # minefilter = { 'kartutsnitt' : '185214.32,6617709.60,201184.26,6630023.57', 'vegsystemreferanse' :  vegkategori + 'v'}  # Vest for Kongsberg Ev134 eksempel for 905 id 779620154
    # minefilter = { 'kartutsnitt' : '413147.36,7302298.06,439536.80,7332742.31', 'vegsystemreferanse' :  vegkategori + 'v'}  # Nordland  905 id 1007822938
    minefilter = {  'vegsystemreferanse' :  vegkategori + 'v'}    

#    miljo = 'utvles'
    # miljo = 'testles'
    miljo = 'prodles'

    bk = nvdbapiv3.nvdbFagdata(vegobjekttype)
    bk.filter( minefilter )
    bk.add_request_arguments( { 'segmentering' : False } )

    if not 'prod' in miljo: 
        print( 'bruker miljø', miljo)
        bk.miljo(miljo)

    if vegobjekttype in [ 890, 892, 894, 901, 903, 905 ]: 
        print( "Må logge inn i miljø=", miljo)
        bk.forbindelse.login( )


    bk1 = bk.nesteForekomst()
    print( bk.sisteanrop )

    skalendres = [ ]
    endret = [ ]
    naboer = [ ]

    naboegenskaper = [ ]

    buffer = 10 
    
    seg1 = None
    while bk1: #  and bk1['id'] in ignorerliste(): 


        temp = deepcopy( bk1 )
        temp['vegsegmenter'] = []
        temp['geometri'] = None


        # Lagrer gamle egenskaper på objektet 
        eksisterende_egenskaper = registreringsegenskaper( temp['egenskaper']  )
        temp['egenskaper'].append({ 'id' : -10, 'navn' : 'gamle_egenskaper', 'verdi' : eksisterende_egenskaper }  ) 

        nabovegkat = set( )

        endres = False 

        for seg in bk1['vegsegmenter']: 

            if seg['vegsystemreferanse']['vegsystem']['vegkategori'] != vegkategori and not 'sluttdato' in seg.keys(): 
                trafikantgruppe = finntrafikantgruppe( seg )

                # Ignorerer gangstier 
                if  trafikantgruppe == 'K':

                    endres = True 


                    print( "Avviker fra vegkategori", vegkategori, seg['vegsystemreferanse']['kortform'], seg['vegsystemreferanse']['strekning']['trafikantgruppe'] )
                    minvegkat = seg['vegsystemreferanse']['vegsystem']['vegkategori'] + 'v' 
                    nabovegkat.add( minvegkat  )
                    if not minvegkat in temp.keys():
                        temp[minvegkat] = { 'id' : bk1['id'], 
                                            'href' : bk1['href'], 
                                            'metadata' : bk1['metadata'],
                                            'lokasjon' : bk1['lokasjon'],
                                            'vegsegmenter' : [], 
                                            'nye_vegreferanser' : [], 
                                            'nye_stedfestinger' : [],
                                            'egenskaper' : deepcopy( temp['egenskaper'] ), 
                                            'bbox' : None }

                    temp[minvegkat]['vegsegmenter'].append( deepcopy( seg ))

                    # Lager boundingbox 
                    geom = wkt.loads( seg['geometri']['wkt'])
                    temp[minvegkat]['bbox'] = joinbbox( temp[minvegkat]['bbox'], geom.bounds)

                    # Lagrer vegnettsdata 
                    temp[minvegkat]['nye_vegreferanser'].append( seg['vegsystemreferanse']['kortform'])
                    temp[minvegkat]['nye_stedfestinger'].append( str( seg['startposisjon'] ) + '-' + str( seg['sluttposisjon'] ) + \
                                                                '@' + str( seg['veglenkesekvensid'] )  )


        for kat in nabovegkat: 
            # Lager felles geometriobjekt for alle vegsegmentene 
            geom = unary_union( [ wkt.loads( seg['geometri']['wkt'] ) for seg in temp[kat]['vegsegmenter']   ] )
            temp[kat]['geometri']  = { 'wkt' : geom.wkt }
            temp[kat]['egenskaper'].append( { 'id' : -100, 'navn' : 'ny_lengde', 'verdi' : geom.length } ) 


            # Ny egenskapverdi for de nye vegreferansene 
            temp[kat]['egenskaper'].append( { 'id' : -50, 'navn' : 'nye_vegreferanser', 'verdi' : ','.join( temp[kat]['nye_vegreferanser']) }  ) 

            # Ny egenskapverdi for nye stedfestinger
            temp[kat]['egenskaper'].append( { 'id' : -60, 'navn' : 'nye_stedfestinger', 'verdi' : ','.join( temp[kat]['nye_stedfestinger']) }  ) 

            # Og kommunenummer 
            temp[kat]['egenskaper'].append( { 'id' : -100, 'navn' : 'kommune', 'verdi' : ','.join( [ str(komm) for komm in temp['lokasjon']['kommuner'] ] ) }  ) 


        if endres: 

            # Henter BK-objekt i nærheten med samme vegkategori
            nabosok = nvdbapiv3.nvdbFagdata( vegobjekttype)
            nabosok.forbindelse = bk.forbindelse 

            for kat in nabovegkat: 

                endres_egenskaper = None 
                endres_egenskaper_flertydig = [ ]                

                nabosok.filter( { 'kartutsnitt' : ','.join( [ str(x) for x in utvidbbox( temp[kat]['bbox'], buffer ) ]) } ) 
                tempnaboer = []

                nabosok.refresh()
                nabosok.filter( { 'vegsystemreferanse'  : kat } )

                enNabo = nabosok.nesteForekomst()

                # Finner ingenting? Prøver med utvidet BBOX
                if not enNabo: 
                    nabosok.filter( { 'kartutsnitt' : ','.join( [ str(x) for x in utvidbbox( temp[kat]['bbox'], 250 ) ] ) } ) 
                    nabosok.refresh()
                    enNabo = nabosok.nesteForekomst()

                while enNabo: 

                    # Vi vil finne vårt eget bk-objektet også, det er jo stedfestet på to vegkategorier 
                    # Og så er vi kun interessert i kjøreveger... 
                    trafikanter = set( [ finntrafikantgruppe( seg) for seg in enNabo['vegsegmenter'] if 'sluttdato' not in seg.keys() ] )
                    if enNabo['id'] != bk1['id'] and 'K' in trafikanter: 

                        # Har vi en og kun en unik kombinasjon av egenskaper fra naboene? 
                        egenskaper = registreringsegenskaper( enNabo['egenskaper']  )
                        if not endres_egenskaper: 
                            endres_egenskaper = egenskaper 
                        elif endres_egenskaper != egenskaper: 
                            endres_egenskaper_flertydig.append( egenskaper )

                        enNabo['egenskaper'].append({ 'id' : -6, 'navn' : 'gamle_egenskaper', 'verdi' : egenskaper }  ) 
                        tempnaboer.append( enNabo )

                    enNabo = nabosok.nesteForekomst( )


                # Sjekker om de livsviktige BK-verdiene er ensartet blant naboene vi sjekket 
                # (mens f.eks strekningsbeskrivelse kan avvike)
                bevart_viktige_egenskaper = bevartBKverdier(  eksisterende_egenskaper, endres_egenskaper)
                temp[kat]['egenskaper'].append( { 'id' : -8, 'navn' : 'bevart_viktige_egenskaper', 'verdi' : bevart_viktige_egenskaper  }  )


                # Sjekker om vi fikk ett og kun ett sett med BK-verdier fra naboene 
                unike_naboegenskaper = False 
                if not endres_egenskaper: # Fant ingen naboer å hente data fra
                    pass 

                # Fant IDENTISKE BK-verdier fra naboene 
                elif len( endres_egenskaper_flertydig ) == 0: 
                    temp[kat]['egenskaper'].append( { 'id' : -6, 'navn' : 'nye_egenskaper', 'verdi' : endres_egenskaper }  )
                    unike_naboegenskaper = True 
                # De VIKTIGSTE BK-verdiene er identiske 
                elif bevart_viktige_egenskaper: 
                    temp[kat]['egenskaper'].append( { 'id' : -6, 'navn' : 'nye_egenskaper', 'verdi' : endres_egenskaper }  )


                # Legger på tagg for om vi har entydige egnskaper fra naboene 
                temp[kat]['egenskaper'].append( { 'id' : -7, 'navn' : 'unike_naboegenskaper', 'verdi' : unike_naboegenskaper  }  )


                # Tagg for gjennomgang QGIS
                temp[kat]['egenskaper'].append( { 'id' : -8, 'navn' : 'skrivnvdb', 'verdi' : False  }  )

                naboer.extend( tempnaboer ) 

                skalendres.append( temp[kat] )
                endret.append( bk1 )

        bk1 = bk.nesteForekomst( )


    # Lagrer til geopackage
    filnavn = 'fiksebk' + str( vegobjekttype ) + '_' + miljo + '.gpkg' 
    # filnavn = 'fiksebk' + str( vegobjekttype ) + 'minidatasett.gpkg' 

    gdf_skalendres = liste2gpkg( skalendres, filnavn, 'skalendres', vegsegmenter=False ) 
    gdf_problemdata = liste2gpkg( endret, filnavn, 'problemdata') 
    gdf_naboer = liste2gpkg( naboer, filnavn, 'naboer') 

    tidsbruk = datetime.now( ) - t0 
    print( "tidsbruk:", tidsbruk.total_seconds( ), "sekunder")