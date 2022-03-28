import pandas as pd


import STARTHER
import nvdbgeotricks
import nvdbapiv3



s = nvdbapiv3.nvdbFagdata( 905)
# s.filter( { 'kommune' : 3007 } )
s.forbindelse.login( miljo='prodles' )

# test = s.forbindelse.les( '/vegobjekter/905/952205504', params={'inkluder' : 'alle' } ).json()
# data = nvdbapiv3.nvdbfagdata2records( [ test ] )

data = []
nvdbId = set( )
for ettobj in s: 
    for seg in ettobj['vegsegmenter']: 
        if not 'strekning' in seg['vegsystemreferanse']: 
            
            if 'vegsystem' in seg['vegsystemreferanse'] and 'vegkategori' in seg['vegsystemreferanse']['vegsystem'] and seg['vegsystemreferanse']['vegsystem']['vegkategori'] in ['P', 'S' ]:
                pass
            elif ettobj['id'] not in nvdbId: 
                data.append( ettobj )
                nvdbId.add( ettobj['id'])

data2 = nvdbapiv3.nvdbfagdata2records( data )
nvdbgeotricks.records2gpkg( data2, 'vegliste_feilvegnett.gpkg', 'bk905' )
mydf = pd.DataFrame( data2 )

mydf2 = mydf[ mydf['trafikantgruppe'].isnull() ].copy()

mydf2['vref'].fillna('', inplace=True)
mydf2['typeVeg'].fillna('', inplace=True)
mydf2['Strekningsbeskrivelse'].fillna('', inplace=True)

result = mydf2.groupby( [ 'kommune', 'vref', 'Strekningsbeskrivelse', 'typeVeg' ] ).agg( { 'segmentlengde' : 'sum', 'nvdbId' : 'nunique'}).reset_index()
result.rename( columns={ 'nvdbId' : 'antall', 'segmentlengde' : 'Lengde (m)' }, inplace=True)


result_enkelt = mydf2.groupby( [ 'kommune' ] ).agg( { 'segmentlengde' : 'sum', 'nvdbId' : 'nunique'}).reset_index()
result_enkelt.rename( columns={ 'nvdbId' : 'antall', 'segmentlengde' : 'Lengde (m)' }, inplace=True)

col = ['nvdbId', 'Bruksklasse', 'Bruksklasse vinter', 'Maks vogntoglengde', 'Strekningsbeskrivelse',  'Merknad', 'vref', 'trafikantgruppe', 'typeVeg' ]