import requests 

from shapely import wkt 
import pandas as pd
import geopandas as gpd 

import STARTHER
import nvdbapiv3 

if __name__ == '__main__': 

    kontraktsomr = requests.get( 'https://nvdbapiles-v3.atlas.vegvesen.no/omrader/kontraktsomrader.json').json()
    

    for kontrakt in kontraktsomr: 

        veg = nvdbapiv3.nvdbVegnett()
        veg.filter( { 'kontraktsomrade' : kontrakt['navn'], 'vegsystemreferanse' : 'Ea,Ra,Fa' })
        mydf = pd.DataFrame( veg.to_records())
        if len( mydf ) > 0: 
            print( f"{kontrakt['navn']} har anleggsveger " )

            for objType in [ 5, 24, 60, 95, 96, 80, 843 ]: 
                sok = nvdbapiv3.nvdbFagdata( objType )
                sok.filter( { 'vegsystemreferanse' : 'Ea,Ra,Fa'})
                mydf = pd.DataFrame( sok.to_records())
                if len( mydf ) > 0: 
                    print(f"\t{kontrakt['navn']} har {len(mydf)} vegsegmenter med objekttype {objType} på anleggsveg" )


