"""
Endrer sekkepost-verdier for en kommune (i første omgang kun for BK tømmertransport, uoffisiell)

Opprinnelig behov: Endre BK-sekkepost for tømmertransport,uoffisiell for Åseral kommune 

Kan sikkert generaliseres (etter hvert)
"""
from http.cookiejar import MozillaCookieJar
import geopandas as gpd 
import pandas as pd 

import STARTHER
from nvdbapiv3 import  nvdbFagdata, apiforbindelse 
import skrivnvdb


from skrivkommunalBK import finnSekkepost



if __name__ == '__main__': 

    # dagens_sekkepost = finnSekkepost( 4224, inkluder_offisiell=False, inkluder_uoffisiell=True )
    # skrivnvdb.fagdata2skrivemal( dagens_sekkepost['tommer'], operasjon='registrer')
    # {'typeId': {'typeId': 901,
    # 'egenskaper': 
    # {'typeId': 10898, 'verdi': ['Bk10 - 50 tonn']},
    #  {'typeId': 10910, 'verdi': ['19,50']},
    #  {'typeId': 12058, 'verdi': ['Nei']}]
    # Pluss mangler strekninsbeskrivelse (10916=null )

    mittfilter =  {   'egenskap' : '(10898=18205) AND (10910=18425) AND (12058=20914) AND (10916=null)' }    
    mittfilter['kommune'] = 4224 
    mittfilter['vegsystemreferanse'] = 'Kv'

    forb = apiforbindelse()
    forb.login( miljo='testles', pw='mass3Fine.data')
    nvdbsok = nvdbFagdata( 901 )
    nvdbsok.forbindelse = forb
    nvdbsok.filter( mittfilter )
    dd = [ etobj for etobj in nvdbsok ]
    junk = skrivnvdb.fagdata2skrivemal( dd, kunDisseEgenskapene=[10910] )

    
