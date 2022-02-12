"""
Finner tidsutvikling for diverse modulvogntog-relaterte datasett


"""
from datetime import datetime

import geopandas as gpd
import pandas as pd
from copy import deepcopy 

import STARTHER
import nvdbapiv3
import nvdbgeotricks


def finndifferanser( sok, kolonnenavn): 
    """
    Henter data fra NVDB for to ulike tidspunkt og returnerer lengder og differanser


    """

    t1 = '2021-01-01'
    t2 = '2021-12-15'
    lengdenavn1     = ' '.join( [ kolonnenavn, t1, '[km]'])
    lengdenavn2     = ' '.join( [ kolonnenavn, t2, '[km]'])
    differansenavn  = ' '.join( [ 'Differanse', kolonnenavn,  '[km]' ] )

    sok.filter( {'tidspunkt' : t1})
    bk1 = pd.DataFrame( sok.to_records() )

    bk1 = bk1[ bk1['vegkategori'] != 'F']
    tall1 = bk1.groupby( ['fylke', 'vegkategori']).agg( {'segmentlengde' : 'sum'}) # .reset_index()
    tall1['segmentlengde'] = tall1['segmentlengde'] / 1000
    tall1.rename( columns={'segmentlengde' : lengdenavn1}, inplace=True )

    sok.refresh()
    sok.filter( {'tidspunkt' : t2})
    bk2 = pd.DataFrame( sok.to_records() )
    bk2 = bk2[ bk2['vegkategori'] != 'P'  ]
    tall2 = bk2.groupby( ['fylke', 'vegkategori']).agg( {'segmentlengde' : 'sum'}) # .reset_index()
    tall2['segmentlengde'] = tall2['segmentlengde'] / 1000
    tall2.rename( columns={'segmentlengde' : lengdenavn2}, inplace=True )


    tall3 = tall1.join( tall2, how='outer' )
    tall3.fillna( 0, inplace=True )
    tall3[differansenavn] = tall3[lengdenavn2] - tall3[lengdenavn1]

    return tall3 

    # from IPython import embed; embed() # For debugging 



if __name__ == '__main__': 

    t0 = datetime.now()

    # Modulvogntog 
    sok = nvdbapiv3.nvdbFagdata( 889)
    # sok.filter( {'fylke' : [42,11] })
    sok.filter({ 'adskiltelop' :  'med,nei', 'sideanlegg' :  'false'  })
    bkmodul= finndifferanser( sok, 'BK Modulvt')

    # Modulvogntog på BK tømmertransport 
    sok = nvdbapiv3.nvdbFagdata( 900 )
    # sok.filter( {'fylke' : [42,11] })
    sok.filter({ 'adskiltelop' :  'med,nei', 'sideanlegg' :  'false'  })
    sok.filter( {'egenskap' : '(12057=20911)'} ) # Tillatt for modulvogntog 1 og 2 med sporingskrav = Ja 
    tommermodul = finndifferanser( sok, 'Bk tømmermodul')

    # Lange og tunge tømmertransporter egenskap=(10909=18238) AND (10921=18269)
    sok = nvdbapiv3.nvdbFagdata( 900 )
    # sok.filter( {'fylke' : [42,11] })
    sok.filter({ 'adskiltelop' :  'med,nei', 'sideanlegg' :  'false'  })
    sok.filter( {'egenskap' : '(10909=18238) AND (10921=18269) AND (10897=18212)'} ) # BK10-50,  60 tonn og 24m.  
    digertommer = finndifferanser( sok, 'Tømmer Bk10-60 24m')

    rapport1 = bkmodul.join( tommermodul, how='outer')
    rapport1.fillna( 0, inplace=True )

    rapport2 = rapport1.join( digertommer, how='outer').reset_index()
    nvdbgeotricks.skrivexcel( 'test-aarsrapport.xlsx', rapport2 )

    print(f"Total kjøretid:  {datetime.now()-t0}")
