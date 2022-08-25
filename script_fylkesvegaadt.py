import pandas as pd
import geopandas as gpd
from shapely import wkt

import STARTHER
import nvdbapiv3 
import nvdbgeotricks 

def lagintervall( aadtverdi, intervaller=[6000, 12000, 20000 ] ): 
    """
    Omsetter tallverdi for ÅDT til intervallverdi
    """

    intervaller = sorted( intervaller  ) 

    intervalltekst = 'Feiler!'

    if aadtverdi < intervaller[0]: 
        intervalltekst = '0 - ' + str( intervaller[0])
    elif aadtverdi >= intervaller[-1]: 
        intervalltekst = ' > ' + str( intervaller[-1])
    else: 
        for ix, dataverdi in enumerate( intervaller[:-1] ): 
            if aadtverdi >= dataverdi and aadtverdi < intervaller[ix+1]:
                intervalltekst = str( dataverdi ) + ' - ' + str( intervaller[ix+1] )

    return intervalltekst

def aadt_adskilte_lop( row ):

    if row['adskilte_lop'].lower() == 'med' and row['antKjorefelt'] >= 4: 
        return row['ÅDT, total'] * 2
    else: 
        return row['ÅDT, total']

def tellkjorefelt( row, feltkolonne='feltoversikt' ): 

    antFelt = len( nvdbgeotricks.filtrerfeltoversikt(  row[feltkolonne].split( ',') , mittfilter=['vanlig', 'F', 'R', 'K'] ) )
    if row['adskilte_lop'].lower() == 'med': 
        antFelt = antFelt * 2 

    if antFelt > 4: 
        antFelt = 4 

    if antFelt < 2: 
        antFelt = 2 

    return antFelt


if __name__ == '__main__': 

    filnavn = 'trafikkmengde.gpkg'
    sok = nvdbapiv3.nvdbFagdata(540 )
    sok.filter( { 'vegsystemreferanse' : 'Fv', 'egenskap' : '4623 >= 6000'})
    tmp = pd.DataFrame( sok.to_records())
    tmp['geometry'] = tmp['geometri'].apply( lambda x: wkt.loads( x ))
    traf = gpd.GeoDataFrame( tmp, geometry='geometry', crs=5973 )

    # traf['ÅDT, korrigert'] = traf.apply( lambda x : aadt_adskilte_lop( x ), axis=1 )
    traf['kategorisering'] = traf['ÅDT, total'].apply( lambda x : lagintervall( x, intervaller=[6000, 8000, 12000, 15000] ))

# 6-8000
# 8-12000
# 12 000-15000
# 15000+


    traf['vegnr'] = traf['vref'].apply( lambda x : x.split()[0])
    traf = traf[ traf['veglenkeType'] == 'HOVED']
    traf = traf[ traf['adskilte_lop'] != 'Mot']

    traf.to_file( filnavn, layer='trafikkmengde_raadata', driver='GPKG')

    # # Laster vegnett 
    # sok = nvdbapiv3.nvdbVegnett()
    # sok.filter( {'vegsystemreferanse' : 'Fv', 'veglenketype' : 'hoved'})
    # tmp = pd.DataFrame( sok.to_records())
    # tmp['geometry'] = tmp['geometri'].apply( lambda x : wkt.loads( x ))
    # veg = gpd.GeoDataFrame( tmp, geometry='geometry', crs=5973 )

    # col_veg = ['veglenkesekvensid', 'startposisjon', 'sluttposisjon',
    #     'type', 'typeVeg', 'feltoversikt',  'vref', 
    #    'medium',  'geometry']

    # col_traf = ['objekttype', 'nvdbId', 'versjon', 'År, gjelder for',
    #    'ÅDT, total', 'ÅDT, andel lange kjøretøy', 'Grunnlag for ÅDT',
    #    'veglenkesekvensid', 'detaljnivå', 'typeVeg', 'kommune', 'fylke',
    #    'vref', 'veglenkeType', 
    #    'startposisjon', 'sluttposisjon',  'adskilte_lop',
    #     'geometry', 'kategorisering', 'vegnr',
    #    ]

    # joined = nvdbgeotricks.finnoverlapp( traf[col_traf], veg[col_veg], klippgeometri=True, prefixB='veg_' )
    # joined['antKjorefelt'] = joined.apply( lambda x : tellkjorefelt( x, feltkolonne='veg_feltoversikt'), axis=1 )

    # joined['ÅDT, korrigert'] = joined.apply( lambda x : aadt_adskilte_lop( x ), axis=1 )
    # joined['kategorisering'] = joined['ÅDT, korrigert'].apply( lambda x : lagintervall( x ))

    # joined.to_file( filnavn, layer='trafikkmengde_feltinfo', driver='GPKG')