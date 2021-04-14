import pandas as pd
import geopandas as gpd
import numpy as np 

import STARTHER
import nvdbapiv3
import spesialrapporter

def finnBKfeil( brutusBK, nvdbBk ): 
    """
    Sammenligner bruksklasse fra Brutus med bruksklasse fra NVDB og returnerer tekststreng 
    """

    tempBrutusBk = spesialrapporter.splitBruksklasse_vekt( brutusBK )
    tempNvdbBK   = spesialrapporter.splitBruksklasse_vekt( nvdbBk )

    result = 'FEIK'
    if np.isnan( tempBrutusBk[0]) or np.isnan( tempBrutusBk[1] ) or np.isnan( tempNvdbBK[0]) or np.isnan( tempNvdbBK[1]):
        result = 'Ugyldige data'
    elif tempBrutusBk[0] < tempNvdbBK[0] or tempBrutusBk[1] < tempNvdbBK[1]:
        result = 'ALARM: Brutus BK < NVDB'
    else: 
        result = 'OK: Brutus BK >= NVDB'

    return result 

if __name__ == '__main__': 

    # Leser inn og bearbeider regneark 
    # exceldump = pd.read_excel( 'Copy of 10032021_BRUKSLAST_Jan Kristian.xlsx', sheet_name='Grunnlag', header=6 )
    exceldump = pd.read_excel( '26032021_BRUKSLAST_Jan Kristian.xlsx', sheet_name='Ark1', header=6 )


    exceldump = exceldump[exceldump['BRUSTATUS'] == 'TR']
    exceldump = exceldump[exceldump['TRAFIKANTGRUPPE'] == 'K']
    exceldump = exceldump[exceldump['ER HOVEDVEGREFERANSE'] == 'J'] # Denne hadde vi ikke før! 
    exceldump = exceldump[exceldump['BELIGGENHET'] == 'P'].copy()

    # Rensker vekk dem uten NVDB id 
    exceldump = exceldump[ exceldump['NVDB_ID'].notnull() ]

    # Korrigerer den ene datafeilen vi fant: 
    junk = exceldump.copy()
    exceldump.at[ exceldump[ exceldump['BRUNAVN'] == 'Eikornrød'].index[0], 'NVDB_ID' ] = 272298201
    exceldump = exceldump[ exceldump['NVDB_ID' ] != 272396176 ] 

    exceldump.reset_index()

    ## Føyer på tallverdier for BK og vekt 
    ## OVERFLØDIG - vi angir dummyvariabel  
    # exceldump['brutus_bktall'] = exceldump['BRUKSLAST'].apply( lambda x : spesialrapporter.splitBruksklasse_vekt( x )[0] )  
    # exceldump['brutus_bkvekt'] = exceldump['BRUKSLAST'].apply( lambda x : spesialrapporter.splitBruksklasse_vekt( x )[1] )  

    # bru = spesialrapporter.brutusBKoverlapp( offisiell=True, mittfilter={'vegsystemreferanse' : 'Ev134'} )

    bru = spesialrapporter.brutusBKoverlapp( offisiell=False, kunEnTypeBK='normal' )
    bru.drop( columns=[ 'bru_objekttype', 'bru_versjon', 'bru_startdato',], inplace=True )
    bru.to_file( 'bruer.gpkg', layer='bruer_plussBKnormal', driver='GPKG')

    # bru = gpd.read_file( 'bruer.gpkg', layer='allebruer' )

    bru.rename( columns={'bru_nvdbId' : 'NVDB_ID'}, inplace=True  )
    merg = pd.merge( bru, exceldump, on='NVDB_ID' )

    merg = gpd.geodataframe.GeoDataFrame( merg, geometry='geometry',  crs=5973 ) 

    # Rensker vekk de vegsegmentene som ikke matcher på vegnummer
    # merg['bru_vegnr'] = merg['bru_vref'].apply( lambda x : x.split()[0] )
    # merg['BRUTUS_VEGNUMMER'] = merg['VEGREFERANSE'].apply( lambda x : x.split()[0] )
    merg['bru_vegnr'] = merg['bru_vref'].apply( lambda x : ' '.join( x.split()[0:2] ))
    merg['BRUTUS_VEGNUMMER'] = merg['VEGREFERANSE'].apply( lambda x : ' '.join( x.split()[0:2] )  )
    merg = merg[ merg['BRUTUS_VEGNUMMER'] == merg['bru_vegnr'] ].copy()

    # Har noen datatyper her som geopackage-formatet ikke takler
    hh = list( merg.select_dtypes([np.datetime64] ).columns )
    for jj in hh: 
        merg[jj] = merg[jj].astype(str)
    merg['KLASSIFISERT DATO'] = merg['KLASSIFISERT DATO'].astype(str)

    bruid = set( list( bru['NVDB_ID'].unique() ))
    exceldbid = set( list( exceldump['NVDB_ID'].unique() ))
    mergid = set( list( merg['NVDB_ID'].unique() ))    

    merg['BKvalidering'] = merg.apply( lambda x : finnBKfeil( x['BRUKSLAST'], x['bk905_Bruksklasse']), axis=1)

    # Fjerner brukategorier som er uviktige
    # Vegbru                  12634 <= TA MED
    # Bru i fylling            5541 <= TA MED
    # Ferjeleie                 394 <= TA MED
    # Tunnel/Vegoverbygg        243
    # G/S-bru                    64
    # Støttekonstruksjon         59
    # Annen byggv.kategori       27
    # Jernbanebru                16

    # merg = merg[  merg['BRUKATEGORI'] != 'Bru i fylling']
    merg = merg[  merg['BRUKATEGORI'] != 'Tunnel/Vegoverbygg']
    merg = merg[  merg['BRUKATEGORI'] != 'G/S-bru']
    merg = merg[  merg['BRUKATEGORI'] != 'Støttekonstruksjon']
    merg = merg[  merg['BRUKATEGORI'] != 'Annen byggv.kategori']
    merg = merg[  merg['BRUKATEGORI'] != 'Jernbanebru']


    gale = merg[ merg['BKvalidering'].str.contains('ALARM')  ]

    gale.to_file( 'bruer.gpkg', layer='avvik_bk_bru', driver='GPKG' )
    merg.to_file( 'bruer.gpkg', layer='blanding_bruer_BK', driver='GPKG' )

    # bru.drop( columns=[ 'bru_objekttype', 'bru_versjon', 'bru_startdato',], inplace=True )

    # Bru-kolonner: 
    # bcols   = [ 'bru_nvdbId', 
    #             'bru_Lengde', 'bru_Veggruppe', 'bru_Vedlikeholdsansvarlig',
    #             'bru_Opprinnelig F-Nr', 'bru_Brukategori', 'bru_Lengste spenn',
    #             'bru_Status', 'bru_Navn', 'bru_Materialtype', 'bru_Byggverkstype',
    #             'bru_Nummer', 'bru_veglenkesekvensid', 'bru_detaljnivå', 'bru_typeVeg',
    #             'bru_kommune', 'bru_fylke', 'bru_vref', 'bru_veglenkeType',
    #             'bru_vegkategori', 'bru_fase', 'bru_vegnummer', 'bru_startposisjon',
    #             'bru_sluttposisjon', 'bru_segmentlengde', 'bru_adskilte_lop',
    #             'bru_trafikantgruppe', 'bru_geometri', 'bru_Sv 12/100 Plassering',
    #             'bru_Sv 12/100 Merknad', 'bru_Sv 12/100 Avstand', 'bru_Byggeår',
    #             'bk905_Maks vogntoglengde', 
    #             'bk905_Bruksklasse', 
    #             'bk905_Merknad',
    #             'bk905_Maks totalvekt kjøretøy, skiltet',
    #             'bk905_Maks totalvekt vogntog, skiltet', 'bk905_bktall', 'bk905_bkvekt',
    #             'bk903_Maks vogntoglengde', 'bk903_Bruksklasse', 'bk903_Veggruppe',
    #             'bk903_Merknad', 'geometry']

    # duplikatliste = ['bru_nvdbId', 'bk905_Maks vogntoglengde', 'bk905_Bruksklasse', 'bk905_Merknad', 'bk905_bktall', 'bk905_bkvekt', 'bk903_Maks vogntoglengde', 'bk903_Bruksklasse', 'bk903_Veggruppe', 'bk903_Merknad']

    # aggfunksjoner = { 'bru_vref'                    : lambda x : ','.join( list( set( list( x )))), 
    #                  'bk905_Maks vogntoglengde'     : lambda x : ','.join( list( set( list( x )))), 
    #                  'bk905_Bruksklasse'            : lambda x : ','.join( list( set( list( x )))), 
    #                  'bk905_Merknad'                : lambda x : ','.join( list( set( list( x )))), 
    #                  'bk905_bktall'                 : lambda x : ','.join( list( set( list( x )))), 
    #                  'bk905_bkvekt'                 : lambda x : ','.join( list( set( list( x )))), 
    #                  'bk903_Maks vogntoglengde'     : lambda x : ','.join( list( set( list( x )))), 
    #                  'bk903_Bruksklasse'            : lambda x : ','.join( list( set( list( x )))), 
    #                  'bk903_Veggruppe'              : lambda x : ','.join( list( set( list( x )))), 
    #                  'bk903_Merknad'                : lambda x : ','.join( list( set( list( x )))) }

