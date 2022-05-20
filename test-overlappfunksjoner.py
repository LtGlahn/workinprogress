"""
Tester nye, kule overlappfunksjoner med geometriredigering på Corinne sin problemstilling: 

Finne overlapp mellom objekttypene 66 skredoverbygg, 67 tunnellø og 60 bru
"""

from datetime import datetime

import pandas as pd 
import geopandas as gpd 
from shapely import wkt 

import STARTHER 
import nvdbapiv3 
import nvdbgeotricks

if __name__ == '__main__':
    t0 = datetime.now()

    filnavn = 'test-overlapp.gpkg'
    
    # Tunnelløp 
    sok = nvdbapiv3.nvdbFagdata( 67 )
    tmp = pd.DataFrame( sok.to_records())
    tmp['geometry'] = tmp['geometri'].apply( lambda x : wkt.loads( x ))
    tun = gpd.GeoDataFrame( tmp, geometry='geometry', crs=5973)
    tun.to_file( filnavn, layer='tunnellop', driver='GPKG')

    # Skredoverbygg
    sok = nvdbapiv3.nvdbFagdata( 66 )
    tmp = pd.DataFrame( sok.to_records())
    tmp['geometry'] = tmp['geometri'].apply( lambda x : wkt.loads( x ))
    skred = gpd.GeoDataFrame( tmp, geometry='geometry', crs=5973)
    skred.to_file( filnavn, layer='skredoverbygg', driver='GPKG')

    # Bru-objekter
    sok = nvdbapiv3.nvdbFagdata( 60 )
    tmp = pd.DataFrame( sok.to_records())
    tmp['geometry'] = tmp['geometri'].apply( lambda x : wkt.loads( x ))
    bru = gpd.GeoDataFrame( tmp, geometry='geometry', crs=5973)
    bru.to_file( filnavn, layer='bru', driver='GPKG')

    tun_bru = nvdbgeotricks.finnoverlapp( tun, bru, klippgeometri=True )
    tun_bru.to_file( filnavn, layer='tunnel_bru', driver='GPKG')

    tun_skred = nvdbgeotricks.finnoverlapp( tun, skred, klippgeometri=True )
    tun_skred.to_file( filnavn, layer='tunnel_skredoverbygg', driver='GPKG')

    bru_skred = nvdbgeotricks.finnoverlapp( bru, skred, klippgeometri=True )
    bru_skred.to_file( filnavn, layer='bru_skredoverbygg', driver='GPKG')

    print( f"Tidsbruk: {datetime.now() - t0}" )

    # Dumper til excel, fordi de ter mer brukervennlig for Corinne 
    col_tun_bru = [ 'objekttype', 'nvdbId', 'versjon', 'Navn', 'kommune', 'fylke', 'vegsystemreferanse', 'segmentlengde', 't60_nvdbId',
                    't60_versjon', 't60_Navn', 't60_Brukategori', 't60_Status', 't60_Byggverkstype', 't60_Brutusnummer',
                    't60_Eier', 't60_Byggeår', 'veglenkesekvensid', 'startposisjon', 'sluttposisjon', 
                    'trafikantgruppe', 'vegkategori', 'fase', 'vegnummer' ]


    col_tun_skred = [ 'objekttype', 'nvdbId', 'versjon', 'Navn', 'Kategori', 'kommune', 'fylke', 'vegsystemreferanse', 
                    'segmentlengde', 't66_objekttype', 't66_nvdbId', 't66_versjon', 't66_Navn', 't66_Brutus_Id', 'vegkategori', 
                    'fase', 'vegnummer', 'veglenkesekvensid', 'startposisjon', 'sluttposisjon', 'adskilte_lop', 'trafikantgruppe' ]

    col_bru_skred = [ 'objekttype', 'nvdbId', 'versjon', 'Navn', 'Brukategori', 'Status', 'Opprinnelig Brutus F-Nr', 
                        'Brutusnummer', 'kommune', 'fylke', 'vegsystemreferanse', 'segmentlengde', 't66_objekttype', 
                        't66_nvdbId', 't66_versjon', 't66_Navn', 't66_Brutus_Id', 't66_Type', 't66_Tunnelnummer', 
                        'vegkategori', 'fase', 'vegnummer', 'veglenkesekvensid', 'startposisjon', 'sluttposisjon', 'trafikantgruppe' ]

    excelDfliste = [ tun_bru[col_tun_bru], tun_skred[col_tun_skred], bru_skred[col_bru_skred] ]

    nvdbgeotricks.skrivexcel( 'Bruoverlapp.xlsx', excelDfliste, sheet_nameListe=[ 'Tunnel og Bruobjekt', 'Tunnel og skredoverbygg', 
                                                            'Bruobjekt og skredoverbygg'   ]  )