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

    t1 = '2020-12-19'
    t2 = '2021-10-16'
    lengdenavn1     = ' '.join( [ kolonnenavn, t1, '[km]'])
    lengdenavn2     = ' '.join( [ kolonnenavn, t2, '[km]'])
    differansenavn  = ' '.join( [ 'Differanse', kolonnenavn,  '[km]' ] )

    sok.filter( {'tidspunkt' : t1})
    bk1 = pd.DataFrame( sok.to_records() )

    tall1 = bk1.groupby( ['fylke', 'vegkategori']).agg( {'segmentlengde' : 'sum'}) # .reset_index()
    tall1['segmentlengde'] = tall1['segmentlengde'] / 1000
    tall1.rename( columns={'segmentlengde' : lengdenavn1}, inplace=True )

    helelandet1 = bk1.groupby( ['vegkategori']).agg( {'segmentlengde' : 'sum'})
    helelandet1['segmentlengde'] = helelandet1['segmentlengde'] / 1000
    helelandet1.rename( columns={'segmentlengde' : lengdenavn1}, inplace=True )

    sok.refresh()
    sok.filter( {'tidspunkt' : t2})
    bk2 = pd.DataFrame( sok.to_records() )
    tall2 = bk2.groupby( ['fylke', 'vegkategori']).agg( {'segmentlengde' : 'sum'}) 
    tall2['segmentlengde'] = tall2['segmentlengde'] / 1000
    tall2.rename( columns={'segmentlengde' : lengdenavn2}, inplace=True )

    helelandet2 = bk2.groupby( ['vegkategori']).agg( {'segmentlengde' : 'sum'})
    helelandet2['segmentlengde'] = helelandet2['segmentlengde'] / 1000
    helelandet2.rename( columns={'segmentlengde' : lengdenavn2}, inplace=True )

    tall3 = tall1.join( tall2, how='outer' )
    # tall3.fillna( 0, inplace=True ) # Trenger ikke erstatte NaN, det blir blanke celler i excel sluttprodukt
    tall3[differansenavn] = tall3[lengdenavn2] - tall3[lengdenavn1]

    helelandet3 = helelandet1.join( helelandet2, how='outer')
    helelandet3[differansenavn] = helelandet3[lengdenavn2] - helelandet3[lengdenavn1]

    # from IPython import embed; embed() # For debugging 

    return (tall3, helelandet3)  


if __name__ == '__main__': 

    t0 = datetime.now()

    # Modulvogntog 
    sok = nvdbapiv3.nvdbFagdata( 889)
    sok.filter({ 'adskiltelop' :  'med,nei', 'sideanlegg' :  'false'  })
    (bkmodulFylke, bkmodulNorge ) = finndifferanser( sok, 'BK Modulvt')

    # Modulvogntog på BK tømmertransport 
    sok = nvdbapiv3.nvdbFagdata( 900 )
    sok.filter({ 'adskiltelop' :  'med,nei', 'sideanlegg' :  'false'  })
    sok.filter( {'egenskap' : '(12057=20911)'} ) # Tillatt for modulvogntog 1 og 2 med sporingskrav = Ja 
    (tommermodulFylke, tommermodulNorge)  = finndifferanser( sok, 'Bk tømmermodul')

    # Lange og tunge tømmertransporter egenskap=(10909=18238) AND (10921=18269)
    sok = nvdbapiv3.nvdbFagdata( 900 )
    sok.filter({ 'adskiltelop' :  'med,nei', 'sideanlegg' :  'false'  })
    sok.filter( {'egenskap' : '(10909=18238) AND (10921=18269) AND (10897=18212)'} ) # BK10-50,  60 tonn og 24m.  
    (digertommerFylke,digertommerNorge) = finndifferanser( sok, 'Tømmer Bk10-60 24m')

    # Slår sammen til en samlet tabell basert på index = fylke, vegkategori 
    rapport1Fylke = bkmodulFylke.join( tommermodulFylke, how='outer')
    rapport2Fylke = rapport1Fylke.join( digertommerFylke, how='outer').reset_index().round(1)

    rapport1Norge = bkmodulNorge.join( tommermodulNorge, how='outer')
    rapport2Norge = rapport1Norge.join( digertommerNorge, how='outer').reset_index().round(1)

    nvdbgeotricks.skrivexcel( 'test-aarsrapport.xlsx', [rapport2Norge, rapport2Fylke], 
                                     sheet_nameListe=['Per vegkategori', 'Per fylke og vegkategori'] )

    print(f"Total kjøretid:  {datetime.now()-t0}")
