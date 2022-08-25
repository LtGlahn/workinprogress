import STARTHER
import pandas as pd
import geopandas as gpd
from shapely import wkt

import nvdbgeotricks
import nvdbapiv3


sok = nvdbapiv3.nvdbFagdata( 595 )
mydf = pd.DataFrame( sok.to_records() )
# mydf.adskilte_lop.value_counts()
# mydf.groupby(  ['Motorvegtype', 'adskilte_lop'] ).agg( {'lengde' : 'sum' } )
# mydf.groupby(  ['Motorvegtype', 'adskilte_lop'] ).agg( {'segmentlengde' : 'sum' } )
tt = mydf.groupby(  ['Motorvegtype', 'adskilte_lop'] ).agg( {'segmentlengde' : 'sum' } )
tt['segmentlengde'] = tt['segmentlengde'] / 1000

# Henter fartsgrense 90, 100 og 110 
sok = nvdbapiv3.nvdbFagdata( 105 )
sok.filter( { 'egenskap' : '2021=2741' } )
mylist = sok.to_records()
sok = nvdbapiv3.nvdbFagdata( 105 )
sok.filter( { 'egenskap' : '2021=5087' } )
mylist.extend( sok.to_records() )
sok = nvdbapiv3.nvdbFagdata( 105 )
sok.filter( { 'egenskap' : '2021=9721' } )
mylist.extend( sok.to_records() )
# Ingen fartsgrense = 120? 
# sok = nvdbapiv3.nvdbFagdata( 105 )
# sok.filter( { 'egenskap' : '2021=19642' } )
# tmp = sok.to_records()
# tmp 
fart = pd.DataFrame( mylist )


mydf['geometry'] = mydf['geometri'].apply( lambda x : wkt.loads(x))
fart['geometry'] = fart['geometri'].apply( lambda x : wkt.loads(x))
fart.drop( columns='relasjoner', inplace=True )
joined = nvdbgeotricks.finnoverlapp( mydf, fart, prefixB='fart_')

joined.rename( columns={'fart_Fartsgrense' : 'Fartsgrense', 'nvdbId' : 'motorveg_nvdbID' }, inplace=True  )


col = ['fylke',
 'kommune',
 'vegkategori',
 'fase',
 'vegnummer',
 'vegsystemreferanse',
 'Motorvegtype',
 'Fartsgrense',
 'typeVeg',
 'adskilte_lop',
 'detaljnivå',
 'veglenkeType',
 'veglenkesekvensid',
 'startposisjon',
 'sluttposisjon',
 'segmentlengde',
 'trafikantgruppe',
 'fart_nvdbId',
 'motorveg_nvdbID']


# mydf.groupby(  ['Motorvegtype', 'adskilte_lop'] ).agg( {'segmentlengde' : 'sum' } )
# mydf.groupby(  ['Motorvegtype', 'adskilte_lop', 'fart_fartsgrense'] ).agg( {'segmentlengde' : 'sum' } )
# mydf.groupby(  ['Motorvegtype', 'adskilte_lop', 'fart_Fartsgrense'] ).agg( {'segmentlengde' : 'sum' } )
# mydf.groupby(  ['Motorvegtype', 'adskilte_lop', 'fart_Fartsgrense'] ).agg( {'segmentlengde' : 'sum' } )
# joined.groupby(  ['Motorvegtype', 'adskilte_lop', 'fart_Fartsgrense'] ).agg( {'segmentlengde' : 'sum' } )
# tt = joined.groupby(  ['Motorvegtype', 'adskilte_lop', 'fart_Fartsgrense'] ).agg( {'segmentlengde' : 'sum' } )
# tt['segmentlengde'] = tt['segmentlengde'] / 1000
# tt
# mydf.groupby(  ['Motorvegtype'] ).agg( {'segmentlengde' : 'sum' } )
# joined.groupby(  ['Motorvegtype'] ).agg( {'segmentlengde' : 'sum' } )
# envegmotorveg = joined[ joined['adskilte_lop'] != 'Mot' ]
# envegmotorveg.groupby(  ['Motorvegtype'] ).agg( {'segmentlengde' : 'sum' } )
# envegmotorveg.groupby(  ['Motorvegtype', 'fart_Fartsgrense'] ).agg( {'segmentlengde' : 'sum' } )
# envegmotorveg.dtypes
# envegmotorveg.veglenkeType.value_counts
# envegmotorveg.veglenkeType.value_counts()
# envegmotorveg = envegmotorveg[ envegmotorveg['veglenkeType'] == 'HOVED' ]
# envegmotorveg.groupby(  ['Motorvegtype', 'typeVeg'] ).agg( {'segmentlengde' : 'sum' } )
# envegmotorveg.groupby(  ['Motorvegtype', 'typeVeg', 'fart_Fartsgrense'] ).agg( {'segmentlengde' : 'sum' } )
# tt = envegmotorveg.groupby(  ['Motorvegtype', 'typeVeg', 'fart_Fartsgrense'] ).agg( {'segmentlengde' : 'sum' } )
# ta = tt.reset_index()
# ?nvdbgeotricks.skrivexcel
# ta
# nvdbgeotricks.skrivexcel( 'temp_motorveger', envegmotorveg )
# nvdbgeotricks.skrivexcel( 'temp_motorveger', ta )
# envegmotorveg.groupby(  ['Motorvegtype','fart_Fartsgrense'] ).agg( {'segmentlengde' : 'sum' } )
# ta
# envegmotorveg.groupby(  ['Motorvegtype','fart_Fartsgrense'] ).agg( {'segmentlengde' : 'sum' } )
# envegmotorveg[ motorveg['typeVeg'] != 'Rampe'] .groupby(  ['Motorvegtype','fart_Fartsgrense'] ).agg( {'segmentlengde' : 'sum' } )
# envegmotorveg[ envegmotorveg['typeVeg'] != 'Rampe'] .groupby(  ['Motorvegtype','fart_Fartsgrense'] ).agg( {'segmentlengde' : 'sum' } )
# envegmotorveg[ envegmotorveg['typeVeg'] == 'Rampe'] .groupby(  ['Motorvegtype','fart_Fartsgrense'] ).agg( {'segmentlengde' : 'sum' } )
# %hist