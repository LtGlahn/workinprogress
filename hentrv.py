from copy import deepcopy 
import pdb 

from shapely import wkt 
from shapely.ops import unary_union
import pandas as pd 
import geopandas as gpd 
from datetime import datetime

import STARTHER
import nvdbapiv3
# import fiksBK_feilvegkat


if __name__ == '__main__': 

    t0 = datetime.now( )
    vref532filter = { 'kartutsnitt' : '-53074.72,6507486.16,-13880.70,6570928.63', 'egenskap' : '4566= 5492 OR 4566=5493' }    
    idagfilter = { 'kartutsnitt' : vref532filter['kartutsnitt'], 'vegsystemreferanse' : 'Rv,Ev' }    


    idag = nvdbapiv3.nvdbVegnett(  )
    idag.filter( idagfilter )


    mindf = pd.DataFrame( idag.to_records( ) ) 

    mindf['geometry'] = mindf['geometri'].apply( wkt.loads )
    mindf.drop( columns=[ 'geometri'], inplace=True)

    minGdf = gpd.GeoDataFrame( mindf, geometry='geometry', crs=5973  )
    minGdf.to_file( 'dagens_riksveger.gpkg', layer='europa_og_riksveg', driver="GPKG")  

    tidsbruk = datetime.now( ) - t0 
    print( "tidsbruk:", tidsbruk.total_seconds( ), "sekunder")