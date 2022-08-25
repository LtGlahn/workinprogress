import requests
import pandas as pd
from shapely import geometry
import geopandas as gpd


data = requests.get( 'https://ws.geonorge.no/stedsnavn/v1/navn?sok=norefjell*&utkoordsys=5973&treffPerSide=100&side=1' ).json()
sted = pd.DataFrame( data['navn'] )
sted['kommunenr'] = sted['kommuner'].apply( lambda x : [ y['kommunenummer'] for y in x ] )
sted['kommunenavn'] = sted['kommuner'].apply( lambda x : [ y['kommunenavn'] for y in x ] )
sted['geometry'] = sted['representasjonspunkt'].apply( lambda x : geometry.Point( [ x['øst'], x['nord'] ] ) )
mittsted = gpd.GeoDataFrame( sted, geometry='geometry', crs=5973 )
mittsted['kommunenr'] = mittsted['kommunenr'].apply( lambda x : ','.join( x ) )
mittsted['kommunenavn'] = mittsted['kommunenavn'].apply( lambda x : ','.join( x ) )
mittsted.drop( columns=['kommuner', 'fylker', 'representasjonspunkt'], inplace=True )

mittsted.to_file( 'norefjell-stedsnavn.gpgk', layer='stedsnavn', driver='GPKG' )