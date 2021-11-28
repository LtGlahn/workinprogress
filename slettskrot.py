from copy import deepcopy 
import pdb 

from shapely import wkt 
from shapely.ops import unary_union
import pandas as pd 
import geopandas as gpd 
from datetime import datetime

import lokal_STARTHER
import nvdbapiv3
import fiksBK_feilvegkat


if __name__ == '__main__': 

    t0 = datetime.now( )
    minefilter = { 'kartutsnitt' : '230367.375,6627530.373,232732.755,6630768.879' }    

    tm = nvdbapiv3.nvdbFagdata(540 )
    tm.filter( { 'tidspunkt' : '2019-12-31' })
    # tm.filter( minefilter)

    mindf = pd.DataFrame( tm.to_records( ) ) 

    mindf['geometry'] = mindf['geometri'].apply( wkt.loads )
    minGdf = gpd.GeoDataFrame( mindf, geometry='geometry', crs=25833 )
    minGdf.to_file( 'trafikkmengde.gpkg', layer='trafikkmengde2019-12-31', driver="GPKG")  

    tidsbruk = datetime.now( ) - t0 
    print( "tidsbruk:", tidsbruk.total_seconds( ), "sekunder")