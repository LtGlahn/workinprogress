"""
Finner vegnett som mangler metrering 
"""
import pandas as pd
import geopandas as gpd 
from shapely import wkt 

import STARTHER
import nvdbapiv3 

v = nvdbapiv3.nvdbVegnett()
# v.filter( {'kommune' : 5001 })
v.filter( {'detaljniva' : 'VT,VTKB' })

utenmetrering = []
for seg in v: 
    if not 'vegsystemreferanse' in seg: 
        utenmetrering.append(  nvdbapiv3.flatutvegnettsegment(seg )  )
    else: 
        if 'strekning' in seg['vegsystemreferanse']:
            pass
        elif 'kryssdel' in seg['vegsystemreferanse']:
            pass 
        elif 'sideanlegg' in seg['vegsystemreferanse']:
            pass
        else: 
            utenmetrering.append( nvdbapiv3.flatutvegnettsegment(seg )  )

if len( utenmetrering ) > 0: 
    print( f"fant {len(utenmetrering)} vegsegmenter uten metrering")
    resultat = pd.DataFrame( utenmetrering )

    resultat['geometry'] = resultat['geometri'].apply( lambda x : wkt.loads( x ))

    resultatGdf = gpd.GeoDataFrame( resultat, geometry='geometry', crs=25833 )  
    resultatGdf.drop( columns=['geometri' ], inplace=True )
    resultatGdf.to_file( 'manglermetrering.gpkg', layer='manglermetrering', driver='GPKG')

else: 
    print( "fant ingen veger uten metrering")