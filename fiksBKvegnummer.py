from copy import deepcopy 
import pdb 

from shapely import wkt 
from shapely.ops import unary_union
import pandas as pd 
import geopandas as gpd 
from datetime import datetime

import STARTHER
import nvdbapiv3
import fiksBK_feilvegkat


if __name__ == '__main__': 

    t0 = datetime.now( )
    vegkategori = 'F'
    vegobjekttype = 904
    minefilter = { 'kartutsnitt' : '-30363,6634094,-30176,6634265' }    
    # minefilter = {  'vegsystemreferanse' :  vegkategori + 'v'}    

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

    alledata = []
    endres = [ ]
    
    seg1 = None
    while bk1: 

        # temp = deepcopy( bk1 )
        # temp['vegsegmenter'] = []
        # temp['geometri'] = None
        # temp['stedfestinger'] = None
        # temp['lokasjon'] = None

        data = {    'nvdbid'     : deepcopy( bk1['id'] ), 
                    'href'       : deepcopy( bk1['href'] ), 
                    'egenskaper' : deepcopy( bk1['egenskaper'] ), 
                    'metadata'   : deepcopy( bk1['metadata'] ),
                    'vegnr' : {  } }


        for seg in bk1['vegsegmenter']: 
            if not 'sluttdato' in seg.keys(): 

                trafikantgruppe = fiksBK_feilvegkat.finntrafikantgruppe( seg )

                vegnrKey = seg['vegsystemreferanse']['kortform'].split()[0] + '-' + trafikantgruppe


                if not vegnrKey in data['vegnr'].keys(): 

                    data['vegnr'][vegnrKey] = {   'geometri' : '', 
                                                    'lengde' :  0,
                                                    'vegsegmenter' : [ seg  ]
                    }

                else: 

                    data['vegnr'][vegnrKey]['vegsegmenter'].append( seg )

                    #   gmlgeom = wkt.loads( data['vegnr'][vegnrKey]['geometri'] )


                # Kode for å manipulere geometri 
                # geoms = [ wkt.loads( seg['geometri']['wkt'] ) for seg in data['vegnr']['EV134-K']['vegsegmenter']  ]
                # geom = wkt.loads( seg['geometri']['wkt'] )
                # nygeom = unary_union( geoms )


        alledata.append( data )
        if len( data['vegnr'].keys( )) > 1:

            for 
            endres.append( data ) 
            

        #     skalendres.append( temp )
        #     endret.append( bk1 )

        bk1 = bk.nesteForekomst( )


    # Lagrer til geopackage
    filnavn = 'fiksebkVegnr' + str( vegobjekttype ) + '_' + miljo + '.gpkg' 
    # filnavn = 'fiksebk' + str( vegobjekttype ) + 'minidatasett.gpkg' 

    # gdf_skalendres = liste2gpkg( skalendres, filnavn, 'skalendres') 
    # gdf_problemdata = liste2gpkg( endret, filnavn, 'problemdata') 
    # gdf_naboer = liste2gpkg( naboer, filnavn, 'naboer') 

    tidsbruk = datetime.now( ) - t0 
    print( "tidsbruk:", tidsbruk.total_seconds( ), "sekunder")