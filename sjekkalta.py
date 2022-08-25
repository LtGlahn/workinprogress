from json.encoder import JSONEncoder
import pdb
import json
from numpy.lib import index_tricks

import pandas as pd
import geopandas as gpd
from shapely import wkt, wkb
from shapely import geometry 
from shapely.geometry import LineString 

import lokal_STARTHER
import nvdbapiv3
import nvdbgeotricks 


if __name__ == '__main__': 

    # mittfilter = {'vegsystemreferanse' : 'Ev6', 'kommune' : 5403 }
    mittfilter = {'vegsystemreferanse' : 'Ev6' }
    skiltsok = nvdbapiv3.nvdbFagdata( 95 )
    skiltsok.filter( mittfilter )

    tunnelsok = nvdbapiv3.nvdbFagdata( 67 )
    # tunnelsok.filter( mittfilter )

    skilt  = pd.DataFrame(  skiltsok.to_records(  vegsegmenter=True ) )
    tunnel = pd.DataFrame( tunnelsok.to_records(  vegsegmenter=True ) )

    skilt.drop( columns='relasjoner', inplace=True )
    tunnel.drop( columns='relasjoner', inplace=True )

    skiltsok2 = nvdbapiv3.nvdbFagdata( 95 )
    # skiltsok2.filter( mittfilter )
    skiltsok2.filter( { 'overlapp' : '67' })
    skilt2 = pd.DataFrame( skiltsok2.to_records( vegsegmenter=True ) ) 
    if 'relasjoner' in skilt2.columns:
        skilt2.drop( columns='relasjoner', inplace=True )

    overlapp = nvdbgeotricks.finnoverlapp( tunnel, skilt  )

    # minGdf.to_file( filnavn, layer='kartvisning_lysarmatur', driver="GPKG")  

    minOverlappId = set( list(  overlapp['t95_nvdbId']  ))
    if len( skilt2 ) > 0:
        print( 'Fant skiltplunkt med overlappsøk')
        apiOverlappId = set( list(  skilt2['nvdbId']  ))
        diff = minOverlappId.symmetric_difference( apiOverlappId )

#   Lagrer til excel 
# with pd.ExcelWriter( 'alta.xlsx') as writer: 

    #     # Fjerner geometrikolonner fra excel 
    #     col_eldf = [ x for x in list( eldf.columns)  if not 'geom' in x.lower()  ]
    #     col_lys =  [ x for x in list( lysdf.columns) if not 'geom' in x.lower() ]
    #     eldf[ col_eldf ].to_excel( writer, sheet_name='Elektrisk anlegg',  index=False )
    #     lysdf[ col_lys ].to_excel( writer, sheet_name='Lysarmatur',        index=False )

    # overlapp.to_excel( writer, sheet_name='Alta overlapp 95 med 67 Ev6', index=False )
    # skilt.to_excel(    writer, sheet_name='95 Skiltpunkt Ev6 Alta', index=False )


# Skriver til geopackage
lagreGpkg = True
if lagreGpkg: 

    overlapp['geometry'] = overlapp['t95_geometri'].apply( lambda x : wkt.loads( x ))
    minOverlappGdf = gpd.GeoDataFrame( overlapp, geometry='geometry', crs=5973 )
    minOverlappGdf.to_file( 'tunnelskiltpunkt.gpkg', layer='jans_overlapp', driver='GPKG' )

    skilt['geometry'] = skilt['geometri'].apply( lambda x : wkt.loads( x ))
    alleskiltGdf = gpd.GeoDataFrame( skilt, geometry='geometry', crs=5973 )
    alleskiltGdf.to_file( 'tunnelskiltpunkt.gpkg', layer='alleskilt', driver='GPKG' )
   
    skilt2['geometry'] = skilt2['geometri'].apply( lambda x : wkt.loads( x ))
    apiOverlappGdf = gpd.GeoDataFrame( skilt2, geometry='geometry', crs=5973 )
    apiOverlappGdf.to_file( 'tunnelskiltpunkt.gpkg', layer='apioverlapp', driver='GPKG' )

    tunnel['geometry'] = tunnel['geometri'].apply( lambda x : wkt.loads( x ))
    tunnelGdf = gpd.GeoDataFrame( tunnel, geometry='geometry', crs=5973 )
    tunnelGdf.to_file( 'tunnelskiltpunkt.gpkg', layer='tunnel', driver='GPKG' )