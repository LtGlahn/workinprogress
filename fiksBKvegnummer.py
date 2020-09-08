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

    debug = False 

    mydebugdata = [ ]

    t0 = datetime.now( )
    vegkategori = 'F'
    vegobjekttype = 904
    minefilter = { 'kartutsnitt' : '-30363,6634094,-30176,6634265' }    # Ev134 rundkjøring + fylkesveg eks 
    minefilter = { 'kartutsnitt' : '321968.88,7114459.05,322351.37,7114804.69' } # Gammel Fv17 - problem N.Trøndelag Malm / Hellbotn-vannet
    minefilter = { 'kartutsnitt' : '316702.63,7107593.89,343391.78, 7137836.55' } # Større BBox rundt Malm/Hellbotn-vannet
    minefilter = { 'fylke' : 50 } 

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

    beholdes = []
    endres = [ ]
    
    seg1 = None
    count = 0 
    if bk1: 
        count +=1

    while bk1: 
        count += 1 

        data = {    'nvdbid'     : deepcopy( bk1['id'] ), 
                    'href'       : deepcopy( bk1['href'] ), 
                    'egenskaper' : deepcopy( bk1['egenskaper'] ), 
                    'metadata'   : deepcopy( bk1['metadata'] ),
                    'vegnr' : {  } }


        # Nedfeller eksisterende egenskaper i dictionary
        # Dette skriver vi direkte til skriveapi 
        data['egenskaper'].append( {    'id' : -10, 
                                        'navn' : 'skrivegenskaper', 
                                        'verdi' : fiksBK_feilvegkat.registreringsegenskaper( bk1['egenskaper'] ) 
                                    }  )

        mal_segmentdata =  {    'id' : bk1['id'], 
                                'href' : bk1['href'], 
                                'metadata' : bk1['metadata'],
                                'lokasjon' : bk1['lokasjon'],
                                'geometri' : { 'wkt' : ''}, 
                                'lengde' :  0,                                
                                'vegsegmenter' : [], 
                                'nye_vegreferanser' : [], 
                                'nye_stedfestinger' : [],
                                'egenskaper' : deepcopy( data['egenskaper'] )
                            }

        for seg in bk1['vegsegmenter']: 

            if not 'sluttdato' in seg.keys(): 

                trafikantgruppe = fiksBK_feilvegkat.finntrafikantgruppe( seg )
                vegkat = seg['vegsystemreferanse']['kortform'][0]
                admgrenser = '_fylke' + str( seg['fylke'] ).zfill( 2)
                if vegkat in ['K', 'P', 'S']: 
                    admgrenser = '_kommune' + str( seg['kommune'] ).zfill( 4)

                vegnrKey = seg['vegsystemreferanse']['kortform'].split()[0] + '-' + trafikantgruppe + admgrenser

                if not vegnrKey in data['vegnr'].keys(): 

                    data['vegnr'][vegnrKey] = deepcopy( mal_segmentdata )
                    data['vegnr'][vegnrKey]['egenskaper'].append({ 'id' : -99, 
                                                                    'navn' : 'vegnrKey', 
                                                                    'verdi' : vegnrKey 
                                                                 })

                # Leggger vegnr-segment der det hører hjemme 
                data['vegnr'][vegnrKey]['vegsegmenter'].append( seg )
                data['vegnr'][vegnrKey]['lengde'] += seg['lengde']

        # Har vi flere enn en "vegnrKey?" => Objektet skal splittes
        # Vi finner den lengste biten (beholdes!) og overskriver de andre. 
        vegnrKeys = data['vegnr'].keys()
        if len( vegnrKeys) <= 1: 
            if debug:
                print( "Trenger ikke endre", vegnrKey, data['nvdbid'])
        else: 

            # Konstruerer felles geometri og øvrige egenskaper for hver vegnrKey - samling av segmenter
            for vegnrKey in vegnrKeys: 
                geoms = [ wkt.loads( seg['geometri']['wkt'] ) for seg in data['vegnr'][vegnrKey]['vegsegmenter']  ]
                nygeom = unary_union( geoms )
                data['vegnr'][vegnrKey]['geometri']['wkt'] = nygeom.wkt

                # Oppsummerer nye vegreferanser 
                data['vegnr'][vegnrKey]['egenskaper'].append(  
                    { 'id' : -60, 
                        'navn' : 'nye_vegreferanser', 
                        'verdi' : ','.join( [ seg['vegsystemreferanse']['kortform'] for seg in data['vegnr'][vegnrKey]['vegsegmenter']  ]  ) 
                        }  )

                # Oppsummerer opprinnelig vegnr 
                gmlvegnr = list( set( [ v['kortform'].split()[0] for v in data['vegnr'][vegnrKey]['lokasjon']['vegsystemreferanser']  ]  ))
                data['vegnr'][vegnrKey]['egenskaper'].append( { 'id' : -3, 'navn' : 'Opprinnelig vegnr', 'verdi' : ','.join( gmlvegnr ) } )

                # Kommune
                kommune = list( set(  [ str( seg['kommune'] ) for seg in data['vegnr'][vegnrKey]['vegsegmenter']  ] ))
                data['vegnr'][vegnrKey]['egenskaper'].append( { 'id' : -45, 
                                                                'navn' : 'kommune', 
                                                                'verdi' : ','.join( kommune )
                                                                } )

                # fylke
                fylke = list( set( [ str( seg['fylke'] ) for seg in data['vegnr'][vegnrKey]['vegsegmenter']  ]  ))
                data['vegnr'][vegnrKey]['egenskaper'].append(     { 'id' : -46, 
                                                                    'navn' : 'fylke', 
                                                                    'verdi' : ','.join(  fylke )
                                                                    }  )


                # Oppsummerer ny stedfesting 
                fra = 'startposisjon'
                til = 'sluttposisjon'
                vid = 'veglenkesekvensid'
                data['vegnr'][vegnrKey]['egenskaper'].append(  
                    { 'id' : -60, 
                        'navn' : 'nye_stedfestinger', 
                        'verdi' : ','.join( [ str( seg[fra]) + '-' + str( seg[til]) + '@' + str( seg[vid] )  for seg in data['vegnr'][vegnrKey]['vegsegmenter']  ]  ) 
                        }  )

                # Manipulerer lengde: 
                data['vegnr'][vegnrKey]['egenskaper'].append( { 'id' : -999, 'navn' : 'Opprinnelig lengde', 'verdi' : data['vegnr'][vegnrKey]['lokasjon']['lengde'] } )
                data['vegnr'][vegnrKey]['lokasjon']['lengde'] = data['vegnr'][vegnrKey]['lengde']

            # Finner lengste gruppe av segmenter 
            lengsteKey = ''
            makslengde = 0 
            for vegnrKey in vegnrKeys: 

                if data['vegnr'][vegnrKey]['lengde'] > makslengde: 
                    lengsteKey = deepcopy( vegnrKey )
                    makslengde = data['vegnr'][vegnrKey]['lengde']

                if debug: 
                    print( vegnrKey, "lengde:", data['vegnr'][vegnrKey]['lengde'])

            # Alle utenom det lengste segmentet skal overskrives 
            for vegnrKey in vegnrKeys: 
                if vegnrKey == lengsteKey: 
                    beholdes.append( data['vegnr'][vegnrKey]  )
                else: 
                    endres.append( data['vegnr'][vegnrKey]  )

        bk1 = bk.nesteForekomst( )

    # Lagrer til geopackage
    filnavn = 'splittBkTrlang' + str( vegobjekttype ) + '_' + miljo + '.gpkg' 
    # filnavn = 'splittBkfiksdill2' + str( vegobjekttype ) + '_' + miljo + '.gpkg' 
    # filnavn = 'splittBk' + str( vegobjekttype ) + 'minidatasett.gpkg' 

    gdf_skalendres = fiksBK_feilvegkat.liste2gpkg( endres, filnavn, 'skalendres', vegsegmenter=False) 
    gdf_uendret    = fiksBK_feilvegkat.liste2gpkg( beholdes, filnavn, 'beholdes', vegsegmenter=False) 

    tidsbruk = datetime.now( ) - t0 
    print( "tidsbruk:", tidsbruk.total_seconds( ), "sekunder")
    print( "Løp gjennom", count, "objekter totalt. Av disse skal", len( beholdes), 'objekt få', len( endres), 'nye strekninger')