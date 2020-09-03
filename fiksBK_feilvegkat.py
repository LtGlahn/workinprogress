import STARTHER
import nvdbapiv3
from copy import deepcopy 

from shapely import wkt 
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

def liste2gpkg( minliste, filnavn, lagnavn):
    """
    Lagrer liste med NVDB-fagdata til geopackage
    ARGUMENTS: 
        minliste - liste med NVDB-objekt
        
        filnavn - navn på .gpkg-fil vi skal skrive til
        lagnavn - navn på tabellen vi skal lagre 
    KEYWORDS: 
        Nada 
    RETURNS: 
        Nada
    """

    liste2 = nvdbapiv3.nvdbfagdata2records( minliste )
    if len( liste2 ) > 0: 
        mindf = pd.DataFrame( liste2 )
        mindf['geometry'] = mindf['geometri'].apply( wkt.loads )
        minGdf = gpd.GeoDataFrame( mindf, geometry='geometry', crs=25833 )
        minGdf.to_file(filnavn, layer=lagnavn, driver="GPKG")  

        return minGdf
    else: 
        print( 'Ingen forekomster å skrive til lag', lagnavn, 'fil', filnavn)

    return None

if __name__ == '__main__': 

    t0 = datetime.now( )
    vegkategori = 'F'
    vegobjekttype = 905
    minefilter = { 'kartutsnitt' : '-30363,6634094,-30176,6634265', 'vegsystemreferanse' :  vegkategori + 'v'}    
    # minefilter = {  'vegsystemreferanse' :  vegkategori + 'v'}    

#    miljo = 'utvles'
    miljo = 'testles'
    # miljo = 'prodles'

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

    skalendres = [ ]
    endret = [ ]
    naboer = [ ]

    naboegenskaper = [ ]

    buffer = 10 
    
    seg1 = None
    while bk1: 

        temp = deepcopy( bk1 )
        temp['vegsegmenter'] = []
        temp['geometri'] = None
        temp['stedfestinger'] = None
        temp['lokasjon'] = None
        nabovegkat = set( )

        endres = False 
        bbox = None 
        endres_egenskaper = None 
        endres_egenskaper_flertydig = [ ]

        for seg in bk1['vegsegmenter']: 
            if seg['vegsystemreferanse']['vegsystem']['vegkategori'] != vegkategori and not 'sluttdato' in seg.keys(): 

                print( "Avviker fra vegkategori", vegkategori, seg['vegsystemreferanse']['kortform'], seg['vegsystemreferanse']['strekning']['trafikantgruppe'] )
                nabovegkat.add( seg['vegsystemreferanse']['vegsystem']['vegkategori'] + 'v'  )
                temp['vegsegmenter'].append( deepcopy( seg ))
                endres = True 

                # Lager boundingbox 
                geom = wkt.loads( seg['geometri']['wkt'])
                bbox = joinbbox( bbox, geom.bounds)

                seg1 = deepcopy( seg ) 

        if endres: 
            
            # Henter BK-objekt i nærheten med samme vegkategori
            nabosok = nvdbapiv3.nvdbFagdata( vegobjekttype)
            nabosok.forbindelse = bk.forbindelse 

            nabosok.filter( { 'kartutsnitt' : ','.join( [ str(x) for x in utvidbbox( bbox, buffer ) ]) } ) 
            tempnaboer = []
            for kat in nabovegkat: 
                nabosok.refresh()
                nabosok.filter( { 'vegsystemreferanse'  : kat } )

                enNabo = nabosok.nesteForekomst( )

                # Har vi en og kun en unik kombinasjon av egenskaper fra naboene? 
                egenskaper = registreringsegenskaper( enNabo['egenskaper']  )
                if not endres_egenskaper: 
                    endres_egenskaper = egenskaper 
                elif endres_egenskaper != egenskaper: 
                    endres_egenskaper_flertydig.append( egenskaper )

                while enNabo: 

                    if enNabo['id'] != bk1['id']: 
                        junk = deepcopy( enNabo )
                        junk['geometri'] = None
                        junk['lokasjon'] = None 
                        tempnaboer.append( enNabo )

                    enNabo = nabosok.nesteForekomst( )

            if len( endres_egenskaper_flertydig ) == 0: 
                temp['egenskaper'].append( { 'id' : -6, 'navn' : 'nye_egenskaper', 'verdi' : endres_egenskaper }  )
                temp['egenskaper'].append( { 'id' : -7, 'navn' : 'unike_naboegenskaper', 'verdi' : True }  )

            else: 
                endres_egenskaper_flertydig.append( endres_egenskaper)
                # temp['egenskaper'].append( { 'id' : -6, 'navn' : 'nye_egenskaper', 'verdi' : endres_egenskaper_flertydig }  )
                temp['egenskaper'].append( { 'id' : -7, 'navn' : 'unike_naboegenskaper', 'verdi' : False  }  )
            
            naboer.extend( tempnaboer ) 

            skalendres.append( temp )
            endret.append( bk1 )

        bk1 = bk.nesteForekomst( )


    # Lagrer til geopackage
    filnavn = 'fiksebk' + str( vegobjekttype ) + '_' + 'miljo .gpkg' 

    gdf_skalendres = liste2gpkg( skalendres, filnavn, 'skalendres') 
    gdf_problemdata = liste2gpkg( endret, filnavn, 'problemdata') 
    gdf_naboer = liste2gpkg( naboer, filnavn, 'naboer') 

    tidsbruk = datetime.now( ) - t0 
    print( "tidsbruk:", tidsbruk.total_seconds( ), "sekunder")