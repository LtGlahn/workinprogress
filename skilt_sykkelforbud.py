import json 

import pandas as pd
import geopandas as gpd
import numpy as np
from shapely import wkt 


import lokal_STARTHER
import nvdbapiv3 


if __name__ == '__main__': 

    # Henter tunneller, der sykkelforbud bor 
    skiltsok = nvdbapiv3.nvdbFagdata( 96 )
    skiltsok.filter( { 'egenskap' : '(5530=7655 OR 5530=7656 OR 5530=7652 OR 5530=7657 OR 5530=12147 OR 5530=7812 OR 5530=9792)'  })

    # 306.3 - Forbudt for traktor og for motorredskap konstruert for fart mindre enn 40 km/t 7652
    # 306.6 - Forbudt for syklende 7655
    # 306.7 - Forbudt for gående 7656
    # 306.8 - Forbudt for gående og syklende 7657
    # 560.2 - Forbudt for gående og syklende på motorveg og motortrafikkveg 12147
    # U808.50b - Tekst, forbudt for gående og syklende 7812
    # U808.50n - Tekst, forbode for gåande og syklande 9792

    resultat = pd.DataFrame( skiltsok.to_records(  ))


    resultat['geometry'] = resultat['geometri'].apply( lambda x : wkt.loads( x ))

    resultatGdf = gpd.GeoDataFrame( resultat, geometry='geometry', crs=25833 )  
    resultatGdf.drop( columns=['geometri', 'relasjoner'], inplace=True )
    resultatGdf.to_file( 'tunnelsykkelforbud.gpkg', layer='forbudsskilt', driver='GPKG')


# https://vegkart.atlas.vegvesen.no/#kartlag:geodata/@-35933,6556674,13/hva:~(~(filter~(~(operator~'*3d~type_id~5530~verdi~(~7655))~(operator~'*3d~type_id~5530~verdi~(~7656))~(operator~'*3d~type_id~5530~verdi~(~7657)))~id~96))/hvor:~(vegsystemreferanse~(~'RV444))/vegnett:~'metrering+~()

