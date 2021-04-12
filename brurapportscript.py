import pandas as pd
import geopandas 
import numpy as np 

import STARTHER
import nvdbapiv3
import spesialrapporter

if __name__ == '__main__': 

    # Leser inn og bearbeider regneark 
    # exceldump = pd.read_excel( 'Copy of 10032021_BRUKSLAST_Jan Kristian.xlsx', sheet_name='Grunnlag', header=6 )
    exceldump = pd.read_excel( '2060302_BRUKSLAST_Jan Kristian.xlsx', sheet_name='Ark 1', header=7 )
    exceldump = exceldump[exceldump['BRUSTATUS'] == 'TR']
    exceldump = exceldump[exceldump['TRAFIKANTGRUPPE'] == 'K']
    exceldump = exceldump[exceldump['BELIGGENHET'] == 'P'].copy()

    # Rensker vekk dem uten NVDB id 
    exceldump = exceldump[ exceldump['NVDB_ID'].notnull() ]

    # Korrigerer den ene datafeilen vi fant: 
    junk = exceldump.copy()
    exceldump.at[ exceldump[ exceldump['BRUNAVN'] == 'Eikornrød'].index[0], 'NVDB_ID' ] = 272298201
    exceldump = exceldump[ exceldump['NVDB_ID' ] != 272396176 ] 


    exceldump.reset_index()

    # Føyer på tallverdier for BK og vekt
    exceldump['brutus_bktall'] = exceldump['BRUKSLAST'].apply( lambda x : spesialrapporter.splitBruksklasse_vekt( x )[0] )  
    exceldump['brutus_bkvekt'] = exceldump['BRUKSLAST'].apply( lambda x : spesialrapporter.splitBruksklasse_vekt( x )[1] )  

    # bru = spesialrapporter.brutusBKoverlapp( offisiell=True, mittfilter={'vegsystemreferanse' : 'Ev134'} )

    bru = spesialrapporter.brutusBKoverlapp( offisiell=False )
    bru.to_file( 'bruer.gpkg', layer='allebruer', driver='GPKG')

    # bru = gpd.read_file( 'bruer.gpkg', layer='allebruer' )

    # Korrigerer den ene datafeilen vi fant: 
    bru = bru[ bru['bru_nvdbId' ] != 272396176 ] 

    bru.rename( columns={'bru_nvdbId' : 'NVDB_ID'}, inplace=True  )
    merg = pd.merge( bru, exceldump, on='NVDB_ID' )

    merg = gpd.geodataframe.GeoDataFrame( merg, geometry='geometry',  crs=5973 ) 

    # 
    hh = list( merg.select_dtypes([np.datetime64] ).columns )
    for jj in hh: 
        merg[jj] = merg[jj].astype(str)
    merg['KLASSIFISERT DATO'] = merg['KLASSIFISERT DATO'].astype(str)


    bruid = set( list( bru['NVDB_ID'].unique() ))
    exceldbid = set( list( exceldump['NVDB_ID'].unique() ))
    mergid = set( list( merg['NVDB_ID'].unique() ))    


    gale = merg[ (merg['brutus_bkvekt'] < merg['bk905_bkvekt']) | (merg['brutus_bkvekt'] < merg['bk905_bkvekt']) ]

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

